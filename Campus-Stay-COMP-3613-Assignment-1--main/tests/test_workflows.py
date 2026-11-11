from datetime import date, timedelta

from sqlmodel import select

from app.models import Booking, BookingStatus, Accommodation, Review, User
from tests.conftest import login


def _accommodation(db, title_part: str) -> Accommodation:
    return db.exec(select(Accommodation).where(Accommodation.title.contains(title_part))).first()


def _iso(offset: int) -> str:
    return (date.today() + timedelta(days=offset)).isoformat()


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_login_and_role_redirects(client):
    assert login(client, "bob", "bobpass").headers["location"] == "/accommodations"
    client.post("/logout")
    assert login(client, "landlord", "landpass").headers["location"] == "/landlord"
    client.post("/logout")
    assert login(client, "admin", "adminpass").headers["location"] == "/admin"
    client.post("/logout")
    assert login(client, "bob", "wrong").status_code == 400


def test_protected_pages_redirect_to_login(client):
    response = client.get("/my/bookings", follow_redirects=False)
    assert response.status_code == 303 and response.headers["location"].startswith("/login")
    login(client, "bob", "bobpass")
    assert client.get("/landlord").status_code == 403


# ---- Workflow 1: Search Accommodation ----

def test_search_by_location_then_filters(client):
    page = client.get("/accommodations?location=Curepe").text
    assert "Modern studio in Curepe" in page and "Sunny private room" not in page

    page = client.get("/accommodations?max_rent=2000").text
    assert "Sunny private room" in page
    assert "Gated studio in Valsayn" not in page  # not verified yet
    assert "Modern studio in Curepe" not in page  # over budget

    page = client.get("/accommodations?bedrooms=2").text
    assert "Tunapuna" in page and "Sunny private room" not in page


def test_available_now_filter_hides_unavailable(client):
    assert "2-bedroom apartment in Trincity" in client.get("/accommodations").text
    assert "2-bedroom apartment in Trincity" not in client.get("/accommodations?available_now=1").text


def test_api_accommodations(client):
    rows = client.get("/api/accommodations?max_rent=1000").json()
    assert [r["title"] for r in rows] == ["Budget room in Arima"]


# ---- Workflow 2: View Accommodation and Reviews ----

def test_detail_shows_reviews_and_rent(client, db):
    sunny = _accommodation(db, "Sunny")
    page = client.get(f"/accommodations/{sunny.id}").text
    assert "Super close to campus" in page and "TT$1,800" in page and "Verified stay" in page


# ---- Workflow 3: Request Accommodation Booking (+ landlord decision) ----

def test_booking_rules_and_landlord_decision(client, db):
    sunny = _accommodation(db, "Sunny")
    login(client, "bob", "bobpass")

    # alice already has an approved stay on days 45..135, so this overlaps and is refused
    client.post(f"/accommodations/{sunny.id}/book", data={"start_date": _iso(60), "end_date": _iso(120)})
    assert db.exec(select(Booking).where(Booking.accommodation_id == sunny.id, Booking.start_date == date.today() + timedelta(days=60))).first() is None

    # too short
    client.post(f"/accommodations/{sunny.id}/book", data={"start_date": _iso(200), "end_date": _iso(210)})
    assert db.exec(select(Booking).where(Booking.start_date == date.today() + timedelta(days=200))).first() is None

    # valid request
    assert client.get(f"/accommodations/{sunny.id}/book").status_code == 200
    response = client.post(
        f"/accommodations/{sunny.id}/book",
        data={"start_date": _iso(150), "end_date": _iso(200), "occupants": "1", "message": "hello"},
        follow_redirects=False,
    )
    booking = db.exec(select(Booking).where(Booking.start_date == date.today() + timedelta(days=150))).one()
    assert booking.status == BookingStatus.PENDING
    assert response.headers["location"] == f"/bookings/{booking.id}/confirmation"
    confirmation = client.get(response.headers["location"]).text
    assert booking.reference in confirmation and "Pending" in confirmation

    # landlord approves
    client.post("/logout")
    login(client, "landlord", "landpass")
    client.post(f"/landlord/bookings/{booking.id}/decide", data={"decision": "approve"})
    db.expire_all()
    assert db.get(Booking, booking.id).status == BookingStatus.APPROVED


