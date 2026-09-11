from app.ai.cross_discipline_intelligence import BoundedCrossDisciplineAI


class _Provider:
    def __init__(self): self.calls = 0
    def complete(self, prompt): self.calls += 1; return "Review the explicit path."


def test_ai_is_bounded_optional_and_non_authoritative():
    provider = _Provider()
    ai = BoundedCrossDisciplineAI(provider, enabled=True)
    result = ai.explain(({"category": "potential_change_impact", "subcode": "eic.explicit_change_path"},))
    assert result and result.advisory and provider.calls == 1
    assert BoundedCrossDisciplineAI(provider, enabled=False).explain(({"category": "x", "subcode": "y"},)) is None
