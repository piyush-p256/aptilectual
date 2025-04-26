# aptitude/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Achievement, CancelledTest, CustomUser, Problem, Test, TestAnswer, UserAnswer, LeaderDaily, Company

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'username', 'is_staff', 'is_active', 'date_joined', 'rating', 'current_streak', 'highest_streak')
    list_filter = ('is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Personal Info', {'fields': ('profile_picture', 'bio')}),
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