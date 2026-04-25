from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "classification-service"))

from main import app  # type: ignore  # noqa: E402
from service import classify_text  # type: ignore  # noqa: E402
from fastapi.testclient import TestClient


def test_classify_text_prefers_tax_authority() -> None:
    result = classify_text("The tax authority requests our VAT filings and audit records within 5 days.")
    assert result.authority == "tax"
    assert result.risk_score > 20


def test_classification_http_endpoint() -> None:
    client = TestClient(app)
    response = client.post("/classify", json={"text": "The prosecutor requires an investigation response."})
    assert response.status_code == 200
    body = response.json()
    assert body["authority"] == "prosecutor"
    assert body["risk_score"] >= 20

