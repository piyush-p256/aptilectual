from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Min, Q, F
from django.http import JsonResponse
from django.contrib import messages
from django.db.utils import IntegrityError
from datetime import timedelta
from .models import (
    CancelledTest, Problem, Test, UserAnswer, CustomUser,
    LeaderDaily, Company, TestAnswer, Achievement, PlacementCompany, PlacementApplication
)
from .forms import SignUpForm, LoginForm, SubmissionForm, PlacementApplicationForm
from .utils import update_rating, send_otp_email
from django.db import transaction
import random
from django.urls import reverse
from django.http import HttpResponseForbidden
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.http import HttpResponse
import openpyxl
from django.core.mail import send_mail, EmailMessage
import csv
from .models import CustomUser  # Adjust if your user model is named differently
from io import TextIOWrapper

TP_PASSWORD = 'tpsecret123'  # Change this to your desired password
EMAIL_PAGE_PASSWORD = 'emailsecret123'  # Change as needed
UPLOAD_CSV_PASSWORD = 'csvsecret123'  # Change this to your desired password

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            # Store all form data in session, including password1 and password2
            form_data = form.cleaned_data.copy()
            # Instead of cleaned_data, use request.POST to preserve raw passwords
            session_data = request.POST.dict()
            otp = '{:06d}'.format(random.randint(0, 999999))
            request.session['signup_form_data'] = session_data
            request.session['signup_otp'] = otp
            request.session['signup_otp_email'] = session_data['email']
            request.session['signup_otp_verified'] = False
            send_otp_email(session_data['email'], otp)
            return redirect('verify_otp')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})


def verify_otp(request):
    if not request.session.get('signup_form_data'):
        return redirect('signup')
    error = None
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        session_otp = request.session.get('signup_otp')
        if entered_otp == session_otp:
            # OTP correct, create user
            form_data = request.session.get('signup_form_data')
            from .forms import SignUpForm
            form = SignUpForm(form_data)
            if form.is_valid():
                form.save()
                # Clear session
                for key in ['signup_form_data', 'signup_otp', 'signup_otp_email', 'signup_otp_verified']:
                    if key in request.session:
                        del request.session[key]
                return redirect('login')
            else:
                error = 'There was an error creating your account. Please try again.'
        else:
            error = 'Invalid OTP. Please try again.'
    return render(request, 'verify_otp.html', {'error': error})


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('profile')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

 

def home(request):
    return render(request, 'home.html')


@login_required
def dailyprobblems(request):
    try:
        now = timezone.localtime()
        today = now.date()
        start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time   = now.replace(hour=23, minute=59, second=0, microsecond=0)

        # Only allow between midnight and 23:59
        if not (start_time <= now <= end_time):
            return render(request, 'dailyprobblems.html', {
                'message': 'Problems will be available from 12:00 AM to 11:59 PM.'
            })

        problems = Problem.objects.filter(is_active=True, done=False)
        attempted_problems = set(
            UserAnswer.objects
                      .filter(user=request.user)
                      .values_list('problem', flat=True)
        )

        if not problems.exists():
            return render(request, 'dailyprobblems.html', {
                'message': 'No problems available today.'
            })

        if request.method == 'POST':
            problem_id = request.POST.get('problem_id')
            problem = get_object_or_404(
                Problem, id=problem_id, is_active=True, done=False
            )
            selected_option    = request.POST.get('selected_option')
            solution_image_url = request.POST.get('solution_image_url', '')

            if problem.id in attempted_problems:
                return JsonResponse({
                    'status': 'error',
                    'message': 'You have already attempted this question.'
                })

            try:
                with transaction.atomic():
                    # Create the answer record
                    submission, created = UserAnswer.objects.get_or_create(
                        user=request.user,
                        problem=problem,
                        defaults={
                            'selected_option': selected_option,
                            'solution_image_url': solution_image_url,
                            'is_correct': (selected_option == str(problem.correct_option)),
                        }
                    )
                    if not created:
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Duplicate submission detected.'
                        })

                    # Load up‐to‐date user fields
                    user = request.user
                    # increment attempt counts
                    user.total_attempted += 1
                    if submission.is_correct:
                        user.total_correct += 1

                    # streak logic
                    yesterday = today - timedelta(days=1)
                    if user.last_active_date == yesterday:
                        user.current_streak += 1
                    else:
                        user.current_streak = 1

                    # record new highest
                    if user.current_streak > user.highest_streak:
                        user.highest_streak = user.current_streak

                    # set this as last active
                    user.last_active_date = today

                    # recalc rating (your existing function)
                    user.rating = update_rating(
                        user,
                        is_correct=submission.is_correct,
                        context='daily'
                    )

                    user.save()

                    # award any achievements (outside the transaction so they see the user update)
                    if user.current_streak == 10:
                        achievement, _ = Achievement.objects.get_or_create(
                            name='10 Day Streak',
                            defaults={'description':
                                      'Solved problems for 10 consecutive days.'}
                        )
                        user.achievements.add(achievement)

                return JsonResponse({
                    'status': 'success',
                    'message': 'Submission successful.'
                })
            except IntegrityError:
                return JsonResponse({
                    'status': 'error',
                    'message': 'An unexpected error occurred.'
                })

        # GET: render the problems page
        return render(request, 'dailyprobblems.html', {
            'problems': problems,
            'attempted_problems': attempted_problems
        })

    except Exception as e:
        # log the traceback for debugging
        import traceback
        print(f"An error occurred: {e}")
        traceback.print_exc()
        return JsonResponse({
            'status': 'error',
            'message': 'An unexpected error occurred.'
        }, status=500)

