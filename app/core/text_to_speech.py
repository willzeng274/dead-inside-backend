import os
import tempfile
from pathlib import Path
from typing import Optional
from enum import Enum

from pydantic import BaseModel, Field
from app.core.config import llm_client


class TTSVoice(str, Enum):
    """Available TTS voices for character speech"""
    ASH = "ash"
    BALLAD = "ballad"
    FABLE = "fable"
    CORAL = "coral"
    ONYX = "onyx"
    NOVA = "nova"
    SHIMMER = "shimmer"
    VERSE = "verse"


class TTSRequest(BaseModel):
    """Request model for text-to-speech"""
    text: str = Field(..., min_length=1, max_length=4000, description="Text to convert to speech")
    stored_file_path: str = Field(..., description="Path to the stored audio file")
    character_id: str = Field(..., description="Character UUID to get voice settings from")
    voice: str = Field(default="alloy", description="Voice to use for speech synthesis")


async def generate_tts(request: TTSRequest):
    """
    Generate text-to-speech audio using OpenAI's gpt-4o-mini-tts model.
    
    Args:
        request: TTSRequest containing text, voice, and optional parameters
        
    Returns:
        None (writes audio to stored_file_path)
        
    Raises:
        ValueError: If text is empty or too long
        Exception: If TTS generation fails
    """
    if not request.text.strip():
        raise ValueError("Text cannot be empty")
    
    if len(request.text) > 4000:
        raise ValueError("Text is too long (max 4000 characters)")
    
    full_text = request.text
    
    try:
        # Ensure the directory exists
        output_dir = os.path.dirname(request.stored_file_path)
        if output_dir:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        response = await llm_client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice=request.voice,
            input=full_text
        )
        
        # Write directly to the specified path
        with open(request.stored_file_path, "wb") as f:
            f.write(response.content)
            
    except Exception as e:
        raise Exception(f"Failed to generate TTS: {str(e)}")


async def text_to_speech(text: str, stored_file_path: str, character_id: str, voice: str = "alloy") -> str:
    """
    Simple text-to-speech function that writes to a specified path.
    
    Args:
        text: Text to convert to speech
        stored_file_path: Path where the audio file should be saved
        character_id: Character UUID to get voice settings from
        voice: Voice to use (default: "alloy")
        
    Returns:
        Path to the generated audio file
    """
    request = TTSRequest(text=text, stored_file_path=stored_file_path, character_id=character_id, voice=voice)
    await generate_tts(request)
    return stored_file_path 