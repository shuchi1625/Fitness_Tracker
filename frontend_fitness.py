# frontend_fitness.py
import streamlit as st
import pandas as pd
from datetime import date, timedelta
import backend_fitness as db

st.set_page_config(page_title="Personal Fitness Tracker", layout="wide")

# ---------- PROJECT SIGNATURE ----------
PROJECT_SIGNATURE = "Shuchi Iyer_30189"

# ---------- SESSION STATE ----------
if "current_user_id" not in st.session_state:
    st.session_state.current_user_id = None

# ---------- SIDEBAR NAV ----------
st.sidebar.title("Navigation")
menu = [
    "User Profile",
    "Friends",
    "Log Workout",
    "Workout History",
    "Goals",
    "Leaderboard",
    "Insights",
]
choice = st.sidebar.radio("Go to", menu, index=0)

# ---------- HELPERS ----------
def ensure_user_selected():
    if st.session_state.current_user_id is None:
        st.warning("Select or create your user profile first.")
        st.stop()

def user_picker():
    users = db.list_users()
    if not users:
        return None, {}
    options = [f"{u[1]} ({u[2]})" for u in users]
    mapping = {f"{u[1]} ({u[2]})": u[0] for u in users}
    selection = st.selectbox("Select your profile", options)
    return mapping[selection], {u[0]: u for u in users}

# ---------- USER PROFILE ----------
if choice == "User Profile":
    st.header("Manage User Profile")
    st.markdown(f"**{PROJECT_SIGNATURE}**")

    tab1, tab2 = st.tabs(["Create / Update", "Select Active User"])

    with tab1:
        with st.form("user_form", clear_on_submit=False):
            name = st.text_input("Name")
            email = st.text_input("Email")
            weight = st.number_input("Weight (kg)", min_value=0.0, step=0.1, format="%.1f")
            submitted = st.form_submit_button("Save")
            if submitted:
                existing = db.get_user_by_email(email)
                try:
                    if existing:
                        db.update_user(existing[0], name or existing[1], email, weight or existing[3])
                        st.success(f"Updated user: {email}")
                    else:
                        uid = db.create_user(name, email, weight if weight > 0 else None)
                        st.success(f"Created user with ID {uid}")
                except Exception as e:
                    st.error(f"Error saving user: {e}")

    with tab2:
        uid, _ = user_picker()
        if uid:
            if st.button("Set as Active User"):
                st.session_state.current_user_id = uid
                user = db.get_user_by_id(uid)
                st.success(f"Active user: {user[1]} ({user[2]})")

# ---------- FRIENDS ----------
elif choice == "Friends":
    st.header("Manage Friends")
    st.markdown(f"**{PROJECT_SIGNATURE}**")
    ensure_user_selected()

    current_user = db.get_user_by_id(st.session_state.current_user_id)
    st.info(f"Active user: {current_user[1]} ({current_user[2]})")

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Add Friend")
        # list all users except self
        users = [u for u in db.list_users() if u[0] != st.session_state.current_user_id]
        if users:
            friend_map = {f"{u[1]} ({u[2]})": u[0] for u in users}
            friend_label = st.selectbox("Choose a user to add", list(friend_map.keys()))
            if st.button("Add Friend"):
                try:
                    db.add_friendship(st.session_state.current_user_id, friend_map[friend_label])
                    st.success("Friend added.")
                except Exception as e:
                    st.error(f"Could not add friend: {e}")
        else:
            st.caption("No other users found. Create another user in 'User Profile' to test friendships.")

    with col_b:
        st.subheader("Your Friends")
        friends = db.list_friends(st.session_state.current_user_id)
        if friends:
            df = pd.DataFrame(friends, columns=["user_id", "name", "email", "weight"])
            st.dataframe(df, use_container_width=True)
            remove_id = st.selectbox("Remove friend", [f"{r[1]} ({r[2]})" for r in friends])
            mapping = {f"{r[1]} ({r[2]})": r[0] for r in friends}
            if st.button("Remove"):
                try:
                    db.remove_friendship(st.session_state.current_user_id, mapping[remove_id])
                    st.success("Friend removed.")
                except Exception as e:
                    st.error(f"Could not remove friend: {e}")
        else:
            st.caption("No friends yet.")

