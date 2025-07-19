import io
import os
import time
from typing import Optional
from abc import ABC, abstractmethod

from app.core.config import llm_client, settings


class SpeechToTextProvider(ABC):
    """Abstract base class for speech-to-text providers."""
    
    @abstractmethod
    async def transcribe(self, bytes_audio: bytes, filename: str) -> str:
        """Transcribe audio to text."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass


class OpenAIWhisperProvider(SpeechToTextProvider):
    """OpenAI Whisper speech-to-text provider."""
    
    def __init__(self, model: str = "gpt-4o-transcribe"):
        self.model = model
    
    @property
    def name(self) -> str:
        return f"OpenAI-{self.model}"
    
    async def transcribe(self, bytes_audio: bytes, filename: str) -> str:
        """Transcribe audio using OpenAI Whisper."""
        file_obj = io.BytesIO(bytes_audio)
        file_obj.name = filename
        
        start_time = time.time()
        
        transcription = await llm_client.audio.transcriptions.create(
            model=self.model,
            file=file_obj,
        )
        
        end_time = time.time()
        latency = end_time - start_time
        print(f"OpenAI transcription latency: {latency:.2f} seconds")
        
        return transcription.text


class GoogleCloudSpeechProvider(SpeechToTextProvider):
    """Google Cloud Speech-to-Text provider."""
    
    def __init__(self):
        try:
            from google.cloud import speech
            self.client = speech.SpeechClient()
        except ImportError:
            raise ImportError("google-cloud-speech not installed. Run: pip install google-cloud-speech")
    
    @property
    def name(self) -> str:
        return "Google-Cloud-Speech"
    
    async def transcribe(self, bytes_audio: bytes, filename: str) -> str:
        """Transcribe audio using Google Cloud Speech-to-Text."""
        from google.cloud import speech
        
        start_time = time.time()
        
        # Configure audio
        audio = speech.RecognitionAudio(content=bytes_audio)
        
        # Configure recognition
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,  # Adjust based on your audio
            language_code="en-US",
            enable_automatic_punctuation=True,
        )
        
        # Perform transcription
        response = self.client.recognize(config=config, audio=audio)
        
        end_time = time.time()
        latency = end_time - start_time
        print(f"Google Cloud transcription latency: {latency:.2f} seconds")
        
        # Extract transcript
        transcript = ""
        for result in response.results:
            transcript += result.alternatives[0].transcript + " "
        
        return transcript.strip()


class FasterWhisperProvider(SpeechToTextProvider):
    """Faster Whisper provider (faster OpenAI Whisper implementation)."""
    
    def __init__(self, model_size: str = "base"):
        try:
            from faster_whisper import WhisperModel
            self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
        except ImportError:
            raise ImportError("Faster Whisper not installed. Run: pip install faster-whisper")
    
    @property
    def name(self) -> str:
        return "Faster-Whisper"
    
    async def transcribe(self, bytes_audio: bytes, filename: str) -> str:
        """Transcribe audio using Faster Whisper."""
        import tempfile
        
        start_time = time.time()
        
        # Save audio to temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(bytes_audio)
            temp_file_path = temp_file.name
        
        try:
            # Transcribe
            segments, _ = self.model.transcribe(temp_file_path)
            transcript = " ".join([segment.text for segment in segments])
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
        
        end_time = time.time()
        latency = end_time - start_time
        print(f"Faster Whisper transcription latency: {latency:.2f} seconds")
        
        return transcript.strip()


class WhisperXProvider(SpeechToTextProvider):
    """WhisperX provider (faster with word-level timestamps)."""
    
    def __init__(self, model_size: str = "base"):
        try:
            import whisperx
            self.model = whisperx.load_model(model_size, device="cpu", compute_type="int8")
        except ImportError:
            raise ImportError("WhisperX not installed. Run: pip install whisperx")
    
    @property
    def name(self) -> str:
        return "WhisperX"
    
    async def transcribe(self, bytes_audio: bytes, filename: str) -> str:
        """Transcribe audio using WhisperX."""
        import tempfile
        
        start_time = time.time()
        
        # Save audio to temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(bytes_audio)
            temp_file_path = temp_file.name
        
        try:
            # Transcribe
            result = self.model.transcribe(temp_file_path)
            transcript = result["segments"][0]["text"] if result["segments"] else ""
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
        
        end_time = time.time()
        latency = end_time - start_time
        print(f"WhisperX transcription latency: {latency:.2f} seconds")
        
        return transcript.strip()


class SpeechToTextService:
    """Main speech-to-text service that can use different providers."""
    
    def __init__(self, provider: Optional[SpeechToTextProvider] = None):
        self.provider = provider or OpenAIWhisperProvider(settings.SPEECH_TO_TEXT_MODEL)
    
    async def transcribe(self, bytes_audio: bytes, filename: str) -> str:
        """Transcribe audio using the configured provider."""
        return await self.provider.transcribe(bytes_audio, filename)


# Default service instance
speech_to_text_service = SpeechToTextService()


async def transcribe_audio(bytes_audio: bytes, filename: str) -> str:
    """
    Transcribe audio file to text using the default speech-to-text service.
    
    Args:
        bytes_audio (bytes): The audio file content as bytes
        filename (str): The name of the audio file
    
    Returns:
        str: Transcribed text
    """
    return await speech_to_text_service.transcribe(bytes_audio, filename) 