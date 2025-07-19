#!/usr/bin/env python3
"""
Test script for Faster Whisper with CUDA support.
"""

import asyncio
import time
from app.core.speech_to_text import FasterWhisperProvider


def check_cuda_availability():
    """Check CUDA and GPU availability."""
    print("=== CUDA/GPU Availability Check ===")

    try:
        import torch

        print(f"PyTorch version: {torch.__version__}")
        print(f"CUDA available: {torch.cuda.is_available()}")

        if torch.cuda.is_available():
            print(f"CUDA version: {torch.version.cuda}")
            print(f"Number of GPUs: {torch.cuda.device_count()}")
            for i in range(torch.cuda.device_count()):
                print(f"  GPU {i}: {torch.cuda.get_device_name(i)}")
        else:
            print("CUDA not available")

        # Check Apple Silicon
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            print("Apple Silicon GPU (MPS) available")
        else:
            print("Apple Silicon GPU (MPS) not available")

    except ImportError:
        print("PyTorch not installed")

    print()


async def test_faster_whisper():
    """Test Faster Whisper with different configurations."""

    print("=== Faster Whisper Test ===")

    # Test different configurations
    configs = [
        ("Auto-detect", None, None),
        ("CUDA", "cuda", "float16"),
        ("CPU", "cpu", "int8"),
    ]

    for name, device, compute_type in configs:
        print(f"\nTesting {name} configuration...")
        try:
            provider = FasterWhisperProvider(
                model_size="base", device=device, compute_type=compute_type
            )
            print(f"✓ {name} configuration initialized successfully")
            print(f"  Device: {provider.device}")
            print(f"  Compute type: {provider.compute_type}")
        except Exception as e:
            print(f"✗ {name} configuration failed: {e}")


async def benchmark_with_audio():
    """Benchmark with actual audio file."""

    audio_path = "/Users/user/Downloads/Recording.wav"

    if not os.path.exists(audio_path):
        print(f"Audio file not found: {audio_path}")
        return

    print(f"\n=== Benchmarking with {audio_path} ===")

    # Read audio file
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()

    # Test different configurations
    configs = [
        ("Auto-detect", None, None),
        ("CUDA", "cuda", "float16"),
        ("CPU", "cpu", "int8"),
    ]

    results = []

    for name, device, compute_type in configs:
        print(f"\nBenchmarking {name}...")
        try:
            provider = FasterWhisperProvider(
                model_size="base", device=device, compute_type=compute_type
            )

            # Run transcription
            start_time = time.time()
            transcript = await provider.transcribe(audio_bytes, "test.wav")
            end_time = time.time()

            latency = end_time - start_time
            results.append((name, latency, transcript))

            print(f"  Latency: {latency:.2f}s")
            print(f"  Transcript: {transcript[:100]}...")

        except Exception as e:
            print(f"  Failed: {e}")

    # Show results summary
    print("\n=== Results Summary ===")
    for name, latency, transcript in sorted(results, key=lambda x: x[1]):
        print(f"{name}: {latency:.2f}s")


if __name__ == "__main__":
    import os

    # Check CUDA availability
    check_cuda_availability()

    # Test configurations
    asyncio.run(test_faster_whisper())

    # Benchmark with audio
    asyncio.run(benchmark_with_audio())
