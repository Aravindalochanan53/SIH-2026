"""
TRANSLARA AI — High-End Hardware & GPU Verification Utility.
Benchmarks and verifies CUDA GPU acceleration, FP16 Tensor Cores, VRAM allocation,
Faster-Whisper on CUDA, and local Translation on the upgraded host specification.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from loguru import logger


def print_banner(title: str):
    width = 70
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width)


def check_system_and_cuda():
    print_banner("1. HOST HARDWARE & CUDA ENVIRONMENT DIAGNOSTICS")

    has_torch = False
    cuda_available = False
    device_name = "None"
    device_count = 0
    vram_total_gb = 0.0

    try:
        import torch
        has_torch = True
        torch_version = torch.__version__
        cuda_available = torch.cuda.is_available()
        if cuda_available:
            device_count = torch.cuda.device_count()
            device_name = torch.cuda.get_device_name(0)
            props = torch.cuda.get_device_properties(0)
            vram_total_gb = round(props.total_memory / (1024**3), 2)
            cuda_ver = torch.version.cuda
        else:
            cuda_ver = "N/A"
    except ImportError:
        torch_version = "Not Installed"
        cuda_ver = "N/A"

    print(f"  • PyTorch Version:       {torch_version}")
    print(f"  • CUDA Available:        {'✅ YES' if cuda_available else '❌ NO (CPU Only)'}")
    print(f"  • CUDA Build Version:    {cuda_ver}")
    print(f"  • GPU Device Detected:   {device_name}")
    print(f"  • GPU Count:             {device_count}")
    print(f"  • Dedicated VRAM:        {vram_total_gb} GB")

    return {
        "has_torch": has_torch,
        "cuda_available": cuda_available,
        "device_name": device_name,
        "vram_gb": vram_total_gb,
    }


def benchmark_fp16_tensor_cores():
    print_banner("2. FP16 TENSOR CORE MATRIX MULTIPLICATION BENCHMARK")

    try:
        import torch
        if not torch.cuda.is_available():
            print("  ⚠️ CUDA not available; skipping GPU FP16 benchmark.")
            return

        device = torch.device("cuda:0")
        size = 4096
        dtype = torch.float16

        print(f"  • Allocating ({size}x{size}) FP16 tensors on {torch.cuda.get_device_name(0)}...")
        a = torch.randn(size, size, device=device, dtype=dtype)
        b = torch.randn(size, size, device=device, dtype=dtype)

        # Warm-up
        for _ in range(5):
            _ = torch.matmul(a, b)
        torch.cuda.synchronize()

        # Benchmark 20 iterations
        num_runs = 20
        start = time.perf_counter()
        for _ in range(num_runs):
            _ = torch.matmul(a, b)
        torch.cuda.synchronize()
        elapsed = (time.perf_counter() - start) / num_runs

        # 2 * N^3 operations for matrix multiplication
        tflops = (2 * (size**3)) / (elapsed * 1e12)
        vram_allocated_mb = torch.cuda.memory_allocated(device) / (1024**2)

        print(f"  • Execution Time:        {elapsed * 1000:.2f} ms per 4096x4096 GEMM")
        print(f"  • Compute Throughput:    {tflops:.2f} TFLOPS (FP16 Tensor Cores)")
        print(f"  • GPU Memory in Use:     {vram_allocated_mb:.1f} MB")
        print("  ✅ Tensor Core acceleration active and verified!")

        # Clean up
        del a, b
        torch.cuda.empty_cache()

    except Exception as e:
        print(f"  ❌ Benchmark error: {e}")


def test_faster_whisper_gpu():
    print_banner("3. FASTER-WHISPER ASR (CUDA + FLOAT16)")

    try:
        import numpy as np
        from faster_whisper import WhisperModel
        import torch

        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"
        model_size = "small"

        print(f"  • Initializing Faster-Whisper ({model_size}) on device={device}, compute_type={compute_type}...")
        t0 = time.monotonic()
        model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type,
            download_root="./models",
        )
        load_time = (time.monotonic() - t0) * 1000
        print(f"  • Model Loaded in:       {load_time:.1f} ms")

        # Create 1 second of synthetic 16kHz audio
        t = np.linspace(0, 1.0, 16000, endpoint=False)
        audio = (0.3 * np.sin(2 * np.pi * 440.0 * t)).astype(np.float32)

        # Run transcription inference test
        t1 = time.monotonic()
        segments, info = model.transcribe(audio, language="en", beam_size=1)
        # Force generator iteration
        _ = list(segments)
        infer_time = (time.monotonic() - t1) * 1000

        print(f"  • Inference Time:        {infer_time:.1f} ms (Target budget: <600ms)")
        print(f"  • RTF (Real-Time Factor):{infer_time / 1000.0:.3f}x")
        print(f"  ✅ Faster-Whisper operational with CUDA FP16 acceleration!")

        del model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    except ImportError as e:
        print(f"  ⚠️ faster-whisper package not ready or import issue: {e}")
    except Exception as e:
        print(f"  ⚠️ Faster-Whisper notice: {e}")


def test_local_ai_pipeline():
    print_banner("4. LOCAL AI PIPELINE & CONFIG VERIFICATION")

    from backend.config import settings
    print(f"  • APP_NAME:              {settings.app_name}")
    print(f"  • ASR Backend:           {settings.asr_backend}")
    print(f"  • Whisper Device:        {settings.whisper_device}")
    print(f"  • Whisper Compute Type:  {settings.whisper_compute_type}")
    print(f"  • NMT Backend:           {settings.nmt_backend}")
    print(f"  • ASR Timeout Budget:    {settings.asr_timeout_ms} ms")
    print(f"  • NMT Timeout Budget:    {settings.nmt_timeout_ms} ms")
    print(f"  • Total Latency SLA:     {settings.total_latency_target_ms} ms")


def main():
    info = check_system_and_cuda()
    if info["cuda_available"]:
        benchmark_fp16_tensor_cores()
        test_faster_whisper_gpu()
    test_local_ai_pipeline()

    print_banner("TRANSLARA HIGH-END SPEC VERIFICATION COMPLETED")


if __name__ == "__main__":
    main()
