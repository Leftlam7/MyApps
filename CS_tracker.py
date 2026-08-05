import streamlit as st
import sqlite3
from datetime import date
import os

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

#create SQLite table workouts
cursor.execute("""
CREATE TABLE IF NOT EXISTS workouts (
    id INTEGER PRIMARY KEY,
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

if "current_workout" not in st.session_state:
    st.session_state.current_workout = []
    
st.title("💪 Calisthenics Tracker")

page = st.sidebar.radio("Menu",
    ["Log Workout", "History", "Manage Exercises", "Statistics", "Settings"])

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

    if st.session_state.current_workout:
    
        if st.button("💾 Save Workout"):
        
            today = date.today().isoformat()
        
            try:
                with conn:
        
                    for item in st.session_state.current_workout:
        
                        category = cursor.execute(
                            "SELECT category FROM exercises WHERE name = ?",
                            (item["exercise"],)
                        ).fetchone()[0]
        
                        performance = calculate_performance(
                            category,
                            item["sets"],
                            item["reps"],
                            item["weight"],
                            item["duration"]
                        )
        
                        cursor.execute(
                            """
                            INSERT INTO workouts
                            (date, exercise, category, sets, reps, weight, duration, performance, notes)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                today,
                                item["exercise"],
                                category,
                                item["sets"],
                                item["reps"],
                                item["weight"],
                                item["duration"],
                                performance,
                                item["notes"],
                            )
                        )
        
                st.session_state.current_workout = []
                st.success("Workout saved! 💪")
        
            except sqlite3.Error as e:
                st.error(f"Database error: {e}")

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
        ORDER BY exercise
        """,
        (category,)
    ).fetchall()

    exercises = [row[0] for row in exercises]

    if exercises:

        exercise = st.selectbox(
            "Choose exercise",
            exercises
        )

        history = cursor.execute(
            """
            SELECT date, performance
            FROM workouts
            WHERE exercise = ?
            AND performance IS NOT NULL
            ORDER BY date
            """,
            (exercise,)
        ).fetchall()

        if history:

            st.subheader(f"{exercise} Progress")

            dates = [row[0] for row in history]
            scores = [row[1] for row in history if row[1] is not None]
            
            # Statistics
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
            chart_data = {
                "Date": dates,
                "Performance": scores
            }

            st.line_chart(
                chart_data,
                x="Date",
                y="Performance"
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
if page == "Settings":

    st.subheader("⚙️ Settings")

    st.warning(
        "The actions below permanently modify your data. "
        "These actions cannot be undone."
    )

    st.divider()

    st.subheader("🗑️ Delete Workout History")

    if st.button("Delete All Workout History", type="primary"):

        cursor.execute("DELETE FROM workouts")
        conn.commit()

        st.success("All workout history has been deleted.")

    st.divider()

    st.subheader("🔄 Reset Application")

    st.write(
        "This will:"
        "\n- Delete all workout history"
        "\n- Remove all custom exercises"
        "\n- Restore the default exercise list"
    )

    if st.button("Reset Everything"):

        cursor.execute("DELETE FROM workouts")

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
