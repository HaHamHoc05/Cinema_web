from django.db import models

from django.contrib.auth.models import User

from django.core.validators import MinValueValidator, MaxValueValidator

from django.utils import timezone


# Model Thể loại phim

class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Tên thể loại")

    description = models.TextField(blank=True, verbose_name="Mô tả")

    class Meta:
        verbose_name = "Thể loại"

        verbose_name_plural = "Thể loại phim"

    def __str__(self):
        return self.name


# Model Phim

class Movie(models.Model):
    RATING_CHOICES = [

        ('P', 'P - Phim dành cho mọi đối tượng'),

        ('K', 'K - Phim dành cho người dưới 13 tuổi với sự hướng dẫn của phụ huynh'),

        ('T13', 'T13 - Phim dành cho khán giả từ đủ 13 tuổi trở lên'),

        ('T16', 'T16 - Phim dành cho khán giả từ đủ 16 tuổi trở lên'),

        ('T18', 'T18 - Phim dành cho khán giả từ đủ 18 tuổi trở lên'),

        ('C', 'C - Phim cấm chiếu'),

    ]

    title = models.CharField(max_length=200, verbose_name="Tên phim")

    slug = models.SlugField(max_length=200, unique=True)

    description = models.TextField(verbose_name="Mô tả")

    director = models.CharField(max_length=100, verbose_name="Đạo diễn")

    cast = models.TextField(verbose_name="Diễn viên")

    duration = models.IntegerField(verbose_name="Thời lượng (phút)")

    release_date = models.DateField(verbose_name="Ngày khởi chiếu")

    end_date = models.DateField(verbose_name="Ngày kết thúc chiếu", null=True, blank=True)

    country = models.CharField(max_length=100, verbose_name="Quốc gia")

    language = models.CharField(max_length=50, verbose_name="Ngôn ngữ")

    rating = models.CharField(max_length=3, choices=RATING_CHOICES, verbose_name="Phân loại")

    poster = models.ImageField(upload_to='movies/posters/', verbose_name="Poster")

    trailer_url = models.URLField(blank=True, verbose_name="Link trailer")

    genres = models.ManyToManyField(Genre, related_name='movies', verbose_name="Thể loại")

    is_active = models.BooleanField(default=True, verbose_name="Đang chiếu")

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Phim"

        verbose_name_plural = "Phim"

        ordering = ['-release_date']

    def __str__(self):
        return self.title


# Model Rạp chiếu phim

class Cinema(models.Model):
    name = models.CharField(max_length=200, verbose_name="Tên rạp")

    address = models.TextField(verbose_name="Địa chỉ")

    city = models.CharField(max_length=100, verbose_name="Thành phố")

    district = models.CharField(max_length=100, verbose_name="Quận/Huyện")

    phone = models.CharField(max_length=20, verbose_name="Số điện thoại")

    email = models.EmailField(verbose_name="Email")

    is_active = models.BooleanField(default=True, verbose_name="Đang hoạt động")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Rạp chiếu"

        verbose_name_plural = "Rạp chiếu phim"

    def __str__(self):
        return f"{self.name} - {self.city}"


# Model Phòng chiếu

class Screen(models.Model):
    SCREEN_TYPE_CHOICES = [

        ('2D', '2D'),

        ('3D', '3D'),

        ('IMAX', 'IMAX'),

        ('4DX', '4DX'),

    ]

    cinema = models.ForeignKey(Cinema, on_delete=models.CASCADE, related_name='screens', verbose_name="Rạp")

    name = models.CharField(max_length=50, verbose_name="Tên phòng")

    screen_type = models.CharField(max_length=10, choices=SCREEN_TYPE_CHOICES, default='2D', verbose_name="Loại phòng")

    total_seats = models.IntegerField(verbose_name="Tổng số ghế")

    rows = models.IntegerField(verbose_name="Số hàng ghế")

    seats_per_row = models.IntegerField(verbose_name="Số ghế mỗi hàng")

    is_active = models.BooleanField(default=True, verbose_name="Đang hoạt động")

    class Meta:
        verbose_name = "Phòng chiếu"

        verbose_name_plural = "Phòng chiếu"

        unique_together = ['cinema', 'name']

    def __str__(self):
        return f"{self.cinema.name} - {self.name}"


# Model Ghế ngồi

class Seat(models.Model):
    SEAT_TYPE_CHOICES = [

        ('STANDARD', 'Ghế thường'),

        ('VIP', 'Ghế VIP'),

        ('COUPLE', 'Ghế đôi'),

    ]

    screen = models.ForeignKey(Screen, on_delete=models.CASCADE, related_name='seats', verbose_name="Phòng chiếu")

    row = models.CharField(max_length=2, verbose_name="Hàng")

    number = models.IntegerField(verbose_name="Số ghế")

    seat_type = models.CharField(max_length=10, choices=SEAT_TYPE_CHOICES, default='STANDARD', verbose_name="Loại ghế")

    is_active = models.BooleanField(default=True, verbose_name="Có thể đặt")

    class Meta:
        verbose_name = "Ghế"

        verbose_name_plural = "Ghế ngồi"

        unique_together = ['screen', 'row', 'number']

        ordering = ['row', 'number']

    def __str__(self):
        return f"{self.screen.name} - {self.row}{self.number}"


