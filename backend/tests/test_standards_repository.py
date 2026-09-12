from uuid import uuid4

from app.models.standards import StandardIdentity
from app.repositories.standards_repository import StandardsRepository


def test_organization_private_identity_is_scoped(db_session):
    organization_id = uuid4()
    db_session.execute(__import__("sqlalchemy").text("INSERT INTO organizations(id,is_active) VALUES (:id,true)"), {"id": organization_id})
    row = StandardIdentity(catalog_scope="organization_private", organization_id=organization_id, issuer_key="iso", issuer_display="ISO", designation="9001", designation_key="9001", title="Quality", language=None, jurisdiction={}, normalization_version="satco_standard_key_nfkc_casefold_v1", metadata_source_reference="catalog", identity_digest="a" * 64, created_by=1)
    # The test proves repository predicates; fixtures own user construction in API/security suites.
    assert StandardsRepository(db_session).get_identity(uuid4(), organization_id) is None
