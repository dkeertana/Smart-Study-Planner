from datetime import date, timedelta
import streamlit as st
from models import Subject, StudyBlock
from scheduler import generate_schedule
from utils import (
    validate_available_hours,
    validate_difficulty,
    validate_exam_date,
    validate_subject_name,
    validate_subjects,
    days_until_exam,
    calculate_progress,
    reschedule_missed_tasks,
)


def init_session_state():
    """Initialize Streamlit session state variables if not present."""
    if "subjects" not in st.session_state:
        st.session_state["subjects"] = []
    if "schedule" not in st.session_state:
        st.session_state["schedule"] = []
    if "available_hours" not in st.session_state:
        st.session_state["available_hours"] = 4.0


def load_demo_data():
    """Populate sample subjects and available hours for quick demo."""
    today = date.today()
    st.session_state["subjects"] = [
        Subject(name="Mathematics", exam_date=today + timedelta(days=5), difficulty=5),
        Subject(name="Physics", exam_date=today + timedelta(days=8), difficulty=4),
        Subject(name="Python", exam_date=today + timedelta(days=12), difficulty=3),
    ]
    st.session_state["available_hours"] = 4.0
    st.session_state["schedule"] = []
    st.success("Loaded demo data! Click 'Generate Study Plan' below to start.")


