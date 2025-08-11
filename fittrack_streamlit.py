import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import time
import calendar
from contextlib import contextmanager

# =========================
# CONFIGURATION
# =========================
APP_DB = "fittrack.db"
# Per your request, using a fixed path for the exercise database.
EXERCISE_CSV_PRIMARY = Path("/Users/johndattoma/Downloads/workout app/megaGymDataset.csv")
EXERCISE_CSV_FALLBACK = Path("megaGymDataset.csv") # Fallback for portability

st.set_page_config(
    page_title="FitTrack",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================
# ELEGANT LIGHT THEME
# =========================
st.markdown("""
<style>
:root {
    --bg-color: #f0f2f6;
    --primary-bg-color: #ffffff;
    --secondary-bg-color: #f7f7fa;
    --border-color: #e0e0e6;
    --primary-text-color: #111827;
    --secondary-text-color: #6b7280;
    --accent-color: #4f46e5;
    --success-color: #16a34a;
    --warning-color: #f59e0b;
}

html, body, .main {
    background-color: var(--bg-color);
    color: var(--primary-text-color);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Inter, system-ui, sans-serif;
}

/* --- Layout & Containers --- */
.block-container {
    padding: 1rem 2rem 3rem 2rem;
}
h1, h2, h3, h4 {
    font-weight: 600;
    color: var(--primary-text-color);
}
hr {
    border-color: var(--border-color);
    margin: 1.5rem 0;
}
.st-emotion-cache-4oy321 { /* st.container(border=True) */
    background-color: var(--primary-bg-color);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 1.25rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
}

/* --- Tabs --- */
.stTabs [data-baseweb="tab-list"] {
    gap: 1rem;
    border-bottom: 2px solid var(--border-color);
}
.stTabs [data-baseweb="tab"] {
    background-color: transparent;
    border-radius: 6px 6px 0 0;
    padding: .75rem 1rem;
    font-weight: 600;
    color: var(--secondary-text-color);
    border: none;
}
.stTabs [aria-selected="true"] {
    color: var(--accent-color);
    background: var(--primary-bg-color);
    border-top: 2px solid var(--accent-color);
    border-left: 1px solid var(--border-color);
    border-right: 1px solid var(--border-color);
    border-bottom: 2px solid var(--primary-bg-color);
    margin-bottom: -2px;
}

/* --- Buttons --- */
.stButton>button {
    width: 100%;
    height: 2.75rem;
    border-radius: 8px;
    border: 1px solid var(--border-color);
    background: var(--primary-bg-color);
    color: var(--primary-text-color);
    font-weight: 600;
    transition: all 0.2s ease-in-out;
}
.stButton>button:hover:not(:disabled) {
    border-color: var(--accent-color);
    color: var(--accent-color);
    background: #f4f4ff;
}
.stButton>button:disabled {
    opacity: 0.5;
}

/* --- Timers & Stats --- */
.stat-card {
    text-align: center;
    border-radius: 12px;
    padding: 1.5rem 1rem;
    background: var(--primary-bg-color);
    border: 1px solid var(--border-color);
}
.stat-card .value {
    font-size: 2.5rem;
    font-weight: 700;
    color: var(--accent-color);
}
.stat-card .label {
    color: var(--secondary-text-color);
    font-weight: 500;
}
.timer {
    font-variant-numeric: tabular-nums;
    text-align: center;
    font-size: 4rem;
    font-weight: 700;
    padding: 1.5rem;
    border-radius: 12px;
    background: var(--secondary-bg-color);
    border: 1px solid var(--border-color);
}
.timer.work { border-left: 4px solid var(--success-color); }
.timer.rest { border-left: 4px solid var(--warning-color); }

/* --- Badges & Progress --- */
.badge {
    display: inline-block;
    padding: .4rem .8rem;
    border-radius: 999px;
    font-weight: 700;
    font-size: .8rem;
    border: 1px solid;
}
.badge.ok { background: #dcfce7; color: #15803d; border-color: #bbf7d0; }
.badge.warn { background: #fef3c7; color: #b45309; border-color: #fde68a; }

/* --- Workout & Calendar Items --- */
.exercise-item {
    border: 1px solid var(--border-color);
    border-radius: 10px;
    padding: 1rem 1.25rem;
    background: var(--primary-bg-color);
    transition: all 0.2s;
    margin-bottom: 0.5rem;
}
.exercise-item.done {
    background: #f0fdf4;
    border-color: #bbf7d0;
}
.calendar-day {
    padding: .8rem .4rem;
    text-align: center;
    border-radius: 8px;
    border: 1px solid var(--border-color);
    background: var(--primary-bg-color);
}
.calendar-day.today { outline: 2px solid var(--accent-color); }
.calendar-day.workout { background-color: var(--accent-color); color: white; font-weight: 700; }
.small { color: var(--secondary-text-color); font-size: .9rem; }
</style>

<script>
// ----- Audio System & Utilities (unchanged) -----
class SimpleAudioSystem {
  constructor(){ this.audioContext = null; this.initialized = false; }
  async init(){ if(this.initialized) return true; try { const Ctx = window.AudioContext || window.webkitAudioContext; if(Ctx){ this.audioContext = new Ctx(); if(this.audioContext.state === 'suspended'){ await this.audioContext.resume(); } this.initialized = true; return true; } }catch(e){ console.error('WebAudio not available', e); } this.initialized = true; return false; }
  async play(type){ if(!this.initialized) await this.init(); if(this.audioContext && this.audioContext.state === 'running'){ this._beep(type); } else { this._fallback(type); } }
  _beep(type){ const map = { countdown:820, transition:980, completion:1200, timer:900 }; const dur = type==='completion'?0.35:0.2; const osc = this.audioContext.createOscillator(); const gain = this.audioContext.createGain(); osc.connect(gain); gain.connect(this.audioContext.destination); osc.frequency.value = map[type] || 800; osc.type = 'sine'; const t = this.audioContext.currentTime; gain.gain.setValueAtTime(0, t); gain.gain.linearRampToValueAtTime(0.35, t+.01); gain.gain.exponentialRampToValueAtTime(0.001, t+dur); osc.start(t); osc.stop(t+dur); if(type==='completion'){ setTimeout(()=>this._beep('completion'), 260); } }
  _fallback(type){ if('vibrate' in navigator){ const pat = {countdown:[80], transition:[140], completion:[80,80,80], timer:[120]}; navigator.vibrate(pat[type] || [80]); } }
}
window.__fitAudio = new SimpleAudioSystem();
document.addEventListener('click', ()=>window.__fitAudio.init(), {once:true});
document.addEventListener('touchstart', ()=>window.__fitAudio.init(), {once:true});
window.requestWakeLock = async() => { try{ if('wakeLock' in navigator){ await navigator.wakeLock.request('screen'); } }catch(e){ console.error('WakeLock failed', e); } };
</script>
""", unsafe_allow_html=True)


# =========================
# DATABASE HELPERS
# =========================
@contextmanager
def db_conn():
    """Context manager for safe database connections."""
    conn = sqlite3.connect(APP_DB)
    try:
        yield conn
    finally:
        conn.close()

def init_database():
    """Initializes all necessary database tables and seeds default data."""
    with db_conn() as conn:
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS workouts(
            id INTEGER PRIMARY KEY AUTOINCREMENT, day TEXT NOT NULL, exercise_name TEXT NOT NULL,
            sets INTEGER, reps TEXT, notes TEXT, exercise_order INTEGER
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS workout_history(
            id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT NOT NULL, day TEXT NOT NULL,
            exercises_completed INTEGER, duration TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS exercise_completion(
            id INTEGER PRIMARY KEY AUTOINCREMENT, day TEXT NOT NULL, exercise_index INTEGER,
            completed BOOLEAN, date TEXT
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS core_exercises(
            id INTEGER PRIMARY KEY AUTOINCREMENT, exercise_name TEXT NOT NULL, exercise_order INTEGER
        )""")
        conn.commit()

        if c.execute("SELECT COUNT(*) FROM workouts").fetchone()[0] == 0:
            populate_default_workouts(conn)
        if c.execute("SELECT COUNT(*) FROM core_exercises").fetchone()[0] == 0:
            populate_default_core_exercises(conn)

def populate_default_workouts(conn):
    """Populate database with default workouts"""
    default_workouts = {
        "dayA": [
            ("Dynamic Warm-up", 1, "5-8 min", "Light cardio and dynamic stretching"),
            ("Seated Machine Chest Press", 3, "10-12", "Control the weight, full range of motion"),
            ("Chest-Supported Cable Row", 3, "10-12", "Squeeze shoulder blades, controlled movement"),
            ("Reverse Lunges", 3, "10-12 each", "Step back, keep front knee over ankle"),
            ("Seated Calf Raise", 2, "12-15", "Full range of motion, pause at top"),
            ("Seated Machine Shoulder Press", 3, "10-12", "Press straight up, controlled descent"),
            ("Wall Sit", 3, "30-45 sec", "Back flat against wall, thighs parallel"),
            ("Pallof Press", 2, "10 each", "Resist rotation, engage core"),
            ("Cool-down Stretching", 1, "5-10 min", "Focus on major muscle groups")
        ],
        "dayB": [
            ("Movement Prep", 1, "5-8 min", "Joint mobility and activation"),
            ("Seated Dumbbell Press", 3, "10-12", "Controlled movement, full range"),
            ("Machine Lat Pulldown", 3, "10-12", "Pull to chest, squeeze lats"),
            ("Forward Lunges", 3, "10-12 each", "Step forward, return to start"),
            ("Hip Adduction Machine", 2, "12-15", "Controlled squeeze, pause at end"),
            ("Seated Lateral Raise", 2, "12-15", "Raise to shoulder height, control down"),
            ("Face Pull", 2, "12-15", "Pull to face level, external rotation"),
            ("Triceps Pushdown", 2, "12-15", "Keep elbows at sides, full extension"),
            ("Seated Bicep Curl", 2, "12-15", "Controlled curl, squeeze at top"),
            ("Modified Plank", 2, "30-45 sec", "Hold position, breathe steadily")
        ],
        "dayC": [
            ("Gentle Movement", 1, "5-8 min", "Light walking or easy movement"),
            ("Pec Deck Machine", 3, "12-15", "Smooth arc, squeeze chest"),
            ("Seated Cable Row", 3, "10-12", "Pull to torso, maintain posture"),
            ("Lateral Lunges", 3, "10-12 each", "Step to side, push back to center"),
            ("Standing Calf Raise", 2, "15-20", "Rise up on toes, controlled descent"),
            ("Seated Cable Fly", 3, "12-15", "Wide arc motion, control the weight"),
            ("Reverse Pec Deck", 2, "12-15", "Squeeze shoulder blades together"),
            ("Curtsy Lunges", 3, "10-12 each", "Step behind and across, alternate sides"),
            ("Seated Knee Raises", 2, "10-12", "Lift knees toward chest"),
            ("Mobility Flow", 1, "10 min", "Full body stretching sequence")
        ]
    }
    c = conn.cursor()
    for day, exs in default_workouts.items():
        for i, (name, sets, reps, notes) in enumerate(exs):
            c.execute("INSERT INTO workouts(day,exercise_name,sets,reps,notes,exercise_order) VALUES(?,?,?,?,?,?)", (day, name, sets, reps, notes, i))
    conn.commit()

def populate_default_core_exercises(conn):
    core = ["Bird-Dog", "Plank", "Side Plank (Right)", "Side Plank (Left)"]
    c = conn.cursor()
    for i, name in enumerate(core):
        c.execute("INSERT INTO core_exercises(exercise_name,exercise_order) VALUES(?,?)", (name, i))
    conn.commit()

# --- CRUD Operations ---
def get_workouts(day):
    with db_conn() as conn:
        return pd.read_sql_query("SELECT * FROM workouts WHERE day=? ORDER BY exercise_order", conn, params=(day,))

def get_core_exercises():
    with db_conn() as conn:
        return pd.read_sql_query("SELECT * FROM core_exercises ORDER BY exercise_order", conn)

def add_core_exercise(name):
    with db_conn() as conn:
        c = conn.cursor()
        max_order = c.execute("SELECT MAX(exercise_order) FROM core_exercises").fetchone()[0] or -1
        c.execute("INSERT INTO core_exercises(exercise_name,exercise_order) VALUES(?,?)", (name, max_order + 1))
        conn.commit()

def delete_core_exercise(eid):
    with db_conn() as conn:
        conn.execute("DELETE FROM core_exercises WHERE id=?", (eid,)); conn.commit()

def get_completion_status(day):
    today = datetime.now().strftime("%Y-%m-%d")
    with db_conn() as conn:
        df = pd.read_sql_query("SELECT exercise_index, completed FROM exercise_completion WHERE day=? AND date=?", conn, params=(day, today))
    return {int(r['exercise_index']): bool(r['completed']) for _, r in df.iterrows()}

def toggle_exercise_completion(day, idx, completed):
    today = datetime.now().strftime("%Y-%m-%d")
    with db_conn() as conn:
        c = conn.cursor()
        row = c.execute("SELECT id FROM exercise_completion WHERE day=? AND exercise_index=? AND date=?", (day, idx, today)).fetchone()
        if row:
            c.execute("UPDATE exercise_completion SET completed=? WHERE id=?", (completed, row[0]))
        else:
            c.execute("INSERT INTO exercise_completion(day,exercise_index,completed,date) VALUES(?,?,?,?)", (day, idx, completed, today))
        conn.commit()

def log_workout(day, done, duration):
    with db_conn() as conn:
        conn.execute("INSERT INTO workout_history(date,day,exercises_completed,duration) VALUES(?,?,?,?)",
                     (datetime.now().strftime("%Y-%m-%d"), day, done, duration))
        conn.commit()

def get_workout_history(limit=365):
    with db_conn() as conn:
        return pd.read_sql_query("SELECT * FROM workout_history ORDER BY timestamp DESC LIMIT ?", conn, params=(limit,))

def get_stats():
    with db_conn() as conn:
        c = conn.cursor()
        total = c.execute("SELECT COUNT(*) FROM workout_history").fetchone()[0]
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        this_week = c.execute("SELECT COUNT(*) FROM workout_history WHERE date>=?", (week_ago,)).fetchone()[0]
        dates = [d[0] for d in c.execute("SELECT DISTINCT date FROM workout_history ORDER BY date DESC").fetchall()]
    streak = 0
    if dates:
        last = datetime.strptime(dates[0], "%Y-%m-%d").date()
        if (datetime.now().date() - last).days <= 1:
            streak = 1
            for i in range(1, len(dates)):
                current_date = datetime.strptime(dates[i], "%Y-%m-%d").date()
                if (last - current_date).days == 1:
                    streak += 1; last = current_date
                else: break
    return total, this_week, streak

def add_exercise(day, name, sets, reps, notes):
    with db_conn() as conn:
        c = conn.cursor()
        max_order = c.execute("SELECT MAX(exercise_order) FROM workouts WHERE day=?", (day,)).fetchone()[0] or -1
        c.execute("INSERT INTO workouts(day,exercise_name,sets,reps,notes,exercise_order) VALUES(?,?,?,?,?,?)",
                  (day, name, sets, reps, notes, max_order + 1))
        conn.commit()

def delete_exercise(ex_id):
    with db_conn() as conn:
        conn.execute("DELETE FROM workouts WHERE id=?", (ex_id,)); conn.commit()

def update_exercise_order(day, ex_id, new_order):
    with db_conn() as conn:
        c = conn.cursor()
        cur = c.execute("SELECT exercise_order FROM workouts WHERE id=?", (ex_id,)).fetchone()[0]
        swap = c.execute("SELECT id FROM workouts WHERE day=? AND exercise_order=?", (day, new_order)).fetchone()
        if swap:
            c.execute("UPDATE workouts SET exercise_order=? WHERE id=?", (cur, swap[0]))
        c.execute("UPDATE workouts SET exercise_order=? WHERE id=?", (new_order, ex_id))
        conn.commit()

def replace_exercise_manually(ex_id, name, sets, reps, notes):
    with db_conn() as conn:
        conn.execute("UPDATE workouts SET exercise_name=?, sets=?, reps=?, notes=? WHERE id=?",
                     (name, sets, reps, notes, ex_id))
        conn.commit()

# =========================
# EXERCISE DB & TIMER UTILS
# =========================
@st.cache_data(show_spinner="Loading exercise database...")
def load_exercise_database():
    """Loads the exercise database from the fixed path."""
    path = EXERCISE_CSV_PRIMARY if EXERCISE_CSV_PRIMARY.exists() else EXERCISE_CSV_FALLBACK
    if not path.exists():
        return pd.DataFrame(), f"NOT FOUND: {path}"
    try:
        df = pd.read_csv(path)
        # Normalize columns
        required_cols = ['Title', 'BodyPart', 'Equipment', 'Level']
        for col in required_cols:
            if col not in df.columns:
                for existing_col in df.columns:
                    if col.lower() == existing_col.lower():
                        df.rename(columns={existing_col: col}, inplace=True)
                        break
                else: df[col] = 'N/A'
        return df, str(path)
    except Exception as e:
        return pd.DataFrame(), f"ERROR loading {path}: {e}"

def init_timer_state():
    """Initializes all timer-related variables in session state."""
    ss = st.session_state
    timers = {
        'timer_running': False, 'timer_start_ts': 0.0, 'timer_elapsed': 0.0, 'timer_preset': 'Stopwatch',
        'wo_running': False, 'wo_start_ts': 0.0, 'wo_elapsed': 0.0,
        'int_running': False, 'int_start_ts': 0.0, 'int_elapsed': 0.0, 'int_set': 1,
        'int_phase': 'WORK', 'int_idx': 0, 'int_done': False, 'int_beep_last': -1
    }
    for k, v in timers.items():
        if k not in ss: ss[k] = v

def fmt_time(sec: float) -> str: return f"{int(sec)//60:02d}:{int(sec)%60:02d}"

def play_sound(kind: str):
    st.components.v1.html(f"<script>window.__fitAudio && window.__fitAudio.play('{kind}');</script>", height=0)

# =========================
# UI PAGES
# =========================
def page_dashboard():
    st.subheader("Dashboard")
    st.markdown("Your daily fitness command center. Let's get moving!")
    st.markdown("---")

    total, this_week, streak = get_stats()
    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='stat-card'><div class='value'>{total}</div><div class='label'>Total Workouts</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='stat-card'><div class='value'>{this_week}</div><div class='label'>This Week</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='stat-card'><div class='value'>{streak}</div><div class='label'>Day Streak</div></div>", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("Recent History")
    hist = get_workout_history(limit=5)
    if hist.empty:
        st.info("No workouts logged yet. Complete a session to see your history here.")
    else:
        for _, r in hist.iterrows():
            with st.container(border=True):
                day_name = {"dayA":"Day A","dayB":"Day B","dayC":"Day C"}.get(r['day'], r['day'])
                date_obj = datetime.strptime(r['date'], "%Y-%m-%d")
                st.markdown(f"**{day_name}** on **{date_obj.strftime('%B %d, %Y')}**")
                st.markdown(f"<span class='small'>Duration: {r.get('duration','N/A')} &bull; Exercises: {r['exercises_completed']}</span>", unsafe_allow_html=True)

def page_start_workout():
    st.subheader("Start Workout")
    day_options = {"dayA": "Day A — Full Body", "dayB": "Day B — Strength", "dayC": "Day C — Mobility"}
    day = st.selectbox("Select a plan to begin:", options=list(day_options.keys()), format_func=lambda x: day_options[x])

    c1, c2 = st.columns([1, 1], gap="large")
    with c1:
        st.markdown("#### Workout Timer")
        with st.container(border=True):
            if st.session_state.wo_running:
                elapsed = time.time() - st.session_state.wo_start_ts
                st.markdown(f"<div class='timer'>{fmt_time(elapsed)}</div>", unsafe_allow_html=True)
                time.sleep(1); st.rerun()
            else:
                st.markdown(f"<div class='timer'>{fmt_time(st.session_state.wo_elapsed)}</div>", unsafe_allow_html=True)

            b1, b2, b3 = st.columns(3)
            if b1.button("Start", key="wo_start", disabled=st.session_state.wo_running):
                st.session_state.wo_running = True
                st.session_state.wo_start_ts = time.time() - st.session_state.wo_elapsed
                st.components.v1.html("<script>window.requestWakeLock();</script>", height=0); st.rerun()
            if b2.button("Pause", key="wo_pause", disabled=not st.session_state.wo_running):
                st.session_state.wo_running = False
                st.session_state.wo_elapsed = time.time() - st.session_state.wo_start_ts
                st.rerun()
            if b3.button("Reset", key="wo_reset"):
                st.session_state.wo_running, st.session_state.wo_elapsed = False, 0.0
                st.rerun()

    with c2:
        st.markdown("#### Rest Timer")
        with st.container(border=True):
            presets = {"45s": 45, "60s": 60, "90s": 90, "120s": 120}
            target_time = st.selectbox("Set rest duration:", list(presets.keys()), index=1)
            
            # This is a placeholder for a more complex timer if needed, for now it's a simple display
            st.markdown(f"<div class='timer'>{fmt_time(presets[target_time])}</div>", unsafe_allow_html=True)
            st.button("Start Rest Timer (Manual)", key="rest_timer_manual", help="This is a visual guide; use a real timer for accuracy.", disabled=True)


    st.markdown("---")
    st.subheader("Today's Exercises")
    workouts = get_workouts(day)
    completion = get_completion_status(day)
    done_count = sum(1 for i in range(len(workouts)) if completion.get(i, False))
    progress_pct = int(100 * (done_count / len(workouts) if len(workouts) > 0 else 0))

    st.progress(progress_pct, text=f"**{progress_pct}% Complete** — {done_count} of {len(workouts)} exercises")

    if done_count == len(workouts) and len(workouts) > 0:
        st.success("Workout Complete! Great job!")
        play_sound("completion")
        if st.button("Log Workout and Reset", use_container_width=True):
            duration_str = fmt_time(st.session_state.wo_elapsed)
            log_workout(day, len(workouts), duration_str)
            with db_conn() as conn:
                conn.execute("DELETE FROM exercise_completion WHERE day=? AND date=?", (day, datetime.now().strftime("%Y-%m-%d")))
            st.session_state.wo_running, st.session_state.wo_elapsed = False, 0.0
            st.toast("Workout logged!"); time.sleep(1); st.rerun()

    for idx, row in workouts.iterrows():
        is_done = completion.get(idx, False)
        with st.container():
            st.markdown(f"<div class='exercise-item {'done' if is_done else ''}'>", unsafe_allow_html=True)
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"**{row['exercise_name']}**")
                st.markdown(f"{row['sets']} sets × {row['reps']} reps <br><span class='small'>{row['notes']}</span>", unsafe_allow_html=True)
            with c2:
                if st.button("Done" if not is_done else "Undo", key=f"ex_done_{day}_{idx}", use_container_width=True):
                    toggle_exercise_completion(day, idx, not is_done); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

def page_cardio_core():
    st.subheader("Cardio & Core Intervals")
    st.markdown("A 5-minute core circuit, perfect after a 15-minute cardio session.")
    st.markdown("---")
    core_exercises = get_core_exercises()
    exercise_list = core_exercises['exercise_name'].tolist()

    if not exercise_list:
        st.error("No core exercises found. Please add some in 'Manage Workouts'."); return

    st.markdown("#### Interval Timer: 4 Sets (60s Work, 10s Rest)")
    ss = st.session_state
    
    with st.container(border=True):
        phase_class = "work" if ss.int_phase == "WORK" else "rest"
        badge_class = "ok" if ss.int_phase == "WORK" else "warn"
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Status:** <span class='badge {badge_class}'>Set {ss.int_set}/4 — {ss.int_phase}</span>", unsafe_allow_html=True)
            if ss.int_running or ss.int_done:
                if ss.int_phase == "WORK": st.markdown(f"**Current:**\n### {exercise_list[ss.int_idx]}")
                else: st.markdown(f"**Next Up:**\n### {exercise_list[(ss.int_idx + 1) % len(exercise_list)]}")
            else:
                st.markdown(f"**First Up:**\n### {exercise_list[0]}")

        with c2:
            if ss.int_done:
                st.success("Intervals Complete!")
                st.markdown("<div class='timer'>DONE</div>", unsafe_allow_html=True)
            elif ss.int_running:
                elapsed = time.time() - ss.int_start_ts
                cycle_duration, work_duration = 70, 60
                current_cycle_num = int(elapsed // cycle_duration)
                time_in_cycle = elapsed % cycle_duration
                
                if elapsed >= (4 * cycle_duration - 10):
                    ss.int_done, ss.int_running = True, False
                    play_sound("completion"); st.rerun()
                else:
                    ss.int_set = current_cycle_num + 1
                    ss.int_idx = current_cycle_num % max(1, len(exercise_list))
                    if time_in_cycle < work_duration:
                        ss.int_phase, remaining = "WORK", work_duration - time_in_cycle
                    else:
                        ss.int_phase, remaining = "REST", cycle_duration - time_in_cycle
                
                rem_int = int(remaining)
                if rem_int <= 3 and rem_int != ss.int_beep_last and rem_int > 0:
                    play_sound("countdown"); ss.int_beep_last = rem_int
                elif rem_int == 0 and ss.int_beep_last != 0:
                    play_sound("transition"); ss.int_beep_last = 0
                
                st.markdown(f"<div class='timer {phase_class}'>{fmt_time(remaining)}</div>", unsafe_allow_html=True)
                time.sleep(1); st.rerun()
            else:
                 st.markdown(f"<div class='timer work'>{fmt_time(60)}</div>", unsafe_allow_html=True)

    b1, b2, b3 = st.columns(3)
    if b1.button("Start", key="int_start", disabled=ss.int_running):
        ss.update({'int_running': True, 'int_start_ts': time.time(), 'int_elapsed': 0.0, 'int_done': False, 'int_beep_last': -1, 'int_set': 1, 'int_phase': 'WORK', 'int_idx': 0})
        st.components.v1.html("<script>window.requestWakeLock();</script>", height=0); st.rerun()
    if b2.button("Pause", key="int_pause", disabled=not ss.int_running):
        ss.update({'int_running': False}); st.rerun()
    if b3.button("Reset", key="int_reset"):
        ss.update({'int_running': False, 'int_elapsed': 0.0, 'int_set': 1, 'int_phase': "WORK", 'int_idx': 0, 'int_done': False})
        st.rerun()
    
    if ss.int_done:
        if st.button("Log as 'Cardio & Core' Workout", use_container_width=True):
            log_workout("Cardio & Core", len(exercise_list), "20:00")
            st.toast("Workout logged!"); time.sleep(1); ss['int_done'] = False; st.rerun()

def page_manage_workouts():
    st.subheader("Manage Workouts")
    exercise_db, db_source = st.session_state.exercise_db_info
    st.caption(f"Exercise Database Source: `{db_source}`")
    
    day_options = {"dayA": "Day A", "dayB": "Day B", "dayC": "Day C", "core": "Core Circuit"}
    day_key = st.selectbox("Select plan to manage:", options=list(day_options.keys()), format_func=lambda x: day_options[x])

    st.markdown("---")

    if day_key == "core":
        st.markdown("#### Edit Core Circuit")
        core_exercises = get_core_exercises()
        for _, r in core_exercises.iterrows():
            c1, c2 = st.columns([5, 1])
            c1.write(f"{r['exercise_order'] + 1}. {r['exercise_name']}")
            if c2.button("Delete", key=f"del_core_{r['id']}", help="Delete this exercise"):
                delete_core_exercise(r['id']); st.rerun()

        with st.form("add_core_form"):
            new_name = st.text_input("New Core Exercise Name")
            if st.form_submit_button("Add to Core Circuit", use_container_width=True):
                if new_name.strip():
                    add_core_exercise(new_name.strip()); st.toast(f"Added '{new_name.strip()}'!"); time.sleep(1); st.rerun()
    else:
        tab1, tab2 = st.tabs(["Edit Plan Manually", "Replace from Database"])
        workouts = get_workouts(day_key)

        with tab1:
            st.markdown("##### Reorder & Delete")
            for _, row in workouts.iterrows():
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns([5, 1, 1, 1])
                    c1.markdown(f"**{row['exercise_order']+1}. {row['exercise_name']}** ({row['sets']}x{row['reps']})")
                    if c2.button("Up", key=f"up_{row['id']}", help="Move Up", disabled=row['exercise_order'] == 0):
                        update_exercise_order(day_key, row['id'], row['exercise_order'] - 1); st.rerun()
                    if c3.button("Down", key=f"down_{row['id']}", help="Move Down", disabled=row['exercise_order'] >= len(workouts) - 1):
                        update_exercise_order(day_key, row['id'], row['exercise_order'] + 1); st.rerun()
                    if c4.button("Delete", key=f"del_{row['id']}", help="Delete"):
                        delete_exercise(row['id']); st.rerun()
            
            st.markdown("##### Add New Exercise")
            with st.form("add_ex_form"):
                name = st.text_input("Exercise Name")
                c1, c2 = st.columns(2)
                sets = c1.number_input("Sets", 1, 10, 3, 1)
                reps = c2.text_input("Reps", "10-12")
                notes = st.text_input("Notes", "Focus on form")
                if st.form_submit_button("Add Exercise", use_container_width=True):
                    if name.strip():
                        add_exercise(day_key, name.strip(), sets, reps, notes.strip()); st.toast(f"Added '{name}'!"); time.sleep(1); st.rerun()

        with tab2:
            if exercise_db.empty:
                st.warning("Exercise database not loaded. This feature is unavailable."); return

            st.markdown("##### Replace an Existing Exercise")
            c1, c2 = st.columns(2)
            ex_to_replace_id = c1.selectbox("Exercise to replace:", options=workouts['id'], format_func=lambda x: workouts[workouts['id']==x]['exercise_name'].iloc[0], key="replace_select")
            
            body_parts = ["All"] + sorted(exercise_db['BodyPart'].dropna().unique().tolist())
            sel_bp = c2.selectbox("Filter by Body Part", body_parts, key="bp_filter")
            
            filtered_db = exercise_db.copy()
            if sel_bp != "All":
                filtered_db = filtered_db[filtered_db['BodyPart'] == sel_bp]
                
            new_exercise_title = st.selectbox("Select replacement:", options=filtered_db['Title'].tolist(), key="new_ex_title")
            
            if st.button("Confirm Replacement", use_container_width=True):
                new_ex_details = filtered_db[filtered_db['Title'] == new_exercise_title].iloc[0]
                original_ex = workouts[workouts['id'] == ex_to_replace_id].iloc[0]
                replace_exercise_manually(ex_to_replace_id, new_exercise_title, original_ex['sets'], original_ex['reps'], f"Equipment: {new_ex_details['Equipment']}")
                st.toast("Exercise replaced!"); time.sleep(1); st.rerun()

def page_history():
    st.subheader("History & Progress")
    tab1, tab2 = st.tabs(["Calendar View", "Full History"])

    with tab1:
        hist = get_workout_history(limit=365)
        workout_dates = set(hist['date'].tolist()) if not hist.empty else set()
        today = datetime.now()

        if 'cal_month' not in st.session_state: st.session_state.cal_month = today.month
        if 'cal_year' not in st.session_state: st.session_state.cal_year = today.year

        c1, c2, c3 = st.columns([2, 3, 2])
        if c1.button("Prev Month", use_container_width=True):
            st.session_state.cal_month -= 1
            if st.session_state.cal_month == 0: st.session_state.cal_month, st.session_state.cal_year = 12, st.session_state.cal_year - 1
            st.rerun()
        c2.markdown(f"<h3 style='text-align: center;'>{datetime(st.session_state.cal_year, st.session_state.cal_month, 1).strftime('%B %Y')}</h3>", unsafe_allow_html=True)
        if c3.button("Next Month", use_container_width=True):
            st.session_state.cal_month += 1
            if st.session_state.cal_month == 13: st.session_state.cal_month, st.session_state.cal_year = 1, st.session_state.cal_year + 1
            st.rerun()
        
        st.markdown("---")
        cal = calendar.monthcalendar(st.session_state.cal_year, st.session_state.cal_month)
        weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        cols = st.columns(7)
        for i, day_name in enumerate(weekdays): cols[i].markdown(f"**{day_name}**")

        for week in cal:
            cols = st.columns(7)
            for i, day_num in enumerate(week):
                if day_num == 0:
                    cols[i].markdown("<div class='calendar-day' style='background:transparent; border:none;'>&nbsp;</div>", unsafe_allow_html=True)
                else:
                    date_str = f"{st.session_state.cal_year:04d}-{st.session_state.cal_month:02d}-{day_num:02d}"
                    classes = "calendar-day"
                    if date_str == today.strftime("%Y-%m-%d"): classes += " today"
                    if date_str in workout_dates: classes += " workout"
                    cols[i].markdown(f"<div class='{classes}'>{day_num}</div>", unsafe_allow_html=True)

    with tab2:
        st.markdown("#### Full Workout Log")
        full_hist = get_workout_history(limit=500)
        if full_hist.empty:
            st.info("No workouts logged yet.")
        else:
            st.dataframe(full_hist, use_container_width=True)
            csv = full_hist.to_csv(index=False).encode('utf-8')
            st.download_button("Download History (CSV)", csv, f"fittrack_history_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv", use_container_width=True)

# =========================
# MAIN APP LOGIC
# =========================
def main():
    init_database()
    init_timer_state()
    
    if 'exercise_db_info' not in st.session_state:
        st.session_state.exercise_db_info = load_exercise_database()

    st.title("FitTrack")

    pages = {
        "Dashboard": page_dashboard,
        "Start Workout": page_start_workout,
        "Cardio & Core": page_cardio_core,
        "Manage Workouts": page_manage_workouts,
        "History": page_history,
    }
    
    selected_tabs = st.tabs(list(pages.keys()))
    
    for i, page_func in enumerate(pages.values()):
        with selected_tabs[i]:
            page_func()

if __name__ == "__main__":
    main()