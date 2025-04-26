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
