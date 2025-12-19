from PIL.ImageChops import screen
from django.contrib.auth import logout, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from pyexpat.errors import messages

from . import services
from .form import SignUpForm
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