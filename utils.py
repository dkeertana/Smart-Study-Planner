from datetime import date, timedelta
from models import Subject, StudyBlock


def validate_subject_name(name: str) -> str:
    """Validate that subject name is a non-empty string."""
    if name is None or not isinstance(name, str) or not name.strip():
        raise ValueError("Subject name cannot be empty.")
    return name.strip()


def validate_difficulty(difficulty: int) -> int:
    """Validate that difficulty is an integer between 1 and 5 inclusive."""
    if isinstance(difficulty, bool) or not isinstance(difficulty, (int, float)):
        raise ValueError("Difficulty must be an integer between 1 and 5.")
    if difficulty != int(difficulty) or difficulty < 1 or difficulty > 5:
        raise ValueError("Difficulty must be an integer between 1 and 5.")
    return int(difficulty)


def validate_available_hours(hours: float) -> float:
    """Validate that available hours per day is a positive number."""
    if isinstance(hours, bool) or not isinstance(hours, (int, float)):
        raise ValueError("Available study hours must be a positive number.")
    if hours <= 0:
        raise ValueError("Available study hours must be a positive number.")
    return float(hours)


def validate_exam_date(
    exam_date: date | str, today: date | None = None, check_past: bool = True
) -> date:
    """Validate exam date and optionally ensure it is not in the past."""
    if exam_date is None:
        raise ValueError("Exam date cannot be None.")

    if isinstance(exam_date, str):
        try:
            parsed_date = date.fromisoformat(exam_date.strip())
        except Exception:
            raise ValueError("Invalid exam date format. Expected YYYY-MM-DD or date object.")
    elif isinstance(exam_date, date):
        parsed_date = exam_date
    else:
        raise ValueError("Exam date must be a valid date object or YYYY-MM-DD string.")

    if check_past:
        ref_today = today if today is not None else date.today()
        if parsed_date < ref_today:
            raise ValueError("Exam date cannot be in the past.")

    return parsed_date


def validate_subject(
    subject: Subject, today: date | None = None, check_past_date: bool = False
) -> Subject:
    """Validate all fields of a Subject instance."""
    if not isinstance(subject, Subject):
        raise ValueError("Expected a Subject instance.")
    validate_subject_name(subject.name)
    validate_difficulty(subject.difficulty)
    validate_exam_date(subject.exam_date, today=today, check_past=check_past_date)
    return subject


def validate_subjects(
    subjects: list[Subject], today: date | None = None, check_past_date: bool = False
) -> list[Subject]:
    """
    Validate a list of subjects, checking for invalid attributes and duplicate names.
    Comparison for duplicate names is case-insensitive and whitespace-aware.
    """
    if subjects is None:
        raise ValueError("Subjects list cannot be None.")

    seen_names = set()
    for subj in subjects:
        validate_subject(subj, today=today, check_past_date=check_past_date)
        normalized_name = subj.name.strip().lower()
        if normalized_name in seen_names:
            raise ValueError(f"Duplicate subject name found: '{subj.name.strip()}'.")
        seen_names.add(normalized_name)

    return subjects


def days_until_exam(exam_date: date, today: date | None = None) -> int:
    """
    Calculate the number of days from today until exam_date.
    If today is not specified, date.today() is used.
    """
    if today is None:
        today = date.today()
    return (exam_date - today).days


def calculate_progress(study_blocks: list[StudyBlock]) -> dict:
    """
    Calculate overall study progress metrics from a list of StudyBlock objects.

    Returns:
        dict: {
            "total_hours": float,
            "completed_hours": float,
            "remaining_hours": float,
            "progress_percentage": float
        }
    """
    if not study_blocks:
        return {
            "total_hours": 0.0,
            "completed_hours": 0.0,
            "remaining_hours": 0.0,
            "progress_percentage": 0.0,
        }

    total_hours = round(sum(block.hours for block in study_blocks), 2)
    completed_hours = round(
        sum(block.hours for block in study_blocks if block.completed), 2
    )
    remaining_hours = round(max(0.0, total_hours - completed_hours), 2)

    progress_percentage = (
        round((completed_hours / total_hours) * 100, 2) if total_hours > 0 else 0.0
    )

    return {
        "total_hours": total_hours,
        "completed_hours": completed_hours,
        "remaining_hours": remaining_hours,
        "progress_percentage": progress_percentage,
    }


