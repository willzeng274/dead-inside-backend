import os
import aiofiles

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.llm import transcribe_audio

router = APIRouter()


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
