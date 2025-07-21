from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('login/', views.login_view, name='login'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('', views.home, name='home'),
    path('dailyprobblems/', views.dailyprobblems, name='dailyprobblems'),
    path('profile/', views.profile, name='profile'),
    path('profile/<str:username>/', views.public_profile, name='public_profile'),
    path('daily_leaderboard/', views.daily_leaderboard, name='daily_leaderboard'),
    path('monthly_leaderboard/', views.monthly_leaderboard, name='monthly_leaderboard'),
    path('past_problems/', views.past_problems, name='past_problems'),
    path('companywise/', views.companywise, name='companywise'),
    path('company/<str:company_name>/', views.company_problems, name='company_problems'),
    path('test/<int:test_id>/', views.test_view, name='test_view'),
    path('test_leaderboard/<int:test_id>/', views.test_leaderboard, name='test_leaderboard'),
    path('user_attempted_questions/<int:test_id>/<int:user_id>/', views.user_attempted_questions, name='user_attempted_questions'),
    path('instructions/<int:test_id>/', views.instructions, name='instructions'),
    path('start_test/<int:test_id>/', views.start_test, name='start_test'),
    path('cancel_test/<int:test_id>/', views.cancel_test, name='cancel_test'),
    path('placement-drive/', views.placement_drive, name='placement_drive'),
    path('placement-apply/<int:company_id>/', views.placement_application, name='placement_application'),
]