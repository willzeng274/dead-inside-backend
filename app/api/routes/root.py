import os
import aiofiles
from datetime import UTC, datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.speech_to_text import transcribe_audio
from app.core.text_to_speech import TTSRequest, generate_tts
from app.core.llm import (
    MessageRole,
    Message,
    CharacterContext,
    get_conversation,
    save_conversation,
    generate_character_response,
    get_character,
    Conversation,
)

router = APIRouter()


async def get_character_context_from_redis(character_id: str) -> CharacterContext:
    """Get character context from Redis using UUID"""
    character_data = await get_character(character_id)
    if not character_data:
        raise HTTPException(status_code=404, detail="Character not found")
    
    return CharacterContext(
        name=character_data["name"],
        gender=character_data["gender"],
        mental_state=character_data["mental_state"],
        problem=character_data["problem"],
        background=character_data["background"],
        interaction_warning=character_data["interaction_warning"],
    )


@router.get("/", response_model=str)
async def index():
    """
    Root endpoint to verify the API is working.
    """
    # Unreachable
    if not hasattr(router, "prefix"):
        raise HTTPException(status_code=500, detail="Router prefix not set.")
    return "Welcome to the Dead Inside Backend API!"


class AudioFileRequest(BaseModel):
    file_path: str


class ZombieInteractionRequest(BaseModel):
    """Request model for zombie interaction with optional audio input"""
    character_id: str = Field(..., description="Character UUID to interact with")
    audio_file_path: Optional[str] = Field(None, description="Optional local file path to audio file")


class ZombieInteractionResponse(BaseModel):
    """Response model for zombie interaction with AI response and mental score"""
    transcription: str = Field(..., description="Transcribed speech from audio")
    character_response: str = Field(..., description="Character's AI response")
    emotional_change: int = Field(..., description="Change in character's emotional state (-50 to +50)")
    emotional_state: int = Field(..., description="Current emotional state (0-100)")
    session_ended: bool = Field(False, description="Whether the therapy session should end")


@router.post("/stt", response_model=str)
async def stt(request: AudioFileRequest):
    """
    Endpoint for speech-to-text functionality.
    """
    file_path = request.file_path

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

    filename = os.path.basename(file_path)

    try:
        async with aiofiles.open(file_path, "rb") as f:
            bytes_audio = await f.read()

        transcription = await transcribe_audio(bytes_audio, filename)
        return transcription
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")


@router.post("/tts")
async def tts(request: TTSRequest):
    """
    Endpoint for text-to-speech functionality using OpenAI's gpt-4o-mini-tts model.
    
    Supports:
    - Text-to-speech conversion with character-specific voice settings
    - Custom output file path via stored_file_path parameter
    """
    try:
        character_data = await get_character(request.character_id)
        if not character_data:
            raise HTTPException(status_code=404, detail="Character not found")
        
        voice_selection = character_data.get("voice_selection", "alloy")
        
        enhanced_request = TTSRequest(
            text=request.text,
            stored_file_path=request.stored_file_path,
            character_id=request.character_id,
            voice=voice_selection
        )
        
        await generate_tts(enhanced_request)
        return None
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")


@router.post("/zombie", response_model=ZombieInteractionResponse)
async def zombie_interaction(request: ZombieInteractionRequest):
    """
    Endpoint for zombie interaction that handles both initial messages and audio responses.
    
    Flow:
    1. If audio_file_path provided: Transcribe audio and get response
    2. If no audio_file_path: Get initial message from zombie
    3. Get character context from Redis
    4. Get or create conversation using character_id as conversation_id
    5. Generate character response based on input
    6. Update emotional state and return response
    """
    # Step 1: Get character context
    try:
        character_context = await get_character_context_from_redis(request.character_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting character context: {str(e)}")
    
    # Step 2: Get or create conversation using character_id as conversation_id
    try:
        conversation = await get_conversation(request.character_id)
        if not conversation:
            # Create new conversation with character_id as the conversation_id
            conversation = Conversation(id=request.character_id, character_id=request.character_id)
            await save_conversation(conversation)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error handling conversation: {str(e)}")
    
    # Step 3: Handle audio transcription or initial message
    if request.audio_file_path:
        # Process audio file
        file_path = request.audio_file_path
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"Audio file not found: {file_path}")
        
        filename = os.path.basename(file_path)
        
        try:
            async with aiofiles.open(file_path, "rb") as f:
                bytes_audio = await f.read()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error reading audio file: {str(e)}")
        
        # Transcribe audio
        try:
            transcription = await transcribe_audio(bytes_audio, filename)
            if not transcription.strip():
                raise HTTPException(status_code=400, detail="No speech detected in audio file")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error transcribing audio: {str(e)}")
        
        # Add transcribed message to conversation
        user_message = Message(role=MessageRole.USER, content=transcription)
        conversation.messages.append(user_message)
        
    else:
        # Generate initial message (no user input)
        transcription = ""  # No transcription for initial message
        initial_prompt = f"""You are {character_context.name} talking to a friend for emotional support.

CHARACTER CONTEXT:
- Mental State: {character_context.mental_state}
- Problem: {character_context.problem}
- Background: {character_context.background}

CONVERSATION STYLE:
- Speak naturally like a real person, not a formal therapy client
- Use casual, conversational language with contractions (I'm, you're, don't, etc.)
- Express emotions authentically - be vulnerable, honest, and human
- Use personal pronouns and speak from your own experience
- Avoid overly formal or clinical language
- Show personality and character quirks
- Be specific about your feelings and experiences

TASK: Write a brief opening statement (1-2 sentences) explaining what's on your mind and why you need to talk. Be honest about your current struggles and emotional state. Speak naturally like you're talking to a close friend, not seeking professional help."""
        
        # Add system message to conversation for context
        system_message = Message(role=MessageRole.SYSTEM, content=initial_prompt)
        conversation.messages.append(system_message)
    
    # Step 4: Generate character response
    try:
        character_response = await generate_character_response(
            messages=conversation.messages,
            character_context=character_context,
            current_emotional_state=conversation.emotional_state
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating character response: {str(e)}")
    
    # Step 5: Add character response to conversation and update emotional state
    assistant_message = Message(
        role=MessageRole.ASSISTANT, content=character_response.comment
    )
    conversation.messages.append(assistant_message)
    
    new_emotional_state = conversation.emotional_state + character_response.emotional_change
    conversation.emotional_state = max(0, min(100, new_emotional_state))
    
    conversation.updated_at = datetime.now(UTC)
    if not conversation.title:
        if request.audio_file_path:
            conversation.title = f"Zombie Therapy: {transcription[:30]}..."
        else:
            conversation.title = f"Zombie Therapy: Initial Session"
    
    # Step 6: Save conversation
    try:
        await save_conversation(conversation)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving conversation: {str(e)}")
    
    # Step 7: Check if session should end
    session_ended = conversation.emotional_state <= 0 or conversation.emotional_state >= 100
    
    return ZombieInteractionResponse(
        transcription=transcription,
        character_response=character_response.comment,
        emotional_change=character_response.emotional_change,
        emotional_state=conversation.emotional_state,
        session_ended=session_ended,
    )
