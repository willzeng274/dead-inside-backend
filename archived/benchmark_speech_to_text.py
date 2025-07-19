#!/usr/bin/env python3
"""
Speech-to-Text Benchmark Script

This script benchmarks various speech-to-text services for speed and accuracy.
Run with: python benchmark_speech_to_text.py
"""

import asyncio
import time
import os
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

# Import our speech-to-text providers
from app.core.speech_to_text import (
    OpenAIWhisperProvider,
    GoogleCloudSpeechProvider,
    SpeechToTextProvider,
)


@dataclass
class BenchmarkResult:
    """Results from a single benchmark run."""

    provider_name: str
    latency: float
    transcript: str
    success: bool
    error: Optional[str] = None


class SpeechToTextBenchmark:
    """Benchmark different speech-to-text providers."""

    def __init__(self, test_audio_path: str):
        self.test_audio_path = test_audio_path
        self.results: List[BenchmarkResult] = []

        # Initialize providers
        self.providers: Dict[str, SpeechToTextProvider] = {}
        self._setup_providers()

    def _setup_providers(self):
        """Setup available speech-to-text providers."""

        # OpenAI providers
        try:
            self.providers["OpenAI-GPT4o-Transcribe"] = OpenAIWhisperProvider(
                "gpt-4o-transcribe"
            )
            self.providers["OpenAI-Whisper-1"] = OpenAIWhisperProvider("whisper-1")
        except Exception as e:
            print(f"Warning: OpenAI providers not available: {e}")

        # Google Cloud Speech
        try:
            self.providers["Google-Cloud-Speech"] = GoogleCloudSpeechProvider()
        except Exception as e:
            print(f"Warning: Google Cloud Speech not available: {e}")

        # Additional fast providers
        self._setup_additional_providers()

    def _setup_additional_providers(self):
        """Setup additional fast speech-to-text providers."""

        # Faster Whisper (faster OpenAI Whisper implementation)
        try:
            from app.core.speech_to_text import FasterWhisperProvider

            self.providers["Faster-Whisper"] = FasterWhisperProvider()
        except ImportError:
            print(
                "Faster Whisper not available. Install with: pip install faster-whisper"
            )
        except Exception as e:
            print(f"Warning: Faster Whisper not available: {e}")

        # WhisperX (faster with word-level timestamps)
        try:
            from app.core.speech_to_text import WhisperXProvider

            self.providers["WhisperX"] = WhisperXProvider()
        except ImportError:
            print("WhisperX not available. Install with: pip install whisperx")
        except Exception as e:
            print(f"Warning: WhisperX not available: {e}")

    async def benchmark_provider(
        self, provider_name: str, provider: SpeechToTextProvider
    ) -> BenchmarkResult:
        """Benchmark a single provider."""

        try:
            # Read test audio file
            with open(self.test_audio_path, "rb") as f:
                audio_bytes = f.read()

            # Run transcription
            start_time = time.time()
            transcript = await provider.transcribe(audio_bytes, "test_audio.wav")
            end_time = time.time()

            latency = end_time - start_time

            return BenchmarkResult(
                provider_name=provider_name,
                latency=latency,
                transcript=transcript,
                success=True,
            )

        except Exception as e:
            return BenchmarkResult(
                provider_name=provider_name,
                latency=0.0,
                transcript="",
                success=False,
                error=str(e),
            )

    async def run_benchmark(
        self, num_runs: int = 3
    ) -> Dict[str, List[BenchmarkResult]]:
        """Run benchmark for all providers multiple times."""

        print(f"Starting speech-to-text benchmark with {num_runs} runs per provider...")
        print(f"Test audio file: {self.test_audio_path}")
        print(f"Available providers: {list(self.providers.keys())}")
        print("-" * 60)

        all_results: Dict[str, List[BenchmarkResult]] = {}

        for provider_name, provider in self.providers.items():
            print(f"\nBenchmarking {provider_name}...")
            provider_results = []

            for run in range(num_runs):
                print(f"  Run {run + 1}/{num_runs}...")
                result = await self.benchmark_provider(provider_name, provider)
                provider_results.append(result)

                if result.success:
                    print(f"    ✓ {result.latency:.2f}s - {result.transcript[:50]}...")
                else:
                    print(f"    ✗ Error: {result.error}")

            all_results[provider_name] = provider_results

        return all_results

    def analyze_results(self, results: Dict[str, List[BenchmarkResult]]) -> None:
        """Analyze and display benchmark results."""

        print("\n" + "=" * 80)
        print("BENCHMARK RESULTS")
        print("=" * 80)

        # Calculate statistics
        stats = {}
        for provider_name, provider_results in results.items():
            successful_runs = [r for r in provider_results if r.success]

            if successful_runs:
                latencies = [r.latency for r in successful_runs]
                avg_latency = sum(latencies) / len(latencies)
                min_latency = min(latencies)
                max_latency = max(latencies)

                # Calculate accuracy (simple word count comparison)
                transcripts = [r.transcript for r in successful_runs]
                avg_transcript_length = sum(len(t.split()) for t in transcripts) / len(
                    transcripts
                )

                stats[provider_name] = {
                    "success_rate": len(successful_runs) / len(provider_results),
                    "avg_latency": avg_latency,
                    "min_latency": min_latency,
                    "max_latency": max_latency,
                    "avg_transcript_length": avg_transcript_length,
                    "sample_transcript": (
                        successful_runs[0].transcript[:100] + "..."
                        if successful_runs[0].transcript
                        else "No transcript"
                    ),
                }
            else:
                stats[provider_name] = {
                    "success_rate": 0.0,
                    "avg_latency": float("inf"),
                    "min_latency": float("inf"),
                    "max_latency": float("inf"),
                    "avg_transcript_length": 0,
                    "sample_transcript": "Failed",
                }

        # Sort by average latency
        sorted_stats = sorted(stats.items(), key=lambda x: x[1]["avg_latency"])

        # Display results table
        print(
            f"{'Provider':<25} {'Success Rate':<12} {'Avg Latency':<12} {'Min Latency':<12} {'Max Latency':<12} {'Avg Words':<10}"
        )
        print("-" * 100)

        for provider_name, stat in sorted_stats:
            if stat["success_rate"] > 0:
                print(
                    f"{provider_name:<25} {stat['success_rate']:<12.1%} {stat['avg_latency']:<12.2f}s {stat['min_latency']:<12.2f}s {stat['max_latency']:<12.2f}s {stat['avg_transcript_length']:<10.0f}"
                )
            else:
                print(
                    f"{provider_name:<25} {'FAILED':<12} {'N/A':<12} {'N/A':<12} {'N/A':<12} {'N/A':<10}"
                )

        # Show sample transcripts
        print("\n" + "=" * 80)
        print("SAMPLE TRANSCRIPTS")
        print("=" * 80)

        for provider_name, stat in sorted_stats:
            if stat["success_rate"] > 0:
                print(f"\n{provider_name}:")
                print(f"  {stat['sample_transcript']}")

        # Recommendations
        print("\n" + "=" * 80)
        print("RECOMMENDATIONS")
        print("=" * 80)

        fast_providers = [
            name
            for name, stat in sorted_stats
            if stat["success_rate"] > 0 and stat["avg_latency"] < 2.0
        ]
        reliable_providers = [
            name for name, stat in sorted_stats if stat["success_rate"] >= 0.8
        ]

        if fast_providers:
            print(f"Fastest providers (< 2s): {', '.join(fast_providers)}")

        if reliable_providers:
            print(
                f"Most reliable providers (≥80% success): {', '.join(reliable_providers)}"
            )

        if sorted_stats:
            fastest = sorted_stats[0]
            if fastest[1]["success_rate"] > 0:
                print(
                    f"Recommended for speed: {fastest[0]} ({fastest[1]['avg_latency']:.2f}s average)"
                )


async def main():
    """Main benchmark function."""

    # Use the specific audio file
    test_audio_path = "/Users/user/Downloads/Recording.wav"
    if not os.path.exists(test_audio_path):
        print(f"Error: Test audio file '{test_audio_path}' not found.")
        print("Please check the file path.")
        return

    print(f"Using audio file: {test_audio_path}")

    # Run benchmark
    benchmark = SpeechToTextBenchmark(test_audio_path)
    results = await benchmark.run_benchmark(num_runs=3)
    benchmark.analyze_results(results)


if __name__ == "__main__":
    asyncio.run(main())
