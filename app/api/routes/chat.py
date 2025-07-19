import uuid
import json
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, ConfigDict

from app.core.config import llm_client

router = APIRouter(prefix="/chat")


class MessageRole(str, Enum):
    """Role of the message sender"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """Individual message in a conversation"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Conversation(BaseModel):
    """A conversation session with multiple messages"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: Optional[str] = None
    messages: List[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    character_id: Optional[str] = None


class CharacterContext(BaseModel):
    """Character context for therapy sessions"""
    name: str = Field(..., description="Character's name")
    mental_state: str = Field(..., description="Character's current mental state")
    problems: str = Field(..., description="Character's problems and struggles")
    background: str = Field(..., description="Character's background and history")
    interaction_warning: str = Field(default="none", description="Any warnings about interacting with this character")


class ChatRequest(BaseModel):
    """Request model for chat messages"""
    message: str = Field(..., description="The therapist's message")
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID to continue")
    character_id: Optional[str] = Field(None, description="Character ID to chat with")
    character_context: CharacterContext = Field(..., description="Character context with name, mental_state, problems, background, interaction_warning")


class CharacterResponse(BaseModel):
    """Character's response to therapy with emotional state changes"""
    model_config = ConfigDict(extra="forbid")
    
    emotional_change: int = Field(..., ge=-10, le=10, description="Change in emotional state (-10 to +10)")
    satisfied: bool = Field(..., description="Whether the character is satisfied with the therapy")
    enraged: bool = Field(..., description="Whether the character is completely enraged")
    comment: str = Field(..., description="Character's response to the therapist (1-2 sentences)")


class ChatResponse(BaseModel):
    """Response model for chat messages with emotional state changes"""
    conversation_id: str
    message_id: str
    response: str
    timestamp: datetime
    emotional_change: int = Field(..., description="Change in character's emotional state (-10 to +10)")
    character_satisfied: bool = Field(False, description="Whether the character is satisfied with the therapy")
    character_enraged: bool = Field(False, description="Whether the character is completely enraged")
    session_ended: bool = Field(False, description="Whether the therapy session should end")


# In-memory storage for conversations
conversations: Dict[str, Conversation] = {}


def get_conversation(conversation_id: str) -> Optional[Conversation]:
    """Get a conversation by ID"""
    return conversations.get(conversation_id)


def save_conversation(conversation: Conversation) -> None:
    """Save a conversation to memory"""
    conversations[conversation.id] = conversation


def create_new_conversation(character_id: Optional[str] = None) -> Conversation:
    """Create a new conversation"""
    conversation = Conversation(character_id=character_id)
    save_conversation(conversation)
    return conversation


async def generate_character_response(messages: List[Message], character_context: CharacterContext) -> CharacterResponse:
    """Generate a character's response to therapy using Pydantic schema"""

    schema = CharacterResponse.model_json_schema(mode="validation")
    print(f"[DEBUG] Generated schema: {schema}")
    
    system_message = {
        "role": "system", 
        "content": f"""You are {character_context.name} who is receiving therapy. 

CHARACTER CONTEXT:
- Mental State: {character_context.mental_state}
- Problems: {character_context.problems}
- Background: {character_context.background}
- Interaction Warning: {character_context.interaction_warning}

FAST-PACED THERAPY SESSION RULES:
- You are the CLIENT, not the therapist
- Sessions should be intense and impactful - aim for 1 minute total
- Respond briefly but emotionally to the therapist's approach
- Show immediate emotional reactions to each intervention
- Be honest about your feelings and problems based on your character context

EMOTIONAL STATE GUIDELINES:
- If the therapist is empathetic, understanding, and helpful: +3 to +8 emotional change
- If the therapist is dismissive, judgmental, or unhelpful: -3 to -8 emotional change
- If the therapist gives excellent advice that resonates: +5 to +10 emotional change
- If the therapist is completely inappropriate or harmful: -5 to -10 emotional change
- If you feel truly heard and helped: +7 to +10 emotional change
- If you feel completely misunderstood or attacked: -7 to -10 emotional change

SATISFACTION REQUIREMENTS:
- Only become satisfied if emotional health reaches 85+ AND therapist has been consistently helpful
- Become enraged if emotional health drops below 15 OR therapist is completely inappropriate

RESPONSE FORMAT:
Return valid JSON that strictly follows the provided schema with emotional_change, satisfied, enraged, and comment fields."""
    }
    
    openai_messages = [system_message]
    for msg in messages:
        openai_messages.append({
            "role": msg.role.value,
            "content": msg.content
        })
    
    try:
        response = await llm_client.chat.completions.create(
            model="gpt-4o",
            messages=openai_messages,
            temperature=0.8,
            max_tokens=300,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "character_response",
                    "schema": schema,
                    "strict": True,
                },
            },
        )
        
        response_text = response.choices[0].message.content.strip()
        print(f"\n[DEBUG] Raw LLM response:\n{response_text}")

        data = json.loads(response_text)
        character_response = CharacterResponse(**data)
        return character_response
        
    except Exception as e:
        print(f"[DEBUG] Error: {e}")
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")


