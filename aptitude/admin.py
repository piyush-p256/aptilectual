# aptitude/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Achievement, CancelledTest, CustomUser, Problem, Test, TestAnswer, UserAnswer, LeaderDaily, Company, PlacementCompany

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = (
        'email', 'username', 'is_staff', 'is_active', 'date_joined', 'rating', 'current_streak', 'highest_streak',
        'cgpa', 'total_percentage', 'class12_percentage', 'class10_percentage',
        'active_backlogs', 'total_backlogs',
        'name', 'student_class'
    )
    list_filter = ('is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal Info', {'fields': (
            'name', 'student_class',
            'profile_picture', 'bio', 'start_year', 'end_year',
            'branch', 'enrollment_number', 'contact_number',
            'sem1_sgpa', 'sem2_sgpa', 'sem3_sgpa', 'sem4_sgpa',
            'sem5_sgpa', 'sem6_sgpa', 'sem7_sgpa', 'sem8_sgpa',
            'cgpa', 'total_percentage', 'class12_percentage', 'class10_percentage',
            'active_backlogs', 'total_backlogs',
        )}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'groups', 'user_permissions')}),
        ('Stats', {'fields': ('total_attempted', 'total_correct', 'current_streak', 'highest_streak', 'rating', 'last_active_date')}),
        ('Achievements', {'fields': ('achievements',)}),
        ('Leaderboard', {'fields': ('first_position_count', 'second_position_count', 'third_position_count')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    search_fields = ('email', 'username')
    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions', 'achievements')



admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Problem)
admin.site.register(UserAnswer)
admin.site.register(LeaderDaily)
admin.site.register(Company)
admin.site.register(TestAnswer)
admin.site.register(Test)
admin.site.register(CancelledTest)
admin.site.register(Achievement)
admin.site.register(PlacementCompany)