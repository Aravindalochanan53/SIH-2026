"""
Seed Database Script for TRANSLARA.
Run: python scripts/seed_database.py
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.cache.seed_cache import seed_all

if __name__ == "__main__":
    print("Seeding TRANSLARA database...")
    phrases_count, entities_count = seed_all()
    print(f"Seeding completed successfully!")
    print(f"- Seeded {phrases_count} multilingual phrases")
    print(f"- Seeded {entities_count} entity gazetteer records")
