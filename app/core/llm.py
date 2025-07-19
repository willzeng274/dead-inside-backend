import io
from app.core.config import llm_client, settings

async def transcribe_audio(bytes_audio: bytes, filename: str) -> str:
    """
    Transcribe audio file to text using a speech-to-text model.

    Args:
        bytes_audio (bytes): The audio file content as bytes
        filename (str): The name of the audio file
    """

    file_obj = io.BytesIO(bytes_audio)
    file_obj.name = filename

    transcription = await llm_client.audio.transcriptions.create(
        model=settings.SPEECH_TO_TEXT_MODEL,
        file=file_obj,
    )

    return transcription.text
