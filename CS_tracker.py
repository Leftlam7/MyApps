import streamlit as st
import sqlite3
from datetime import date
import os
import pandas as pd
from supabase import create_client

supabase = create_client(
    st.secrets["supabase"]["url"],
    st.secrets["supabase"]["key"]
)

try:
    result = supabase.table("exercises").select("*").execute()
    st.success(f"Supabase read works! Found {len(result.data)} exercises.")

except Exception as e:
    st.error(f"Supabase read failed: {e}")
    
DB_PATH = os.path.join(
    os.path.dirname(__file__),
    "workouts.db"
) 
    
@st.cache_resource
def get_connection():
    return sqlite3.connect(
        DB_PATH,
        check_same_thread=False
    )

conn = get_connection()
cursor = conn.cursor()

cursor.execute("PRAGMA journal_mode=WAL;")

##  Configuring the page
st.set_page_config(page_title="SthenoS", page_icon="💪", layout="centered")
#accept html
st.markdown("""
<link rel="manifest" href="/app/static/manifest.json">
<meta name="theme-color" content="#000000">
""", unsafe_allow_html=True)

cursor.execute("PRAGMA journal_mode=WAL;")

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")

conn.commit()

cursor.execute("""
CREATE TABLE IF NOT EXISTS profile (
    id INTEGER PRIMARY KEY,
    name TEXT,
    age INTEGER,
    height REAL,
    weight REAL,
    goal TEXT
)
""")
conn.commit()

#create SQLite table workouts
cursor.execute("""
CREATE TABLE IF NOT EXISTS workouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    date TEXT,
    exercise TEXT,
    category TEXT,
    sets INTEGER,
    reps INTEGER,
    weight REAL,
    duration REAL,
    performance REAL,
    notes TEXT
)
""")

conn.commit() #saves changes after creating table

# temporary database fix
columns = [row[1] for row in cursor.execute("PRAGMA table_info(workouts)")]

if "user_id" not in columns:
    cursor.execute(
        "ALTER TABLE workouts ADD COLUMN user_id INTEGER"
    )
    conn.commit()
    

default_exercises = [
    ("Push-ups", "Push"),
    ("Dips", "Push"),
    ("Pike Push-ups", "Push"),
    ("Pseudo Planche Push-ups", "Push"),
    ("Handstand Push-ups", "Push"),

    ("Pull-ups", "Pull"),
    ("Chin-ups", "Pull"),
    ("Australian Rows", "Pull"),
    ("Front Lever Raises", "Pull"),

    ("Squats", "Legs"),
    ("Bulgarian Split Squats", "Legs"),
    ("Pistol Squats", "Legs"),
    ("Nordic Curls", "Legs"),
    ("Calf Raises", "Legs"),

    ("Plank", "Core"),
    ("Side Plank", "Core"),
    ("Hollow Body Hold", "Core"),
    ("Leg Raises", "Core"),
    ("Hanging Leg Raises", "Core"),
    ("L-Sit", "Core"),
    ("Dragon Flag", "Core"),
    ("Bicycle Crunches", "Core"),
]

for name, category in default_exercises:
    supabase.table("exercises").upsert(
        {
            "name": name,
            "category": category
        },
        on_conflict="name"
    ).execute()



def calculate_performance(category, sets, reps, weight, duration):

    # normalize values
    sets_score = sets / 5
    reps_score = reps / 50
    weight_score = weight / 50
    duration_score = duration / 120

    if category == "Push":
        score = (
            0.25 * sets_score +
            0.45 * reps_score +
            0.20 * weight_score +
            0.10 * duration_score
        )

    elif category == "Pull":
        score = (
            0.25 * sets_score +
            0.40 * reps_score +
            0.25 * weight_score +
            0.10 * duration_score
        )

    elif category == "Legs":
        score = (
            0.25 * sets_score +
            0.50 * reps_score +
            0.15 * weight_score +
            0.10 * duration_score
        )

    elif category == "Core":
        score = (
            0.20 * sets_score +
            0.20 * reps_score +
            0.60 * duration_score
        )

    else:
        score = 0

    return round(score * 100, 2)

