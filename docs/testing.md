# Campus Stay Test Plan

**Student:** Dinesh Kanhai  
**Student ID:** 816036619  
**Project:** Campus Stay — Student Accommodation  
**Repository:** https://github.com/deen123123/comp3613_a2_816036619

## 1. Scope and approach

Testing focuses on the three student workflows shown in the supplied wireframes:

1. Search accommodation by location and filters.
2. View a verified listing, its availability, and reviews.
3. Submit a booking request and receive a confirmation.

Supporting authorization, landlord decisions, admin verification, and review eligibility are included because they affect the integrity of those workflows. Unit tests isolate deterministic rules and transformations. Integration tests exercise the FastAPI application, its database-backed services, session authorization, templates, and API routes using a temporary SQLite database seeded with repeatable demo data. The Postman collection checks the running application's public API over HTTP.

## 2. Test environment and execution

- Python 3.10 or later; install project dependencies with `pip install -r requirements.txt`.
- Unit and integration tests use pytest and the in-memory SQLite fixture in `tests/conftest.py`; they do not require the development database.
- Run all automated tests from the project root: `python -m pytest -v`.
- For Postman, start and seed the local application with `python manage.py init` followed by `python manage.py run`. Import `postman/Campus-Stay-API.postman_collection.json`, set `baseUrl` to the running server (default `http://127.0.0.1:5000`), and run the complete collection.

## 3. Unit test plan

Unit tests verify one module's rules without HTTP requests or database access.

| ID | Component / case | Expected result | Implemented in |
|---|---|---|---|
| U-01 | Clean optional text | Leading/trailing whitespace is removed; `None` becomes an empty string | `tests/unit/test_validators.py` |
| U-02 | Parse integer within bounds | Valid boundary and in-range values return integers | `tests/unit/test_validators.py` |
| U-03 | Parse integer invalid, below minimum, or above maximum | A `ServiceError` explains the invalid value or violated bound | `tests/unit/test_validators.py` |
| U-04 | Parse distance as float | Valid numeric input is returned; invalid or out-of-range values raise `ServiceError` | `tests/unit/test_validators.py` |
| U-05 | Parse booking date | ISO `YYYY-MM-DD` is accepted; another format raises `ServiceError` | `tests/unit/test_validators.py` |
| U-06 | Convert optional filter integer | Numeric input converts; blank or malformed input safely becomes `None` | `tests/unit/test_validators.py` |
| U-07 | Normalize accommodation query parameters | Location, rent, bedroom, availability, and sort values are parsed consistently | `tests/unit/test_accommodation_filters.py` |
| U-08 | Invalid filter defaults | Invalid numbers are ignored and unknown sorting falls back to `recommended` | `tests/unit/test_accommodation_filters.py` |
| U-09 | Availability truth values | Supported checked values are interpreted as `True` | `tests/unit/test_accommodation_filters.py` |
| U-10 | Booking reference and duration | Reference follows `CS-<10000 + id>`; nights use checkout-exclusive dates | `tests/unit/test_booking_model.py` |
| U-11 | Booking display status | Pending and declined states are preserved; approved stays are active or completed according to dates | `tests/unit/test_booking_model.py` |

## 4. Integration test plan

Integration tests run through the application or its database-backed services with the seeded temporary database.

| ID | Workflow / scenario | Expected result | Implemented in |
|---|---|---|---|
| I-01 | Health endpoint | `GET /health` returns HTTP 200 and `{"status":"ok"}` | `tests/integration/test_api.py` |
| I-02 | Search by location and rent | Search results match the requested location and rent bounds | `tests/integration/test_api.py`, `tests/test_workflows.py` |
| I-03 | Available-now filter | Unavailable Trincity listing is excluded | `tests/integration/test_api.py`, `tests/test_workflows.py` |
| I-04 | Public search visibility | Unverified Valsayn listing is not returned to a public search | `tests/integration/test_api.py`, `tests/test_workflows.py` |
| I-05 | Search response contract | JSON list contains the accommodation card fields and only verified listings | `tests/integration/test_api.py` |
| I-06 | Detail and review display | Listing details show rent and verified student review | `tests/test_workflows.py` |
| I-07 | Booking request validations | Overlapping, too-short, or unavailable stays cannot be requested | `tests/test_workflows.py` |
| I-08 | Booking confirmation and decision | Valid request is pending, has a reference, and can be approved by its landlord | `tests/test_workflows.py` |
| I-09 | Role-based access | Unauthenticated users are directed to login; wrong roles receive HTTP 403 | `tests/test_workflows.py` |
| I-10 | Booking conflict handling | Approval closes overlapping pending requests; another landlord cannot decide a request | `tests/test_workflows.py` |
| I-11 | Review eligibility | Review is accepted once for a completed stay and rejected for an upcoming stay | `tests/test_workflows.py` |
| I-12 | Admin verification | An unverified listing becomes visible only after admin verification | `tests/test_workflows.py` |
| I-13 | Landlord listing creation | A new accommodation is created as unverified until admin review | `tests/test_workflows.py` |

