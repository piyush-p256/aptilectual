# aptitude/models.py

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, username, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    total_attempted = models.IntegerField(default=0)
    total_correct = models.IntegerField(default=0)
    current_streak = models.IntegerField(default=0)
    highest_streak = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    first_position_count = models.IntegerField(default=0)
    second_position_count = models.IntegerField(default=0)
    third_position_count = models.IntegerField(default=0)

    groups = models.ManyToManyField(
        Group,
        related_name='customuser_set',
        related_query_name='customuser',
        blank=True,
        verbose_name='groups',
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.'
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='customuser_set',
        related_query_name='customuser',
        blank=True,
        verbose_name='user permissions',
        help_text='Specific permissions for this user.'
    )

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

class Problem(models.Model):
    id = models.AutoField(primary_key=True)  # Explicitly define the id field
    question = models.TextField(null=True, blank=True)
    option1 = models.CharField(max_length=255, null=True, blank=True)
    option2 = models.CharField(max_length=255, null=True, blank=True)
    option3 = models.CharField(max_length=255, null=True, blank=True)
    option4 = models.CharField(max_length=255, null=True, blank=True)
    correct_option = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(4)],
        null=True,
        blank=True
    )
    is_active = models.BooleanField(default=True, null=True, blank=True)
    done = models.BooleanField(default=False, null=True, blank=True)
    answerurl = models.URLField(null=True, blank=True)
    companyname = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.question or "No question"

class UserAnswer(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    selected_option = models.IntegerField()
    solution_image_url = models.URLField(null=True, blank=True)
    time_solved = models.DateTimeField(auto_now_add=True)
    is_correct = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'problem')  # Ensure a user can only solve a problem once

class LeaderDaily(models.Model):
    show_leaderboard = models.BooleanField(default=False)

    def __str__(self):
        return f"Show Leaderboard: {self.show_leaderboard}"
    


class Company(models.Model):
    name = models.CharField(max_length=255, unique=True)
    logo_url = models.URLField(null=True, blank=True)
    hired_last_year = models.IntegerField(null=True, blank=True)  # New field
    description = models.CharField(max_length=500, null=True, blank=True)  # New field

    def __str__(self):
        return self.name