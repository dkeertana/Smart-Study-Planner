from datetime import date, timedelta
import streamlit as st
from models import Subject
from scheduler import generate_schedule
from utils import (
    validate_subjects,
    calculate_progress,
    reschedule_missed_tasks,
)


def main():
    st.set_page_config(page_title="Smart Study Planner", page_icon="📚", layout="wide")
    st.title("📚 Smart Study Planner")
    st.write("Generate a personalized, rule-based study timetable and adaptively reschedule missed tasks.")

    st.sidebar.header("Configuration")
    available_hours = st.sidebar.number_input(
        "Daily Available Study Hours", min_value=0.5, max_value=24.0, value=4.0, step=0.5
    )

    st.header("Subject List")
    sample_subjects = [
        Subject(name="Mathematics", exam_date=date.today() + timedelta(days=5), difficulty=5),
        Subject(name="Physics", exam_date=date.today() + timedelta(days=8), difficulty=4),
        Subject(name="Python", exam_date=date.today() + timedelta(days=12), difficulty=3),
    ]

    for subj in sample_subjects:
        st.write(f"• **{subj.name}** | Exam Date: `{subj.exam_date}` | Difficulty: `{subj.difficulty}/5`")

    if st.button("Generate Timetable", type="primary"):
        try:
            # 1. Validate inputs
            validated = validate_subjects(sample_subjects)

            # 2. Call Member A's generate_schedule()
            schedule = generate_schedule(validated, available_hours)

            if not schedule:
                st.info("No study blocks generated.")
            else:
                st.session_state["schedule"] = schedule
                st.success(f"Generated {len(schedule)} study blocks!")

        except ValueError as e:
            st.error(f"Validation Error: {e}")

    # Display schedule & progress if present in session_state
    if "schedule" in st.session_state:
        schedule = st.session_state["schedule"]
        
        # Calculate progress
        prog = calculate_progress(schedule)
        st.subheader("Progress Metrics")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Hours", f"{prog['total_hours']}h")
        col2.metric("Completed", f"{prog['completed_hours']}h")
        col3.metric("Remaining", f"{prog['remaining_hours']}h")
        col4.metric("Progress", f"{prog['progress_percentage']}%")

        st.subheader("Daily Timetable")
        by_date = {}
        for block in schedule:
            by_date.setdefault(block.date, []).append(block)

        for study_date in sorted(by_date.keys()):
            blocks = by_date[study_date]
            day_total = sum(b.hours for b in blocks)
            with st.expander(f"📅 {study_date} — Total: {day_total}h", expanded=True):
                for b in blocks:
                    st.write(f"- **{b.subject}**: `{b.hours} hours` (Completed: `{b.completed}`)")

        if st.button("Reschedule Missed Tasks"):
            res = reschedule_missed_tasks(schedule, available_hours, subjects=sample_subjects)
            st.session_state["schedule"] = res["schedule"]
            st.success(f"Rescheduled {res['rescheduled_hours']}h! Unallocated: {res['unallocated_hours']}h.")
            st.rerun()


if __name__ == "__main__":
    main()
