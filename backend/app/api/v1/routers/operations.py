import hmac

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import PlainTextResponse

from app.core.config import settings
from app.core.operations import safe_diagnostic_snapshot
from app.core.operations import readiness_snapshot
from app.dependencies.auth import require_role


router = APIRouter(prefix="/operations", tags=["Operations"])


def require_monitoring_principal(
    x_satco_monitoring_token: str | None = Header(default=None),
) -> None:
    try:
        expected = settings.resolved_monitoring_token()
    except OSError as exc:
        raise HTTPException(status_code=503, detail="unavailable") from exc
    if (
        not expected
        or not x_satco_monitoring_token
        or not hmac.compare_digest(x_satco_monitoring_token, expected)
    ):
        raise HTTPException(status_code=403, detail="forbidden")


@router.get("/diagnostics")
def diagnostics(_current_user=Depends(require_role("admin"))):
    """Protected bounded operational categories; no raw configuration or content."""

    return safe_diagnostic_snapshot(settings)


@router.get("/metrics", response_class=PlainTextResponse)
def metrics(_monitoring_principal=Depends(require_monitoring_principal)):
    snapshot = readiness_snapshot(settings)
    ready = 1 if snapshot.ready else 0
    writable = 1 if snapshot.mode == "normal" else 0
    return (
        "# TYPE satco_ready gauge\n"
        f"satco_ready {ready}\n"
        "# TYPE satco_governed_writes_enabled gauge\n"
        f"satco_governed_writes_enabled {writable}\n"
    )