# Model Suất chiếu

class Showtime(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='showtimes', verbose_name="Phim")

    screen = models.ForeignKey(Screen, on_delete=models.CASCADE, related_name='showtimes', verbose_name="Phòng chiếu")

    start_time = models.DateTimeField(verbose_name="Giờ chiếu")

    end_time = models.DateTimeField(verbose_name="Giờ kết thúc")

    base_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Giá vé cơ bản")

    is_active = models.BooleanField(default=True, verbose_name="Đang hoạt động")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Suất chiếu"

        verbose_name_plural = "Suất chiếu"

        ordering = ['start_time']

    def __str__(self):
        return f"{self.movie.title} - {self.screen.cinema.name} - {self.start_time.strftime('%d/%m/%Y %H:%M')}"

    def is_available(self):
        return self.start_time > timezone.now() and self.is_active


# Model Giá vé theo loại ghế

class TicketPrice(models.Model):
    showtime = models.ForeignKey(Showtime, on_delete=models.CASCADE, related_name='ticket_prices',
                                 verbose_name="Suất chiếu")

    seat_type = models.CharField(max_length=10, choices=Seat.SEAT_TYPE_CHOICES, verbose_name="Loại ghế")

    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Giá vé")

    class Meta:
        verbose_name = "Giá vé"

        verbose_name_plural = "Bảng giá vé"

        unique_together = ['showtime', 'seat_type']

    def __str__(self):
        return f"{self.showtime} - {self.get_seat_type_display()}: {self.price:,.0f}đ"


# Model Đơn hàng

class Booking(models.Model):
    STATUS_CHOICES = [

        ('PENDING', 'Chờ thanh toán'),

        ('PAID', 'Đã thanh toán'),

        ('CANCELLED', 'Đã hủy'),

        ('EXPIRED', 'Hết hạn'),

    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings', verbose_name="Người đặt")

    showtime = models.ForeignKey(Showtime, on_delete=models.CASCADE, related_name='bookings', verbose_name="Suất chiếu")

    booking_code = models.CharField(max_length=20, unique=True, verbose_name="Mã đặt vé")

    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Tổng tiền")

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING', verbose_name="Trạng thái")

    payment_method = models.CharField(max_length=50, blank=True, verbose_name="Phương thức thanh toán")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Thời gian đặt")

    paid_at = models.DateTimeField(null=True, blank=True, verbose_name="Thời gian thanh toán")

    expires_at = models.DateTimeField(verbose_name="Hết hạn lúc")

    class Meta:
        verbose_name = "Đơn đặt vé"

        verbose_name_plural = "Đơn đặt vé"

        ordering = ['-created_at']

    def __str__(self):
        return f"{self.booking_code} - {self.user.username}"


# Model Vé

class Ticket(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='tickets', verbose_name="Đơn hàng")

    seat = models.ForeignKey(Seat, on_delete=models.CASCADE, verbose_name="Ghế")

    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Giá vé")

    is_used = models.BooleanField(default=False, verbose_name="Đã sử dụng")

    used_at = models.DateTimeField(null=True, blank=True, verbose_name="Thời gian sử dụng")

    class Meta:
        verbose_name = "Vé"

        verbose_name_plural = "Vé xem phim"

        unique_together = ['booking', 'seat']

    def __str__(self):
        return f"{self.booking.booking_code} - {self.seat}"


# Model Ghế đã đặt (tạm giữ ghế trong thời gian thanh toán)

class SeatReservation(models.Model):
    showtime = models.ForeignKey(Showtime, on_delete=models.CASCADE, verbose_name="Suất chiếu")

    seat = models.ForeignKey(Seat, on_delete=models.CASCADE, verbose_name="Ghế")

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Đơn hàng")

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Người đặt")

    reserved_at = models.DateTimeField(auto_now_add=True, verbose_name="Thời gian đặt")

    expires_at = models.DateTimeField(verbose_name="Hết hạn lúc")

    is_active = models.BooleanField(default=True, verbose_name="Đang giữ chỗ")

    class Meta:
        verbose_name = "Ghế đã đặt"

        verbose_name_plural = "Ghế đã đặt"

        unique_together = ['showtime', 'seat']

    def __str__(self):
        return f"{self.showtime} - {self.seat} - {self.user.username}"


# Model Đánh giá phim

class Review(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='reviews', verbose_name="Phim")

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews', verbose_name="Người đánh giá")

    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="Đánh giá")

    comment = models.TextField(verbose_name="Bình luận")

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Đánh giá"

        verbose_name_plural = "Đánh giá phim"

        unique_together = ['movie', 'user']

        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.movie.title} - {self.rating}★"