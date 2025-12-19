from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.core.exceptions import ValidationError

from .models import Movie, Showtime, Booking, Ticket, Seat
from .form import SignUpForm, ReviewForm, UserUpdateForm
# Đảm bảo bạn đã có file services.py và hàm create_booking
from .services import create_booking


def movie_list(request):
    query = request.GET.get('q')
    if query:
        movies = Movie.objects.filter(
            Q(title__icontains=query) | Q(director__icontains=query),
            is_active=True
        )
    else:
        movies = Movie.objects.filter(is_active=True)
    return render(request, 'movies/movie_list.html', {'movies': movies})


def search_suggestions(request):
    query = request.GET.get('term', '')
    if query:
        movies = Movie.objects.filter(title__icontains=query, is_active=True)[:5]
        results = [{'id': m.id, 'title': m.title, 'poster': m.poster.url if m.poster else ''} for m in movies]
    else:
        results = []
    return JsonResponse(results, safe=False)


def movie_detail(request, movie_id):
    movie = get_object_or_404(Movie, pk=movie_id)
    showtimes = movie.showtimes.filter(is_active=True).order_by('start_time')
    reviews = movie.reviews.all()
    form = ReviewForm(request.POST or None)

    if request.method == 'POST' and form.is_valid() and request.user.is_authenticated:
        rv = form.save(commit=False)
        rv.movie = movie
        rv.user = request.user
        rv.save()
        messages.success(request, "Đã đăng đánh giá!")
        return redirect('movie_detail', movie_id=movie_id)

    return render(request, 'movies/movie_detail.html', {
        'movie': movie,
        'showtimes': showtimes,
        'reviews': reviews,
        'form': form
    })


def showtime_detail(request, showtime_id):
    showtime = get_object_or_404(Showtime, pk=showtime_id)
    all_seats = Seat.objects.filter(screen=showtime.screen).order_by('row', 'number')

    occupied_seats = Ticket.objects.filter(
        booking__showtime=showtime,
        booking__status__in=['PAID', 'PENDING']
    ).values_list('seat_id', flat=True)

    return render(request, 'movies/showtime_detail.html', {
        'showtime': showtime,
        'all_seats': all_seats,
        'occupied_seats': list(occupied_seats),
    })


@login_required(login_url='login')
@require_POST
def book_tickets(request, showtime_id):
    seat_ids = request.POST.getlist('selected_seats')
    if not seat_ids:
        messages.error(request, "Bạn chưa chọn ghế nào!")
        return redirect('showtime_detail', showtime_id=showtime_id)

    try:
        # Gọi Service xử lý transaction
        booking = create_booking(request.user, showtime_id, seat_ids)
        messages.success(request, "Đặt vé thành công! Vui lòng thanh toán.")
        return redirect('booking_success', booking_id=booking.id)

    except ValidationError as e:
        # SỬA LỖI Ở ĐÂY: Dùng e.messages hoặc str(e) thay vì e.message
        error_msg = ""
        if hasattr(e, 'message'):
            error_msg = e.message
        elif hasattr(e, 'messages'):
            error_msg = ", ".join(e.messages)
        else:
            error_msg = str(e)

        messages.error(request, f"Lỗi đặt vé: {error_msg}")
        return redirect('showtime_detail', showtime_id=showtime_id)

    except Exception as e:
        print(f"Error booking tickets: {e}")  # In lỗi ra console để debug
        messages.error(request, "Có lỗi hệ thống xảy ra. Vui lòng thử lại.")
        return redirect('showtime_detail', showtime_id=showtime_id)


def booking_success(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    return render(request, 'movies/booking_success.html', {'booking': booking})


@login_required
def pay_booking(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    if booking.status == 'PENDING':
        booking.status = 'PAID'
        # Nếu model có trường paid_at thì bỏ comment dòng dưới
        # from django.utils import timezone
        # booking.paid_at = timezone.now()
        booking.save()
        messages.success(request, "Thanh toán thành công! Chúc bạn xem phim vui vẻ.")
    return redirect('booking_success', booking_id=booking.id)


# --- Auth Views ---
def register_view(request):
    form = SignUpForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f"Chào mừng {user.username} đến với Cinema Pro!")
        return redirect('movie_list')
    return render(request, 'movies/register.html', {'form': form})


def login_view(request):
    form = AuthenticationForm(data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        next_url = request.POST.get('next') or 'movie_list'
        return redirect(next_url)
    return render(request, 'movies/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('movie_list')


@login_required
def profile_view(request):
    form = UserUpdateForm(request.POST or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Cập nhật thông tin thành công!")
    return render(request, 'movies/profile.html', {'form': form})


@login_required
def my_tickets(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'movies/my_tickets.html', {'bookings': bookings})