from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from .models import Booking, Ticket, Seat, Showtime, TicketPrice
import uuid


def get_occupied_seats(showtime_id):
    sold_seats = Ticket.objects.filter(
        booking__showtime_id=showtime_id,
        booking__status__in=['PAID', 'PENDING']
    ).values_list('seat_id', flat=True)
    return set(sold_seats)


@transaction.atomic
def create_booking(user, showtime_id, seat_ids):
    # 1. Lấy suất chiếu và khóa dòng (nếu DB hỗ trợ)
    try:
        showtime = Showtime.objects.select_for_update().get(id=showtime_id)
    except Showtime.DoesNotExist:
        raise ValidationError("Suất chiếu không tồn tại!")

    # 2. Kiểm tra ghế đã bị đặt chưa
    occupied_seats = get_occupied_seats(showtime_id)
    seats_to_book = Seat.objects.filter(id__in=seat_ids, screen=showtime.screen)

    if len(seats_to_book) != len(seat_ids):
        raise ValidationError("Danh sách ghế không hợp lệ!")

    for seat in seats_to_book:
        if seat.id in occupied_seats:
            raise ValidationError(f"Ghế {seat.row}{seat.number} vừa có người khác đặt!")

    ticket_prices = TicketPrice.objects.filter(showtime=showtime)
    price_map = {tp.seat_type: tp.price for tp in ticket_prices}

    # 3. Tạo Booking
    booking = Booking.objects.create(
        user=user,
        showtime=showtime,
        booking_code=str(uuid.uuid4())[:8].upper(),
        status='PENDING',
        expires_at=timezone.now() + timedelta(minutes=15),
        total_amount=0
    )

    total_amount = 0
    for seat in seats_to_book:

        price = price_map.get(seat.seat_type)

        if price is None:
            # Logic dự phòng (Fallback) nếu Admin quên nhập bảng giá
            price = showtime.base_price
            if seat.seat_type == 'VIP':
                price += 10000
            elif seat.seat_type == 'COUPLE':
                price += 20000

        total_amount += price
        Ticket.objects.create(booking=booking, seat=seat, price=price)

    booking.total_amount = total_amount
    booking.save()

    return booking