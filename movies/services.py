from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Q
import uuid

# Import các model từ models.py
from .models import Booking, Ticket, Seat, Showtime, TicketPrice, SeatReservation


def get_occupied_seats(showtime_id):
    # lay cac ghe da co
    sold_or_pendding_tickets = Ticket.objects.filter(
        booking__showtime_id=showtime_id,
        booking__status=['PAID', 'PENDING']
    ).values_list('seat_id', flat=True)

    #lay cac ghe dang duoc giu cho
    reserved_seats = SeatReservation.objects.filter(
        showtime_id=showtime_id,
        expires_at__gt=timezone.now(),
        is_active=True
    ).values_list('seat_id', flat=True)

    #gop 2 danh sach lai
    return set(sold_or_pendding_tickets) | set(reserved_seats)

@transaction.atomic
def create_booking(user, showtime_id, seat_ids):
    # kiem tra lai ghe co trong kh
    occupied_seats = get_occupied_seats(showtime_id)
    for seat_id in seat_ids:
        if seat_id in occupied_seats:
            raise ValidationError(f"Ghế có ID {seat_id} đã bị người khác đặt!")

    # lay thong tin suat chieu
    try:
        showtime = Showtime.objects.get(id=showtime_id)
    except Showtime.DoesNotExist:
        raise ValidationError("Suất chiếu không tồn tại!")

    # de tra cu nhanh dua bang gia ve vao Dictionary
    ticket_prices = TicketPrice.objects.filter(showtime=showtime)
    price_map = {tp.seat_type: tp.price for tp in ticket_prices}

    if not price_map:
        #lay gia co ban khi admin quen nhap gia ve rieng
        pass
    # tao don hang
    booking = Booking.objects.create(
        user=user,
        showtime=showtime,
        booking_code=str(uuid.uuid4())[:8].upper(), #tao ma 8 ki tu random
        total_amount=0,
        status='PENDING',
        expires_at=timezone.now() + timezone.timedelta(minustes=10)
    )

    # tao tung ve va tong tin
    total_amount = 0
    seats = Seat.objects.filter(id__in=seat_ids) #lay thong tin ve tu DB dua tren id

    for seat in seats:
        #lay gia ve uu tien trong price_map, neu kh co lay gia goc
        price = price_map.get(seat.seat_type, showtime.base_price)

        Ticket.objects.create(
            booking=booking,
            seat=seat,
            price=price
        )
        total_amount += price

    # cap nhap tong tien cho booking
    booking.total_amount = total_amount
    booking.save()
    return booking