@login_required
def profile(request):
    user = request.user
    if request.method == 'POST':
        # Update bio and profile picture URL from the submitted form
        bio = request.POST.get('bio')
        profile_picture = request.POST.get('profile_picture')
        user.bio = bio
        if profile_picture:
            user.profile_picture = profile_picture
        user.save()
        return redirect('profile')
    return render(request, 'profile.html', {
        'email': user.email,
        'username': user.username,
        'enrollment_number' : user.enrollment_number,
        'end_year' : user.end_year,
        'start_year' : user.start_year,
        'total_attempted': user.total_attempted,
        'total_correct': user.total_correct,
        'current_streak': user.current_streak,
        'highest_streak': user.highest_streak,
        'rating': user.rating,
        'profile_picture': user.profile_picture,
        'bio': user.bio,
        'first_position_count': user.first_position_count,
        'second_position_count': user.second_position_count,
        'third_position_count': user.third_position_count,
        'achievements': user.achievements.all(),
    })


def public_profile(request, username):
    """
    Public profile view to display a user's public information.
    """
    user = get_object_or_404(CustomUser, username=username)
    return render(request, 'public_profile.html', {
        'email': user.email,
        'enrollment_number' : user.enrollment_number,
        'end_year' : user.end_year,
        'start_year' : user.start_year,
        'username': user.username,
        'total_attempted': user.total_attempted,
        'total_correct': user.total_correct,
        'current_streak': user.current_streak,
        'highest_streak': user.highest_streak,
        'rating': user.rating,
        'profile_picture': user.profile_picture,
        'bio': user.bio,
        'first_position_count': user.first_position_count,
        'second_position_count': user.second_position_count,
        'third_position_count': user.third_position_count,
        'achievements': user.achievements.all(),
    })


@login_required
def daily_leaderboard(request):
    leader_daily = LeaderDaily.objects.first()
    if leader_daily and leader_daily.show_leaderboard:
        now = timezone.localtime()
        start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = now.replace(hour=23, minute=59, second=59, microsecond=999999)

        users_with_answers = UserAnswer.objects.filter(time_solved__range=(start_time, end_time))
        users = CustomUser.objects.filter(
            id__in=users_with_answers.values_list('user', flat=True)
        ).annotate(
            correct_answers_today=Count('useranswer', filter=Q(useranswer__is_correct=True, useranswer__time_solved__range=(start_time, end_time))),
            min_time_solved=Min('useranswer__time_solved', filter=Q(useranswer__is_correct=True, useranswer__time_solved__range=(start_time, end_time)))
        ).order_by('-correct_answers_today', 'min_time_solved')[:3]

        leaderboard_data = []
        for rank, user in enumerate(users, start=1):
            user_answers = UserAnswer.objects.filter(user=user, time_solved__range=(start_time, end_time))
            solution_image_url = user_answers.first().solution_image_url if user_answers.exists() else None
            leaderboard_data.append({
                'rank': rank,
                'username': user.username,
                'solution_image_url': solution_image_url,
            })

        return render(request, 'daily_leaderboard.html', {'leaderboard_data': leaderboard_data})
    else:
        return render(request, 'daily_leaderboard.html', {'error': "Leaderboard is not available at this time."})


