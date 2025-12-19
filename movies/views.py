from PIL.ImageChops import screen
from django.contrib.auth import logout, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.mail import send_mail
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags
from django.views.decorators.http import require_POST
from pyexpat.errors import messages

from . import services
from .form import SignUpForm, UserUpdateForm, ReviewForm
from .models import Movie, Showtime, Seat, Booking


def movie_list(request):
    movies = Movie.objects.filter(is_active=True)
    return render(request, 'movies/movie_list.html', {'movies': movies})

# trang chi tiet suat chieu
def showtime_detail(request, showtime_id):
    #lay suat nhieu, neu kh tim thay bao loi 404
    showtime = get_object_or_404(Showtime, pk=showtime_id)

    #goi service: lay danh sach ghe da PAID hoac PENDING
    occupied_seats = services.get_occupied_seats(showtime_id)

    # ve so do phong chieu va sap xep theo hang ,so
    all_seats = Seat.objects.filter(screen=showtime.screen).order_by('row', 'number')

    return render(request, 'movies/showtime_detail.html', {
        'showtime': showtime,
        'all_seats': all_seats,
        'occupied_seats': occupied_seats, # truyen danh sach ghe paid, pending

    })

# xu ly dat ve ( chi nhan req POST)
@login_required(login_url='login')
@require_POST # cho phe gui du lieu ngam, kh cho truc tiep
def book_tickets(request, showtime_id):
    try:
        # lay ds id ghe ma kh chon tu form
        seat_ids = request.POST.getlist('selected_seats')
        #chuyen doi id tu chuoi sang so
        seat_ids = [int(id) for id in seat_ids]

        if not seat_ids:
            messages.warning(request, "Bạn chưa chọn ghế nào!")
            return  redirect('showtime_detail', showtime_id=showtime_id)

        #goi serviec de thuc hienj gd
        booking = services.create_booking(request.user, showtime_id, seat_ids)

        return redirect('booking_success', booking_id=booking.id)

    except Exception as e:
        #neu loi
        messages.error(request, f'Lỗi đặt vé: {str(e)}')
        return redirect('showtime_detail', showtime_id=showtime_id)

def booking_success(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    return render(request, 'movies/booking_success.html', {'booking': booking})

def register_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Đăng ký xong tự động đăng nhập luôn
            messages.success(request, "Đăng ký thành công!")
            return redirect('movie_list')
    else:
        form = SignUpForm()
    return render(request, 'movies/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # Nếu người dùng bị chuyển hướng từ trang đặt vé, quay lại đó
            if 'next' in request.POST:
                return redirect(request.POST.get('next'))
            return redirect('movie_list')
    else:
        form = AuthenticationForm()
    return render(request, 'movies/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('movie_list')


@login_required(login_url='login')
def my_tickets(request):
    # Lấy danh sách booking của user hiện tại, sắp xếp mới nhất lên đầu
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')

    return render(request, 'movies/my_tickets.html', {'bookings': bookings})


def movie_list(request):
    query = request.GET.get('q')
    if query:
        # Tìm theo tên phim hoặc tên đạo diễn
        movies = Movie.objects.filter(
            Q(title__icontains=query) | Q(director__icontains=query),
            is_active=True
        )
    else:
        movies = Movie.objects.filter(is_active=True)
    return render(request, 'movies/movie_list.html', {'movies': movies, 'query': query})


# 2. Thêm trang Chi Tiết Phim + Review (Thay vì chỉ xem suất chiếu)
def movie_detail(request, movie_id):
    movie = get_object_or_404(Movie, pk=movie_id)
    reviews = movie.reviews.all()

    # Xử lý form review
    if request.method == 'POST' and request.user.is_authenticated:
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.movie = movie
            review.user = request.user
            review.save()
            messages.success(request, "Cảm ơn bạn đã đánh giá!")
            return redirect('movie_detail', movie_id=movie_id)
    else:
        form = ReviewForm()

    return render(request, 'movies/movie_detail.html', {
        'movie': movie,
        'reviews': reviews,
        'form': form
    })


# 3. Hàm Gửi Email (Helper function)
def send_booking_email(booking):
    subject = f'Vé xem phim: {booking.showtime.movie.title}'
    html_message = render_to_string('movies/email_template.html', {'booking': booking})
    plain_message = strip_tags(html_message)

    send_mail(
        subject,
        plain_message,
        'booking@cinemapro.vn',
        [booking.user.email],
        html_message=html_message,
    )


# 4. Hàm Thanh Toán (Giả lập)
@login_required(login_url='login')
def pay_booking(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)

    if booking.status == 'PENDING':
        booking.status = 'PAID'
        booking.payment_method = 'VNPAY_Sandbox'  # Giả lập
        booking.paid_at = timezone.now()
        booking.save()

        # Gửi email sau khi thanh toán thành công
        try:
            send_booking_email(booking)
            messages.success(request, "Thanh toán thành công! Vé đã được gửi tới Email.")
        except Exception as e:
            messages.warning(request, "Thanh toán thành công nhưng không gửi được mail.")

    return redirect('booking_success', booking_id=booking.id)


# 5. Hàm Quản lý Profile
@login_required(login_url='login')
def profile_view(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Cập nhật thông tin thành công!")
            return redirect('profile')
    else:
        form = UserUpdateForm(instance=request.user)
    return render(request, 'movies/profile.html', {'form': form})