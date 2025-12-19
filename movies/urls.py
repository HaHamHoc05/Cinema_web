from django.urls import path
from . import views

urlpatterns = [
    path('', views.movie_list, name='movie_list'),

    path('showtime/<int:showtime_id>/', views.showtime_detail, name='showtime_detail'),

    path('showtime/<int:showtime_id>/book/', views.book_tickets, name='book_tickets'),

    path('booking/success/<int:booking_id>/', views.booking_success, name='booking_success'),
]