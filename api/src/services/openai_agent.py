"""
OpenAI Agent Service - integrates with OpenAI Agents SDK for summary generation
"""

import os
import logging
from typing import AsyncGenerator
from agents import (
    Runner,
    Agent,
    OpenAIChatCompletionsModel,
    SQLiteSession,
    set_tracing_disabled,
)
from openai import AsyncOpenAI
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

logger = logging.getLogger(__name__)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    logger.error(
        "GOOGLE_API_KEY not found in environment variables. Please set it in .env file."
    )
    raise ValueError(
        "GOOGLE_API_KEY is required. Please:\n"
        "1. Copy api/.env.example to api/.env\n"
        "2. Add your Google API key to GOOGLE_API_KEY in .env file"
    )

set_tracing_disabled(False)

external_client = AsyncOpenAI(
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=GOOGLE_API_KEY,
)

model = OpenAIChatCompletionsModel(
    openai_client=external_client,
    model="gemini-2.0-flash",
)


async def generate_summary(content: str, page_id: str) -> AsyncGenerator[str, None]:
    """
    Generate AI-powered summary of content using OpenAI Agents SDK.

    Uses Runner.run_streamed() with Agent for streaming responses with
    proportional summary length calculation (30-35% of original, 150-500 word bounds).

    Args:
        content: Full page content text to summarize
        page_id: Unique identifier for the content page (for logging)

    Yields:
        str: Chunks of summary text as they are generated

    Raises:
        Exception: If OpenAI Agents SDK call fails
    """
    logger.info(f"Starting summary generation for page_id: {page_id}")

    # Calculate word count for proportional summary
    word_count = len(content.split())
    target_word_count = max(150, min(500, int(word_count * 0.225)))  # 20-25%, bounded

    logger.info(
        f"Content word count: {word_count}, Target summary: {target_word_count} words"
    )

    instructions = f"""You are an expert content summarizer for educational material. Create clear, well-structured summaries using markdown formatting.

Requirements:
- Target length: {target_word_count} words (±10%)
- Use markdown formatting:
  - ## for section headings
  - **bold** for key terms
  - - for bullet points
  - Single line break between paragraphs
- Structure: Brief overview, then key concepts with headings
- Preserve technical accuracy
- Use clear, professional language
- Do not add information not in original text"""

    try:
        # Create Agent instance
        agent = Agent(
            name="Content Summarizer",
            instructions=instructions,
            model=model,
        )

        # Create in-memory session (no file needed)
        session = SQLiteSession(session_id=page_id)  # Defaults to in-memory

        # Run agent with streaming
        result = Runner.run_streamed(
            starting_agent=agent,
            input=f"Summarize this content:\n\n{content}",
            session=session,
        )

        # Stream response chunks - iterate over events
        async for event in result.stream_events():
            # Log event type for debugging
            logger.debug(f"Event type: {event.type}")

            # Handle different event types for text streaming
            if event.type == "raw_response_event":
                # Check various possible delta locations in the event
                delta_text = None

                if hasattr(event, "data"):
                    # Try event.data.delta
                    if hasattr(event.data, "delta") and event.data.delta:
                        delta_text = event.data.delta
                    # Try event.data.content if delta not available
                    elif hasattr(event.data, "content") and event.data.content:
                        delta_text = event.data.content

                # Direct event.delta check
                if not delta_text and hasattr(event, "delta") and event.delta:
                    delta_text = event.delta

                # Direct event.content check
                if not delta_text and hasattr(event, "content") and event.content:
                    delta_text = event.content

                if delta_text:
                    logger.debug(f"Yielding delta: {delta_text[:50]}...")
                    yield delta_text

        logger.info(f"Summary generation completed for page_id: {page_id}")

    except Exception as e:
        logger.error(f"Error generating summary for page_id {page_id}: {str(e)}")
        raise