if "user" not in st.session_state:
    st.session_state.user = None
    
if "current_workout" not in st.session_state:
    st.session_state.current_workout = []

if st.session_state.user is None:

    st.title("💪 Welcome to SthenoS")

    login_tab, register_tab = st.tabs(
        ["Login", "Create Account"]
    )

    with register_tab:

        username = st.text_input("Username")
        password = st.text_input(
            "Password",
            type="password"
        )

        if st.button("Create Account"):

            try:
                cursor.execute(
                    """
                    INSERT INTO users(username,password)
                    VALUES (?,?)
                    """,
                    (username,password)
                )

                conn.commit()

                st.success("Account created!")

            except sqlite3.IntegrityError:
                st.error("Username already exists")


    with login_tab:

        username = st.text_input(
            "Username",
            key="login_user"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="login_pass"
        )

        if st.button("Login"):

            user = cursor.execute(
                """
                SELECT id, username
                FROM users
                WHERE username=?
                AND password=?
                """,
                (username,password)
            ).fetchone()


            if user:
                # Make sure this user also exists in Supabase
                supabase.table("users").upsert({
                    "id": user[0],
                    "username": user[1],
                    "password": password
                }).execute()
            
                st.session_state.user = {
                    "id": user[0],
                    "username": user[1]
                }
                st.rerun()

            else:
                st.error("Wrong login")


    st.stop()


st.title("💪 Calisthenics Tracker")

st.sidebar.write(
    f"👤 {st.session_state.user['username']}"
)

if st.sidebar.button("Logout"):
    st.session_state.user = None
    st.rerun()
    
page = st.sidebar.radio("Menu",
    ["Log Workout", "History", "Manage Exercises", "Settings"])

exercise_result = supabase.table("exercises").select(
    "name, category"
).execute()

all_exercises = exercise_result.data

push_exercises = [
    item["name"]
    for item in all_exercises
    if item["category"] == "Push"
]

pull_exercises = [
    item["name"]
    for item in all_exercises
    if item["category"] == "Pull"
]

leg_exercises = [
    item["name"]
    for item in all_exercises
    if item["category"] == "Legs"
]

core_exercises = [
    item["name"]
    for item in all_exercises
    if item["category"] == "Core"
]

if page == "Log Workout":
    st.subheader("Today's Workout")

    categories = {
        "Push": push_exercises,
        "Pull": pull_exercises,
        "Legs": leg_exercises,
        "Core": core_exercises,
    }
    tabs = st.tabs(list(categories.keys()))
    
    for tab, (category, exercises) in zip(tabs, categories.items()):
        with tab:
            exercise = st.selectbox("Exercise", exercises, key=f"{category}_exercise")
            sets = st.number_input("Sets", min_value=1, step=1, key=f"{category}_sets")

            reps = st.number_input("Reps", min_value=1, step=1, key=f"{category}_reps")
            
            weight = st.number_input("Weight (kg)", min_value=0.0, key=f"{category}_weight")
    
            duration = st.number_input("Executing duration (s)", min_value=0.0, step=1.0, key=f"{category}_duration")
            
            notes = st.text_area("Notes", key=f"{category}_notes")
   
            if st.button("➕ Add Exercise", key=f"{category}_add"):
                st.session_state.current_workout.append(
                    {
                        "exercise": exercise,
                        "category": category,
                        "sets": sets,
                        "reps": reps,
                        "weight": weight,
                        "duration": duration,
                        "notes": notes,
                    }
                )
        
                st.success(f"{exercise} added to workout!")

    st.divider() #adds a visual line

    st.subheader("Current Workout")

    if not st.session_state.current_workout:
        st.info("No exercises added yet.")
    else:
        for i, item in enumerate(st.session_state.current_workout):

            col1, col2 = st.columns([5, 1])
    
            with col1:
                st.write(
                    f"**{i+1}. {item['exercise']}** — "
                    f"{item['sets']} × {item['reps']} "
                    f"@ {item['weight']} kg "
                    f"⏱️ {item['duration']} s"
                )
        
            with col2:
                if st.button("🗑️", key=f"remove_{i}"):
                    st.session_state.current_workout.pop(i)
                    st.rerun()


    if st.button("🧪 Test Supabase Workout"):
        try:
            supabase.table("workouts").insert({
                "user_id": st.session_state.user["id"],
                "date": date.today().isoformat(),
                "exercise": "TEST",
                "category": "Push",
                "sets": 1,
                "reps": 1,
                "weight": 0,
                "duration": 0,
                "performance": 0,
                "notes": "Supabase test"
            }).execute()
    
            st.success("Supabase workout write works!")
    
        except Exception as e:
            st.error(f"Supabase workout write failed: {e}")
    if st.session_state.current_workout:
    
        if st.button("💾 Save Workout"):
        
            today = date.today().isoformat()
        
            try:
            
                for item in st.session_state.current_workout:
            
                    category = item["category"]
            
                    performance = calculate_performance(
                        category,
                        item["sets"],
                        item["reps"],
                        item["weight"],
                        item["duration"]
                    )
            
                    supabase.table("workouts").insert({
                        "user_id": st.session_state.user["id"],
                        "date": today,
                        "exercise": item["exercise"],
                        "category": category,
                        "sets": item["sets"],
                        "reps": item["reps"],
                        "weight": item["weight"],
                        "duration": item["duration"],
                        "performance": performance,
                        "notes": item["notes"]
                    }).execute()
            
                st.session_state.current_workout = []
            
                st.success("Workout saved! 💪")
                st.rerun()
            
            except Exception as e:
                st.error(f"Could not save workout: {e}")

if page == "History":

    st.subheader("📈 Performance History")

    # Select category
    category = st.selectbox(
        "Choose training day",
        ["Push", "Pull", "Legs", "Core"]
    )

    formulas = {
        "Push": "25% Sets + 45% Reps + 20% Weight + 10% Duration",
        "Pull": "25% Sets + 40% Reps + 25% Weight + 10% Duration",
        "Legs": "25% Sets + 50% Reps + 15% Weight + 10% Duration",
        "Core": "20% Sets + 20% Reps + 60% Duration",
    }
    
    st.info(f"Performance formula: {formulas[category]}")
    
    # Get exercises from selected category
    exercises = cursor.execute(
        """
        SELECT DISTINCT exercise
        FROM workouts
        WHERE category = ?
        AND user_id = ?
        ORDER BY exercise
        """,
        (category, st.session_state.user["id"])
    ).fetchall()

    exercises = [row[0] for row in exercises]

    if exercises:

        exercise = st.selectbox(
            "Choose exercise",
            exercises
        )

        history = cursor.execute(
            """
            SELECT 
                date,
                sets,
                reps,
                weight,
                duration,
                performance
            FROM workouts
            WHERE exercise = ?
            AND user_id = ?
            ORDER BY date
            """,
            (exercise, st.session_state.user["id"])
        ).fetchall()

        if history:

            st.subheader(f"{exercise} Progress")

            df = pd.DataFrame(
                history,
                columns=[
                    "Date",
                    "Sets",
                    "Reps",
                    "Weight (kg)",
                    "Duration (s)",
                    "Performance"
                ]
            )
        
            st.markdown(
                df.to_html(index=False),
                unsafe_allow_html=True
            )

            st.subheader("Performance Trend")
            
            st.line_chart(
                df,
                x="Date",
                y="Performance"
            )
            # Statistics
            scores = df["Performance"].tolist()
            
            best_score = max(scores)
            first_score = scores[0]
            latest_score = scores[-1]
            
            if first_score > 0:
                improvement = ((latest_score - first_score) / first_score) * 100
            else:
                improvement = 0
        
            col1, col2, col3 = st.columns(3)
        
            with col1:
                st.metric(
                    "🏆 Best Performance",
                    f"{best_score:.1f}"
                )
        
            with col2:
                st.metric(
                    "📈 Improvement",
                    f"{improvement:+.1f}%"
                )
        
            with col3:
                st.metric(
                    "📅 Sessions",
                    len(scores)
                )

        else:
            st.info("No data for this exercise yet.")

    else:
        st.info("No workouts recorded for this category.")

