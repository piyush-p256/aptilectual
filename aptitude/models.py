from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
try:
    from multiselectfield import MultiSelectField
    MULTISELECT_AVAILABLE = True
except ImportError:
    MULTISELECT_AVAILABLE = False
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings

BRANCH_CHOICES = [
    ('IT', 'IT'),
    ('CSE', 'CSE'),
    ('ECE', 'ECE'),
    ('EEE', 'EEE'),
    ('ICE', 'ICE'),
]


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


class Achievement(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    icon_url = models.URLField(null=True, blank=True)

    def __str__(self):
        return self.name


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    start_year = models.IntegerField(null=True, blank=True)
    end_year = models.IntegerField(null=True, blank=True)
    branch = models.CharField(max_length=100, null=True, blank=True)
    enrollment_number = models.CharField(max_length=100, null=True, blank=True, unique=True)
    contact_number = models.CharField(max_length=15, null=True, blank=True)
    total_attempted = models.IntegerField(default=0)
    total_correct = models.IntegerField(default=0)
    current_streak = models.IntegerField(default=0)
    highest_streak = models.IntegerField(default=0)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    rating = models.FloatField(default=0)  # New rating field
    last_active_date = models.DateField(null=True, blank=True)  # For streak calculation
    profile_picture = models.URLField(null=True, blank=True)  # Public profile picture URL
    bio = models.TextField(null=True, blank=True)  # User bio
    first_position_count = models.IntegerField(default=0)
    second_position_count = models.IntegerField(default=0)
    third_position_count = models.IntegerField(default=0)
    last_active_date = models.DateField(null=True, blank=True)
    sem1_sgpa = models.FloatField(null=True, blank=True)
    sem2_sgpa = models.FloatField(null=True, blank=True)
    sem3_sgpa = models.FloatField(null=True, blank=True)
    sem4_sgpa = models.FloatField(null=True, blank=True)
    sem5_sgpa = models.FloatField(null=True, blank=True)
    sem6_sgpa = models.FloatField(null=True, blank=True)
    sem7_sgpa = models.FloatField(null=True, blank=True)
    sem8_sgpa = models.FloatField(null=True, blank=True)
    cgpa = models.FloatField(null=True, blank=True)
    active_backlogs = models.IntegerField(default=0)
    total_backlogs = models.IntegerField(default=0)
    class12_percentage = models.FloatField(null=True, blank=True)
    class10_percentage = models.FloatField(null=True, blank=True)
    total_percentage = models.FloatField(null=True, blank=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    student_class = models.IntegerField(null=True, blank=True)

    
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
    # New Many-to-Many field for Achievements/Badges
    achievements = models.ManyToManyField(Achievement, blank=True)
    
    date_joined = models.DateTimeField(default=timezone.now)

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
    type = models.CharField(max_length=255, null=True, blank=True)
    test_id = models.IntegerField(null=True, blank=True)
    questionimage = models.URLField(null=True, blank=True)

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
    description = models.CharField(max_length=5000, null=True, blank=True)  # New field

    def __str__(self):
        return self.name


class TestAnswer(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    problem = models.ForeignKey('Problem', on_delete=models.CASCADE)
    selected_option = models.CharField(max_length=1)
    solution_image_url = models.URLField(null=True, blank=True)
    is_correct = models.BooleanField(default=False)
    time_solved = models.DateTimeField(auto_now_add=True)
    test_id = models.IntegerField()

    def __str__(self):
        return f"TestAnswer by {self.user.username} for Problem {self.problem.id} (Test ID: {self.test_id})"


class Test(models.Model):
    test_id = models.IntegerField(primary_key=True)
    test_name = models.CharField(max_length=255)
    duration_in_hours = models.FloatField(null=True, blank=True)
    start_time = models.DateTimeField(null=True, blank=True)

    def is_start_time_reached(self):
        return timezone.now() >= self.start_time

    def __str__(self):
        return self.test_name


class CancelledTest(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    test_id = models.IntegerField()
    cancelled_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - Test ID: {self.test_id}"


class PlacementCompany(models.Model):
    for_batch = models.IntegerField()
    company_name = models.CharField(max_length=255)
    role_offered = models.CharField(max_length=255)
    ctc = models.CharField(max_length=100)
    min_percent = models.FloatField()
    min_cgpa = models.FloatField()
    total_backlog = models.CharField(max_length=30, blank=True)
    active_backlog = models.CharField(max_length=30, blank=True)
    description = models.CharField(max_length=2000)
    apply_link = models.URLField()
    deadline = models.DateTimeField()
    logo_url = models.URLField()
    class12_10_percent = models.FloatField(null=True, blank=True)
    generate_form = models.BooleanField(default=False, help_text='Generate application form for this company')

    if MULTISELECT_AVAILABLE:
        branches = MultiSelectField(choices=BRANCH_CHOICES, blank=True)
    else:
        branches = models.CharField(max_length=100, blank=True, help_text='Comma-separated branches (e.g. IT,CSE)')

    def __str__(self):
        return f"{self.company_name} - {self.role_offered} ({self.for_batch})"


@receiver(post_save, sender=PlacementCompany)
def notify_users_on_new_placement(sender, instance, created, **kwargs):
    if not created:
        return
    # Get eligible users
    from .models import CustomUser
    batch = instance.for_batch
    # Determine allowed branches
    if hasattr(instance, 'branches') and instance.branches:
        if isinstance(instance.branches, (list, tuple)):
            allowed_branches = set(instance.branches)
        else:
            allowed_branches = set([b.strip() for b in instance.branches.split(',') if b.strip()])
    else:
        allowed_branches = set()
    users = CustomUser.objects.filter(end_year=batch)
    if allowed_branches:
        users = users.filter(branch__in=allowed_branches)
    # Compose email
    for user in users:
        subject = f"New Placement Opportunity: {instance.company_name} ({instance.role_offered})"
        placement_url = settings.SITE_URL + reverse('placement_drive')
        details = f"""
Hello {user.username},

The placement cell is announcing a new placement opportunity!

Company: {instance.company_name}
Role: {instance.role_offered}
Batch: {instance.for_batch}
Branches: {', '.join(allowed_branches) if allowed_branches else 'All'}
CTC: {instance.ctc}
Min %: {instance.min_percent}
Min CGPA: {instance.min_cgpa}
Deadline: {instance.deadline.strftime('%Y-%m-%d %H:%M')}

Apply fast using the link below:
{placement_url}

T&P Cell
"""
        send_mail(subject, details, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)


class PlacementApplication(models.Model):
    company = models.ForeignKey(PlacementCompany, on_delete=models.CASCADE)
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    branch = models.CharField(max_length=100)
    enrollment_number = models.CharField(max_length=100)
    student_class = models.IntegerField(null=True, blank=True)
    cgpa = models.FloatField(null=True, blank=True)
    total_percentage = models.FloatField(null=True, blank=True)
    resume_link = models.URLField()
    github_link = models.URLField(blank=True)
    linkedin_link = models.URLField(blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('company', 'user')

    def __str__(self):
        return f"{self.user.username} - {self.company.company_name}"
