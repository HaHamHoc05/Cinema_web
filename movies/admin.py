from django.contrib import admin
from django.contrib import messages
from .models import (
    Genre, Movie, Cinema, Screen, Seat,
    Showtime, TicketPrice, Booking, Ticket,
    SeatReservation, Review, Concession, BookingConcession
)


class SeatInline(admin.TabularInline):
    model = Seat
    extra = 0
    readonly_fields = ('row', 'number')
    can_delete = True


@admin.register(Screen)
class ScreenAdmin(admin.ModelAdmin):
    list_display = ['name', 'cinema', 'screen_type', 'total_seats', 'count_seats_real']
    list_filter = ['cinema', 'screen_type']
    search_fields = ['name', 'cinema__name']
    inlines = [SeatInline]

    def count_seats_real(self, obj):
        count = obj.seats.count()
        return f"{count} ghế"

    count_seats_real.short_description = "Dữ liệu ghế thực tế"

    actions = ['generate_seats']

    def generate_seats(self, request, queryset):
        for screen in queryset:
            if not screen.rows or not screen.seats_per_row:
                self.message_user(request, f"Lỗi: Phòng {screen.name} chưa nhập số hàng/ghế!", level=messages.ERROR)
                continue

            # Xóa ghế cũ để tạo lại
            Seat.objects.filter(screen=screen).delete()

            row_labels = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            seats_created = 0

            for r in range(screen.rows):
                if r >= len(row_labels): break
                row_char = row_labels[r]

                # --- LOGIC PHÂN LOẠI GHẾ THÔNG MINH ---
                # 1. Hàng cuối cùng -> Ghế Đôi (COUPLE)
                if r == screen.rows - 1:
                    seat_type = 'COUPLE'
                # 2. Các hàng giữa (từ hàng thứ 3 đếm ngược lên) -> Ghế VIP
                # (Ví dụ: Có 10 hàng thì hàng F, G, H, I là VIP)
                elif r >= screen.rows - 5:
                    seat_type = 'VIP'
                # 3. Còn lại (đầu màn hình) -> Ghế Thường (STANDARD)
                else:
                    seat_type = 'STANDARD'

                for n in range(1, screen.seats_per_row + 1):
                    # Nếu là ghế đôi, thường chỉ có số chẵn hoặc ít ghế hơn
                    # Ở đây ta cứ tạo đủ, bạn có thể xóa bớt trong Admin sau nếu muốn
                    Seat.objects.create(
                        screen=screen,
                        row=row_char,
                        number=n,
                        seat_type=seat_type
                    )
                    seats_created += 1

            self.message_user(request, f"✅ Đã tạo {seats_created} ghế cho {screen.name} (Có VIP & Couple)!")

    generate_seats.short_description = "⚡ Tự động tạo ghế (VIP giữa, Couple cuối)"


# ... (Giữ nguyên các phần đăng ký model khác bên dưới) ...
admin.site.register(Genre)
admin.site.register(Movie)
admin.site.register(Cinema)


# Lưu ý: Class SeatAdmin cũ của bạn có thể giữ nguyên hoặc cập nhật để hiển thị màu sắc cho vui (nâng cao)
@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ['screen', 'row', 'number', 'seat_type', 'is_active']
    list_filter = ['screen', 'seat_type']
    search_fields = ['row', 'number']


admin.site.register(Showtime)
admin.site.register(TicketPrice)
admin.site.register(Booking)
admin.site.register(Ticket)
admin.site.register(SeatReservation)
admin.site.register(Review)
admin.site.register(Concession)
admin.site.register(BookingConcession)