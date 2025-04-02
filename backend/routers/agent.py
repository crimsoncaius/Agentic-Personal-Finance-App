from fastapi import APIRouter, HTTPException, Depends, Request, File, UploadFile, Body
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from datetime import date
import json

from ..database import get_db
from ..models import User
from ..auth import get_current_active_user
from ..schemas import ChatMessage, ChatResponse
from .conversation_memory import ConversationMemory
from .response_generator import ResponseGenerator
from .sql_generator import generate_sql_with_llm
from .sql_executor import execute_sql_query

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/agent", tags=["agent"])

# Global dictionary to store conversation memories for each user
conversation_memories = {}


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ChatResponse:
    """
    Process a chat message and return a response.
    """
    try:
        # Log raw request data before any parsing
        body = await request.body()
        logger.info("Raw request body: %s", body.decode())
        logger.info("Request headers: %s", dict(request.headers))

        # Parse the raw JSON ourselves to see what's being sent
        try:
            body_json = json.loads(body.decode())
            logger.info("Parsed JSON body: %s", body_json)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON body: %s", e)
            raise HTTPException(
                status_code=422, detail=f"Invalid JSON format: {str(e)}"
            )

        # Validate the required fields
        if "content" not in body_json:
            logger.error("Missing 'content' field in request body")
            raise HTTPException(
                status_code=422, detail="Missing required field: content"
            )

        content = body_json["content"]
        if not isinstance(content, str):
            logger.error(f"'content' field is not a string: {type(content)}")
            raise HTTPException(
                status_code=422, detail="'content' field must be a string"
            )

        if not content.strip():
            logger.error("Empty content string")
            raise HTTPException(status_code=422, detail="Content cannot be empty")

        # Create message object
        message = ChatMessage(content=content)
        logger.info("Created ChatMessage object: %s", message.model_dump())

        # Get or create conversation memory for the user
        try:
            if current_user.id not in conversation_memories:
                logger.info(
                    f"Creating new conversation memory for user {current_user.id}"
                )
                conversation_memories[current_user.id] = ConversationMemory(
                    current_user.id
                )
            memory = conversation_memories[current_user.id]
        except Exception as e:
            logger.error(f"Error managing conversation memory: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to manage conversation memory: {str(e)}",
            )

        # Create response generator
        try:
            response_generator = ResponseGenerator(db, current_user.id)
        except Exception as e:
            logger.error(f"Error creating response generator: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize response generator: {str(e)}",
            )

        # Generate response
        try:
            response = response_generator.generate_response(message.content)
            logger.info(f"Generated response: {response.model_dump()}")
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to generate response: {str(e)}"
            )

        # Store interaction in memory
        try:
            memory.add_interaction(message.content, response.response)
        except Exception as e:
            logger.error(f"Error storing interaction in memory: {e}")
            # Don't fail the request if memory storage fails
            # Just log the error and continue

        return response

    except HTTPException as he:
        # Re-raise HTTP exceptions as they already have the correct format
        raise he
    except Exception as e:
        logger.error(f"Unexpected error processing chat message: {e}")
        return ChatResponse(
            response="I encountered an unexpected error processing your request. Please try again.",
            success=False,
            error=str(e),
        )


@router.post("/chat/reset", response_model=ChatResponse)
async def reset_chat(
    current_user: User = Depends(get_current_active_user),
) -> ChatResponse:
    """
    Reset the conversation memory for the current user.
    """
    try:
        if current_user.id in conversation_memories:
            conversation_memories[current_user.id].clear()
            del conversation_memories[current_user.id]

        return ChatResponse(
            response="Chat history has been cleared. How can I help you today?",
            success=True,
        )
    except Exception as e:
        logger.error(f"Error resetting chat: {e}")
        return ChatResponse(
            response="I encountered an error resetting the chat. Please try again.",
            success=False,
            error=str(e),
        )