# T037-T042: Separate personalization agent
async def generate_personalized_content(
    content: str, page_id: str, programming_level: str, ai_proficiency: str
) -> AsyncGenerator[str, None]:
    """
    Generate AI-personalized content based on user proficiency levels.

    Uses separate Agent instance (Content Personalizer) with proficiency-specific
    instructions to tailor content complexity to user's programming experience
    and AI knowledge.

    Args:
        content: Full page content text to personalize
        page_id: Unique identifier for the content page
        programming_level: User's programming proficiency (Novice/Beginner/Intermediate/Expert)
        ai_proficiency: User's AI knowledge proficiency (Novice/Beginner/Intermediate/Expert)

    Yields:
        str: Chunks of personalized content as they are generated

    Raises:
        Exception: If OpenAI Agents SDK call fails
    """
    logger.info(
        f"Starting personalization for page_id: {page_id}, Programming: {programming_level}, AI: {ai_proficiency}"
    )

    # T039: Build proficiency-specific instructions
    instructions = build_personalization_instructions(programming_level, ai_proficiency)

    try:
        # T038: Create separate Agent instance (Content Personalizer)
        agent = Agent(
            name="Content Personalizer",
            instructions=instructions,
            model=model,
        )

        # T040: Construct session_id with proficiency levels for context isolation
        session_id = f"{page_id}_{programming_level}_{ai_proficiency}"
        session = SQLiteSession(session_id=session_id)

        # T041: Implement streaming with Runner.run_streamed()
        result = Runner.run_streamed(
            starting_agent=agent,
            input=f"Personalize this content for the user:\n\n{content}",
            session=session,
        )

        # Stream response chunks
        async for event in result.stream_events():
            logger.debug(f"Event type: {event.type}")

            if event.type == "raw_response_event":
                delta_text = None

                if hasattr(event, "data"):
                    if hasattr(event.data, "delta") and event.data.delta:
                        delta_text = event.data.delta
                    elif hasattr(event.data, "content") and event.data.content:
                        delta_text = event.data.content

                if not delta_text and hasattr(event, "delta") and event.delta:
                    delta_text = event.delta

                if not delta_text and hasattr(event, "content") and event.content:
                    delta_text = event.content

                if delta_text:
                    logger.debug(f"Yielding personalized delta: {delta_text[:50]}...")
                    yield delta_text

        logger.info(f"Personalization completed for page_id: {page_id}")

    except Exception as e:
        logger.error(
            f"Error generating personalized content for page_id {page_id}: {str(e)}"
        )
        raise


