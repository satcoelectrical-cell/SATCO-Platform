from math import ceil


def build_pagination(
    *,
    items,
    total: int,
    page: int,
    size: int,
):
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": ceil(total / size) if total else 0,
        "has_next": page * size < total,
        "has_prev": page > 1,
    }
