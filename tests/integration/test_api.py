def test_health_endpoint_returns_success_status(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_accommodation_api_returns_verified_listings_and_card_fields(client):
    response = client.get("/api/accommodations")

    assert response.status_code == 200
    listings = response.json()
    assert listings
    assert all(listing["is_verified"] is True for listing in listings)
    assert {
        "id",
        "title",
        "area",
        "address",
        "rent",
        "bedrooms",
        "availability_status",
        "is_verified",
        "avg_rating",
        "review_count",
    } <= listings[0].keys()


def test_accommodation_api_applies_location_and_rent_filters(client):
    response = client.get(
        "/api/accommodations",
        params={"location": "Arima", "min_rent": "800", "max_rent": "1000"},
    )

    assert response.status_code == 200
    listings = response.json()
    assert [listing["title"] for listing in listings] == ["Budget room in Arima"]
    assert all(800 <= listing["rent"] <= 1000 for listing in listings)


def test_accommodation_api_available_now_filter_excludes_unavailable_listings(client):
    response = client.get("/api/accommodations", params={"available_now": "1"})

    assert response.status_code == 200
    listings = response.json()
    assert all(listing["availability_status"] == "Available" for listing in listings)
    assert all("Trincity" not in listing["title"] for listing in listings)


def test_accommodation_api_does_not_expose_unverified_listings(client):
    response = client.get("/api/accommodations", params={"location": "Valsayn"})

    assert response.status_code == 200
    assert response.json() == []
