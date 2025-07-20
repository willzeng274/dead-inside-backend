from datetime import UTC, datetime
from typing import Optional, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.llm import (
    MessageRole,
    Message,
    CharacterContext,
    get_conversation,
    save_conversation,
    create_new_conversation,
    delete_conversation,
    get_all_conversation_ids,
    generate_character_response,
    get_character,
    get_all_characters,
)

router = APIRouter(prefix="/legacy/chat")


class ChatRequest(BaseModel):
    """Request model for chat messages"""

    message: str = Field(..., description="The therapist's message")
    conversation_id: Optional[str] = Field(
        None, description="Existing conversation ID to continue"
    )
    character_id: str = Field(..., description="Character UUID to chat with")


class ChatResponse(BaseModel):
    """Response model for chat messages with emotional state changes"""

    conversation_id: str
    message_id: str
    response: str
    timestamp: datetime
    emotional_change: int = Field(
        ..., description="Change in character's emotional state (-10 to +10)"
    )
    emotional_state: int = Field(
        ..., description="Current emotional state (0-100)"
    )
    # character_satisfied: bool = Field(
    #     False, description="Whether the character is satisfied with the therapy"
    # )
    # character_enraged: bool = Field(
    #     False, description="Whether the character is completely enraged"
    # )
    session_ended: bool = Field(
        False, description="Whether the therapy session should end"
    )


class CharacterGenerationRequest(BaseModel):
    """Request model for character generation"""
    theme: str = Field(..., description="Theme for character generation")


async def get_character_context_from_redis(character_id: str) -> CharacterContext:
    """Get character context from Redis using UUID"""
    character_data = await get_character(character_id)
    if not character_data:
        raise HTTPException(status_code=404, detail="Character not found")
    
    return CharacterContext(
        name=character_data["name"],
        mental_state=character_data["mental_state"],
        problems=character_data["problems"],
        background=character_data["background"],
        interaction_warning=character_data["interaction_warning"],
    )


@router.post("/conversations", response_model=ChatResponse)
async def start_conversation(request: ChatRequest):
    """Start a new therapy session or continue an existing one"""

    character_context = await get_character_context_from_redis(request.character_id)

    if request.conversation_id:
        conversation = await get_conversation(request.conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = await create_new_conversation(request.character_id)

    user_message = Message(role=MessageRole.USER, content=request.message)
    conversation.messages.append(user_message)

    character_response = await generate_character_response(
        messages=conversation.messages, 
        character_context=character_context,
        current_emotional_state=conversation.emotional_state
    )

    assistant_message = Message(
        role=MessageRole.ASSISTANT, content=character_response.comment
    )
    conversation.messages.append(assistant_message)

    new_emotional_state = conversation.emotional_state + character_response.emotional_change
    conversation.emotional_state = max(0, min(100, new_emotional_state))

    conversation.updated_at = datetime.now(UTC)
    if not conversation.title and len(conversation.messages) == 2:
        conversation.title = f"Therapy Session: {request.message[:30]}..."

    await save_conversation(conversation)

    session_ended = conversation.emotional_state <= 0 or conversation.emotional_state >= 100

    return ChatResponse(
        conversation_id=conversation.id,
        message_id=assistant_message.id,
        response=character_response.comment,
        timestamp=assistant_message.timestamp,
        emotional_change=character_response.emotional_change,
        emotional_state=conversation.emotional_state,
        session_ended=session_ended,
    )


@router.get("/conversations")
async def list_conversations():
    """List all therapy sessions"""
    conversation_list = []
    conversation_ids = await get_all_conversation_ids()
    
    for conv_id in conversation_ids:
        conv = await get_conversation(conv_id)
        if conv:
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
    conversation = await get_conversation(conversation_id)
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
async def delete_conversation_endpoint(conversation_id: str):
    """Delete a therapy session"""
    conversation = await get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    success = await delete_conversation(conversation_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete conversation")
    
    return {"message": "Therapy session deleted successfully"}


@router.post("/conversations/{conversation_id}/messages", response_model=ChatResponse)
async def add_message_to_conversation(conversation_id: str, request: ChatRequest):
    """Add a message to an existing therapy session"""
    conversation = await get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    character_context = await get_character_context_from_redis(request.character_id)

    user_message = Message(role=MessageRole.USER, content=request.message)
    conversation.messages.append(user_message)

    character_response = await generate_character_response(
        messages=conversation.messages, 
        character_context=character_context,
        current_emotional_state=conversation.emotional_state
    )

    assistant_message = Message(
        role=MessageRole.ASSISTANT, content=character_response.comment
    )
    conversation.messages.append(assistant_message)

    new_emotional_state = conversation.emotional_state + character_response.emotional_change
    conversation.emotional_state = max(0, min(100, new_emotional_state))

    conversation.updated_at = datetime.now(UTC)
    await save_conversation(conversation)

    session_ended = conversation.emotional_state <= 0 or conversation.emotional_state >= 100

    return ChatResponse(
        conversation_id=conversation.id,
        message_id=assistant_message.id,
        response=character_response.comment,
        timestamp=assistant_message.timestamp,
        emotional_change=character_response.emotional_change,
        emotional_state=conversation.emotional_state,
        session_ended=session_ended,
    )


@router.delete("/cleanup")
async def cleanup_all_data():
    """Delete all data from Redis (for testing purposes)"""
    try:
        from app.core.redis_client import redis_client

        all_keys = await redis_client.redis_client.keys("*")
        
        if all_keys:
            deleted_count = await redis_client.redis_client.delete(*all_keys)
            return {
                "message": f"Cleaned up {deleted_count} items from Redis",
                "deleted_count": deleted_count
            }
        else:
            return {
                "message": "Redis is already empty",
                "deleted_count": 0
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


@router.get("/characters/{character_id}")
async def get_character_details(character_id: str):
    """Get character details by UUID"""
    character_data = await get_character(character_id)
    if not character_data:
        raise HTTPException(status_code=404, detail="Character not found")
    
    return character_data


@router.get("/characters")
async def list_characters():
    """List all characters in Redis"""
    characters = await get_all_characters()
    return {
        "characters": characters,
        "total": len(characters)
    }


@router.post("/characters/generate")
async def generate_characters(request: CharacterGenerationRequest):
    """Generate characters with auto-generated UUIDs"""
    try:
        from app.core.llm import generate_characters_from_theme
        response = await generate_characters_from_theme(request.theme)
        return {
            "theme": response.theme,
            "characters": [char.model_dump() for char in response.characters],
            "total": len(response.characters)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Character generation failed: {str(e)}")