# ---------- LOG WORKOUT ----------
elif choice == "Log Workout":
    st.header("Log a Workout")
    st.markdown(f"**{PROJECT_SIGNATURE}**")
    ensure_user_selected()

    with st.form("workout_form"):
        w_date = st.date_input("Workout date", value=date.today())
        duration = st.number_input("Duration (minutes)", min_value=1, step=1)
        submitted = st.form_submit_button("Create Workout")
        if submitted:
            try:
                wid = db.log_workout(st.session_state.current_user_id, w_date, int(duration))
                st.success(f"Workout created (ID {wid}). Now add exercises below.")
                st.session_state["last_workout_id"] = wid
            except Exception as e:
                st.error(f"Error creating workout: {e}")

    # Add exercises to the most recent or selected workout
    st.subheader("Add Exercises")
    # Allow selecting a workout
    workouts = db.list_workouts(st.session_state.current_user_id)
    if workouts:
        wmap = {f"{w[1]} (ID {w[0]}) — {w[2]} min": w[0] for w in workouts}
        default_index = 0
        if "last_workout_id" in st.session_state:
            # try to set default to last created
            try:
                default_index = list(wmap.values()).index(st.session_state["last_workout_id"])
            except ValueError:
                default_index = 0
        selected_label = st.selectbox("Select workout", list(wmap.keys()), index=default_index)
        selected_workout_id = wmap[selected_label]

        with st.form("exercise_form"):
            ex_name = st.text_input("Exercise name (e.g., Bench Press)")
            ex_sets = st.number_input("Sets", min_value=0, step=1)
            ex_reps = st.number_input("Reps per set", min_value=0, step=1)
            ex_weight = st.number_input("Weight lifted (kg)", min_value=0.0, step=0.5, format="%.1f")
            add_ex = st.form_submit_button("Add Exercise")
            if add_ex:
                try:
                    ex_id = db.add_exercise(
                        selected_workout_id,
                        ex_name,
                        int(ex_reps) if ex_reps > 0 else None,
                        int(ex_sets) if ex_sets > 0 else None,
                        float(ex_weight) if ex_weight > 0 else None,
                    )
                    st.success(f"Exercise added (ID {ex_id}).")
                except Exception as e:
                    st.error(f"Error adding exercise: {e}")

        st.subheader("Exercises in Selected Workout")
        ex = db.list_exercises(selected_workout_id)
        if ex:
            ex_df = pd.DataFrame(ex, columns=["exercise_id", "name", "reps", "sets", "weight_kg"])
            st.dataframe(ex_df, use_container_width=True)
        else:
            st.caption("No exercises yet.")
    else:
        st.caption("No workouts yet. Create one above.")

# ---------- WORKOUT HISTORY ----------
elif choice == "Workout History":
    st.header("Workout History")
    st.markdown(f"**{PROJECT_SIGNATURE}**")
    ensure_user_selected()

    col1, col2 = st.columns(2)
    with col1:
        start = st.date_input("Start date", value=date.today() - timedelta(days=30))
    with col2:
        end = st.date_input("End date", value=date.today())

    data = db.list_workouts(st.session_state.current_user_id, start, end)
    if data:
        df = pd.DataFrame(data, columns=["workout_id", "date", "duration_min"])
        st.dataframe(df, use_container_width=True)
        st.bar_chart(df.set_index("date")["duration_min"])
        # Delete option
        to_del = st.selectbox("Delete workout (optional)", [f"ID {r[0]} — {r[1]} ({r[2]} min)" for r in data])
        if st.button("Delete selected workout"):
            wid = int(to_del.split()[1])
            try:
                db.delete_workout(wid, st.session_state.current_user_id)
                st.success("Workout deleted.")
            except Exception as e:
                st.error(f"Could not delete workout: {e}")
    else:
        st.caption("No workouts found in this period.")

