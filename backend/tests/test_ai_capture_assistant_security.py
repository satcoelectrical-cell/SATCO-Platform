import inspect

from app.adapters.ai_capture_assistant import CanonicalCaptureAdviceSource
from app.api.v1.routers.ai_capture_assistant import advise_capture


def test_source_adapter_uses_only_canonical_service_boundary():
    source = inspect.getsource(CanonicalCaptureAdviceSource)
    for prohibited in ("Session", "Repository", "UnitOfWork", ".query("):
        assert prohibited not in source


def test_router_is_transport_only():
    source = inspect.getsource(advise_capture)
    for prohibited in ("Session", "Repository", "UnitOfWork", "authorize", "provider"):
        assert prohibited not in source
