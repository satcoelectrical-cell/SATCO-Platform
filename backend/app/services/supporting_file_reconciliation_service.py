"""Bounded Supporting File object/DB mismatch reconciliation."""
from app.enums.supporting_file import SupportingFileLifecycle


class SupportingFileReconciliationService:
    def __init__(self, *, uow, objects): self.uow, self.objects = uow, objects
    def reconcile_reservation(self, reservation, *, limit: int = 1) -> str:
        """No list/scan/promotion fallback: report exact object state only."""
        if limit != 1 or reservation.status not in {"reserved", "uploaded"}: return "no_action"
        if reservation.asset_id is None: return "reservation_without_asset"
        asset = self.uow.repository.get_scoped(reservation.asset_id, reservation.organization_id)
        if asset is None: return "missing_asset"
        receipt = self.objects.head_exact(asset.storage_key, asset.object_version)
        if receipt is None: return "missing_object"
        if receipt.byte_size != asset.byte_size or receipt.sha256 != asset.content_digest: return "integrity_mismatch"
        return "quarantined_pending_scan" if asset.lifecycle == SupportingFileLifecycle.QUARANTINED.value else "consistent"
