"""
T043-T050: Personalization endpoint router with SSE streaming.

Provides GET /personalize endpoint that streams AI-personalized content
based on user proficiency levels using Server-Sent Events (SSE).

Pattern mirrors summarize.py but adds programmingLevel and aiLevel parameters.
"""

import json
import logging
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse
from src.services import openai_agent

router = APIRouter()
logger = logging.getLogger(__name__)


# T044: GET /personalize endpoint with proficiency query params
@router.get("/personalize")
async def personalize_content(
    pageId: str = Query(..., description="Unique identifier for the content page"),
    content: str = Query(..., description="Full page content text to personalize"),
    token: str = Query(..., description="Authentication token (dummy_token prefix)"),
    programmingLevel: str = Query(..., description="User's programming proficiency (Novice/Beginner/Intermediate/Expert)"),
    aiLevel: str = Query(..., description="User's AI knowledge proficiency (Novice/Beginner/Intermediate/Expert)"),
):
    """
    Stream AI-personalized content tailored to user's proficiency levels.
    
    Uses Server-Sent Events (SSE) to stream personalized content as it's generated,
    providing real-time feedback to the user.
    
    Query Parameters:
        pageId: Unique identifier for the content page
        content: Full page content text to personalize
        token: Authentication token (must start with 'dummy_token')
        programmingLevel: Programming proficiency (Novice/Beginner/Intermediate/Expert)
        aiLevel: AI knowledge proficiency (Novice/Beginner/Intermediate/Expert)
    
    Returns:
        StreamingResponse: SSE stream of personalized content chunks
        
    Raises:
        HTTPException 401: If token is missing or invalid
        HTTPException 400: If content is too short or proficiency levels are invalid
    """
    # T103: Enhanced request logging for debugging
    token_prefix = token[:20] if token else "None"
    logger.info(
        f"Personalization request - pageId: {pageId}, "
        f"Programming: {programmingLevel}, AI: {aiLevel}, "
        f"Token: {token_prefix}..., Content length: {len(content)} chars"
    )
    
    # T045: Token validation
    if not token:
        logger.warning(f"Personalization request missing token for pageId: {pageId}")
        raise HTTPException(status_code=401, detail="Authentication token required")
    
    if not token.startswith("dummy_token"):
        logger.warning(f"Invalid token format for pageId {pageId}: {token[:20]}...")
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    
    # T105: Content length validation (reject if >50,000 chars per API contract)
    if len(content) < 100:
        logger.warning(f"Content too short for pageId {pageId}: {len(content)} characters")
        raise HTTPException(
            status_code=400,
            detail="Content must be at least 100 characters for personalization"
        )
    
    if len(content) > 50000:
        logger.warning(f"Content too long for pageId {pageId}: {len(content)} characters")
        raise HTTPException(
            status_code=400,
            detail="Content must not exceed 50,000 characters for personalization"
        )
    
    # T047: Validate proficiency levels
    valid_levels = ["Novice", "Beginner", "Intermediate", "Expert"]
    
    if programmingLevel not in valid_levels:
        logger.warning(f"Invalid programming level for pageId {pageId}: {programmingLevel}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid programmingLevel. Must be one of: {', '.join(valid_levels)}"
        )
    
    if aiLevel not in valid_levels:
        logger.warning(f"Invalid AI level for pageId {pageId}: {aiLevel}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid aiLevel. Must be one of: {', '.join(valid_levels)}"
        )
    
    # T104: Rate limiting consideration
    # TODO: Future enhancement - implement rate limiting strategy:
    # - Option 1: FastAPI Limiter (https://github.com/long2ice/fastapi-limiter) with Redis backend
    # - Option 2: slowapi (https://github.com/laurents/slowapi) for in-memory rate limiting
    # - Suggested limits: 10 requests/minute per user, 100 requests/hour per user
    # - Track by token or IP address
    # - Return 429 (Too Many Requests) when limit exceeded
    
    # T048: Define event stream generator
    async def event_stream():
        """
        Generate Server-Sent Events stream for personalized content.
        
        Yields SSE-formatted events containing personalized content chunks.
        Follows SSE format: data: {JSON}\n\n
        """
        try:
            # T049: Stream chunks from generate_personalized_content()
            async for chunk in openai_agent.generate_personalized_content(
                content=content,
                page_id=pageId,
                programming_level=programmingLevel,
                ai_proficiency=aiLevel
            ):
                event_data = json.dumps({
                    "chunk": chunk,
                    "done": False
                })
                yield f"data: {event_data}\n\n"
            
            # Send completion event
            completion_data = json.dumps({
                "chunk": "",
                "done": True
            })
            yield f"data: {completion_data}\n\n"
            
            logger.info(f"Personalization stream completed for pageId: {pageId}")
            
        except Exception as e:
            logger.error(f"Error during personalization stream for pageId {pageId}: {str(e)}")
            # Send error event
            error_data = json.dumps({
                "chunk": "",
                "done": True,
                "error": str(e)
            })
            yield f"data: {error_data}\n\n"
    
    # Return SSE streaming response
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )
