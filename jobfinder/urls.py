from django.urls import path, include
from .import views
from .views import match_jobs_view, match_jobs

app_name = 'jobfinder'

urlpatterns = [
    path('', views.home, name='home'),
    path('jobs/', views.job_list, name='job_list'),
    path("api/match/<int:cv_id>/", match_jobs, name="match_jobs_json"),
    path("match/<int:cv_id>/", match_jobs_view, name="match_jobs_view"),
]