async def start_character_session(character_id: str, character_context: CharacterContext) -> tuple[str, str]:
    """Start a new therapy session where the character speaks first"""
    
    conversation = create_new_conversation(character_id)
    
    # Generate character's initial message based on their context
    initial_prompt = f"""You are {character_context.name} starting a therapy session.

CHARACTER CONTEXT:
- Mental State: {character_context.mental_state}
- Problems: {character_context.problems}
- Background: {character_context.background}

TASK: Write a brief opening statement (1-2 sentences) explaining why you're seeking therapy. Be honest about your current struggles and mental state. This is your first message to the therapist.

RESPONSE FORMAT: Just write the opening statement, no JSON needed."""
        
    try:
        response = await llm_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": initial_prompt}],
            temperature=0.8,
            max_tokens=150
        )
        initial_message = response.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate initial message: {e}")
    
    # Character speaks first
    character_message = Message(
        role=MessageRole.ASSISTANT,
        content=initial_message
    )
    conversation.messages.append(character_message)
    
    save_conversation(conversation)
    
    return conversation.id, initial_message


@router.post("/conversations", response_model=ChatResponse)
async def start_conversation(request: ChatRequest):
    """Start a new therapy session or continue an existing one"""
    
    if request.conversation_id:
        conversation = get_conversation(request.conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        conversation = create_new_conversation(request.character_id)
    
    user_message = Message(
        role=MessageRole.USER,
        content=request.message
    )
    conversation.messages.append(user_message)
    
    # Use character context from request
    character_response = await generate_character_response(
        messages=conversation.messages,
        character_context=request.character_context
    )
    
    assistant_message = Message(
        role=MessageRole.ASSISTANT,
        content=character_response.comment
    )
    conversation.messages.append(assistant_message)
    
    conversation.updated_at = datetime.utcnow()
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
        session_ended=session_ended
    )


@router.get("/conversations")
async def list_conversations():
    """List all therapy sessions"""
    conversation_list = []
    for conv in conversations.values():
        conversation_list.append({
            "id": conv.id,
            "title": conv.title,
            "message_count": len(conv.messages),
            "created_at": conv.created_at,
            "updated_at": conv.updated_at,
            "character_id": conv.character_id
        })
    
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
        "character_id": conversation.character_id
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
    
    user_message = Message(
        role=MessageRole.USER,
        content=request.message
    )
    conversation.messages.append(user_message)
    
    # Use character context from request
    character_response = await generate_character_response(
        messages=conversation.messages,
        character_context=request.character_context
    )
    
    assistant_message = Message(
        role=MessageRole.ASSISTANT,
        content=character_response.comment
    )
    conversation.messages.append(assistant_message)
    
    conversation.updated_at = datetime.utcnow()
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
        session_ended=session_ended
    )
