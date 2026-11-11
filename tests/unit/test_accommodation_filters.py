from app.schemas.accommodation import AccommodationFilters


def test_filters_normalize_search_and_filter_parameters():
    filters = AccommodationFilters.from_params(
        "  Curepe ",
        "1200",
        "3500",
        "2",
        "yes",
        "price_asc",
    )

    assert filters.location == "Curepe"
    assert filters.min_rent == 1200
    assert filters.max_rent == 3500
    assert filters.bedrooms == 2
    assert filters.available_now is True
    assert filters.sort == "price_asc"


def test_filters_use_safe_defaults_for_unknown_sort_and_invalid_numbers():
    filters = AccommodationFilters.from_params(
        min_rent="not-a-number",
        max_rent="",
        bedrooms="-",
        available_now="off",
        sort="unrecognized",
    )

    assert filters.min_rent is None
    assert filters.max_rent is None
    assert filters.bedrooms is None
    assert filters.available_now is False
    assert filters.sort == "recommended"


def test_filters_accept_supported_true_values():
    for value in ("1", "on", "true", "yes", " YES "):
        assert AccommodationFilters.from_params(available_now=value).available_now is True
