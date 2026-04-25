from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "compliance-service"))

from main import app  # type: ignore  # noqa: E402
from service import check_compliance  # type: ignore  # noqa: E402
from fastapi.testclient import TestClient


def test_compliance_flags_forbidden_phrase() -> None:
    result = check_compliance(
        "Background. Analysis. Conclusion. We guarantee full compliance with this request.",
        "tax",
    )
    assert not result.passed
    assert result.forbidden_terms_found


def test_compliance_http_endpoint() -> None:
    client = TestClient(app)
    response = client.post(
        "/compliance/check",
        json={"text": "Background. Analysis. Conclusion. respectfully subject to verification without prejudice based on the documents reviewed.", "authority": "tax"},
    )
    assert response.status_code == 200
    assert response.json()["passed"] is True

