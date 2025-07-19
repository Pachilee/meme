from django.urls import path
from .views import landing_page, movie_detail, user_based_recommendation

urlpatterns = [
    path ("", landing_page, name="landing_page"),
    path("movie/<int:movie_id>", movie_detail, name="movie_detail"),
    path("recommendations/", user_based_recommendation, name="user_recommendation"),
]