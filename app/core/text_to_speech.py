import os
from pathlib import Path
from enum import Enum

from pydantic import BaseModel, Field
from app.core.config import llm_client
from pydub import AudioSegment
from app.core.llm import get_character


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
        
        # Fetch character from Redis to get voice and instructions
        character = await get_character(request.character_id)
        if not character:
            raise Exception(f"Character {request.character_id} not found in Redis")
        voice = character.get("voice_selection", "alloy")
        voice_instructions = character.get("voice_instructions", "")
        
        response = await llm_client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice=voice,
            input=full_text,
            instructions=voice_instructions
        )
        
        with open(request.stored_file_path, "wb") as f:
            f.write(response.content)
        
        ext = os.path.splitext(request.stored_file_path)[1].lower()
        if ext != ".mp3":
            temp_mp3_path = request.stored_file_path + ".temp.mp3"
            os.rename(request.stored_file_path, temp_mp3_path)
            audio = AudioSegment.from_file(temp_mp3_path, format="mp3")
            audio.export(request.stored_file_path, format=ext[1:])
            os.remove(temp_mp3_path)
            
    except Exception as e:
        raise Exception(f"Failed to generate TTS: {str(e)}")


async def text_to_speech(text: str, stored_file_path: str, character_id: str) -> str:
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
    request = TTSRequest(text=text, stored_file_path=stored_file_path, character_id=character_id)
    await generate_tts(request)
    return stored_file_path 