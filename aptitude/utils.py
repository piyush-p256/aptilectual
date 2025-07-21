from django.core.mail import send_mail
import random

def update_rating(user, is_correct, context='daily'):
    """
    A simple rating update helper function.
    - For daily problems: add 10 points for a correct answer plus a bonus based on the current streak.
    - For tests: a fixed bonus (this can be expanded based on test-specific logic).
    """
    base_rating = user.rating
    bonus = 0
    if context == 'daily':
        bonus += 2 if is_correct else 0
        bonus += 5 * user.current_streak  # Streak bonus
    elif context == 'test':
        bonus += 20  # Example bonus for tests
    return base_rating + bonus

def send_otp_email(email, otp):
    subject = 'Your OTP for Signup Verification'
    message = f'Your OTP for signup is: {otp}\nThis OTP is valid for 10 minutes.'
    from_email = None  # Uses DEFAULT_FROM_EMAIL from settings
    recipient_list = [email]
    send_mail(subject, message, from_email, recipient_list)
