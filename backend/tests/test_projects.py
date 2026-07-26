from app.models.audit_log import AuditLog


def create_customer(client, headers, name):
    response = client.post(
        "/customers/",
        json={"name": name},
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()["id"]


def create_project(client, headers, customer_id, name):
    response = client.post(
        "/projects/",
        json={
            "name": name,
            "customer_id": customer_id,
        },
        headers=headers,
    )
    assert response.status_code == 200
    return response


def test_project_rejects_missing_customer(
    client,
    engineer_headers,
):
    response = client.post(
        "/projects/",
        json={
            "name": "Invalid Project",
            "customer_id": 999999,
        },
        headers=engineer_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Customer not found"


def test_project_crud_filters_sorting_pagination_and_audits(
    client,
    db_session,
    engineer_headers,
    admin_headers,
):
    customer_one = create_customer(
        client,
        engineer_headers,
        "Project Customer One",
    )
    customer_two = create_customer(
        client,
        engineer_headers,
        "Project Customer Two",
    )

    project_z = create_project(
        client,
        engineer_headers,
        customer_one,
        "Zulu Project",
    ).json()
    project_a = create_project(
        client,
        engineer_headers,
        customer_two,
        "Alpha Project",
    ).json()

    listed = client.get(
        "/projects/",
        params={
            "page": 1,
            "size": 1,
            "sort_by": "name",
            "order": "asc",
        },
        headers=engineer_headers,
    )
    assert listed.status_code == 200
    assert listed.json()["total"] == 2
    assert listed.json()["items"][0]["name"] == "Alpha Project"

    descending = client.get(
        "/projects/",
        params={
            "sort_by": "name",
            "order": "desc",
        },
        headers=engineer_headers,
    )
    assert descending.status_code == 200
    assert descending.json()["items"][0]["name"] == "Zulu Project"

    customer_filtered = client.get(
        "/projects/",
        params={"customer_id": customer_one},
        headers=engineer_headers,
    )
    assert customer_filtered.status_code == 200
    assert customer_filtered.json()["total"] == 1
    assert customer_filtered.json()["items"][0]["id"] == project_z["id"]

    updated = client.put(
        f"/projects/{project_z['id']}",
        json={
            "name": "Beta Project",
            "customer_id": customer_two,
            "status": "in_progress",
        },
        headers=engineer_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Beta Project"
    assert updated.json()["customer"]["id"] == customer_two
    assert updated.json()["status"] == "in_progress"

    status_filtered = client.get(
        "/projects/",
        params={
            "status": "in_progress",
            "sort_by": "status",
            "order": "asc",
        },
        headers=engineer_headers,
    )
    assert status_filtered.status_code == 200
    assert status_filtered.json()["total"] == 1
    assert status_filtered.json()["items"][0]["id"] == project_z["id"]

    created_sorted = client.get(
        "/projects/",
        params={
            "sort_by": "created_at",
            "order": "asc",
        },
        headers=engineer_headers,
    )
    assert created_sorted.status_code == 200
    assert created_sorted.json()["total"] == 2

    invalid_customer_update = client.put(
        f"/projects/{project_z['id']}",
        json={"customer_id": 999999},
        headers=engineer_headers,
    )
    assert invalid_customer_update.status_code == 404

    missing_update = client.put(
        "/projects/999999",
        json={"name": "Missing"},
        headers=engineer_headers,
    )
    assert missing_update.status_code == 404

    engineer_delete = client.delete(
        f"/projects/{project_z['id']}",
        headers=engineer_headers,
    )
    assert engineer_delete.status_code == 403

    deleted = client.delete(
        f"/projects/{project_z['id']}",
        headers=admin_headers,
    )
    assert deleted.status_code == 200

    missing_delete = client.delete(
        "/projects/999999",
        headers=admin_headers,
    )
    assert missing_delete.status_code == 404

    audits = (
        db_session.query(AuditLog)
        .filter(
            AuditLog.entity == "PROJECT",
            AuditLog.entity_id == project_z["id"],
        )
        .all()
    )
    assert {row.action for row in audits} == {
        "CREATE",
        "UPDATE",
        "DELETE",
    }

    for audit in audits:
        assert audit.user_id is not None
        assert audit.details["project_name"]
        assert audit.details["customer_id"] == customer_two or (
            audit.action == "CREATE"
            and audit.details["customer_id"] == customer_one
        )
        assert audit.details["status"]

    update_audit = next(
        row for row in audits
        if row.action == "UPDATE"
    )
    assert set(update_audit.details["changed_fields"]) == {
        "name",
        "customer_id",
        "status",
    }

    assert project_a["id"] != project_z["id"]