## 5. API test plan

The Postman collection exercises the HTTP API available in `app/routers/api.py`. Each request contains executable Postman assertions.

| ID | Request | Assertions |
|---|---|---|
| A-01 | `GET /health` | HTTP 200 and exact healthy status JSON |
| A-02 | `GET /api/accommodations` | HTTP 200; array response; required listing fields; returned listings are verified |
| A-03 | `GET /api/accommodations?location=Arima&min_rent=800&max_rent=1000` | HTTP 200; matching location and rent range; at least one result |
| A-04 | `GET /api/accommodations?available_now=1` | HTTP 200; every result is marked Available; unavailable Trincity is absent |
| A-05 | `GET /api/accommodations?location=Valsayn` | HTTP 200 and an empty array, because the seeded Valsayn listing is unverified |

**Collection file:** [`postman/Campus-Stay-API.postman_collection.json`](../postman/Campus-Stay-API.postman_collection.json)

## 6. User Acceptance Test plan

### UAT preparation

- **Tester:** Student / intended student user
- **Build and date:** To be recorded during the demonstration
- **Preconditions:** Application is running; seeded database is available; tester can sign in as `bob` with `bobpass`.
- **Acceptance rule:** Mark a case Pass only when all listed success criteria are observed. Record actual outcome and any defect before sign-off.

### UAT-01 — Search accommodation

**Wireframe:** [`docs/wireframes/search-results.png`](wireframes/search-results.png)

1. Open Find Accommodation.
2. Search for `Curepe`.
3. Apply a maximum rent of TT$2,000 and submit.
4. Clear filters, set Bedrooms to 2, enable Available Now, and apply.

**Success criteria:** Search results respond to the entered location and filters; each result presents listing identity, location, monthly rent, bedroom count, and a View Details action; unverified and unavailable listings are not presented as available options.

### UAT-02 — View listing and reviews

**Wireframe:** [`docs/wireframes/listing-details-reviews.png`](wireframes/listing-details-reviews.png)

1. Select View Details on the verified Sunny private room listing.
2. Review its monthly rent, location, bedroom count, availability, and description.
3. Read the displayed student reviews and review summary.

**Success criteria:** The selected listing's details are visible and correspond to the listing selected; verified-stay reviews and rating information are readable; the booking action is available to an authenticated student when the accommodation is available.

### UAT-03 — Request a booking

**Wireframe:** [`docs/wireframes/booking-request-confirmation.png`](wireframes/booking-request-confirmation.png)

1. From an available verified listing, open Request Accommodation Booking.
2. Enter valid future move-in and move-out dates at least 28 days apart, occupants within the listing limit, and an optional message.
3. Submit the booking request.
4. Check the confirmation reference, dates, property, and request status.

**Success criteria:** A valid request creates one booking; confirmation displays the correct property and dates, a booking reference, and Pending Approval status. An unavailable property or invalid dates/occupant count must not produce a successful booking.

### UAT record and sign-off

| Case | Pass / Fail / Blocked | Actual result / defect reference |
|---|---|---|
| UAT-01 Search accommodation | Not yet executed | Complete during student demonstration |
| UAT-02 View listing and reviews | Not yet executed | Complete during student demonstration |
| UAT-03 Request a booking | Not yet executed | Complete during student demonstration |

**Tester comments:** To be completed by the tester.  
**Tester name / signature:** ______________________________  
**Date:** __________________  
**Overall acceptance:** Pending student execution and sign-off.

## 7. Test reporting and evidence

Automated test source is in `tests/unit/`, `tests/integration/`, and `tests/test_workflows.py`. Run `python -m pytest -v` and retain the actual terminal output or a screenshot as submission evidence. Run the Postman collection in the Postman Collection Runner and capture its actual run summary. No test result or screenshot is claimed here before those runs are performed.

| Report | Evidence status |
|---|---|
| Unit test report | **PASS:** 19 tests passed. Captured command output is rendered in `docs/evidence/unit-test-results.png`. |
| Integration test report | **PASS:** 19 tests passed. Captured command output is rendered in `docs/evidence/integration-test-results.png`. |
| Full pytest suite | **PASS:** 38 tests passed using `python -m pytest -q`. |
| Postman collection run report | Collection is implemented but has not been run with Postman; capture the actual Collection Runner results |
| User acceptance report | Execute UAT-01 to UAT-03 and complete the result table and sign-off |

The pytest evidence images reproduce the output captured from actual local pytest commands; they are rendered report images, not direct desktop screenshots. A direct Postman Collection Runner screenshot has not been captured and must be added after the collection is run in Postman.

## 8. Test limitations

- Automated tests use SQLite and seeded data; production database behavior should also be checked in the deployment environment.
- Postman request/response tests depend on the seeded demo fixtures and the API response contract.
- UAT requires a human to interact with the wireframe-matched interface. It is intentionally left pending rather than represented as completed without a tester.
- Screenshots and Postman run results must come from the student's actual execution.