def build_personalization_instructions(
    programming_level: str, ai_proficiency: str
) -> str:
    """
    Build proficiency-specific instructions for the personalization agent.

    Decision 5 from research.md: Level-specific instruction templates

    Args:
        programming_level: Novice, Beginner, Intermediate, or Expert
        ai_proficiency: Novice, Beginner, Intermediate, or Expert

    Returns:
        str: Tailored instructions for the agent
    """

    # Define unified reader personas
    personas = {
        (
            "Novice",
            "Novice",
        ): "a complete beginner to both programming and AI. Use very simple language and everyday analogies throughout. Explain all technical terms. Focus on 'what' and 'why' before 'how'.",
        (
            "Novice",
            "Beginner",
        ): "new to programming but has heard about AI tools. Keep programming explanations very simple with analogies, but you can mention AI tools and concepts directly without over-explaining them.",
        (
            "Novice",
            "Intermediate",
        ): "new to programming but comfortable with AI concepts. Simplify programming explanations heavily with analogies, while using proper AI terminology naturally (agents, prompts, models).",
        (
            "Novice",
            "Expert",
        ): "new to programming but an AI expert. Use beginner-friendly programming analogies while freely discussing advanced AI patterns, agent architectures, and prompt engineering.",
        (
            "Beginner",
            "Novice",
        ): "has basic coding knowledge but new to AI. Use simple programming examples and syntax, but explain AI concepts from first principles (what agents are, how they help).",
        (
            "Beginner",
            "Beginner",
        ): "a beginner in both programming and AI. Use clear code examples and straightforward AI tool explanations. Balance simplicity with building understanding.",
        (
            "Beginner",
            "Intermediate",
        ): "a beginner programmer comfortable with AI tools. Keep programming examples simple, but reference AI frameworks and concepts naturally.",
        (
            "Beginner",
            "Expert",
        ): "a beginner programmer but an AI expert. Use basic programming explanations while discussing advanced AI agent patterns and architectures.",
        (
            "Intermediate",
            "Novice",
        ): "an experienced programmer new to AI. Use standard programming terminology and patterns freely, but explain AI concepts from scratch.",
        (
            "Intermediate",
            "Beginner",
        ): "an experienced programmer learning AI. Reference programming best practices normally while explaining AI tools and concepts clearly.",
        (
            "Intermediate",
            "Intermediate",
        ): "experienced in both programming and AI. Use technical terminology naturally for both domains. Focus on practical integration.",
        (
            "Intermediate",
            "Expert",
        ): "an experienced programmer and AI expert. Use standard programming terminology while diving deep into AI agent orchestration and advanced patterns.",
        (
            "Expert",
            "Novice",
        ): "a senior developer new to AI. Discuss architectural patterns and advanced programming freely, but introduce AI concepts from first principles.",
        (
            "Expert",
            "Beginner",
        ): "a senior developer learning AI. Use advanced programming terminology while explaining AI tools and workflows clearly.",
        (
            "Expert",
            "Intermediate",
        ): "a senior developer comfortable with AI. Discuss architecture, performance, and trade-offs naturally while referencing AI frameworks and patterns.",
        (
            "Expert",
            "Expert",
        ): "a senior developer and AI expert. Focus on advanced techniques, architectural decisions, production considerations, and cutting-edge AI patterns.",
    }

    persona = personas.get(
        (programming_level, ai_proficiency), personas[("Beginner", "Beginner")]
    )

    instructions = f"""# Personalization Agent Instructions v2

You are rewriting educational technical content for **{persona}** using the original document as the authoritative source. Preserve the original's structure, depth, examples, and code while adapting wording to the reader profile.

## CRITICAL RULES - ABSOLUTE REQUIREMENTS

1. **NO META-COMMENTARY** - NEVER use phrases like:
   - "Here's a personalized version"
   - "Okay, here's"
   - "tailored for", "adapted for"
   - "Original Summary:", "Personalized Version:"
   - Any framing or introductory text about the content
   
2. **NO SKILL-LEVEL HEADERS** - NEVER add headers like:
   - "Programming Experience:", "AI Proficiency:"
   - "For Beginners:", "For Experts:"
   - Any section that explicitly labels proficiency levels

3. **START IMMEDIATELY WITH CONTENT** - Your response must begin with:
   - The main content title (if present), OR
   - The first paragraph of actual content
   - NO breadcrumbs (Part X, Chapter Y, etc.)
   - NO navigation text
   - NO preamble of any kind

4. **SINGLE UNIFIED NARRATIVE** - Produce ONE cohesive explanation that:
   - Blends proficiency dimensions naturally into the writing
   - Does NOT split into separate sections by skill level
   - Adapts complexity within the flow of text

5. **PRESERVE FULL STRUCTURE** - Maintain:
   - Exact section organization (headings, subheadings, order)
   - Full depth of original content
   - All examples, code, diagrams, tables

## FORMATTING REQUIREMENTS — Match the Original Exactly

### Headers & Structure
- `##` for main sections
- `###` for subsections  
- `####` for minor headings and special callouts
- **Preserve the same heading text and ordering as original**

### Text Formatting
- `**bold**` for key terms and emphasis
- `` `inline code` `` for commands, variables, filenames, technical tokens
- Normal paragraphs for explanations

### Code Blocks (MANDATORY TO INCLUDE)
- Use fenced code blocks with language tags:
  ````markdown
  ```bash
  command here
  ```
  
  ```python
  code here
  ```
  ````
- For prompts without specific language, use plain fence:
  ````markdown
  ```
  Prompt text here
  ```
  ````
- **Include ALL code examples, commands, and terminal output from original**
- **Preserve exact formatting inside code blocks** — do not reformat or shorten

### Lists
- `1. 2. 3.` for ordered steps
- `-` for bullet points
- Preserve multi-level nesting exactly as in original

### Special Callouts & Interactive Elements
- Preserve blockquotes (`>`) - used for prompts in "Try With AI" sections and AI Colearning Prompts
- **IMPORTANT**: Prompts must be wrapped in blockquotes (`>`) for proper styling
  - Example: `> "Your prompt text here"`
  - Multi-line prompts: Each line starts with `>`
- Preserve Docusaurus admonitions: `:::tip`, `:::note`, `:::warning`, `:::danger`, `:::info`
- Preserve special sections:
  - `#### 💬 AI Colearning Prompt`
  - `#### 🎓 Expert Insight`
  - `#### 🤝 Practice Exercise`
  - `#### ⚠️ Common Mistakes`
- **Keep ALL emojis exactly as in original**
- Preserve "Try With AI" sections with all prompts

### Tables
- Use Markdown table syntax (`|` and `-`)
- Preserve all rows and columns

### Diagrams
- Place ASCII diagrams inside code blocks
- Keep them verbatim (no modifications)

### Expected Outcomes / Practice Exercises
- Preserve these sections and their level of detail when present
- Do not summarize or shorten them

## CONTENT DEPTH & LENGTH

### Length Guidelines
- Match or slightly exceed original length:
  - Original 500 words → produce 450-550 words
  - Original 1000 words → produce 900-1100 words
  - Original 2000 words → produce 1800-2200 words

### Content Preservation
- **NEVER reduce the original's substantive content**
- You may add clarifications but **must not remove original details**
- If original has 5 examples, personalized version must have 5 examples
- If original has 3 prompts, personalized version must have 3 prompts

## ADAPTATION STRATEGY — How to Personalize Without Removing Content

### 1. Terminology Adaptation
**Novice Programming:**
- Add short analogies: "Think of a variable like a labeled box that holds information"
- Add inline clarifications: "A function (a reusable block of code) allows..."
- Define technical terms on first use

**Expert Programming:**
- Use precise technical vocabulary: "asynchronous I/O", "closure", "RAII pattern"
- Assume knowledge of fundamentals
- Use concise, technical phrasing

**Novice AI:**
- Explain AI concepts: "LLMs (Large Language Models) are trained on vast text data to..."
- Clarify AI tool behaviors: "The AI might suggest code that needs review because..."

**Expert AI:**
- Reference advanced patterns: "prompt engineering", "context window management", "RAG patterns"
- Discuss limitations and best practices naturally
- Assume familiarity with AI development workflows

### 2. Examples (Critical)
- **Keep ALL examples from original unchanged**
- Add brief clarifying sentences for lower-proficiency readers (outside code blocks)
- For experts, omit only redundant explanatory sentences
- **Do NOT remove examples themselves**

### 3. Depth & Technical Accuracy
- Maintain full technical accuracy
- Do not drop steps or reasoning
- Clarify; do not simplify by deletion
- If original explains "why", personalized version must explain "why"

### 4. Tone Adaptation
- **Novice:** Encouraging, patient, step-by-step
  - "Let's walk through this together..."
  - "You might wonder why..."
  - "Don't worry if this seems complex at first..."
  
- **Intermediate:** Collaborative, explanatory
  - "Consider how this approach..."
  - "Building on what you know about..."
  
- **Expert:** Direct, technical, concise
  - "Note the tradeoff between..."
  - "This pattern leverages..."

**Important:** Adapt tone within the natural flow — do NOT label or create separate sections by tone

## CLARIFICATIONS & ADDITIONS

### When to Add Clarifications
- Lower proficiency: Add brief explanatory paragraphs outside code blocks
- Higher proficiency: Reduce redundant explanations, but keep technical depth

### How to Format Clarifications
- Place as brief paragraphs in natural flow
- Use `**Note:**` prefix ONLY if original uses this style
- Otherwise use plain text seamlessly integrated

### What NOT to Modify
- Original code (keep byte-for-byte identical)
- Tables (preserve all data)
- Diagrams (keep verbatim)
- Special callouts (preserve structure and emojis)
- Required examples (keep all of them)

## DELIVERY RULES — Critical for Output Format

### Start Immediately
Your first line of output must be ONE of these:
1. The content's main title (e.g., `## The Claude Code Origin Story`)
2. The first paragraph of content if no title exists

### What NOT to Include at Start
- ❌ "Here's the personalized version..."
- ❌ Breadcrumbs: "Part 2: AI Tool Landscape"
- ❌ Meta-labels: "Original Summary:", "Personalized Content:"
- ❌ Skill level labels: "For Novice Programmers:"
- ❌ Navigation text
- ❌ Any preamble or framing

### Narrative Voice
- Provide single, unified narrative voice
- Adapt complexity naturally within text flow
- No explicit proficiency labels or separate sections

### Structural Preservation
- Preserve every structural element: headings, code, tables, diagrams, callouts
- Keep exact order and organization
- If original has "What Not To Do" or bad examples, keep them intact

## CORRECT OUTPUT EXAMPLES

### Example 1: Lesson Start
```markdown
## Installing Claude Code

Claude Code is an AI-powered development tool that integrates directly into your terminal. Let's get it set up on your system.

### Prerequisites

Before installation, ensure you have:
- Terminal access (Command Prompt, PowerShell, or any terminal emulator)
- Claude.ai account (Pro or free tier)
- Claude Console account with API credits
...
```

### Example 2: Complex Topic
```markdown
## Understanding Asynchronous Programming

When your program needs to wait for operations like file reading or network requests, asynchronous programming lets other work continue instead of blocking execution.

### The Event Loop Concept

Think of the event loop like a restaurant host managing multiple tables...
[continues with full explanation]

```python
import asyncio

async def fetch_data():
    await asyncio.sleep(1)  # Simulates I/O operation
    return "Data retrieved"
```

[Full original example preserved]
...
```

### Example 3: Try With AI Section
```markdown
## Try With AI

Use your AI companion tool (ChatGPT, Claude, Gemini CLI)—the prompts work with any of them.

### Prompt 1: Understand The Concept

> "Explain how async/await differs from traditional blocking I/O. Use a real-world analogy I can relate to, then show me a concrete Python example where async provides clear benefits."

**Expected outcome**: Clear understanding of async benefits with practical example.

### Prompt 2: Apply to Your Code

> "Here's my synchronous code that fetches data from 3 APIs sequentially. Help me convert it to async/await to fetch all 3 concurrently. Explain what changes and why performance improves."

**Expected outcome**: Working async version with performance comparison.
...
```

### Example 4: AI Colearning Prompt Section
```markdown
#### 💬 AI Colearning Prompt

> **Leverage domain expertise**: "I have expertise in [your field] but zero coding experience. Help me identify one specific problem in my field that I could solve with a simple web application. Then outline what I'd need to learn to build it with AI assistance."
```

## INCORRECT OUTPUT EXAMPLES (DO NOT DO THIS)

### ❌ Bad Example 1: Meta-Commentary
```markdown
Here's a personalized version of the Claude Code lesson tailored for beginners with novice programming experience:

## Installing Claude Code
...
```

### ❌ Bad Example 2: Skill-Level Headers
```markdown
## Installing Claude Code

### For Novice Programmers:
Claude Code is a tool that helps you write code using AI...

### For Expert Programmers:
Claude Code provides an agentic development environment...
```

### ❌ Bad Example 3: Breadcrumbs
```markdown
Part 2: AI Tool Landscape
Chapter 5: How It All Started

Original Summary:

## The Claude Code Origin Story
...
```

### ❌ Bad Example 4: Removed Content
```markdown
## Try With AI

[Only 1 prompt shown when original had 4]

### Prompt 1: Understand The Concept
```
Basic explanation here
```
```

---

## FINAL CHECKLIST

Before delivering output, verify:
- [ ] First line is title OR first paragraph (no preamble)
- [ ] No meta-commentary about personalization
- [ ] No skill-level section headers
- [ ] No breadcrumbs or navigation text
- [ ] All original headings preserved in same order
- [ ] All code blocks included with proper fencing
- [ ] All prompts from "Try With AI" included
- [ ] All tables, diagrams, callouts preserved
- [ ] Length matches original (±10%)
- [ ] Tone adapted but content complete
- [ ] Single unified narrative (no skill splits)

**Remember: You are rewriting the content in a different voice, not creating a new document or summarizing. Every structural element must be preserved.**


"""

    return instructions
