from fastapi import APIRouter, HTTPException, UploadFile

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
    audio_file: UploadFile
):
    """
    Endpoint for speech-to-text functionality.
    """
    bytes_audio = await audio_file.read()

    try:
        transcription = await transcribe_audio(bytes_audio, audio_file.filename)
        return transcription
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing audio: {str(e)}")
