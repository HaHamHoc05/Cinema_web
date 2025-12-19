import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from movies.models import Movie, Cinema, Screen, Seat, Showtime, Booking, Ticket
from faker import Faker


class Command(BaseCommand):
    help = 'Tạo dữ liệu giả 6 tháng'

    def handle(self, *args, **kwargs):
        fake = Faker(['vi_VN'])
        self.stdout.write('Đang dọn dẹp dữ liệu cũ...')

        # Xóa Booking và Showtime cũ
        Booking.objects.all().delete()
        Showtime.objects.all().delete()

        movies = Movie.objects.all()
        screens = Screen.objects.all()

        if not movies.exists() or not screens.exists():
            self.stdout.write(self.style.ERROR('Chưa có Phim hoặc Phòng chiếu!'))
            return

        self.stdout.write('Bắt đầu tạo dữ liệu cho 6 tháng qua...')

        # Tạo User giả (nếu chưa có nhiều)
        if User.objects.count() < 10:
            for _ in range(10):
                User.objects.create_user(username=fake.unique.user_name(), email=fake.email(), password='password123')

        users = User.objects.filter(is_superuser=False)  # Lấy user thường

        end_date = timezone.now()
        # SỬA Ở ĐÂY: 180 ngày = 6 tháng
        start_date = end_date - timedelta(days=180)

        current_date = start_date
        total_bookings = 0

        while current_date <= end_date:
            # Tạo ít hơn: 2-4 suất chiếu mỗi ngày
            for _ in range(random.randint(2, 4)):
                movie = random.choice(movies)
                screen = random.choice(screens)

                # Giờ chiếu ngẫu nhiên
                hour = random.randint(9, 23)
                show_time = current_date.replace(hour=hour, minute=0, second=0)

                showtime = Showtime.objects.create(
                    movie=movie,
                    screen=screen,
                    start_time=show_time,
                    end_time=show_time + timedelta(minutes=movie.duration),
                    base_price=60000
                )

                # Mỗi suất tạo 0-10 đơn hàng
                for _ in range(random.randint(0, 10)):
                    if not users.exists(): break
                    user = random.choice(users)

                    # 95% là thanh toán thành công để biểu đồ đẹp
                    status = 'PAID' if random.random() > 0.05 else 'CANCELLED'

                    booking = Booking.objects.create(
                        user=user,
                        showtime=showtime,
                        booking_code=fake.uuid4()[:8].upper(),
                        total_amount=0,
                        status=status,
                        expires_at=showtime.start_time
                    )

                    # QUAN TRỌNG: Gán ngày tạo đơn trùng với ngày giả lập
                    booking.created_at = show_time
                    booking.save()

                    # Random 1-3 vé
                    num_tickets = random.randint(1, 3)
                    seats = Seat.objects.filter(screen=screen).order_by('?')[:num_tickets]

                    booking_total = 0
                    for seat in seats:
                        price = showtime.base_price
                        Ticket.objects.create(booking=booking, seat=seat, price=price)
                        booking_total += price

                    booking.total_amount = booking_total
                    booking.save()
                    total_bookings += 1

            current_date += timedelta(days=1)
            self.stdout.write(f'-> Xong ngày {current_date.strftime("%d/%m/%Y")}')

        self.stdout.write(self.style.SUCCESS(f'Xong! Đã tạo {total_bookings} đơn hàng trong 6 tháng.'))