import io
import os
import time
from typing import Optional
import tempfile

from app.core.config import settings


def get_device():
    """Get the best available device for faster-whisper."""
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
        # Note: faster-whisper doesn't support MPS (Apple Silicon GPU)
        # It only supports CUDA and CPU
        else:
            return "cpu"
    except ImportError:
        return "cpu"


def get_compute_type(device: str):
    """Get the best compute type for the device."""
    if device == "cuda":
        return "float16"  # Best performance on CUDA
    else:
        return "int8"  # Best performance on CPU


class FasterWhisperProvider:
    """Faster Whisper provider with CUDA support."""
    
    def __init__(self, model_size: str = "base", device: Optional[str] = None, compute_type: Optional[str] = None):
        try:
            from faster_whisper import WhisperModel
            
            # Auto-detect device if not specified
            if device is None:
                device = get_device()
            
            # Auto-detect compute type if not specified
            if compute_type is None:
                compute_type = get_compute_type(device)
            
            print(f"Initializing Faster Whisper with device={device}, compute_type={compute_type}")
            
            self.model = WhisperModel(
                model_size, 
                device=device, 
                compute_type=compute_type
            )
            self.device = device
            self.compute_type = compute_type
            
        except ImportError:
            raise ImportError("Faster Whisper not installed. Run: pip install faster-whisper")
    
    async def transcribe(self, bytes_audio: bytes, filename: str) -> str:
        """Transcribe audio using Faster Whisper."""
        
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
        print(f"Faster Whisper ({self.device}) transcription latency: {latency:.2f} seconds")
        
        return transcript.strip()


# Default provider instance
speech_to_text_provider = FasterWhisperProvider()


async def transcribe_audio(bytes_audio: bytes, filename: str) -> str:
    """
    Transcribe audio file to text using Faster Whisper.
    
    Args:
        bytes_audio (bytes): The audio file content as bytes
        filename (str): The name of the audio file
    
    Returns:
        str: Transcribed text
    """
    return await speech_to_text_provider.transcribe(bytes_audio, filename)


def create_provider(model_size: str = "base", device: Optional[str] = None, compute_type: Optional[str] = None) -> FasterWhisperProvider:
    """
    Create a custom Faster Whisper provider with specific settings.
    
    Args:
        model_size: Model size (tiny, base, small, medium, large)
        device: Device to use (cuda, mps, cpu)
        compute_type: Compute type (float16, int8, int8_float16)
    
    Returns:
        FasterWhisperProvider: Configured provider
    """
    return FasterWhisperProvider(model_size=model_size, device=device, compute_type=compute_type) 