def test_cannot_book_unavailable_accommodation(client, db):
    trincity = _accommodation(db, "Trincity")
    login(client, "bob", "bobpass")
    response = client.get(f"/accommodations/{trincity.id}/book", follow_redirects=False)
    assert response.headers["location"] == f"/accommodations/{trincity.id}"


def test_approving_closes_overlapping_requests(client, db):
    curepe = _accommodation(db, "Curepe")
    bobs = db.exec(select(Booking).join(User, Booking.student_id == User.id).where(
        Booking.accommodation_id == curepe.id, User.username == "bob", Booking.status == BookingStatus.PENDING)).one()
    alices = db.exec(select(Booking).join(User, Booking.student_id == User.id).where(
        Booking.accommodation_id == curepe.id, User.username == "alice", Booking.status == BookingStatus.PENDING)).one()
    login(client, "carla", "carlapass")
    client.post(f"/landlord/bookings/{bobs.id}/decide", data={"decision": "approve"})
    db.expire_all()
    assert db.get(Booking, bobs.id).status == BookingStatus.APPROVED
    assert db.get(Booking, alices.id).status == BookingStatus.DECLINED


def test_other_landlords_cannot_decide(client, db):
    sunny_pending = db.exec(select(Booking).where(Booking.status == BookingStatus.PENDING)).first()
    owner_is_landlord = sunny_pending.accommodation.landlord.username == "landlord"
    login(client, "carla" if owner_is_landlord else "landlord", "carlapass" if owner_is_landlord else "landpass")
    response = client.post(f"/landlord/bookings/{sunny_pending.id}/decide", data={"decision": "approve"})
    assert response.status_code == 403


# ---- Supporting: reviews after a stay, admin verification ----

def test_review_only_after_stay_and_only_once(client, db):
    bob = db.exec(select(User).where(User.username == "bob")).one()
    finished = next(
        b for b in db.exec(select(Booking).where(Booking.student_id == bob.id)).all()
        if b.stay_ended and not db.exec(select(Review).where(Review.booking_id == b.id)).first()
    )
    upcoming = db.exec(select(Booking).where(Booking.student_id == bob.id, Booking.status == BookingStatus.PENDING)).first()
    login(client, "bob", "bobpass")

    client.post(f"/bookings/{upcoming.id}/review", data={"rating": "5", "comment": "Not stayed yet at all"})
    assert db.exec(select(Review).where(Review.booking_id == upcoming.id)).first() is None

    client.post(f"/bookings/{finished.id}/review", data={"rating": "5", "comment": "Great spot, very quiet."})
    assert db.exec(select(Review).where(Review.booking_id == finished.id)).first() is not None

    client.post(f"/bookings/{finished.id}/review", data={"rating": "1", "comment": "Second attempt should fail"})
    assert len(db.exec(select(Review).where(Review.booking_id == finished.id)).all()) == 1


def test_admin_verification_controls_visibility(client, db):
    valsayn = _accommodation(db, "Valsayn")
    login(client, "bob", "bobpass")
    assert client.get(f"/accommodations/{valsayn.id}").status_code == 404
    client.post("/logout")

    login(client, "admin", "adminpass")
    client.post(f"/admin/accommodations/{valsayn.id}/verify", data={"verified": "1"})
    client.post("/logout")

    login(client, "bob", "bobpass")
    assert client.get(f"/accommodations/{valsayn.id}").status_code == 200


def test_landlord_accommodation_starts_unverified(client, db):
    login(client, "landlord", "landpass")
    response = client.post("/landlord/accommodations/new", data={
        "title": "Test room near campus", "description": "A clean test room with everything you need.",
        "area": "Curepe", "address": "1 Test Street", "room_type": "room", "rent": "1500",
        "bedrooms": "1", "max_tenants": "1", "distance_km": "1.2", "amenities": ["wifi"],
    }, follow_redirects=False)
    assert response.status_code == 303
    accommodation = _accommodation(db, "Test room near campus")
    assert accommodation is not None and accommodation.is_verified is False
