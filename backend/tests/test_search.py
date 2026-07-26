def create_search_records(client, headers):
    customer = client.post(
        "/customers/",
        json={"name": "Searchable Customer"},
        headers=headers,
    )
    assert customer.status_code == 200
    customer_id = customer.json()["id"]

    contact = client.post(
        "/contacts/",
        json={
            "customer_id": customer_id,
            "first_name": "Searchable",
            "last_name": "Contact",
        },
        headers=headers,
    )
    assert contact.status_code == 200

    project = client.post(
        "/projects/",
        json={
            "customer_id": customer_id,
            "name": "Searchable Project",
        },
        headers=headers,
    )
    assert project.status_code == 200


def test_search_requires_authentication(client):
    response = client.get(
        "/search/",
        params={"q": "Searchable"},
    )

    assert response.status_code == 401


def test_authenticated_search_preserves_results(
    client,
    engineer_headers,
):
    create_search_records(client, engineer_headers)

    response = client.get(
        "/search/",
        params={"q": "Searchable"},
        headers=engineer_headers,
    )

    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results["customers"]) == 1
    assert len(results["contacts"]) == 1
    assert len(results["projects"]) == 1
