from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from .models import Movie, Showtime, Booking, Ticket, Seat, Review
# SỬA LỖI Ở ĐÂY: đổi .forms thành .form (khớp với file bạn có)
from .form import SignUpForm, ReviewForm, UserUpdateForm


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


def showtime_detail(request, showtime_id):
    showtime = get_object_or_404(Showtime, pk=showtime_id)
    # QUAN TRỌNG: Phải order_by thì sơ đồ mới xếp đúng hàng A, B, C
    all_seats = Seat.objects.filter(screen=showtime.screen).order_by('row', 'number')
    occupied_seats = Ticket.objects.filter(booking__showtime=showtime).values_list('seat_id', flat=True)
    return render(request, 'movies/showtime_detail.html', {
        'showtime': showtime,
        'all_seats': all_seats,
        'occupied_seats': occupied_seats,
    })


@login_required(login_url='login')
@require_POST
def book_tickets(request, showtime_id):
    showtime = get_object_or_404(Showtime, pk=showtime_id)
    seat_ids = request.POST.getlist('selected_seats')
    if not seat_ids:
        messages.error(request, "Vui lòng chọn ghế!")
        return redirect('showtime_detail', showtime_id=showtime_id)

    total = 0
    selected_seats = Seat.objects.filter(id__in=seat_ids)
    for seat in selected_seats:
        price = showtime.base_price
        # Logic cộng tiền đơn giản
        if seat.seat_type == 'VIP':
            price += 10000
        elif seat.seat_type == 'COUPLE':
            price += 20000
        total += price

    booking = Booking.objects.create(user=request.user, showtime=showtime, total_amount=total, status='PENDING')
    for seat in selected_seats:
        Ticket.objects.create(booking=booking, seat=seat)

    return redirect('booking_success', booking_id=booking.id)


def booking_success(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id)
    return render(request, 'movies/booking_success.html', {'booking': booking})


@login_required(login_url='login')
def pay_booking(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    if booking.status == 'PENDING':
        booking.status = 'PAID'
        booking.save()
        messages.success(request, "Thanh toán thành công!")
    return redirect('booking_success', booking_id=booking.id)


def movie_detail(request, movie_id):
    movie = get_object_or_404(Movie, pk=movie_id)
    reviews = movie.reviews.all()
    form = ReviewForm(request.POST or None)
    if request.method == 'POST' and form.is_valid() and request.user.is_authenticated:
        rv = form.save(commit=False)
        rv.movie = movie
        rv.user = request.user
        rv.save()
        return redirect('movie_detail', movie_id=movie_id)
    return render(request, 'movies/movie_detail.html', {'movie': movie, 'reviews': reviews, 'form': form})


def register_view(request):
    form = SignUpForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect('movie_list')
    return render(request, 'movies/register.html', {'form': form})


def login_view(request):
    form = AuthenticationForm(data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        if 'next' in request.POST: return redirect(request.POST.get('next'))
        return redirect('movie_list')
    return render(request, 'movies/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('movie_list')


@login_required
def profile_view(request):
    form = UserUpdateForm(request.POST or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
    return render(request, 'movies/profile.html', {'form': form})


@login_required
def my_tickets(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'movies/my_tickets.html', {'bookings': bookings})