if page == "Manage Exercises":

    st.subheader("Manage Exercises")

    new_name = st.text_input("Exercise name")

    new_category = st.selectbox(
        "Category",
        ["Push", "Pull", "Legs", "Core"]
    )

    if st.button("Add Exercise"):
    
        try:
            supabase.table("exercises").insert({
                "name": new_name,
                "category": new_category
            }).execute()
    
            st.success("Exercise added!")
            st.rerun()
    
        except Exception as e:
            st.error(f"Could not add exercise: {e}")


    st.subheader("Existing Exercises")

    exercise_result = supabase.table("exercises") \
        .select("id, name, category") \
        .order("category") \
        .order("name") \
        .execute()
    
    exercise_data = exercise_result.data

    for exercise in exercise_data:

        exercise_id = exercise["id"]
        name = exercise["name"]
        category = exercise["category"]
    
        col1, col2 = st.columns([6, 1])
    
        with col1:
            st.write(f"**{name}** — {category}")
    
        with col2:
    
            # Only show delete button for custom exercises
            if (name, category) not in default_exercises:
    
                if st.button("🗑️", key=f"delete_exercise_{exercise_id}"):
                
                    try:
                        supabase.table("exercises") \
                            .delete() \
                            .eq("id", exercise_id) \
                            .execute()
                
                        st.success(f"{name} removed!")
                        st.rerun()
                
                    except Exception as e:
                        st.error(f"Could not delete exercise: {e}")

if page == "Settings":

    st.subheader("⚙️ Settings")

    st.warning(
        "The actions below permanently modify your data. "
        "These actions cannot be undone."
    )

    st.divider()

    st.subheader("🗑️ Delete Workout History")

    if st.button("Delete My Workout History", type="primary"):
    
        cursor.execute(
            """
            DELETE FROM workouts
            WHERE user_id = ?
            """,
            (st.session_state.user["id"],)
        )
    
        conn.commit()
    
        st.success("Your workout history has been deleted.")

    st.divider()

    st.subheader("🔄 Reset Application")

    st.write(
        "This will:"
        "\n- Delete all workout history"
        "\n- Remove all custom exercises"
        "\n- Restore the default exercise list"
    )

    if st.button("Reset Everything"):

        cursor.execute(
            """
            DELETE FROM workouts
            WHERE user_id = ?
            """,
            (st.session_state.user["id"],)
        )

        cursor.execute("DELETE FROM exercises")

        cursor.executemany(
            """
            INSERT INTO exercises (name, category)
            VALUES (?, ?)
            """,
            default_exercises
        )

        conn.commit()

        st.success("Application has been reset to default.")

        st.rerun()
        
    st.divider()

    st.subheader("⚠️ Delete Account")

    st.warning(
        "This will permanently delete your account and all your workout data. "
        "This action cannot be undone."
    )

    if st.button("Delete My Account", type="primary"):

        user_id = st.session_state.user["id"]

        # Delete user's workouts
        cursor.execute(
            """
            DELETE FROM workouts
            WHERE user_id = ?
            """,
            (user_id,)
        )

        # Delete user's profile if exists
        cursor.execute(
            """
            DELETE FROM profile
            WHERE id = ?
            """,
            (user_id,)
        )

        # Delete user account
        cursor.execute(
            """
            DELETE FROM users
            WHERE id = ?
            """,
            (user_id,)
        )

        conn.commit()

        # Logout after deletion
        st.session_state.user = None
        st.session_state.current_workout = []

        st.success("Account deleted successfully.")

        st.rerun()
