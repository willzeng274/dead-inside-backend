#!/usr/bin/env python3
"""
OpenAI TTS Benchmark Script

Benchmarks the three OpenAI TTS models: gpt-4o-mini-tts, tts-1, and tts-1-hd
Run with: python benchmark_tts.py
"""

import asyncio
import time
import json
from typing import Dict, List
from dataclasses import dataclass
from pathlib import Path
from enum import Enum

from pydantic import BaseModel, Field
from app.core.config import llm_client


class TTSModel(str, Enum):
    """Available OpenAI TTS models"""
    GPT4O_MINI_TTS = "gpt-4o-mini-tts"
    TTS_1 = "tts-1"
    TTS_1_HD = "tts-1-hd"


class TTSVoice(str, Enum):
    """Available TTS voices"""
    ALLOY = "alloy"
    ECHO = "echo"
    FABLE = "fable"
    ONYX = "onyx"
    NOVA = "nova"
    SHIMMER = "shimmer"


class TTSBenchmarkConfig(BaseModel):
    """Configuration for TTS benchmarking"""
    test_texts: List[str] = Field(
        default=[
            "Hello, this is a test of the text-to-speech system.",
            "The quick brown fox jumps over the lazy dog.",
            "Artificial intelligence is transforming technology.",
        ]
    )
    voices: List[TTSVoice] = Field(default=[TTSVoice.ALLOY, TTSVoice.NOVA])
    num_runs: int = Field(default=3)
    output_dir: str = Field(default="./tts_benchmark_output")


@dataclass
class TTSResult:
    """Results from a single TTS benchmark run."""
    model: str
    voice: str
    text: str
    latency: float
    file_size: int
    success: bool
    error: str = None


class TTSBenchmark:
    """Benchmark OpenAI TTS models."""

    def __init__(self, config: TTSBenchmarkConfig):
        self.config = config
        self.client = llm_client
        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(exist_ok=True)

    async def benchmark_single(self, model: TTSModel, voice: TTSVoice, text: str) -> TTSResult:
        """Benchmark a single TTS generation."""
        try:
            timestamp = int(time.time() * 1000)
            filename = f"{model.value}_{voice.value}_{timestamp}.mp3"
            file_path = self.output_dir / filename
            
            start_time = time.time()
            response = await self.client.audio.speech.create(
                model=model.value,
                voice=voice.value,
                input=text
            )
            response.stream_to_file(str(file_path))
            latency = time.time() - start_time
            
            file_size = file_path.stat().st_size
            
            return TTSResult(
                model=model.value,
                voice=voice.value,
                text=text,
                latency=latency,
                file_size=file_size,
                success=True
            )
        except Exception as e:
            return TTSResult(
                model=model.value,
                voice=voice.value,
                text=text,
                latency=0.0,
                file_size=0,
                success=False,
                error=str(e)
            )

    async def run_benchmark(self) -> Dict[str, List[TTSResult]]:
        """Run benchmark for all combinations."""
        print(f"Benchmarking TTS models: {[m.value for m in TTSModel]}")
        print(f"Voices: {[v.value for v in self.config.voices]}")
        print(f"Texts: {len(self.config.test_texts)}")
        print(f"Runs per combination: {self.config.num_runs}")
        print("-" * 60)
        
        results = {}
        
        for model in TTSModel:
            model_results = []
            print(f"\nTesting {model.value}...")
            
            for voice in self.config.voices:
                for text in self.config.test_texts:
                    for run in range(self.config.num_runs):
                        result = await self.benchmark_single(model, voice, text)
                        model_results.append(result)
                        
                        if result.success:
                            print(f"  ✓ {result.latency:.2f}s - {result.file_size} bytes")
                        else:
                            print(f"  ✗ Error: {result.error}")
            
            results[model.value] = model_results
        
        return results

    def analyze_results(self, results: Dict[str, List[TTSResult]]) -> None:
        """Analyze and display results."""
        print("\n" + "=" * 80)
        print("TTS BENCHMARK RESULTS")
        print("=" * 80)
        
        for model_name, model_results in results.items():
            successful = [r for r in model_results if r.success]
            
            if successful:
                latencies = [r.latency for r in successful]
                file_sizes = [r.file_size for r in successful]
                
                print(f"\n{model_name}:")
                print(f"  Success Rate: {len(successful)}/{len(model_results)} ({len(successful)/len(model_results):.1%})")
                print(f"  Avg Latency: {sum(latencies)/len(latencies):.2f}s")
                print(f"  Min Latency: {min(latencies):.2f}s")
                print(f"  Max Latency: {max(latencies):.2f}s")
                print(f"  Avg File Size: {sum(file_sizes)/len(file_sizes):.0f} bytes")
            else:
                print(f"\n{model_name}: Failed")
        
        # Save results
        results_file = self.output_dir / "benchmark_results.json"
        with open(results_file, 'w') as f:
            json.dump({
                "results": {
                    model: [
                        {
                            "model": r.model,
                            "voice": r.voice,
                            "text": r.text,
                            "latency": r.latency,
                            "file_size": r.file_size,
                            "success": r.success,
                            "error": r.error
                        }
                        for r in model_results
                    ]
                    for model, model_results in results.items()
                }
            }, f, indent=2)
        
        print(f"\nResults saved to: {results_file}")
        print(f"Audio files saved to: {self.output_dir}")


async def main():
    """Run the TTS benchmark."""
    config = TTSBenchmarkConfig()
    benchmark = TTSBenchmark(config)
    results = await benchmark.run_benchmark()
    benchmark.analyze_results(results)


if __name__ == "__main__":
    asyncio.run(main()) 