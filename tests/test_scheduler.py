from datetime import date, timedelta
import pytest

from models import Subject, StudyBlock
from scheduler import generate_schedule


def test_one_subject():
    """Test 1: Single subject generates a valid schedule."""
    today = date(2026, 10, 8)
    math = Subject(name="Mathematics", exam_date=today + timedelta(days=3), difficulty=4)

    schedule = generate_schedule([math], available_hours_per_day=4.0, start_date=today)

    assert len(schedule) > 0
    for block in schedule:
        assert isinstance(block, StudyBlock)
        assert block.subject == "Mathematics"
        assert block.hours <= 4.0
        assert block.completed is False


def test_multiple_subjects():
    """Test 2: Multiple subjects appear in the schedule."""
    today = date(2026, 10, 8)
    subjects = [
        Subject(name="Mathematics", exam_date=today + timedelta(days=5), difficulty=5),
        Subject(name="Physics", exam_date=today + timedelta(days=8), difficulty=4),
        Subject(name="Python", exam_date=today + timedelta(days=12), difficulty=3),
    ]

    schedule = generate_schedule(subjects, available_hours_per_day=4.0, start_date=today)

    scheduled_subjects = set(block.subject for block in schedule)
    assert "Mathematics" in scheduled_subjects
    assert "Physics" in scheduled_subjects
    assert "Python" in scheduled_subjects


def test_daily_capacity():
    """Test 3: Daily study hours never exceed available hours per day."""
    today = date(2026, 10, 8)
    subjects = [
        Subject(name="Mathematics", exam_date=today + timedelta(days=5), difficulty=5),
        Subject(name="Physics", exam_date=today + timedelta(days=8), difficulty=4),
        Subject(name="Python", exam_date=today + timedelta(days=12), difficulty=3),
    ]
    available_hours = 4.0

    schedule = generate_schedule(subjects, available_hours_per_day=available_hours, start_date=today)

    # Group blocks by date
    daily_totals = {}
    for block in schedule:
        daily_totals[block.date] = daily_totals.get(block.date, 0.0) + block.hours

    for block_date, total_hours in daily_totals.items():
        assert total_hours <= available_hours + 1e-6, f"Day {block_date} exceeded daily capacity: {total_hours} > {available_hours}"


def test_priority_allocation():
    """Test 4: Higher-priority subject receives greater attention than lower-priority subject on active days."""
    today = date(2026, 10, 8)
    high_priority = Subject(name="Mathematics", exam_date=today + timedelta(days=3), difficulty=5)
    low_priority = Subject(name="Python", exam_date=today + timedelta(days=10), difficulty=2)

    schedule = generate_schedule([high_priority, low_priority], available_hours_per_day=4.0, start_date=today)

    # On the first day when both are active, high-priority subject should receive more hours
    today_blocks = {b.subject: b.hours for b in schedule if b.date == today}
    assert today_blocks["Mathematics"] > today_blocks["Python"], (
        f"Expected Math daily hours ({today_blocks.get('Mathematics')}) > "
        f"Python daily hours ({today_blocks.get('Python')})"
    )


def test_empty_subjects():
    """Test 5: Empty subject list returns empty schedule safely."""
    schedule = generate_schedule([], available_hours_per_day=4.0)
    assert schedule == []


def test_invalid_study_hours():
    """Test 6: Invalid/zero/negative available hours raise ValueError."""
    today = date(2026, 10, 8)
    math = Subject(name="Mathematics", exam_date=today + timedelta(days=3), difficulty=4)

    with pytest.raises(ValueError):
        generate_schedule([math], available_hours_per_day=0)

    with pytest.raises(ValueError):
        generate_schedule([math], available_hours_per_day=-2.0)

    with pytest.raises(ValueError):
        generate_schedule([math], available_hours_per_day="invalid")  # type: ignore


def test_difficulty_validation():
    """Test 7: Difficulty values outside 1-5 raise ValueError."""
    today = date(2026, 10, 8)

    with pytest.raises(ValueError):
        invalid_sub_low = Subject(name="Math", exam_date=today + timedelta(days=3), difficulty=0)
        generate_schedule([invalid_sub_low], available_hours_per_day=4.0)

    with pytest.raises(ValueError):
        invalid_sub_high = Subject(name="Math", exam_date=today + timedelta(days=3), difficulty=6)
        generate_schedule([invalid_sub_high], available_hours_per_day=4.0)


def test_exam_date_edge_cases():
    """Test 8: Exam-date edge cases (today, tomorrow, past date, same exam date)."""
    today = date(2026, 10, 8)

    # Exam today
    sub_today = Subject(name="ExamToday", exam_date=today, difficulty=4)
    sch_today = generate_schedule([sub_today], available_hours_per_day=4.0, start_date=today)
    assert len(sch_today) == 1
    assert sch_today[0].date == today

    # Exam tomorrow
    sub_tomorrow = Subject(name="ExamTomorrow", exam_date=today + timedelta(days=1), difficulty=4)
    sch_tomorrow = generate_schedule([sub_tomorrow], available_hours_per_day=4.0, start_date=today)
    assert len(sch_tomorrow) >= 1

    # Past exam date relative to start_date
    sub_past = Subject(name="ExamPast", exam_date=today - timedelta(days=2), difficulty=4)
    sch_past = generate_schedule([sub_past], available_hours_per_day=4.0, start_date=today)
    assert sch_past == []

    # Same exam date for multiple subjects
    sub1 = Subject(name="SubA", exam_date=today + timedelta(days=2), difficulty=5)
    sub2 = Subject(name="SubB", exam_date=today + timedelta(days=2), difficulty=3)
    sch_same_date = generate_schedule([sub1, sub2], available_hours_per_day=4.0, start_date=today)
    
    assert len(sch_same_date) > 0
    for d in set(b.date for b in sch_same_date):
        day_sum = sum(b.hours for b in sch_same_date if b.date == d)
        assert day_sum <= 4.0


def test_determinism():
    """Test 9: Running the scheduler twice with the same input produces the exact same schedule."""
    today = date(2026, 10, 8)
    subjects = [
        Subject(name="Mathematics", exam_date=today + timedelta(days=5), difficulty=5),
        Subject(name="Physics", exam_date=today + timedelta(days=8), difficulty=4),
        Subject(name="Python", exam_date=today + timedelta(days=12), difficulty=3),
    ]

    schedule1 = generate_schedule(subjects, available_hours_per_day=4.0, start_date=today)
    schedule2 = generate_schedule(subjects, available_hours_per_day=4.0, start_date=today)

    assert schedule1 == schedule2