# ---------- GOALS ----------
elif choice == "Goals":
    st.header("Goals")
    st.markdown(f"**{PROJECT_SIGNATURE}**")
    ensure_user_selected()

    with st.form("goal_form"):
        desc = st.text_area("Goal description (e.g., 'Workout 5 times a week')")
        start_d = st.date_input("Start date", value=date.today())
        end_d = st.date_input("End date", value=date.today() + timedelta(days=7))
        submitted = st.form_submit_button("Create Goal")
        if submitted:
            if end_d < start_d:
                st.error("End date must be after start date.")
            else:
                try:
                    gid = db.create_goal(st.session_state.current_user_id, desc, start_d, end_d)
                    st.success(f"Goal created (ID {gid}).")
                except Exception as e:
                    st.error(f"Error creating goal: {e}")

    st.subheader("Your Goals")
    goals = db.list_goals(st.session_state.current_user_id)
    if goals:
        gdf = pd.DataFrame(
            goals, columns=["goal_id", "description", "start", "end", "completed"]
        )
        st.dataframe(gdf, use_container_width=True)
        # Toggle completion
        target = st.selectbox("Select goal", [f"ID {g[0]} — {g[1][:40]}" for g in goals])
        gid = int(target.split()[1])
        mark_done = st.checkbox("Mark as completed")
        if st.button("Update status"):
            try:
                db.set_goal_completed(gid, st.session_state.current_user_id, mark_done)
                st.success("Goal status updated.")
            except Exception as e:
                st.error(f"Could not update goal: {e}")

        # Delete goal
        if st.button("Delete selected goal"):
            try:
                db.delete_goal(gid, st.session_state.current_user_id)
                st.success("Goal deleted.")
            except Exception as e:
                st.error(f"Could not delete goal: {e}")
    else:
        st.caption("No goals yet.")

# ---------- LEADERBOARD ----------
elif choice == "Leaderboard":
    st.header("Weekly Leaderboard")
    st.markdown(f"**{PROJECT_SIGNATURE}**")
    ensure_user_selected()

    today = date.today()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)

    st.caption(f"Current week: {monday} to {sunday}")
    metric = st.selectbox("Rank by", ["Total workouts", "Total minutes"])
    key = "workouts" if metric == "Total workouts" else "minutes"

    data = db.leaderboard_for_week(
        st.session_state.current_user_id, key, monday, sunday
    )
    if data:
        df = pd.DataFrame(data, columns=["user_id", "name", "value"]).reset_index(drop=True)
        df.index = df.index + 1
        df.rename(columns={"value": metric}, inplace=True)
        st.dataframe(df[["name", metric]], use_container_width=True)
    else:
        st.caption("No activity yet this week for you or your friends.")

# ---------- INSIGHTS ----------
elif choice == "Insights":
    st.header("Your Insights")
    st.markdown(f"**{PROJECT_SIGNATURE}**")
    ensure_user_selected()

    stats = db.overall_insights(st.session_state.current_user_id)
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total workouts", stats["total_workouts"])
    c2.metric("Total minutes", stats["total_minutes"])
    c3.metric("Avg duration", f"{stats['avg_duration']} min")
    c4.metric("Min duration", f"{stats['min_duration']} min")
    c5.metric("Max duration", f"{stats['max_duration']} min")
    c6.metric("Total exercises", stats["total_exercises"])

    # Trend: minutes per day (last 30 days)
    st.subheader("Last 30 days — Minutes per day")
    from datetime import timedelta
    last30_start = date.today() - timedelta(days=30)
    workouts = db.list_workouts(st.session_state.current_user_id, last30_start, date.today())
    if workouts:
        df = pd.DataFrame(workouts, columns=["workout_id", "date", "minutes"])
        agg = df.groupby("date", as_index=True)["minutes"].sum()
        st.line_chart(agg)
    else:
        st.caption("No workouts in the last 30 days.")
