"""Append-only explicit source-release mapping; no directory scanning."""

from .release_051_core_v1 import RELEASE_051_CORE_V1
from .release_052_eic_v1 import RELEASE_052_EIC_V1

RELEASES = {
    RELEASE_051_CORE_V1.release_id: RELEASE_051_CORE_V1,
    RELEASE_052_EIC_V1.release_id: RELEASE_052_EIC_V1,
}
