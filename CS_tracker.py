import streamlit as st
import sqlite3
from datetime import date

##  Configuring the page
st.set_page_config(page_title="SthenoS", page_icon="💪", layout="centered")
#accept html
st.markdown("""
<link rel="manifest" href="/app/static/manifest.json">
<meta name="theme-color" content="#000000">
""", unsafe_allow_html=True)

# Connecting to the database
conn = sqlite3.connect("workouts.db")
cursor = conn.cursor() #create cursor

#create SQLite table workouts
cursor.execute("""
CREATE TABLE IF NOT EXISTS workouts (
    id INTEGER PRIMARY KEY,
    date TEXT,
    exercise TEXT,
    sets INTEGER,
    reps INTEGER,
    weight REAL,
    duration REAL,
    notes TEXT
)
""")

conn.commit() #saves changes after creating table

#create SQLite exersise table
cursor.execute("""
CREATE TABLE IF NOT EXISTS exercises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    category TEXT
)
""")

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

cursor.executemany(
    """
    INSERT OR IGNORE INTO exercises (name, category)
    VALUES (?, ?)
    """,
    default_exercises,
)

conn.commit()

if "current_workout" not in st.session_state:
    st.session_state.current_workout = []
    
st.title("💪 Calisthenics Tracker")

page = st.sidebar.radio("Menu",
    ["Log Workout", "History", "Manage Exercises", "Statistics"])

push_exercises = [
    row[0]
    for row in cursor.execute(
        "SELECT name FROM exercises WHERE category='Push'"
    ).fetchall()
]

pull_exercises = [
    row[0]
    for row in cursor.execute(
        "SELECT name FROM exercises WHERE category='Pull'"
    ).fetchall()
]

leg_exercises = [
    row[0]
    for row in cursor.execute(
        "SELECT name FROM exercises WHERE category='Legs'"
    ).fetchall()
]

core_exercises = [
    row[0]
    for row in cursor.execute(
        "SELECT name FROM exercises WHERE category='Core'"
    ).fetchall()
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
                    {"exercise": exercise, "sets": sets, "reps": reps, "weight": weight, "duration": duration, "notes": notes,}
                )
        
                st.success(f"{exercise} added to workout!")

    st.divider() #adds a visual line

    st.subheader("Current Workout")

    if not st.session_state.current_workout:
        st.info("No exercises added yet.")
    else:
        for i, item in enumerate(st.session_state.current_workout):

            col1, col2 = st.columns([6, 1])
    
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

    if st.session_state.current_workout:
    
        if st.button("💾 Save Workout"):
    
            today = date.today().isoformat()
    
            for item in st.session_state.current_workout:
                cursor.execute(
                    """
                    INSERT INTO workouts
                    (date, exercise, sets, reps, weight, duration, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        today,
                        item["exercise"],
                        item["sets"],
                        item["reps"],
                        item["weight"],
                        item["duration"],
                        item["notes"],
                    )
                )
    
            conn.commit()
    
            st.session_state.current_workout = []
    
            st.success("Workout saved! 💪")

if page == "History":

    st.subheader("Workout History")

    data = cursor.execute(
        "SELECT * FROM workouts ORDER BY id DESC"
    ).fetchall()

    st.write(data)

st.divider()

if page == "Manage Exercises":

    st.subheader("Manage Exercises")

    new_name = st.text_input("Exercise name")

    new_category = st.selectbox(
        "Category",
        ["Push", "Pull", "Legs", "Core"]
    )

    if st.button("Add Exercise"):
        cursor.execute(
            """
            INSERT OR IGNORE INTO exercises 
            (name, category)
            VALUES (?, ?)
            """,
            (new_name, new_category)
        )

        conn.commit()

        st.success("Exercise added!")


    st.subheader("Existing Exercises")

    exercise_data = cursor.execute(
        """
        SELECT id, name, category
        FROM exercises
        ORDER BY category, name
        """
    ).fetchall()

    for exercise_id, name, category in exercise_data:

        col1, col2 = st.columns([6, 1])

        with col1:
            st.write(f"**{name}** — {category}")

        with col2:
            if st.button("🗑️", key=f"delete_exercise_{exercise_id}"):

                cursor.execute(
                    "DELETE FROM exercises WHERE id = ?",
                    (exercise_id,)
                )

                conn.commit()

                st.success(f"{name} removed!")

                st.rerun()

if page == "Statistics":

    st.subheader("📊 Statistics")

    total_workouts = cursor.execute(
        "SELECT COUNT(*) FROM workouts"
    ).fetchone()[0]

    st.metric(
        "Total Workouts",
        total_workouts
    )
