from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Min, Q, F
from django.http import JsonResponse
from django.db.utils import IntegrityError
from datetime import timedelta
from .models import (
    CancelledTest, Problem, Test, UserAnswer, CustomUser,
    LeaderDaily, Company, TestAnswer, Achievement
)
from .forms import SignUpForm, LoginForm, SubmissionForm
from .utils import update_rating


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})


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
    now = timezone.localtime()
    today = now.date()
    start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_time = now.replace(hour=23, minute=59, second=0, microsecond=0)

    if start_time <= now <= end_time:
        problems = Problem.objects.filter(is_active=True, done=False)
        attempted_problems = set(UserAnswer.objects.filter(user=request.user).values_list('problem', flat=True))

        if problems.exists():
            if request.method == 'POST':
                problem_id = request.POST.get('problem_id')
                problem = get_object_or_404(Problem, id=problem_id, is_active=True, done=False)
                selected_option = request.POST.get('selected_option')
                solution_image_url = request.POST.get('solution_image_url', '')

                if problem.id in attempted_problems:
                    return JsonResponse({'status': 'error', 'message': 'You have already attempted this question.'})

                try:
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
                        return JsonResponse({'status': 'error', 'message': 'Duplicate submission detected.'})

                    user = request.user
                    user.total_attempted = F('total_attempted') + 1
                    if submission.is_correct:
                        user.total_correct = F('total_correct') + 1

                    # Update streak logic based on any attempt (correct or not)
                    yesterday = today - timedelta(days=1)
                    if user.last_active_date == yesterday:
                        user.current_streak = F('current_streak') + 1
                    else:
                        user.current_streak = 1

                    if user.current_streak > user.highest_streak:
                        user.highest_streak = F('current_streak')

                    user.last_active_date = today

                    # Update user rating based on the daily problem attempt
                    user.rating = update_rating(user, is_correct=submission.is_correct, context='daily')

                    user.save()

                    # Example: Award achievement for a 10-day streak
                    if user.current_streak == 10:
                        achievement, created = Achievement.objects.get_or_create(
                            name='10 Day Streak',
                            defaults={'description': 'Solved problems for 10 consecutive days.'}
                        )
                        user.achievements.add(achievement)
                        user.save()

                    return JsonResponse({'status': 'success', 'message': 'Submission successful.'})
                except IntegrityError:
                    return JsonResponse({'status': 'error', 'message': 'An unexpected error occurred.'})
            else:
                return render(request, 'dailyprobblems.html', {
                    'problems': problems,
                    'attempted_problems': attempted_problems
                })
        else:
            return render(request, 'dailyprobblems.html', {'message': 'No problems available today.'})
    else:
        return render(request, 'dailyprobblems.html', {'message': 'Problems will be available from 1:00 to 6:00.'})


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
