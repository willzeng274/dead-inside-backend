from datetime import UTC, datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.llm import (
    MessageRole,
    Message,
    CharacterContext,
    conversations,
    get_conversation,
    save_conversation,
    create_new_conversation,
    generate_character_response,
)

router = APIRouter(prefix="/chat")


class ChatRequest(BaseModel):
    """Request model for chat messages"""

    message: str = Field(..., description="The therapist's message")
    conversation_id: Optional[str] = Field(
        None, description="Existing conversation ID to continue"
    )
    character_id: Optional[str] = Field(None, description="Character ID to chat with")
    character_context: CharacterContext = Field(
        ...,
        description="Character context with name, mental_state, problems, background, interaction_warning",
    )


class ChatResponse(BaseModel):
    """Response model for chat messages with emotional state changes"""

    conversation_id: str
    message_id: str
    response: str
    timestamp: datetime
    emotional_change: int = Field(
        ..., description="Change in character's emotional state (-10 to +10)"
    )
    character_satisfied: bool = Field(
        False, description="Whether the character is satisfied with the therapy"
    )
    character_enraged: bool = Field(
        False, description="Whether the character is completely enraged"
    )
    session_ended: bool = Field(
        False, description="Whether the therapy session should end"
    )


@router.post("/conversations", response_model=ChatResponse)
async def start_conversation(request: ChatRequest):
    """Start a new therapy session or continue an existing one"""

    if request.conversation_id:
        conversation = get_conversation(request.conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = create_new_conversation(request.character_id)

    user_message = Message(role=MessageRole.USER, content=request.message)
    conversation.messages.append(user_message)

    character_response = await generate_character_response(
        messages=conversation.messages, character_context=request.character_context
    )

    assistant_message = Message(
        role=MessageRole.ASSISTANT, content=character_response.comment
    )
    conversation.messages.append(assistant_message)

    conversation.updated_at = datetime.now(UTC)
    if not conversation.title and len(conversation.messages) == 2:
        conversation.title = f"Therapy Session: {request.message[:30]}..."

    save_conversation(conversation)

    session_ended = character_response.satisfied or character_response.enraged

    return ChatResponse(
        conversation_id=conversation.id,
        message_id=assistant_message.id,
        response=character_response.comment,
        timestamp=assistant_message.timestamp,
        emotional_change=character_response.emotional_change,
        character_satisfied=character_response.satisfied,
        character_enraged=character_response.enraged,
        session_ended=session_ended,
    )


@router.get("/conversations")
async def list_conversations():
    """List all therapy sessions"""
    conversation_list = []
    for conv in conversations.values():
        conversation_list.append(
            {
                "id": conv.id,
                "title": conv.title,
                "message_count": len(conv.messages),
                "created_at": conv.created_at,
                "updated_at": conv.updated_at,
                "character_id": conv.character_id,
            }
        )

    conversation_list.sort(key=lambda x: x["updated_at"], reverse=True)
    return {"conversations": conversation_list, "total": len(conversation_list)}


@router.get("/conversations/{conversation_id}")
async def get_conversation_details(conversation_id: str):
    """Get detailed information about a specific therapy session"""
    conversation = get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {
        "id": conversation.id,
        "title": conversation.title,
        "messages": [msg.model_dump() for msg in conversation.messages],
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "character_id": conversation.character_id,
    }


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a therapy session"""
    conversation = get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    del conversations[conversation_id]
    return {"message": "Therapy session deleted successfully"}


@router.post("/conversations/{conversation_id}/messages", response_model=ChatResponse)
async def add_message_to_conversation(conversation_id: str, request: ChatRequest):
    """Add a message to an existing therapy session"""
    conversation = get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    user_message = Message(role=MessageRole.USER, content=request.message)
    conversation.messages.append(user_message)

    character_response = await generate_character_response(
        messages=conversation.messages, character_context=request.character_context
    )

    assistant_message = Message(
        role=MessageRole.ASSISTANT, content=character_response.comment
    )
    conversation.messages.append(assistant_message)

    conversation.updated_at = datetime.now(UTC)
    save_conversation(conversation)

    session_ended = character_response.satisfied or character_response.enraged

    return ChatResponse(
        conversation_id=conversation.id,
        message_id=assistant_message.id,
        response=character_response.comment,
        timestamp=assistant_message.timestamp,
        emotional_change=character_response.emotional_change,
        character_satisfied=character_response.satisfied,
        character_enraged=character_response.enraged,
        session_ended=session_ended,
    )
