from sklearn.linear_model import LinearRegression

import numpy as np
import pandas as pd
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models.functions import ExtractQuarter, TruncMonth, TruncDay, ExtractHour
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count, Sum
from django.core.exceptions import ValidationError
import json


from .models import Movie, Showtime, Booking, Ticket, Seat, TicketPrice, Concession
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


    ticket_prices = TicketPrice.objects.filter(showtime=showtime)
    price_map = {tp.seat_type: tp.price for tp in ticket_prices}

    concessions = Concession.objects.all()

    return render(request, 'movies/showtime_detail.html', {
        'showtime': showtime,
        'all_seats': all_seats,
        'occupied_seats': list(occupied_seats),
        'price_map': price_map,
        'concessions': concessions,
    })


@login_required(login_url='login')
@require_POST
def book_tickets(request, showtime_id):
    seat_ids = request.POST.getlist('selected_seats')
    if not seat_ids:
        messages.error(request, "Bạn chưa chọn ghế nào!")
        return redirect('showtime_detail', showtime_id=showtime_id)
    # bap nuoc
    concession_data = {}
    for key, value in request.POST.items():
        if key.startswith('concession_'):
            try:
                qty = int(value)
                if qty > 0:
                    c_id = int(key.split('_')[1])
                    concession_data[c_id] = qty
            except ValueError:
                continue
    try:
        # Gọi Service xử lý transaction
        booking = create_booking(request.user, showtime_id, seat_ids, concession_data)
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


@staff_member_required(login_url='login')
def admin_statistics(request):
    # 1. Lọc dữ liệu (Filter)
    current_date = timezone.now()
    try:
        year = int(request.GET.get('year', current_date.year))
    except ValueError:
        year = current_date.year

    month = request.GET.get('month')
    quarter = request.GET.get('quarter')
    day = request.GET.get('day')

    # Queryset gốc: Đơn hàng ĐÃ THANH TOÁN
    # Lưu ý: Lọc theo năm được chọn để hiển thị số liệu thống kê
    bookings = Booking.objects.filter(status='PAID', created_at__year=year)

    chart_title = f"Biểu đồ doanh thu năm {year}"
    group_by_field = TruncMonth('created_at')  # Mặc định gom nhóm theo Tháng
    time_format = "%m/%Y"

    if quarter:
        bookings = bookings.annotate(quarter=ExtractQuarter('created_at')).filter(quarter=quarter)
        chart_title = f"Biểu đồ doanh thu Quý {quarter}/{year}"
        # Quý thì vẫn xem theo tháng

    if month:
        bookings = bookings.filter(created_at__month=month)
        chart_title = f"Biểu đồ doanh thu Tháng {month}/{year}"
        group_by_field = TruncDay('created_at')  # Nếu chọn tháng -> Xem theo Ngày
        time_format = "%d/%m"

        if day:
            bookings = bookings.filter(created_at__day=day)
            chart_title = f"Biểu đồ doanh thu Ngày {day}/{month}/{year}"
            group_by_field = ExtractHour('created_at')  # Nếu chọn ngày -> Xem theo Giờ
            time_format = "%H:00"

    # 2. Xử lý dữ liệu cho Biểu đồ Đường (Line Chart)
    # Gom nhóm theo thời gian (Tháng/Ngày/Giờ) dựa trên bộ lọc
    revenue_over_time = bookings.annotate(
        period=group_by_field
    ).values('period').annotate(
        total=Sum('total_amount')
    ).order_by('period')

    chart_labels = []
    chart_data = []

    for item in revenue_over_time:
        if isinstance(item['period'], int):  # Trường hợp group theo Giờ (trả về số int)
            label = f"{item['period']}:00"
        else:  # Trường hợp Ngày/Tháng (trả về datetime)
            label = item['period'].strftime(time_format)

        chart_labels.append(label)
        chart_data.append(float(item['total']))

    # 3. Thống kê tổng quan (Top Cards)
    total_revenue = bookings.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_tickets = bookings.aggregate(Count('tickets'))['tickets__count'] or 0

    # 4. Thống kê Top Phim (Để hiển thị bảng chi tiết bên dưới)
    movie_stats = bookings.values('showtime__movie__title').annotate(
        revenue=Sum('total_amount'),
        ticket_count=Count('tickets')
    ).order_by('-revenue')

    # 5. DỰ ĐOÁN DOANH THU THÁNG TỚI & TĂNG TRƯỞNG (AI)
    # Lưu ý: Dùng TOÀN BỘ dữ liệu lịch sử để train model cho chính xác (không lọc theo year)
    all_history = Booking.objects.filter(status='PAID').annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        revenue=Sum('total_amount')
    ).order_by('month')

    df = pd.DataFrame(list(all_history))

    predicted_revenue = 0
    growth_percent = 0
    current_month_revenue = 0

    if not df.empty:
        # Doanh thu tháng hiện tại (Tháng gần nhất trong DB)
        current_month_revenue = df['revenue'].iloc[-1]

        # Train AI
        df['month_num'] = np.arange(len(df))
        X = df[['month_num']]
        y = df['revenue']

        model = LinearRegression()
        model.fit(X, y)

        # Dự đoán tháng tiếp theo
        next_month_index = df['month_num'].iloc[-1] + 1
        prediction = model.predict([[next_month_index]])
        predicted_revenue = max(0, round(prediction[0]))  # Không lấy số âm

        # Tính % Tăng trưởng: (Dự đoán - Hiện tại) / Hiện tại * 100
        if current_month_revenue > 0:
            growth_percent = ((predicted_revenue - current_month_revenue) / current_month_revenue) * 100
        else:
            growth_percent = 100 if predicted_revenue > 0 else 0

    # Danh sách năm cho dropdown
    available_years = Booking.objects.dates('created_at', 'year', order='DESC')
    years_list = [y.year for y in available_years] if available_years else [current_date.year]

    return render(request, 'movies/admin_stats.html', {
        'chart_labels': chart_labels,  # Nhãn thời gian (Trục X)
        'chart_data': chart_data,  # Doanh thu (Trục Y)
        'chart_title': chart_title,

        'predicted_revenue': predicted_revenue,
        'growth_percent': round(growth_percent, 1),
        'current_month_revenue': current_month_revenue,

        'movie_stats': movie_stats,
        'total_revenue': total_revenue,
        'total_tickets': total_tickets,
        'years_list': years_list,
        'selected_year': year,
        'selected_month': int(month) if month else '',
        'selected_quarter': int(quarter) if quarter else '',
        'selected_day': int(day) if day else '',
    })

def movie_list(request):
    query = request.GET.get('q')
    today = timezone.now().date()  # Lấy ngày hôm nay

    # Lọc cơ bản: Phải là phim đang Active (hiển thị trên web)
    base_movies = Movie.objects.filter(is_active=True)

    if query:
        # Nếu đang tìm kiếm thì tìm chung cả 2 loại
        movies_now = base_movies.filter(
            Q(title__icontains=query) | Q(director__icontains=query),
            release_date__lte=today
        )
        movies_upcoming = base_movies.filter(
            Q(title__icontains=query) | Q(director__icontains=query),
            release_date__gt=today
        )
    else:
        # Phim đang chiếu: Ngày chiếu <= Hôm nay
        movies_now = base_movies.filter(release_date__lte=today).order_by('-release_date')

        # Phim sắp chiếu: Ngày chiếu > Hôm nay
        movies_upcoming = base_movies.filter(release_date__gt=today).order_by('release_date')

    return render(request, 'movies/movie_list.html', {
        'movies_now': movies_now,
        'movies_upcoming': movies_upcoming,
        'query': query
    })