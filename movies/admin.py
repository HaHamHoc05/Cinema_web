from django.contrib import admin
from .models import (
    Genre, Movie, Cinema, Screen, Seat,
    Showtime, TicketPrice, Booking, Ticket,
    SeatReservation, Review
)

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ['title', 'director', 'release_date', 'duration', 'rating', 'is_active']
    list_filter = ['rating', 'is_active', 'release_date', 'genres']
    search_fields = ['title', 'director', 'cast']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'release_date'

@admin.register(Cinema)
class CinemaAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'district', 'phone', 'is_active']
    list_filter = ['city', 'is_active']
    search_fields = ['name', 'address', 'city']

@admin.register(Screen)
class ScreenAdmin(admin.ModelAdmin):
    list_display = ['name', 'cinema', 'screen_type', 'total_seats', 'is_active']
    list_filter = ['cinema', 'screen_type', 'is_active']
    search_fields = ['name', 'cinema__name']

@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ['screen', 'row', 'number', 'seat_type', 'is_active']
    list_filter = ['screen', 'seat_type', 'is_active']
    search_fields = ['row', 'number']

@admin.register(Showtime)
class ShowtimeAdmin(admin.ModelAdmin):
    list_display = ['movie', 'screen', 'start_time', 'base_price', 'is_active']
    list_filter = ['screen__cinema', 'is_active', 'start_time']
    search_fields = ['movie__title', 'screen__name']
    date_hierarchy = 'start_time'

@admin.register(TicketPrice)
class TicketPriceAdmin(admin.ModelAdmin):
    list_display = ['showtime', 'seat_type', 'price']
    list_filter = ['seat_type']

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['booking_code', 'user', 'showtime', 'total_amount', 'status', 'created_at']
    list_filter = ['status', 'created_at', 'payment_method']
    search_fields = ['booking_code', 'user__username']
    date_hierarchy = 'created_at'

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['booking', 'seat', 'price', 'is_used']
    list_filter = ['is_used', 'booking__status']
    search_fields = ['booking__booking_code']

@admin.register(SeatReservation)
class SeatReservationAdmin(admin.ModelAdmin):
    list_display = ['showtime', 'seat', 'user', 'reserved_at', 'expires_at', 'is_active']
    list_filter = ['is_active', 'reserved_at']
    search_fields = ['user__username', 'seat__row']

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['movie', 'user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['movie__title', 'user__username', 'comment']