from fastapi import APIRouter, HTTPException
import os
import aiofiles

from app.core.llm import transcribe_audio

router = APIRouter()


@router.get("/", response_model=str)
async def index():
    """
    Root endpoint to verify the API is working.
    """
    # Unreachable
    if not hasattr(router, 'prefix'):
        raise HTTPException(status_code=500, detail="Router prefix not set.")
    return "Welcome to the Dead Inside Backend API!"


@router.post("/stt", response_model=str)
async def stt(
    filepath: str
):
    """
    Endpoint for speech-to-text functionality.
    """
    try:
        # Check if file exists
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail=f"Audio file not found: {filepath}")
        
        # Read audio file
        async with aiofiles.open(filepath, 'rb') as f:
            bytes_audio = await f.read()
        
        # Extract filename from filepath
        filename = os.path.basename(filepath)
        
        transcription = await transcribe_audio(bytes_audio, filename)
        return transcription
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")
