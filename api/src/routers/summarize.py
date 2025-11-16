"""
Summarization API endpoints
"""
import logging
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse
from src.services import openai_agent
from src.models.schemas import ErrorResponse
import json

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/summarize")
async def summarize_content(
    pageId: str = Query(..., description="Unique identifier for the content page"),
    token: str = Query(..., description="Authentication token"),
    content: str = Query(..., description="Page content to summarize"),
):
    """
    Generate streaming summary for content page using Server-Sent Events (SSE).
    
    Validates authentication token, retrieves content, and streams AI-generated summary.
    """
    logger.info(f"Summarize request for pageId: {pageId}")
    logger.info(f"Content length: {len(content)} characters")
    logger.info(f"Content preview: {content[:200]}...")
    
    # Auth token validation (dummy implementation)
    if not token or token.strip() == "":
        logger.warning(f"Missing auth token for pageId: {pageId}")
        raise HTTPException(status_code=401, detail="Missing or invalid authentication token")
    
    # For dummy implementation, accept any token
    # Future: Implement proper JWT validation with SSO
    if not token.startswith("dummy_token"):
        logger.warning(f"Invalid token format for pageId: {pageId}")
        # Still accept for demo purposes
        pass
    
    # PageId validation
    if not pageId or len(pageId) < 3:
        logger.warning(f"Invalid pageId: {pageId}")
        raise HTTPException(status_code=400, detail="Invalid page identifier")
    
    # Content validation
    if not content or len(content) < 50:
        logger.warning(f"Content too short for pageId: {pageId}")
        raise HTTPException(status_code=400, detail="Content too short to summarize")
    
    async def event_stream():
        """Generate Server-Sent Events stream"""
        try:
            # Stream summary chunks
            async for chunk in openai_agent.generate_summary(content, pageId):
                # Format as SSE
                event_data = json.dumps({"chunk": chunk, "done": False})
                yield f"data: {event_data}\n\n"
            
            # Send completion event
            completion_data = json.dumps({"chunk": "", "done": True})
            yield f"data: {completion_data}\n\n"
            
        except Exception as e:
            logger.error(f"Error in event_stream for pageId {pageId}: {str(e)}")
            error_data = json.dumps({"chunk": "", "done": True, "error": str(e)})
            yield f"data: {error_data}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )
