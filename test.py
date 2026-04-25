"""Local smoke test for the legal AI platform."""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def load_module(name: str, path: Path):
    spec = spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


classification_module = load_module("classification_service", ROOT / "services" / "classification-service" / "service.py")
compliance_module = load_module("compliance_service", ROOT / "services" / "compliance-service" / "service.py")


def main() -> None:
    sample = "The tax authority requests VAT records within 5 days."
    classification = classification_module.classify_text(sample)
    draft = (
        "Background. Analysis. Conclusion. respectfully subject to verification without prejudice based on the documents reviewed."
    )
    compliance = compliance_module.check_compliance(draft, classification.authority)
    print(
        {
            "classification": classification.model_dump(),
            "compliance": compliance.model_dump(),
        }
    )


if __name__ == "__main__":
    main()
