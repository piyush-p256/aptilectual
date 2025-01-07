from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Min, Q
from django.utils import timezone
from django.db.models import F
from datetime import timedelta
from .models import Problem, UserAnswer, CustomUser, LeaderDaily
from .forms import SignUpForm, LoginForm, SubmissionForm

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

@login_required
def home(request):
    return render(request, 'home.html')

@login_required
def dailyprobblems(request):
    now = timezone.now()
    start_time = now.replace(hour=1, minute=0, second=0, microsecond=0)
    end_time = now.replace(hour=22, minute=0, second=0, microsecond=0)

    if start_time <= now <= end_time:
        problems = Problem.objects.filter(is_active=True, done=False)
        if problems.exists():
            if request.method == 'POST':
                problem_id = request.POST.get('problem_id')
                problem = Problem.objects.get(id=problem_id)
                form = SubmissionForm(request.POST)
                if form.is_valid():
                    # Check if the user has already attempted this problem
                    if UserAnswer.objects.filter(user=request.user, problem=problem).exists():
                        return render(request, 'dailyprobblems.html', {'problems': problems, 'form': form, 'message': 'You have already attempted this question.'})

                    submission = form.save(commit=False)
                    submission.user = request.user
                    submission.problem = problem
                    submission.is_correct = (submission.selected_option == problem.correct_option)
                    submission.save()

                    # Update user stats
                    user = request.user
                    user.total_attempted = F('total_attempted') + 1
                    if submission.is_correct:
                        user.total_correct = F('total_correct') + 1

                    # Update streak logic
                    today = timezone.now().date()
                    yesterday = today - timedelta(days=1)
                    solved_yesterday = UserAnswer.objects.filter(user=user, time_solved__date=yesterday).exists()

                    if solved_yesterday:
                        user.current_streak = F('current_streak') + 1
                    else:
                        user.current_streak = 1

                    if user.current_streak > user.highest_streak:
                        user.highest_streak = F('current_streak')

                    user.save()
                    return redirect('dailyprobblems')
            else:
                form = SubmissionForm()
            return render(request, 'dailyprobblems.html', {'problems': problems, 'form': form})
        else:
            return render(request, 'dailyprobblems.html', {'message': 'No problems available today.'})
    else:
        return render(request, 'dailyprobblems.html', {'message': 'Problems will be available from 17:00 to 22:00.'})
    

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import UserAnswer, CustomUser

@login_required
def profile(request):
    user = request.user

    # Retrieve data from the CustomUser model
    total_attempted = user.total_attempted
    total_correct = user.total_correct
    current_streak = user.current_streak
    highest_streak = user.highest_streak

    return render(request, 'profile.html', {
        'email': user.email,
        'username': user.username,
        'total_attempted': total_attempted,
        'total_correct': total_correct,
        'current_streak': current_streak,
        'highest_streak': highest_streak,
    })

@login_required
def daily_leaderboard(request):
    leader_daily = LeaderDaily.objects.first()
    if leader_daily and leader_daily.show_leaderboard:
        now = timezone.now()
        start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = now.replace(hour=23, minute=59, second=59, microsecond=999999)

        users_with_answers = UserAnswer.objects.filter(time_solved__range=(start_time, end_time))
        users = CustomUser.objects.filter(id__in=users_with_answers.values_list('user', flat=True)).annotate(
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