@login_required
def monthly_leaderboard(request):
    now = timezone.now()
    users = CustomUser.objects.filter(
        useranswer__time_solved__month=now.month,
        useranswer__time_solved__year=now.year
    ).distinct().annotate(
        total_correct_answers=Count('useranswer', filter=Q(useranswer__is_correct=True)),
        total_answers=Count('useranswer')
    ).order_by('-total_correct_answers', '-first_position_count', '-second_position_count', '-third_position_count')

    return render(request, 'monthly_leaderboard.html', {'users': users})


@login_required
def past_problems(request):
    past_problems = Problem.objects.filter(done=True)
    return render(request, 'past_problems.html', {'past_problems': past_problems})


def logout_view(request):
    logout(request)
    return redirect('login')


def companywise(request):
    companies = Company.objects.all()
    return render(request, 'companywise.html', {'companies': companies})


def company_problems(request, company_name):
    company = get_object_or_404(Company, name=company_name)
    problems = Problem.objects.filter(companyname=company_name, done=True)
    return render(request, 'company_problems.html', {
        'company': company,
        'problems': problems
    })


@login_required
def test_leaderboard(request, test_id):
    now = timezone.now()
    start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_time = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    users_with_answers = TestAnswer.objects.filter(time_solved__range=(start_time, end_time), test_id=test_id)
    users = CustomUser.objects.filter(
        id__in=users_with_answers.values_list('user', flat=True)
    ).annotate(
        correct_answers_today=Count('testanswer', filter=Q(
            testanswer__is_correct=True,
            testanswer__time_solved__range=(start_time, end_time),
            testanswer__test_id=test_id
        )),
        total_answers_today=Count('testanswer', filter=Q(
            testanswer__time_solved__range=(start_time, end_time),
            testanswer__test_id=test_id
        )),
        min_time_solved=Min('testanswer__time_solved', filter=Q(
            testanswer__is_correct=True,
            testanswer__time_solved__range=(start_time, end_time),
            testanswer__test_id=test_id
        ))
    ).order_by('-correct_answers_today', 'min_time_solved')

    leaderboard_data = []
    for rank, user in enumerate(users, start=1):
        # Update position counts based on rank
        if rank == 1:
            user.first_position_count = F('first_position_count') + 1
        elif rank == 2:
            user.second_position_count = F('second_position_count') + 1
        elif rank == 3:
            user.third_position_count = F('third_position_count') + 1
        leaderboard_data.append({
            'rank': rank,
            'username': user.username,
            'correct_answers': user.correct_answers_today,
            'total_answers': user.total_answers_today,
            'user_id': user.id,
            'is_current_user': user.id == request.user.id
        })

    for user in users:
        user.save()

    return render(request, 'test_leaderboard.html', {'leaderboard_data': leaderboard_data, 'test_id': test_id})


