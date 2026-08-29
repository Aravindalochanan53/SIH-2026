"""Quick verification script for TRANSLARA AI system."""
import sys
sys.path.insert(0, ".")
from backend.ml_engine.model_registry import get_model_registry

r = get_model_registry()
models = r.list_models()

print("=" * 65)
print("  TRANSLARA AI — Model Registry Status")
print("=" * 65)
for m in models:
    status_icon = "✅" if m["status"] == "READY" else "⏳"
    print(f"  {status_icon} {m['model_name']:<28s} [{m['status']:<12s}]")
    print(f"     Base: {m['base_model']}")
    print(f"     Languages: {', '.join(m['languages'][:6])}")
    if m['training_date']:
        print(f"     Trained: {m['training_date']}")
    if m['evaluation_metrics']:
        print(f"     Metrics: {m['evaluation_metrics']}")
    print()

report = r.get_status_report()
print(f"  Ready:  {report['ready_count']} / {report['total_count']} models")
print()
print(f"  {report['note']}")
print("=" * 65)
