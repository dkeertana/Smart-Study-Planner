# Smart Study Planner — Core Engine & Supporting Logic

A deterministic, rule-based scheduling and adaptive rescheduling engine built for university students to automatically generate and adapt daily study timetables based on subject difficulty and exam dates.

---

## 🧠 Core Features & Architecture

### 1. Primary Scheduler
Ranks study priorities using a simple rule-based formula:

$$\text{Priority} = \text{Difficulty} \times \text{Urgency}$$

- **Urgency**: Calculated as $\text{Urgency} = \frac{1}{\text{Days Remaining} + 1}$.
  - Exam Today ($0$ days left) $\rightarrow$ $\text{Urgency} = 1.0$ (highest priority).
  - Exam Tomorrow ($1$ day left) $\rightarrow$ $\text{Urgency} = 0.5$.
- **Difficulty**: Rating from 1 (easiest) to 5 (hardest).
- **Daily Capacity Constraint**: Total scheduled study hours on any single day **never** exceed `available_hours_per_day`.
- **Determinism**: Identical inputs always produce the exact same schedule with zero randomness.

---

### 2. Supporting Logic & Validation (`utils.py`)
- **Input Validation**: `validate_subject_name`, `validate_difficulty` (1-5), `validate_available_hours` (>0), `validate_exam_date` (rejects past dates), and `validate_subjects` (prevents duplicate subject names).
- **Date Utilities**: `days_until_exam(exam_date, today=None)` returns days remaining.
- **Progress Tracking**: `calculate_progress(study_blocks)` returns total, completed, remaining hours, and progress percentage.

---

### 3. Adaptive Rescheduling (`reschedule_missed_tasks`)
- **Missed Work Detection**: Identifies uncompleted study blocks whose scheduled date has passed (`block.date < today` and `completed == False`).
- **Preserves Completed Work**: Completed tasks (`completed == True`) remain untouched on their original dates.
- **Capacity & Exam Boundaries**: Redistributes missed hours into future daily available capacity up to the subject's exam date. Never schedules after an exam date or exceeds daily limits.
- **Unallocated Work Reporting**: Reports any missed work that cannot fit before an exam date.

---

## 📁 Project Structure

```text
smart-study-planner/
├── app.py                  # Streamlit UI integration reference
├── scheduler.py            # Core initial scheduling engine (Member A)
├── models.py               # Data models (Subject, StudyBlock)
├── utils.py                # Input validation, date helpers, progress, rescheduling
├── requirements.txt        # Minimal dependencies
├── README.md               # Project documentation
└── tests/
    ├── test_scheduler.py   # Scheduler tests (9 tests)
    └── test_utils.py       # Supporting logic & integration tests (18 tests)
```

---

## ⚡ Quickstart & Testing

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Streamlit Application
```bash
streamlit run app.py
```

### 3. Run Test Suite
```bash
pytest
```

---

## 🔌 API Integration Contract

### Validation & Initial Schedule Generation
```python
from datetime import date, timedelta
from models import Subject
from scheduler import generate_schedule
from utils import validate_subjects, calculate_progress, reschedule_missed_tasks

subjects = [
    Subject("Mathematics", date.today() + timedelta(days=5), 5),
    Subject("Physics", date.today() + timedelta(days=8), 4),
]

# 1. Validate inputs
validated_subjects = validate_subjects(subjects)

# 2. Generate initial schedule
schedule = generate_schedule(validated_subjects, available_hours_per_day=4.0)

# 3. Calculate progress
progress = calculate_progress(schedule)
print(f"Progress: {progress['progress_percentage']}%")

# 4. Adaptively reschedule missed tasks
result = reschedule_missed_tasks(schedule, available_hours_per_day=4.0, subjects=validated_subjects)
updated_schedule = result["schedule"]
print(f"Unallocated hours: {result['unallocated_hours']}h")
```