@login_required
def user_attempted_questions(request, test_id, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    attempted_questions = TestAnswer.objects.filter(user=user, test_id=test_id).select_related('problem')

    attempted_data = []
    for attempt in attempted_questions:
        attempted_data.append({
            'question': attempt.problem.question,
            'selected_option': attempt.selected_option,
            'is_correct': attempt.is_correct,
            'correct_option': attempt.problem.correct_option,
            'explanation': getattr(attempt.problem, 'explanation', ''),
            'option1': attempt.problem.option1,
            'option2': attempt.problem.option2,
            'option3': attempt.problem.option3,
            'option4': attempt.problem.option4,
        })

    return render(request, 'user_attempted_questions.html', {'attempted_data': attempted_data, 'test_id': test_id})


@login_required
def instructions(request, test_id):
    test = get_object_or_404(Test, test_id=test_id)
    return render(request, 'instructions.html', {'test': test})


@login_required
def start_test(request, test_id):
    test = get_object_or_404(Test, test_id=test_id)
    if not test.is_start_time_reached():
        return redirect('instructions', test_id=test_id)
    return redirect('test_view', test_id=test_id)

@login_required
def test_view(request, test_id):
    test = get_object_or_404(Test, test_id=test_id)
    now = timezone.now()
    problems = Problem.objects.filter(test_id=test_id, is_active=True, done=False)
    attempted_problems = set(TestAnswer.objects.filter(user=request.user, test_id=test_id).values_list('problem', flat=True))

    if CancelledTest.objects.filter(user=request.user, test_id=test_id).exists():
        return render(request, 'test.html', {
            'message': 'Your test has been canceled due to suspected cheating. If you believe this was a mistake, please contact the administrator.',
            'test_id': test_id
        })

    if problems.exists():
        if request.method == 'POST':
            submissions = []
            for problem in problems:
                problem_id = request.POST.get(f'problem_id_{problem.id}')
                selected_option = request.POST.get(f'selected_option_{problem.id}')
                solution_image_url = request.POST.get('solution_image_url', '')

                if problem.id in attempted_problems:
                    return JsonResponse({'status': 'error', 'message': 'You have already attempted this question.'})

                try:
                    submission, created = TestAnswer.objects.get_or_create(
                        user=request.user,
                        problem=problem,
                        test_id=test_id,
                        defaults={
                            'selected_option': selected_option,
                            'solution_image_url': solution_image_url,
                            'is_correct': (selected_option == str(problem.correct_option)),
                        }
                    )
                    if not created:
                        return JsonResponse({'status': 'error', 'message': 'Duplicate submission detected.'})

                    submissions.append(submission)
                except IntegrityError:
                    return JsonResponse({'status': 'error', 'message': 'An unexpected error occurred.'})

            user = request.user
            user.total_attempted = F('total_attempted') + len(submissions)
            user.total_correct = F('total_correct') + sum(1 for s in submissions if s.is_correct)
            user.save()

            return JsonResponse({'status': 'success', 'message': 'Submission successful.'})
        else:
            return render(request, 'test.html', {
                'problems': problems,
                'type' : Problem.type,
                'attempted_problems': attempted_problems,
                'test_id': test_id,
                'test': test
            })
    else:
        return render(request, 'test.html', {
            'message': 'No problems available for this test.',
            'test_id': test_id
        })


@login_required
def cancel_test(request, test_id):
    test = get_object_or_404(Test, test_id=test_id)
    CancelledTest.objects.create(user=request.user, test_id=test_id)
    return redirect('test_leaderboard', test_id=test_id)


@login_required
def placement_drive(request):
    user = request.user
    companies = PlacementCompany.objects.all().order_by('deadline')
    company_list = []
    for company in companies:
        deadline_passed = company.deadline < timezone.now()
        # Backlog checks: only if the field is a digit
        total_backlog_ok = True
        active_backlog_ok = True
        if company.total_backlog and company.total_backlog.isdigit():
            total_backlog_ok = (user.total_backlogs is not None and user.total_backlogs <= int(company.total_backlog))
        if company.active_backlog and company.active_backlog.isdigit():
            active_backlog_ok = (user.active_backlogs is not None and user.active_backlogs <= int(company.active_backlog))
        # Branch eligibility
        branch_ok = True
        if hasattr(company, 'branches') and company.branches:
            if isinstance(company.branches, (list, tuple)):
                branch_ok = user.branch in company.branches
            else:
                # CharField: comma-separated
                allowed_branches = [b.strip() for b in company.branches.split(',') if b.strip()]
                branch_ok = user.branch in allowed_branches
        eligible = (
            (user.total_percentage is not None and user.total_percentage >= company.min_percent) and
            (user.cgpa is not None and user.cgpa >= company.min_cgpa) and
            total_backlog_ok and
            active_backlog_ok and
            (user.end_year is not None and company.for_batch == user.end_year) and
            branch_ok
        )
        # Add class 12/10 percent check if company has set it
        if company.class12_10_percent is not None:
            eligible = eligible and (
                (user.class12_percentage is not None and user.class12_percentage >= company.class12_10_percent) and
                (user.class10_percentage is not None and user.class10_percentage >= company.class12_10_percent)
            )
        company_list.append({
            'company': company,
            'eligible': eligible,
            'deadline_passed': deadline_passed
        })
    return render(request, 'placement-drive.html', {'company_list': company_list})


def is_user_eligible_for_company(user, company):
    # Copy the eligibility logic from placement_drive
    total_backlog_ok = True
    active_backlog_ok = True
    if company.total_backlog and company.total_backlog.isdigit():
        total_backlog_ok = (user.total_backlogs is not None and user.total_backlogs <= int(company.total_backlog))
    if company.active_backlog and company.active_backlog.isdigit():
        active_backlog_ok = (user.active_backlogs is not None and user.active_backlogs <= int(company.active_backlog))
    branch_ok = True
    if hasattr(company, 'branches') and company.branches:
        if isinstance(company.branches, (list, tuple)):
            branch_ok = user.branch in company.branches
        else:
            allowed_branches = [b.strip() for b in company.branches.split(',') if b.strip()]
            branch_ok = user.branch in allowed_branches
    eligible = (
        (user.total_percentage is not None and user.total_percentage >= company.min_percent) and
        (user.cgpa is not None and user.cgpa >= company.min_cgpa) and
        total_backlog_ok and
        active_backlog_ok and
        (user.end_year is not None and company.for_batch == user.end_year) and
        branch_ok
    )
    if company.class12_10_percent is not None:
        eligible = eligible and (
            (user.class12_percentage is not None and user.class12_percentage >= company.class12_10_percent) and
            (user.class10_percentage is not None and user.class10_percentage >= company.class12_10_percent)
        )
    return eligible


@login_required
def placement_application(request, company_id):
    company = get_object_or_404(PlacementCompany, id=company_id)
    if not is_user_eligible_for_company(request.user, company):
        return HttpResponseForbidden("You are not eligible to apply for this opportunity.")
    # Check if already applied
    if PlacementApplication.objects.filter(company=company, user=request.user).exists():
        return render(request, 'already_applied.html', {'company': company})
    if request.method == 'POST':
        form = PlacementApplicationForm(request.POST)
        if form.is_valid():
            app = form.save(commit=False)
            app.company = company
            app.user = request.user
            app.save()
            return render(request, 'application_success.html', {'company': company})
    else:
        # Prefill user data
        form = PlacementApplicationForm(initial={
            'name': request.user.name,
            'branch': request.user.branch,
            'enrollment_number': request.user.enrollment_number,
            'student_class': request.user.student_class,
            'cgpa': request.user.cgpa,
            'total_percentage': request.user.total_percentage,
        })
        for field in ['name', 'branch', 'enrollment_number', 'student_class', 'cgpa', 'total_percentage']:
           form.fields[field].widget.attrs['disabled'] = 'disabled'
    return render(request, 'placement_application_form.html', {'form': form, 'company': company})

# Hook: When PlacementCompany is created/updated with generate_form=True, set apply_link
@receiver(post_save, sender=PlacementCompany)
def set_apply_link(sender, instance, created, **kwargs):
    if instance.generate_form:
        url = reverse('placement_application', args=[instance.id])
        site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        full_url = site_url + url
        if instance.apply_link != full_url:
            instance.apply_link = full_url
            instance.save(update_fields=['apply_link'])


def tp_page(request):
    if not request.session.get('tp_authenticated'):
        if request.method == 'POST':
            password = request.POST.get('tp_password')
            if password == TP_PASSWORD:
                request.session['tp_authenticated'] = True
            else:
                return render(request, 'tp_page.html', {'auth_required': True, 'error': 'Invalid password'})
        else:
            return render(request, 'tp_page.html', {'auth_required': True})
    companies = PlacementCompany.objects.filter(generate_form=True)
    return render(request, 'tp_page.html', {'companies': companies, 'auth_required': False})

def tp_download_excel(request, company_id):
    company = get_object_or_404(PlacementCompany, id=company_id)
    applications = PlacementApplication.objects.filter(company=company)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Applications'
    ws.append([
        'Name', 'Branch', 'Enrollment Number', 'Class', 'CGPA', 'Total Percentage',
        'Resume Link', 'GitHub Link', 'LinkedIn Link', 'Applied At', 'User Email'
    ])
    for app in applications:
        ws.append([
            app.name, app.branch, app.enrollment_number, app.student_class, app.cgpa, app.total_percentage,
            app.resume_link, app.github_link, app.linkedin_link, app.applied_at.strftime('%Y-%m-%d %H:%M'), app.user.email
        ])
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = f"{company.company_name}_{company.for_batch}.xlsx".replace(' ', '_')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response

@login_required
def send_custom_email(request):
    # Password protection
    if not request.session.get('email_page_authenticated'):
        if request.method == 'POST' and 'email_page_password' in request.POST:
            if request.POST.get('email_page_password') == EMAIL_PAGE_PASSWORD:
                request.session['email_page_authenticated'] = True
            else:
                return render(request, 'send_custom_email.html', {'auth_required': True, 'error': 'Invalid password'})
        else:
            return render(request, 'send_custom_email.html', {'auth_required': True})
    # Get filter options
    batches = sorted(set(CustomUser.objects.exclude(end_year=None).values_list('end_year', flat=True)))
    branches = ['IT', 'CSE', 'ECE', 'EEE', 'ICE']
    companies = PlacementCompany.objects.all()
    users = CustomUser.objects.all()
    filtered_users = None
    message_sent = False
    error = None
    if request.method == 'POST' and 'email_page_password' not in request.POST:
        # Get filters
        selected_batches = request.POST.getlist('batch')
        selected_branches = request.POST.getlist('branch')
        company_id = request.POST.get('company')
        eligibility_type = request.POST.get('eligibility_type')  # eligible_only or all
        registration_type = request.POST.get('registration_type')  # registered or not_registered
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        users = CustomUser.objects.all()
        if selected_batches:
            users = users.filter(end_year__in=selected_batches)
        if selected_branches:
            users = users.filter(branch__in=selected_branches)
        if company_id and company_id != '':
            company = PlacementCompany.objects.get(id=company_id)
            if eligibility_type == 'eligible_only':
                users = [u for u in users if is_user_eligible_for_company(u, company)]
            if registration_type == 'registered':
                registered_ids = PlacementApplication.objects.filter(company=company).values_list('user_id', flat=True)
                users = [u for u in users if u.id in registered_ids]
            elif registration_type == 'not_registered':
                registered_ids = PlacementApplication.objects.filter(company=company).values_list('user_id', flat=True)
                users = [u for u in users if u.id not in registered_ids]
        # Remove duplicates if any
        if isinstance(users, list):
            filtered_users = users
        else:
            filtered_users = list(users.distinct())
        # Handle attachments
        attachments = request.FILES.getlist('attachments') if hasattr(request, 'FILES') else []
        # Send email (HTML)
        if filtered_users and subject and message:
            for user in filtered_users:
                email = EmailMessage(
                    subject=subject,
                    body=message,
                    from_email=None,
                    to=[user.email],
                )
                email.content_subtype = 'html'  # Send as HTML
                for f in attachments:
                    email.attach(f.name, f.read(), f.content_type)
                email.send(fail_silently=True)
            message_sent = True
        else:
            error = 'No users found or subject/message missing.'
    return render(request, 'send_custom_email.html', {
        'batches': batches,
        'branches': branches,
        'companies': companies,
        'message_sent': message_sent,
        'error': error,
        'auth_required': False
    })

@login_required
def upload_csv(request):
    # Restrict to superusers
    if not request.user.is_superuser:
        return render(request, 'upload_csv.html', {'permission_denied': True})
    # Password protection like tp_page
    if not request.session.get('upload_csv_authenticated'):
        if request.method == 'POST' and 'upload_csv_password' in request.POST:
            if request.POST.get('upload_csv_password') == UPLOAD_CSV_PASSWORD:
                request.session['upload_csv_authenticated'] = True
            else:
                return render(request, 'upload_csv.html', {'auth_required': True, 'error': 'Invalid password'})
        else:
            return render(request, 'upload_csv.html', {'auth_required': True})

    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        decoded_file = TextIOWrapper(csv_file.file, encoding='utf-8')
        reader = csv.DictReader(decoded_file)
        updated, not_found = 0, 0

        for row in reader:
            enrollment_number = row.get('enrollment_number')
            try:
                user = CustomUser.objects.get(enrollment_number=enrollment_number)
                fields = [
                    'sem1_sgpa', 'sem2_sgpa', 'sem3_sgpa', 'sem4_sgpa',
                    'sem5_sgpa', 'sem6_sgpa', 'sem7_sgpa', 'sem8_sgpa',
                    'cgpa', 'active_backlogs', 'total_backlogs',
                    'class12_percentage', 'class10_percentage', 'total_percentage'
                ]
                changed = False
                for field in fields:
                    value = row.get(field)
                    if value is not None:
                        value = value.strip()
                    if value:  # Only update if value is not empty after stripping
                        current = getattr(user, field, None)
                        if current in [None, '', 0]:
                            setattr(user, field, value)
                            changed = True
                if changed:
                    user.save()
                    updated += 1
            except CustomUser.DoesNotExist:
                not_found += 1

        messages.success(request, f"Updated {updated} users. {not_found} enrollment numbers not found.")
        return redirect('upload_csv')

    return render(request, 'upload_csv.html', {'auth_required': False})
