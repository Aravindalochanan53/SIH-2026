"""
Production Model Downloader for TRANSLARA.
Run: python scripts/download_models.py --backend all
"""
import argparse
from pathlib import Path


def download_faster_whisper(model_size="small", dest_dir="./models"):
    print(f"Downloading Multilingual Faster-Whisper ({model_size}) into {dest_dir}...")
    try:
        from faster_whisper import WhisperModel
        WhisperModel(model_size, download_root=dest_dir)
        print("Faster-Whisper model downloaded successfully.")
    except ImportError:
        print("faster-whisper package not installed. Run: pip install faster-whisper")


def download_indictrans2(model_id="ai4bharat/indictrans2-indic-indic-dist-320M", dest_dir="./models"):
    print(f"Downloading IndicTrans2 ({model_id})...")
    try:
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        AutoTokenizer.from_pretrained(model_id, trust_remote_code=True, cache_dir=dest_dir)
        AutoModelForSeq2SeqLM.from_pretrained(model_id, trust_remote_code=True, cache_dir=dest_dir)
        print("IndicTrans2 downloaded successfully.")
    except ImportError:
        print("transformers / torch not installed. Run: pip install transformers torch")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download AI models for local inference")
    parser.add_argument("--backend", default="whisper", choices=["whisper", "indictrans2", "all"])
    parser.add_argument("--dest", default="./models")
    args = parser.parse_args()

    Path(args.dest).mkdir(parents=True, exist_ok=True)

    if args.backend in ("whisper", "all"):
        download_faster_whisper(dest_dir=args.dest)
    if args.backend in ("indictrans2", "all"):
        download_indictrans2(dest_dir=args.dest)
