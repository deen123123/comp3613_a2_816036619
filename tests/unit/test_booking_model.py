from datetime import date, datetime, timedelta

import pytest

from app.models import Booking, BookingStatus


def test_booking_reference_is_derived_from_persisted_id():
    today = datetime.now().astimezone().date()
    booking = Booking(
        id=42,
        accommodation_id=1,
        student_id=2,
        start_date=today,
        end_date=today + timedelta(days=30),
    )
    assert booking.reference == "CS-10042"


def test_booking_nights_uses_checkout_exclusive_duration():
    booking = Booking(
        accommodation_id=1,
        student_id=2,
        start_date=date(2030, 1, 1),
        end_date=date(2030, 2, 1),
    )

    assert booking.nights == 31


@pytest.mark.parametrize(
    ("status", "start_offset", "end_offset", "expected"),
    [
        (BookingStatus.PENDING, -5, 5, BookingStatus.PENDING),
        (BookingStatus.APPROVED, -5, 10, "active"),
        (BookingStatus.APPROVED, -10, -1, "completed"),
        (BookingStatus.DECLINED, -10, -1, BookingStatus.DECLINED),
    ],
)
def test_display_status_reflects_booking_state_and_dates(
    status, start_offset, end_offset, expected
):
    today = datetime.now().astimezone().date()
    booking = Booking(
        accommodation_id=1,
        student_id=2,
        start_date=today + timedelta(days=start_offset),
        end_date=today + timedelta(days=end_offset),
        status=status,
    )

    assert booking.display_status == expected
