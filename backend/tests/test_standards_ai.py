import json
import pytest
from app.ai.standards_intelligence import MAX_INPUT_BYTES, compose_envelope, validate_output

def test_ai_output_accepts_only_known_safe_references():
    output = json.dumps({"suggestions":[{"handle":"stdh_a","rationale_code":"eligible","advisory":"Review this bounded reference with the responsible Human."}]}).encode()
    result = validate_output(output, known_handles={"stdh_a"}, known_codes={"eligible"})
    assert result.suggestions[0]["handle"] == "stdh_a"

@pytest.mark.parametrize("output", [b'{"suggestions":[{"handle":"invented","rationale_code":"eligible","advisory":"review"}]}', b'{"suggestions":[{"handle":"stdh_a","rationale_code":"eligible","advisory":"This is compliant."}]}'])
def test_ai_output_rejects_invented_or_authoritative_claims(output):
    with pytest.raises(ValueError): validate_output(output, known_handles={"stdh_a"}, known_codes={"eligible"})

def test_ai_context_limit_fails_closed():
    with pytest.raises(ValueError): compose_envelope(handles=("x" * MAX_INPUT_BYTES,), rationale_codes=("eligible",), purpose="x")


def test_https_standards_provider_cannot_be_mislabelled_local():
    from app.core.config import Settings

    settings = Settings(
        SATCO_ENVIRONMENT="production",
        STANDARDS_INTELLIGENCE_ENABLED=True,
        STANDARDS_INTELLIGENCE_PROVIDER_ENDPOINT="https://processor.example.test/advice",
        STANDARDS_INTELLIGENCE_PROVIDER_API_KEY="test-key",
        STANDARDS_INTELLIGENCE_PROVIDER_ID="local",
    )
    assert "standards_intelligence" in settings.production_validation_errors()
