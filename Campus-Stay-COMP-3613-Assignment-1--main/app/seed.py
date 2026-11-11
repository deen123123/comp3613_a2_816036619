"""Demo data: users, accommodations, bookings and reviews so every workflow has something to show."""

from datetime import date, timedelta

from sqlmodel import Session

from app.models import Availability, Booking, BookingStatus, Accommodation, Review, Role, User, pack_amenities
from app.repositories import accommodation_repo, user_repo
from app.repositories.base import count
from app.utilities.security import hash_password

DEMO_USERS = [
    # username, password, role, full name
    ("admin", "adminpass", Role.ADMIN, "Campus Stay Admin"),
    ("bob", "bobpass", Role.STUDENT, "Bob Ramdass"),
    ("alice", "alicepass", Role.STUDENT, "Alice Mohammed"),
    ("landlord", "landpass", Role.LANDLORD, "Sandra Khan"),
    ("carla", "carlapass", Role.LANDLORD, "Carla Joseph"),
]

# key, landlord, title, area, type, price, beds, sleeps, km, amenities, verified, description
ACCOMMODATIONS = [
    ("sunny", "landlord", "Sunny private room by the UWI gate", "St. Augustine", "room", 1800, 1, 1, 0.6,
     ["wifi", "water", "electricity", "furnished", "study_desk", "security"], True,
     "Bright, quiet room a 10-minute walk from the campus gate. Includes a study desk, fast Wi-Fi and a secure gate."),
    ("curepe", "carla", "Modern studio in Curepe", "Curepe", "studio", 3200, 1, 2, 2.1,
     ["wifi", "air_conditioning", "kitchen", "furnished", "laundry", "parking"], True,
     "Self-contained studio with its own kitchenette and AC. Short maxi ride to campus with a taxi stand next door."),
    ("tunapuna", "landlord", "Shared 3-bedroom house in Tunapuna", "Tunapuna", "shared", 1200, 3, 3, 3.4,
     ["wifi", "water", "kitchen", "laundry"], True,
     "Friendly student house with a shared kitchen and backyard. Each tenant has a lockable bedroom."),
    ("trincity", "carla", "2-bedroom apartment in Trincity", "Trincity", "apartment", 4500, 2, 4, 6.0,
     ["wifi", "air_conditioning", "kitchen", "furnished", "parking", "security"], True,
     "Spacious apartment in a gated complex, ideal for two students splitting the rent. Mall within walking distance."),
    ("arima", "landlord", "Budget room in Arima", "Arima", "room", 900, 1, 1, 9.5,
     ["water", "electricity"], True,
     "Simple, affordable room on the Arima main road. Good for students who don't mind the commute."),
    ("mthope", "carla", "Quiet room in Mt. Hope", "Mt. Hope", "room", 2000, 1, 1, 4.0,
     ["wifi", "water", "furnished", "study_desk"], True,
     "Calm residential street, furnished room with a desk. Direct route to campus by maxi taxi."),
    ("valsayn", "carla", "Gated studio in Valsayn", "Valsayn", "studio", 3800, 1, 2, 1.8,
     ["wifi", "air_conditioning", "kitchen", "furnished", "security", "parking"], False,
     "Brand new gated studio. Waiting for admin verification."),
    ("augsouth", "landlord", "Cosy room in St. Augustine South", "St. Augustine", "room", 1600, 1, 1, 0.9,
     ["wifi", "water", "electricity"], False,
     "Small cosy room close to the campus, available now. Waiting for admin verification."),
]


def _ensure_users(session: Session) -> dict:
    users = {}
    for username, password, role, full_name in DEMO_USERS:
        user = user_repo.get_by_username(session, username)
        if user is None:
            user = user_repo.add(
                session,
                User(
                    username=username,
                    email=f"{username}@example.com",
                    full_name=full_name,
                    password_hash=hash_password(password),
                    role=role,
                ),
            )
        users[username] = user
    return users


def seed(session: Session) -> dict:
    """Idempotent: users are added if missing; accommodations/bookings only on an empty accommodations table."""
    users = _ensure_users(session)
    summary = {"users": len(users), "accommodations": 0, "bookings": 0, "reviews": 0}
    if count(session, Accommodation) > 0:
        return summary

    today = date.today()
    by_key = {}
    for key, owner, title, area, rtype, price, beds, sleeps, km, amenities, verified, desc in ACCOMMODATIONS:
        by_key[key] = accommodation_repo.add(
            session,
            Accommodation(
                landlord_id=users[owner].id, title=title, description=desc,
                address=f"{area}, Trinidad", area=area, room_type=rtype, rent=price,
                bedrooms=beds, max_tenants=sleeps, distance_km=km,
                amenities=pack_amenities(amenities), is_verified=verified,
            ),
        )
    by_key["trincity"].availability_status = Availability.UNAVAILABLE  # shows the Available Now filter
    session.add(by_key["trincity"])
    session.commit()
    summary["accommodations"] = len(by_key)

    def day(offset: int) -> date:
        return today + timedelta(days=offset)

    # (student, accommodation, start offset, end offset, status, review (rating, comment) or None)
    plan = [
        ("alice", "sunny", -300, -180, BookingStatus.APPROVED, (5, "Super close to campus and the landlord was very responsive. Quiet at night, great for studying.")),
        ("alice", "curepe", -200, -100, BookingStatus.APPROVED, (4, "Lovely studio, AC worked well. Parking can be tight in the evenings.")),
        ("bob", "tunapuna", -400, -250, BookingStatus.APPROVED, (4, "Good housemates and a decent kitchen. Wi-Fi dropped now and then.")),
        ("bob", "trincity", -500, -400, BookingStatus.APPROVED, (3, "Nice apartment but far from campus without a car.")),
        ("alice", "arima", -250, -150, BookingStatus.APPROVED, (4, "Cheap and cheerful. Long commute but fair value for the price.")),
        # Bob finished a stay and has NOT reviewed it yet -> review workflow demo
        ("bob", "sunny", -120, -30, BookingStatus.APPROVED, None),
        # Pending requests for the landlord / carla to manage
        ("alice", "tunapuna", 15, 105, BookingStatus.PENDING, None),
        ("bob", "arima", 10, 100, BookingStatus.PENDING, None),
        ("bob", "curepe", 20, 110, BookingStatus.PENDING, None),
        ("alice", "curepe", 40, 130, BookingStatus.PENDING, None),  # overlaps bob's: approving one closes the other
        ("alice", "mthope", 30, 120, BookingStatus.PENDING, None),
        # An approved upcoming stay
        ("alice", "sunny", 45, 135, BookingStatus.APPROVED, None),
    ]
    reviews = 0
    for student, key, start, end, status, review in plan:
        booking = Booking(
            accommodation_id=by_key[key].id, student_id=users[student].id, start_date=day(start),
            end_date=day(end), status=status, message="Hi! I'm a UWI student looking for a place.",
        )
        session.add(booking)
        session.commit()
        session.refresh(booking)
        if review:
            session.add(
                Review(
                    accommodation_id=booking.accommodation_id, student_id=booking.student_id,
                    booking_id=booking.id, rating=review[0], comment=review[1],
                )
            )
            session.commit()
            reviews += 1
    summary["bookings"] = len(plan)
    summary["reviews"] = reviews
    return summary
