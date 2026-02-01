"""
Chat API endpoints
"""
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import json

from app.schemas.chat import ChatRequest, ChatResponse, Source, ChatMetadata
from app.llm import ResponseGenerator
from app.utils.logger import setup_logger
from app.utils.cache_manager import get_cache_manager

logger = setup_logger("api_chat", "./logs/api_chat.log")

# Initialize response generator (singleton)
generator = None

router = APIRouter(prefix="/chat", tags=["chat"])


def get_generator():
    """Get or create response generator instance."""
    global generator
    if generator is None:
        logger.info("Initializing ResponseGenerator...")
        generator = ResponseGenerator()
    return generator


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint - Ask questions about university regulations.
    
    Args:
        request: ChatRequest with question and optional conversation history
    
    Returns:
        ChatResponse with answer, sources, and metadata
    """
    try:
        logger.info(f"Received chat request: '{request.question[:50]}...'")
        
        # Get generator
        gen = get_generator()
        
        # Generate response
        response = gen.generate_response(
            question=request.question,
            conversation_history=request.conversation_history,
            include_sources=request.include_sources
        )
        
        # Convert to response model
        chat_response = ChatResponse(
            answer=response["answer"],
            sources=[Source(**src) for src in response["sources"]],
            metadata=ChatMetadata(**response["metadata"])
        )
        
        logger.info(f"Response generated successfully: {response['metadata']['tokens']} tokens")
        
        return chat_response
    
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """
    Streaming chat endpoint.
    
    Args:
        request: ChatRequest with question
    
    Returns:
        Streaming response with chunks
    """
    try:
        logger.info(f"Received streaming chat request: '{request.question[:50]}...'")
        
        gen = get_generator()
        
        async def generate():
            """Generate streaming response."""
            try:
                for chunk in gen.generate_response_stream(request.question):
                    yield f"data: {json.dumps({'chunk': chunk})}\n\n"
                
                yield "data: {\"done\": true}\n\n"
            
            except Exception as e:
                logger.error(f"Error in streaming: {e}", exc_info=True)
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream"
        )
    
    except Exception as e:
        logger.error(f"Error in streaming endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/stats")
async def get_cache_stats():
    """
    Get cache statistics.
    
    Returns cache hit/miss rates and current cache size.
    """
    try:
        cache = get_cache_manager()
        stats = cache.get_stats()
        
        return {
            "status": "success",
            "cache": stats
        }
    
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/clear")
async def clear_cache(pattern: Optional[str] = None):
    """
    Clear cache.
    
    Args:
        pattern: Optional key pattern to clear (e.g., 'response:*')
    
    Returns:
        Number of keys cleared
    """
    try:
        cache = get_cache_manager()
        count = cache.clear(pattern=pattern)
        
        logger.info(f"Cache cleared: {count} keys (pattern: {pattern})")
        
        return {
            "status": "success",
            "cleared_keys": count,
            "pattern": pattern
        }
    
    except Exception as e:
        logger.error(f"Error clearing cache: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
