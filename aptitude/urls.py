from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('', views.home, name='home'),
    path('dailyprobblems/', views.dailyprobblems, name='dailyprobblems'),
    path('profile/', views.profile, name='profile'),
    path('daily_leaderboard/', views.daily_leaderboard, name='daily_leaderboard'),
    path('monthly_leaderboard/', views.monthly_leaderboard, name='monthly_leaderboard'),
    path('past_problems/', views.past_problems, name='past_problems'),
]