def main():
    st.set_page_config(
        page_title="Smart Study Planner",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    init_session_state()

    # --- Header & Intro ---
    st.title("📚 Smart Study Planner")
    st.caption("Plan smarter. Revise better. Rule-based revision timetabling & adaptive rescheduling.")

    # Top Action Bar
    col_demo, _ = st.columns([1, 4])
    with col_demo:
        if st.button("⚡ Load Demo Data", help="Quickly populate sample subjects and settings"):
            load_demo_data()

    st.markdown("---")

    # --- Sidebar Configuration ---
    st.sidebar.header("⚙️ Configuration")
    available_hours = st.sidebar.number_input(
        "Available Study Hours / Day",
        min_value=0.5,
        max_value=24.0,
        value=float(st.session_state["available_hours"]),
        step=0.5,
        help="Maximum hours you can dedicate to studying each day.",
    )
    st.session_state["available_hours"] = available_hours

    # --- Section 1: Subject Entry ---
    st.header("1. Subjects & Exams")

    with st.expander("➕ Add New Subject", expanded=len(st.session_state["subjects"]) == 0):
        with st.form("add_subject_form", clear_on_submit=True):
            col_name, col_date, col_diff = st.columns([2, 2, 1])
            with col_name:
                sub_name = st.text_input("Subject Name", placeholder="e.g. Mathematics")
            with col_date:
                sub_date = st.date_input(
                    "Exam Date",
                    value=date.today() + timedelta(days=7),
                    min_value=date.today(),
                )
            with col_diff:
                sub_diff = st.slider("Difficulty (1-5)", min_value=1, max_value=5, value=3)

            submitted = st.form_submit_button("Add Subject", type="secondary")
            if submitted:
                try:
                    name_clean = validate_subject_name(sub_name)
                    validate_difficulty(sub_diff)
                    validate_exam_date(sub_date, check_past=True)

                    # Check duplicate in existing state
                    existing_names = [s.name.strip().lower() for s in st.session_state["subjects"]]
                    if name_clean.lower() in existing_names:
                        st.error(f"Subject '{name_clean}' already exists.")
                    else:
                        new_subj = Subject(name=name_clean, exam_date=sub_date, difficulty=sub_diff)
                        st.session_state["subjects"].append(new_subj)
                        st.success(f"Added '{name_clean}'!")
                        st.rerun()
                except ValueError as err:
                    st.error(str(err))

    # Display Current Subjects
    if st.session_state["subjects"]:
        st.subheader("Entered Subjects")
        for idx, subj in enumerate(st.session_state["subjects"]):
            days_left = days_until_exam(subj.exam_date)
            col_s1, col_s2, col_s3, col_s4 = st.columns([3, 3, 2, 1])
            with col_s1:
                st.markdown(f"**{subj.name}**")
            with col_s2:
                st.caption(f"📅 Exam: {subj.exam_date} ({days_left} days left)")
            with col_s3:
                st.caption(f"⭐ Difficulty: {subj.difficulty}/5")
            with col_s4:
                if st.button("🗑️", key=f"del_{idx}", help=f"Remove {subj.name}"):
                    st.session_state["subjects"].pop(idx)
                    st.session_state["schedule"] = []
                    st.rerun()
    else:
        st.info("No subjects added yet. Add a subject above or click '⚡ Load Demo Data'.")

    st.markdown("---")

    # --- Section 2: Timetable Generation ---
    st.header("2. Timetable Generation")

    if st.button("🚀 Generate Study Plan", type="primary"):
        try:
            if not st.session_state["subjects"]:
                st.error("Please add at least one subject before generating a study plan.")
            else:
                validated_subs = validate_subjects(st.session_state["subjects"], check_past_date=True)
                validated_h = validate_available_hours(available_hours)

                # Call Member A's generate_schedule()
                schedule = generate_schedule(validated_subs, validated_h)
                if not schedule:
                    st.warning("No future study blocks could be scheduled for the given subjects.")
                else:
                    st.session_state["schedule"] = schedule
                    st.success(f"Successfully generated timetable with {len(schedule)} study blocks!")
                    st.rerun()
        except ValueError as err:
            st.error(f"Validation Error: {err}")

    # --- Section 3: Schedule, Progress & Rescheduling ---
    schedule = st.session_state["schedule"]
    if schedule:
        st.markdown("---")
        st.header("3. Your Personal Study Plan & Dashboard")

        # Summary Metrics
        progress_info = calculate_progress(schedule)
        nearest_exam_subj = min(st.session_state["subjects"], key=lambda s: s.exam_date) if st.session_state["subjects"] else None
        nearest_days = days_until_exam(nearest_exam_subj.exam_date) if nearest_exam_subj else 0

        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Total Subjects", len(st.session_state["subjects"]))
        col_m2.metric(
            "Nearest Exam",
            f"{nearest_exam_subj.name if nearest_exam_subj else 'N/A'}",
            f"{nearest_days} days left" if nearest_exam_subj else "",
        )
        col_m3.metric("Planned Study Hours", f"{progress_info['total_hours']}h")
        col_m4.metric("Overall Progress", f"{progress_info['progress_percentage']}%")

        st.subheader("Progress Tracker")
        st.progress(min(1.0, max(0.0, progress_info["progress_percentage"] / 100.0)))
        st.caption(
            f"Completed: **{progress_info['completed_hours']}h** | "
            f"Remaining: **{progress_info['remaining_hours']}h** | "
            f"Total: **{progress_info['total_hours']}h**"
        )

        st.markdown("---")

        # Timetable Checklist View
        st.subheader("📅 Daily Study Timetable & Checklist")
        st.caption("Mark completed tasks to update your progress in real-time.")

        # Group blocks by date
        by_date = {}
        for block in schedule:
            by_date.setdefault(block.date, []).append(block)

        for study_date in sorted(by_date.keys()):
            blocks = by_date[study_date]
            day_total = round(sum(b.hours for b in blocks), 2)
            is_today = (study_date == date.today())
            date_label = f"📅 {study_date.strftime('%A, %b %d, %Y')} {'(Today)' if is_today else ''}"

            with st.expander(f"{date_label} — Scheduled: {day_total}h / {available_hours}h limit", expanded=True):
                for idx, block in enumerate(blocks):
                    cb_key = f"cb_{block.date}_{block.subject}_{idx}"
                    checked = st.checkbox(
                        f"**{block.subject}**: {block.hours} hours",
                        value=block.completed,
                        key=cb_key,
                    )
                    # Update StudyBlock completion state in session_state
                    if checked != block.completed:
                        block.completed = checked
                        st.rerun()

        st.markdown("---")

        # --- Section 4: Adaptive Rescheduling ---
        st.header("4. 🔄 Adaptive Rescheduling")
        st.write("Fell behind or missed a study block? Automatically redistribute uncompleted past tasks into remaining future study capacity.")

        if st.button("🔄 Reschedule Missed Tasks", help="Redistribute uncompleted past study blocks"):
            res = reschedule_missed_tasks(
                schedule,
                available_hours_per_day=available_hours,
                subjects=st.session_state["subjects"],
            )
            st.session_state["schedule"] = res["schedule"]
            if res["unallocated_hours"] > 0:
                st.warning(
                    f"⚠️ Rescheduled {res['rescheduled_hours']}h. Note: {res['unallocated_hours']}h could not be rescheduled before exam dates due to daily capacity limits."
                )
            elif res["rescheduled_hours"] > 0:
                st.success(f"✅ Successfully rescheduled {res['rescheduled_hours']}h of missed study tasks into future days!")
            else:
                st.info("No missed past study tasks detected to reschedule.")
            st.rerun()


if __name__ == "__main__":
    main()