def reschedule_missed_tasks(
    study_blocks: list[StudyBlock],
    available_hours_per_day: float,
    subjects: list[Subject] | None = None,
    today: date | None = None,
) -> dict:
    """
    Adaptively reschedule missed study tasks into future available daily capacity.

    Rules:
    - Missed task: completed == False and block.date < today.
    - Completed tasks: preserved unchanged on their original dates.
    - Daily capacity: total hours on any date never exceed available_hours_per_day.
    - Exam boundary: no task is rescheduled after the subject's exam date.
    - Priority: urgent subjects (closer exam + higher difficulty) rescheduled first.

    Returns:
        dict: {
            "schedule": list[StudyBlock],
            "unallocated_hours": float,
            "rescheduled_hours": float
        }
    """
    validated_hours = validate_available_hours(available_hours_per_day)
    ref_today = today if today is not None else date.today()

    if not study_blocks:
        return {
            "schedule": [],
            "unallocated_hours": 0.0,
            "rescheduled_hours": 0.0,
        }

    # 1. Separate preserved blocks vs missed past blocks
    preserved_blocks: list[StudyBlock] = []
    missed_hours_by_subject: dict[str, float] = {}

    for b in study_blocks:
        if b.completed or b.date >= ref_today:
            preserved_blocks.append(b)
        else:
            # Missed block (uncompleted and in the past)
            missed_hours_by_subject[b.subject] = (
                missed_hours_by_subject.get(b.subject, 0.0) + b.hours
            )

    if not missed_hours_by_subject:
        # No missed work to reschedule
        return {
            "schedule": list(study_blocks),
            "unallocated_hours": 0.0,
            "rescheduled_hours": 0.0,
        }

    # 2. Build subject metadata (exam_date, difficulty) for missed subjects
    subject_map: dict[str, Subject] = {}
    if subjects:
        for s in subjects:
            subject_map[s.name.strip().lower()] = s

    missed_subject_info = []
    for subj_name, missed_h in missed_hours_by_subject.items():
        norm_name = subj_name.strip().lower()
        if norm_name in subject_map:
            s_obj = subject_map[norm_name]
            e_date = s_obj.exam_date
            diff = s_obj.difficulty
        else:
            # Derive exam_date from schedule or default to max date in schedule
            matching_dates = [
                b.date for b in study_blocks if b.subject.strip().lower() == norm_name
            ]
            e_date = max(matching_dates) if matching_dates else ref_today
            diff = 3  # Default fallback difficulty

        # Calculate priority on ref_today
        days = (e_date - ref_today).days
        urgency = 1.0 / (days + 1) if days >= 0 else 0.0
        priority = diff * urgency

        missed_subject_info.append({
            "subject_name": subj_name,
            "exam_date": e_date,
            "difficulty": diff,
            "priority": priority,
            "missed_hours": missed_h,
        })

    # Sort missed subjects by priority desc, exam_date asc, name asc
    missed_subject_info.sort(
        key=lambda x: (-x["priority"], x["exam_date"], x["subject_name"])
    )

    # 3. Track daily capacity already used by preserved blocks on or after ref_today
    daily_used_hours: dict[date, float] = {}
    for b in preserved_blocks:
        if b.date >= ref_today:
            daily_used_hours[b.date] = round(
                daily_used_hours.get(b.date, 0.0) + b.hours, 2
            )

    # 4. Redistribute missed hours into future capacity
    rescheduled_blocks: list[StudyBlock] = []
    total_rescheduled_hours = 0.0
    total_unallocated_hours = 0.0

    step_size = 0.5 if validated_hours >= 0.5 else validated_hours

    for item in missed_subject_info:
        subj_name = item["subject_name"]
        e_date = item["exam_date"]
        hours_needed = round(item["missed_hours"], 2)

        curr = ref_today
        while curr <= e_date and hours_needed > 1e-4:
            used = daily_used_hours.get(curr, 0.0)
            capacity_left = round(max(0.0, validated_hours - used), 2)

            if capacity_left >= step_size:
                # Determine how many hours we can schedule today
                alloc_h = min(hours_needed, capacity_left)
                # Round to step size increments
                alloc_chunks = int(alloc_h / step_size)
                if alloc_chunks > 0:
                    alloc_h = round(alloc_chunks * step_size, 2)
                    rescheduled_blocks.append(
                        StudyBlock(
                            date=curr,
                            subject=subj_name,
                            hours=alloc_h,
                            completed=False,
                        )
                    )
                    daily_used_hours[curr] = round(used + alloc_h, 2)
                    hours_needed = round(hours_needed - alloc_h, 2)
                    total_rescheduled_hours = round(
                        total_rescheduled_hours + alloc_h, 2
                    )

            curr += timedelta(days=1)

        if hours_needed > 1e-4:
            total_unallocated_hours = round(
                total_unallocated_hours + hours_needed, 2
            )

    # 5. Merge rescheduled blocks with preserved blocks and sort by date
    all_final_blocks = list(preserved_blocks) + rescheduled_blocks
    all_final_blocks.sort(key=lambda b: (b.date, b.subject))

    return {
        "schedule": all_final_blocks,
        "unallocated_hours": total_unallocated_hours,
        "rescheduled_hours": total_rescheduled_hours,
    }
