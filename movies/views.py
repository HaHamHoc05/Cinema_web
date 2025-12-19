from django.shortcuts import render
from .models import Movie

def movie_list(self, request):
    movies = Movie.objects.filter(is_active=True)
    return render(request, 'movies/movie_list.html', {'movies': movies})