import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import json
from pathlib import Path
import time
import calendar
import base64

# Database setup functions remain the same
def init_database():
    """Initialize SQLite database with tables"""
    conn = sqlite3.connect('fittrack.db')
    c = conn.cursor()

    # Create tables
    c.execute('''CREATE TABLE IF NOT EXISTS workouts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  day TEXT NOT NULL,
                  exercise_name TEXT NOT NULL,
                  sets INTEGER,
                  reps TEXT,
                  notes TEXT,
                  exercise_order INTEGER)''')

    c.execute('''CREATE TABLE IF NOT EXISTS workout_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  date TEXT NOT NULL,
                  day TEXT NOT NULL,
                  exercises_completed INTEGER,
                  duration TEXT,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')

    c.execute('''CREATE TABLE IF NOT EXISTS exercise_completion
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  day TEXT NOT NULL,
                  exercise_index INTEGER,
                  completed BOOLEAN,
                  date TEXT)''')

    # Create core exercises table
    c.execute('''CREATE TABLE IF NOT EXISTS core_exercises
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  exercise_name TEXT NOT NULL,
                  exercise_order INTEGER)''')

    conn.commit()

    # Check if workouts exist, if not, populate with default
    c.execute("SELECT COUNT(*) FROM workouts")
    if c.fetchone()[0] == 0:
        populate_default_workouts(conn)

    # Check if core exercises exist, if not, populate with default
    c.execute("SELECT COUNT(*) FROM core_exercises")
    if c.fetchone()[0] == 0:
        populate_default_core_exercises(conn)

    conn.close()

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
    for day, exercises in default_workouts.items():
        for i, (name, sets, reps, notes) in enumerate(exercises):
            c.execute("INSERT INTO workouts (day, exercise_name, sets, reps, notes, exercise_order) VALUES (?, ?, ?, ?, ?, ?)",
                     (day, name, sets, reps, notes, i))
    conn.commit()

def populate_default_core_exercises(conn):
    """Populate database with default core exercises"""
    default_core_exercises = [
        "Bird-Dogs",
        "Plank",
        "Right Side Plank", 
        "Left Side Plank"
    ]
    
    c = conn.cursor()
    for i, exercise in enumerate(default_core_exercises):
        c.execute("INSERT INTO core_exercises (exercise_name, exercise_order) VALUES (?, ?)",
                 (exercise, i))
    conn.commit()

# All the database functions remain the same
def get_workouts(day):
    conn = sqlite3.connect('fittrack.db')
    df = pd.read_sql_query(
        "SELECT * FROM workouts WHERE day = ? ORDER BY exercise_order",
        conn, params=(day,)
    )
    conn.close()
    return df

def get_core_exercises():
    conn = sqlite3.connect('fittrack.db')
    df = pd.read_sql_query(
        "SELECT * FROM core_exercises ORDER BY exercise_order",
        conn
    )
    conn.close()
    return df

def add_core_exercise(exercise_name):
    conn = sqlite3.connect('fittrack.db')
    c = conn.cursor()
    c.execute("SELECT MAX(exercise_order) FROM core_exercises")
    max_order = c.fetchone()[0] or -1
    c.execute("INSERT INTO core_exercises (exercise_name, exercise_order) VALUES (?, ?)",
              (exercise_name, max_order + 1))
    conn.commit()
    conn.close()

def delete_core_exercise(exercise_id):
    conn = sqlite3.connect('fittrack.db')
    c = conn.cursor()
    c.execute("DELETE FROM core_exercises WHERE id = ?", (exercise_id,))
    conn.commit()
    conn.close()

def get_completion_status(day):
    conn = sqlite3.connect('fittrack.db')
    today = datetime.now().strftime("%Y-%m-%d")
    df = pd.read_sql_query(
        "SELECT exercise_index, completed FROM exercise_completion WHERE day = ? AND date = ?",
        conn, params=(day, today)
    )
    conn.close()
    return {row['exercise_index']: row['completed'] for _, row in df.iterrows()}

def toggle_exercise_completion(day, exercise_index, completed):
    conn = sqlite3.connect('fittrack.db')
    c = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("SELECT id FROM exercise_completion WHERE day = ? AND exercise_index = ? AND date = ?",
              (day, exercise_index, today))
    result = c.fetchone()
    if result:
        c.execute("UPDATE exercise_completion SET completed = ? WHERE id = ?",
                 (completed, result[0]))
    else:
        c.execute("INSERT INTO exercise_completion (day, exercise_index, completed, date) VALUES (?, ?, ?, ?)",
                 (day, exercise_index, completed, today))
    conn.commit()
    conn.close()

def log_workout(day, exercises_completed, duration):
    conn = sqlite3.connect('fittrack.db')
    c = conn.cursor()
    c.execute("INSERT INTO workout_history (date, day, exercises_completed, duration) VALUES (?, ?, ?, ?)",
              (datetime.now().strftime("%Y-%m-%d"), day, exercises_completed, duration))
    conn.commit()
    conn.close()

def get_workout_history(limit=100):
    conn = sqlite3.connect('fittrack.db')
    df = pd.read_sql_query(
        "SELECT * FROM workout_history ORDER BY timestamp DESC LIMIT ?",
        conn, params=(limit,)
    )
    conn.close()
    return df

def get_stats():
    conn = sqlite3.connect('fittrack.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM workout_history")
    total = c.fetchone()[0]
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    c.execute("SELECT COUNT(*) FROM workout_history WHERE date >= ?", (week_ago,))
    this_week = c.fetchone()[0]
    c.execute("SELECT DISTINCT date FROM workout_history ORDER BY date DESC")
    dates = [row[0] for row in c.fetchall()]
    streak = 0
    if dates:
        last_date = datetime.strptime(dates[0], "%Y-%m-%d").date()
        if (datetime.now().date() - last_date).days <= 1:
            streak = 1
            for i in range(1, len(dates)):
                workout_date = datetime.strptime(dates[i], "%Y-%m-%d").date()
                if (last_date - workout_date).days == 1:
                    streak += 1
                    last_date = workout_date
                else:
                    break
    conn.close()
    return total, this_week, streak

def add_exercise(day, name, sets, reps, notes):
    conn = sqlite3.connect('fittrack.db')
    c = conn.cursor()
    c.execute("SELECT MAX(exercise_order) FROM workouts WHERE day = ?", (day,))
    max_order = c.fetchone()[0] or -1
    c.execute("INSERT INTO workouts (day, exercise_name, sets, reps, notes, exercise_order) VALUES (?, ?, ?, ?, ?, ?)",
              (day, name, sets, reps, notes, max_order + 1))
    conn.commit()
    conn.close()

def delete_exercise(exercise_id):
    conn = sqlite3.connect('fittrack.db')
    c = conn.cursor()
    c.execute("DELETE FROM workouts WHERE id = ?", (exercise_id,))
    conn.commit()
    conn.close()

def update_exercise_order(day, exercise_id, new_order):
    conn = sqlite3.connect('fittrack.db')
    c = conn.cursor()
    c.execute("SELECT exercise_order FROM workouts WHERE id = ?", (exercise_id,))
    current_order = c.fetchone()[0]
    c.execute("SELECT id FROM workouts WHERE day = ? AND exercise_order = ?", (day, new_order))
    swap_id = c.fetchone()
    if swap_id:
        c.execute("UPDATE workouts SET exercise_order = ? WHERE id = ?", (current_order, swap_id[0]))
    c.execute("UPDATE workouts SET exercise_order = ? WHERE id = ?", (new_order, exercise_id))
    conn.commit()
    conn.close()

def replace_exercise(exercise_id, new_name, new_notes=None):
    conn = sqlite3.connect('fittrack.db')
    c = conn.cursor()
    if new_notes:
        c.execute("UPDATE workouts SET exercise_name = ?, notes = ? WHERE id = ?",
                 (new_name, new_notes, exercise_id))
    else:
        c.execute("UPDATE workouts SET exercise_name = ? WHERE id = ?",
                 (new_name, exercise_id))
    conn.commit()
    conn.close()

def replace_exercise_manually(exercise_id, new_name, new_sets, new_reps, new_notes):
    conn = sqlite3.connect('fittrack.db')
    c = conn.cursor()
    c.execute("UPDATE workouts SET exercise_name = ?, sets = ?, reps = ?, notes = ? WHERE id = ?",
              (new_name, new_sets, new_reps, new_notes, exercise_id))
    conn.commit()
    conn.close()

# Enhanced timer persistence function
def get_actual_elapsed_time(timer_key, start_time_key):
    """Calculate actual elapsed time accounting for app suspension"""
    if timer_key not in st.session_state or not st.session_state[timer_key]:
        return 0
    
    if start_time_key not in st.session_state:
        return 0
    
    # Calculate time based on stored start time
    current_time = time.time()
    start_time = st.session_state[start_time_key]
    return current_time - start_time

# Initialize Streamlit
st.set_page_config(
    page_title="FitTrack Pro",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Clean, professional CSS
st.markdown("""
<style>
    /* Clean, professional styling */
    .main { 
        padding: 1rem 2rem; 
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }
    
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        height: 3rem;
        font-weight: 500;
        border: 1px solid #d1d5db;
        background: white;
        color: #374151;
        transition: all 0.2s;
    }
    
    .stButton > button:hover {
        background: #f9fafb;
        border-color: #9ca3af;
    }
    
    .workout-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border: 1px solid #e5e7eb;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    }
    
    .completed-card {
        background: #f0fdf4;
        border-color: #22c55e;
    }
    
    .timer-display {
        font-size: 3rem;
        font-weight: 600;
        text-align: center;
        color: #111827;
        font-family: -apple-system, BlinkMacSystemFont, monospace;
        padding: 2rem;
        background: #f9fafb;
        border-radius: 8px;
        margin: 1rem 0;
        border: 1px solid #e5e7eb;
    }
    
    .interval-timer-display {
        font-size: 4rem;
        font-weight: 600;
        text-align: center;
        color: #111827;
        font-family: -apple-system, BlinkMacSystemFont, monospace;
        padding: 2rem;
        background: #f9fafb;
        border-radius: 8px;
        margin: 1rem 0;
        border: 2px solid #3b82f6;
    }
    
    .work-timer {
        background: #ecfdf5;
        border-color: #10b981;
        color: #059669;
    }
    
    .rest-timer {
        background: #fef3c7;
        border-color: #f59e0b;
        color: #d97706;
    }
    
    .interval-exercise {
        font-size: 1.5rem;
        font-weight: 500;
        text-align: center;
        color: #374151;
        margin-bottom: 1rem;
        padding: 1rem;
        background: #f3f4f6;
        border-radius: 8px;
        border: 1px solid #d1d5db;
    }
    
    .interval-status {
        font-size: 1.25rem;
        font-weight: 500;
        text-align: center;
        margin-bottom: 1rem;
        padding: 0.75rem;
        border-radius: 8px;
        border: 1px solid #d1d5db;
    }
    
    .work-status {
        background: #ecfdf5;
        color: #059669;
        border-color: #10b981;
    }
    
    .rest-status {
        background: #fef3c7;
        color: #d97706;
        border-color: #f59e0b;
    }
    
    .stat-card {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        text-align: center;
        border: 1px solid #e5e7eb;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        height: 100%;
    }
    
    .stat-value {
        font-size: 2.5rem;
        font-weight: 600;
        color: #3b82f6;
        margin-bottom: 0.5rem;
    }
    
    .stat-label {
        font-weight: 500;
        color: #6b7280;
    }
    
    .exercise-db-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        border: 1px solid #e5e7eb;
        transition: all 0.2s;
    }
    
    .exercise-db-card:hover {
        background: #f9fafb;
        border-color: #d1d5db;
    }
    
    .calendar-day {
        padding: 0.5rem;
        text-align: center;
        border-radius: 4px;
        height: 3rem;
        line-height: 2rem;
        box-sizing: border-box;
        border: 1px solid #e5e7eb;
        background: white;
    }
    
    .calendar-day.today {
        font-weight: 600;
        background: #eff6ff;
        border-color: #3b82f6;
        color: #1d4ed8;
    }
    
    .calendar-day.workout-day {
        font-weight: 600;
        background: #ecfdf5;
        border-color: #10b981;
        color: #059669;
    }
    
    .music-button {
        display: inline-block;
        padding: 0.75rem 1.5rem;
        background: #000;
        color: white;
        text-decoration: none;
        border-radius: 8px;
        font-weight: 500;
        text-align: center;
        transition: all 0.2s;
        border: none;
        cursor: pointer;
        width: 100%;
    }
    
    .music-button:hover {
        background: #1f2937;
        text-decoration: none;
        color: white;
    }
    
    .warning-box {
        background: #fef3c7;
        border: 1px solid #f59e0b;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>

<script>
// Fixed Audio System - Simple and reliable
class SimpleAudioSystem {
    constructor() {
        this.audioContext = null;
        this.isInitialized = false;
    }
    
    async init() {
        if (this.isInitialized) return true;
        
        try {
            // Try to create audio context
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            if (AudioContext) {
                this.audioContext = new AudioContext();
                
                // Handle suspended state (iOS requirement)
                if (this.audioContext.state === 'suspended') {
                    await this.audioContext.resume();
                }
                
                this.isInitialized = true;
                console.log('Audio system initialized');
                return true;
            }
        } catch (e) {
            console.log('Web Audio not available, using fallback');
        }
        
        this.isInitialized = true;
        return false;
    }
    
    async playSound(type) {
        console.log(`Playing ${type} sound`);
        
        // Initialize if needed
        if (!this.isInitialized) {
            await this.init();
        }
        
        // Try Web Audio API first
        if (this.audioContext && this.audioContext.state === 'running') {
            try {
                this.playWebAudio(type);
                return;
            } catch (e) {
                console.log('Web Audio failed, using fallback');
            }
        }
        
        // Fallback to simple beep
        this.playFallbackSound(type);
    }
    
    playWebAudio(type) {
        const frequencies = {
            countdown: 800,
            transition: 1000,
            completion: 1200,
            timer: 900
        };
        
        const duration = type === 'completion' ? 0.4 : 0.2;
        const freq = frequencies[type] || 800;
        
        const oscillator = this.audioContext.createOscillator();
        const gainNode = this.audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(this.audioContext.destination);
        
        oscillator.frequency.setValueAtTime(freq, this.audioContext.currentTime);
        oscillator.type = 'sine';
        
        // Envelope
        gainNode.gain.setValueAtTime(0, this.audioContext.currentTime);
        gainNode.gain.linearRampToValueAtTime(0.3, this.audioContext.currentTime + 0.01);
        gainNode.gain.exponentialRampToValueAtTime(0.001, this.audioContext.currentTime + duration);
        
        oscillator.start(this.audioContext.currentTime);
        oscillator.stop(this.audioContext.currentTime + duration);
        
        // Multiple beeps for completion
        if (type === 'completion') {
            setTimeout(() => this.playWebAudio('completion'), 300);
        }
    }
    
    playFallbackSound(type) {
        // Try vibration on mobile
        if ('vibrate' in navigator) {
            const patterns = {
                countdown: [100],
                transition: [200],
                completion: [100, 100, 100],
                timer: [150]
            };
            navigator.vibrate(patterns[type] || [100]);
        }
        
        // Visual feedback
        document.body.style.backgroundColor = '#f3f4f6';
        setTimeout(() => {
            document.body.style.backgroundColor = '';
        }, 100);
    }
}

// Apple Music Integration - Actually works
function openAppleMusic() {
    console.log('Opening Apple Music...');
    
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
    const isMac = navigator.platform.indexOf('Mac') > -1;
    
    if (isIOS || isMac) {
        // Try to open native Apple Music app
        window.location.href = 'music://';
        
        // Fallback to web version after 2 seconds
        setTimeout(() => {
            window.open('https://music.apple.com', '_blank');
        }, 2000);
    } else {
        // Open web version directly for other platforms
        window.open('https://music.apple.com', '_blank');
    }
}

// Wake Lock for keeping screen on
async function requestWakeLock() {
    try {
        if ('wakeLock' in navigator) {
            const wakeLock = await navigator.wakeLock.request('screen');
            console.log('Screen wake lock active');
            return wakeLock;
        }
    } catch (err) {
        console.log('Wake lock not supported or failed');
    }
    return null;
}

// Initialize audio system
const audioSystem = new SimpleAudioSystem();

// Auto-initialize on any user interaction
document.addEventListener('click', () => audioSystem.init(), { once: true });
document.addEventListener('touchstart', () => audioSystem.init(), { once: true });

// Global functions for Streamlit
window.playCountdownBeep = () => audioSystem.playSound('countdown');
window.playTransitionBeep = () => audioSystem.playSound('transition');
window.playTimerBeep = () => audioSystem.playSound('timer');
window.playCompletionBeep = () => audioSystem.playSound('completion');
window.openAppleMusic = openAppleMusic;
window.requestWakeLock = requestWakeLock;

console.log('FitTrack Pro audio and music systems loaded');
</script>
""", unsafe_allow_html=True)

# Initialize database
init_database()

# Load exercise database
@st.cache_data
def load_exercise_database():
    csv_path = Path('megaGymDataset.csv')
    if csv_path.exists():
        try:
            df = pd.read_csv(csv_path)
            if 'Unnamed: 0' in df.columns:
                df = df.drop(columns=['Unnamed: 0'])
            return df, True
        except Exception as e:
            st.error(f"Error loading exercise database: {e}")
            return pd.DataFrame(), False
    else:
        st.warning("megaGymDataset.csv not found. Using a minimal exercise database.")
        return pd.DataFrame({
            'Title': ['Push-ups', 'Squats', 'Plank', 'Lunges', 'Burpees'],
            'BodyPart': ['Chest', 'Legs', 'Core', 'Legs', 'Full Body'],
            'Equipment': ['Body Only', 'Body Only', 'Body Only', 'Body Only', 'Body Only'],
            'Level': ['Beginner', 'Beginner', 'Beginner', 'Beginner', 'Intermediate'],
            'Type': ['Strength', 'Strength', 'Strength', 'Strength', 'Cardio']
        }), False

exercise_db, db_loaded = load_exercise_database()

# Enhanced session state initialization with persistence timestamps
if 'timer_running' not in st.session_state:
    st.session_state.timer_running = False
    st.session_state.timer_start_timestamp = None  # Actual timestamp for persistence
    st.session_state.timer_elapsed = 0
    st.session_state.timer_preset = "Stopwatch"
    st.session_state.timer_last_beep_second = -1

if 'workout_timer_running' not in st.session_state:
    st.session_state.workout_timer_running = False
    st.session_state.workout_timer_start_timestamp = None
    st.session_state.workout_timer_elapsed = 0

if 'interval_timer_running' not in st.session_state:
    st.session_state.interval_timer_running = False
    st.session_state.interval_timer_start_timestamp = None
    st.session_state.interval_timer_elapsed = 0
    st.session_state.current_set = 1
    st.session_state.current_phase = "WORK"
    st.session_state.current_exercise_index = 0
    st.session_state.interval_completed = False
    st.session_state.last_beep_second = -1

def format_time(seconds):
    """Format seconds to MM:SS"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"

def play_audio(audio_type):
    """Play audio with fixed system"""
    audio_script = f"""
    <script>
    (async function() {{
        try {{
            if (window.audioSystem) {{
                await window.audioSystem.playSound('{audio_type}');
            }} else {{
                console.log('Audio system not ready');
            }}
        }} catch (error) {{
            console.error('Audio playback failed:', error);
        }}
    }})();
    </script>
    """
    st.components.v1.html(audio_script, height=0)

# Main App
def main():
    st.title("FitTrack Pro")
    st.markdown("Your personal workout companion with persistent data storage")

    # Quick access section at the top
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Fixed Apple Music button
        if st.button("Open Apple Music", key="apple_music_btn"):
            st.components.v1.html("""
            <script>
            if (window.openAppleMusic) {
                window.openAppleMusic();
            } else {
                console.log('Apple Music function not available');
            }
            </script>
            """, height=0)
            st.success("Opening Apple Music...")
    
    with col2:
        if st.button("Enable Notifications"):
            st.components.v1.html("""
            <script>
            if ('Notification' in window) {
                Notification.requestPermission().then(permission => {
                    if (permission === 'granted') {
                        new Notification('FitTrack Pro', {
                            body: 'Notifications enabled! You\\'ll get timer alerts.',
                            icon: '/favicon.ico'
                        });
                    }
                });
            }
            </script>
            """, height=0)
            st.success("Notification permission requested!")
    
    with col3:
        if st.button("Keep Screen On"):
            st.components.v1.html("<script>window.requestWakeLock && window.requestWakeLock();</script>", height=0)
            st.info("Screen will stay on during timers")

    if db_loaded:
        st.success(f"Loaded {len(exercise_db)} exercises from megaGymDataset.csv")
    else:
        st.info("Using default exercise database. Place megaGymDataset.csv in the same folder as the app for the full database.")

    # Timer persistence warning
    with st.expander("Mobile Timer Important Info", expanded=False):
        st.markdown("""
        <div class="warning-box">
        <strong>Mobile Browser Limitations:</strong><br>
        • Timers may pause when screen locks or app is backgrounded<br>
        • For best results, keep screen on during workouts<br>
        • Consider using the "Keep Screen On" button above<br>
        • Audio works best with screen active and volume up<br>
        <br>
        <strong>Tips for Better Experience:</strong><br>
        • Add this page to your home screen for app-like experience<br>
        • Enable notifications for timer alerts<br>
        • Keep your phone plugged in during workouts<br>
        • Use Do Not Disturb mode to prevent interruptions
        </div>
        """, unsafe_allow_html=True)

    # Sidebar navigation
    with st.sidebar:
        st.header("Navigation")
        page = st.radio(
            "Select Page",
            ["Workout", "Cardio & Core", "Browse & Replace", "Edit Workouts",
             "Calendar", "Progress", "Guide"],
            label_visibility="collapsed"
        )

    if page == "Workout":
        workout_page()
    elif page == "Cardio & Core":
        cardio_core_page()
    elif page == "Browse & Replace":
        browse_replace_page()
    elif page == "Edit Workouts":
        edit_page()
    elif page == "Calendar":
        calendar_page()
    elif page == "Progress":
        progress_page()
    elif page == "Guide":
        guide_page()

def cardio_core_page():
    st.header("20-Minute Cardio & Core")
    st.markdown("**Light cardio warm-up followed by core interval training**")
    
    # Get core exercises
    core_exercises = get_core_exercises()
    exercise_list = core_exercises['exercise_name'].tolist()
    
    if not exercise_list:
        st.error("No core exercises found. Please add some exercises first.")
        return
    
    # Cardio instructions
    st.subheader("Part 1: Light Cardio (15 minutes)")
    st.markdown("""
    Choose one of the following light cardio activities:
    - **Walking** on treadmill or outdoors
    - **Stationary bike** at comfortable pace
    - **Elliptical** with moderate resistance
    - **Marching in place** with arm movements
    
    *Maintain a pace where you can still hold a conversation*
    """)
    
    st.divider()
    
    # Audio test section - simplified
    st.subheader("Audio Test & Setup")
    
    col1, col2 = st.columns(2)
    with col1:
        st.info("**Test sounds before starting:**")
        if st.button("Test Countdown"):
            play_audio("countdown")
        if st.button("Test Transition"):
            play_audio("transition")
        if st.button("Test Completion"):
            play_audio("completion")
    
    with col2:
        st.info("**Audio troubleshooting:**")
        st.markdown("""
        • Volume up & ringer on
        • Tap screen if no sound
        • Keep app in foreground
        • Grant notification permission
        """)
    
    st.divider()
    
    # Core interval timer section
    st.subheader("Part 2: Core Interval Training (5 minutes)")
    st.markdown("**4 sets × 1 minute work + 10 seconds rest**")
    
    # Display current exercise
    if st.session_state.current_exercise_index < len(exercise_list):
        current_exercise = exercise_list[st.session_state.current_exercise_index]
        st.markdown(f'<div class="interval-exercise">Current Exercise: {current_exercise}</div>', 
                   unsafe_allow_html=True)
    
    # Timer controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Start Interval", key="start_interval", disabled=st.session_state.interval_timer_running):
            st.session_state.interval_timer_running = True
            st.session_state.interval_timer_start_timestamp = time.time()
            st.session_state.interval_timer_elapsed = 0
            st.session_state.current_set = 1
            st.session_state.current_phase = "WORK"
            st.session_state.current_exercise_index = 0
            st.session_state.interval_completed = False
            st.session_state.last_beep_second = -1
            st.components.v1.html("<script>window.requestWakeLock && window.requestWakeLock();</script>", height=0)
            st.rerun()
    
    with col2:
        if st.button("Pause", key="pause_interval", disabled=not st.session_state.interval_timer_running):
            st.session_state.interval_timer_running = False
            st.session_state.interval_timer_elapsed = get_actual_elapsed_time('interval_timer_running', 'interval_timer_start_timestamp')
            st.rerun()
    
    with col3:
        if st.button("Reset", key="reset_interval"):
            st.session_state.interval_timer_running = False
            st.session_state.interval_timer_elapsed = 0
            st.session_state.current_set = 1
            st.session_state.current_phase = "WORK"
            st.session_state.current_exercise_index = 0
            st.session_state.interval_completed = False
            st.session_state.last_beep_second = -1
            st.rerun()
    
    # Interval timer logic - same as before but with fixed audio
    if st.session_state.interval_timer_running and not st.session_state.interval_completed:
        # Calculate actual elapsed time accounting for potential app suspension
        actual_elapsed = get_actual_elapsed_time('interval_timer_running', 'interval_timer_start_timestamp')
        st.session_state.interval_timer_elapsed = actual_elapsed
        
        total_elapsed = st.session_state.interval_timer_elapsed
        cycle_duration = 70  # 60 seconds work + 10 seconds rest
        
        if total_elapsed < 4 * 60 + 3 * 10:  # Total duration: 4 minutes work + 3 rest periods
            # Determine current set and phase
            if total_elapsed < cycle_duration:
                st.session_state.current_set = 1
                if total_elapsed < 60:
                    st.session_state.current_phase = "WORK"
                    remaining = 60 - total_elapsed
                    st.session_state.current_exercise_index = 0
                else:
                    st.session_state.current_phase = "REST"
                    remaining = cycle_duration - total_elapsed
            elif total_elapsed < 2 * cycle_duration:
                st.session_state.current_set = 2
                set_elapsed = total_elapsed - cycle_duration
                if set_elapsed < 60:
                    st.session_state.current_phase = "WORK"
                    remaining = 60 - set_elapsed
                    st.session_state.current_exercise_index = 1 % len(exercise_list)
                else:
                    st.session_state.current_phase = "REST"
                    remaining = cycle_duration - set_elapsed
            elif total_elapsed < 3 * cycle_duration:
                st.session_state.current_set = 3
                set_elapsed = total_elapsed - 2 * cycle_duration
                if set_elapsed < 60:
                    st.session_state.current_phase = "WORK"
                    remaining = 60 - set_elapsed
                    st.session_state.current_exercise_index = 2 % len(exercise_list)
                else:
                    st.session_state.current_phase = "REST"
                    remaining = cycle_duration - set_elapsed
            else:
                st.session_state.current_set = 4
                set_elapsed = total_elapsed - 3 * cycle_duration
                if set_elapsed < 60:
                    st.session_state.current_phase = "WORK"
                    remaining = 60 - set_elapsed
                    st.session_state.current_exercise_index = 3 % len(exercise_list)
                else:
                    st.session_state.interval_completed = True
                    st.session_state.interval_timer_running = False
                    remaining = 0
        else:
            st.session_state.interval_completed = True
            st.session_state.interval_timer_running = False
            remaining = 0
        
        # Display current status and timer
        if not st.session_state.interval_completed:
            phase_class = "work-status" if st.session_state.current_phase == "WORK" else "rest-status"
            st.markdown(f'<div class="interval-status {phase_class}">Set {st.session_state.current_set}/4 - {st.session_state.current_phase}</div>', 
                       unsafe_allow_html=True)
            
            if st.session_state.current_phase == "WORK":
                current_exercise = exercise_list[st.session_state.current_exercise_index]
                st.markdown(f'<div class="interval-exercise">Current Exercise: {current_exercise}</div>', 
                           unsafe_allow_html=True)
            
            timer_class = "work-timer" if st.session_state.current_phase == "WORK" else "rest-timer"
            remaining_time = max(0, remaining)
            st.markdown(f'<div class="interval-timer-display {timer_class}">{format_time(remaining_time)}</div>', 
                       unsafe_allow_html=True)
            
            # Audio cues - fixed
            remaining_seconds = int(remaining_time)
            if remaining_seconds <= 10 and remaining_seconds > 0 and remaining_seconds != st.session_state.last_beep_second:
                play_audio("countdown")
                st.session_state.last_beep_second = remaining_seconds
            
            if remaining_seconds == 0 and st.session_state.last_beep_second != 0:
                if st.session_state.current_set == 4 and st.session_state.current_phase == "WORK":
                    play_audio("completion")
                else:
                    play_audio("transition")
                st.session_state.last_beep_second = 0
            
            time.sleep(0.1)
            st.rerun()
    
    elif st.session_state.interval_completed:
        st.success("Core interval workout complete! Great job!")
        st.markdown('<div class="interval-timer-display">COMPLETE!</div>', unsafe_allow_html=True)
        
        if st.button("Log Workout", type="primary"):
            log_workout("Cardio & Core", 1, "20 minutes")
            st.success("Workout logged!")
            st.rerun()
    
    else:
        st.markdown('<div class="interval-status work-status">Ready to Start - Set 1/4 - WORK</div>', 
                   unsafe_allow_html=True)
        if exercise_list:
            st.markdown(f'<div class="interval-exercise">First Exercise: {exercise_list[0]}</div>', 
                       unsafe_allow_html=True)
        st.markdown('<div class="interval-timer-display">01:00</div>', unsafe_allow_html=True)
    
    # Rest of the function remains the same (core exercise management)
    st.divider()
    
    # Core exercise management
    st.subheader("Manage Core Exercises")
    
    # Display current exercises
    st.write("**Current Core Exercises:**")
    for idx, row in core_exercises.iterrows():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"{row['exercise_order'] + 1}. {row['exercise_name']}")
        with col2:
            if st.button("Delete", key=f"delete_core_{row['id']}"):
                delete_core_exercise(row['id'])
                st.rerun()
    
    st.divider()
    
    # Browse and add from exercise database
    st.write("**Add from Exercise Database:**")
    
    # Filters for exercise database
    col1, col2, col3 = st.columns(3)
    
    with col1:
        body_parts = ["All"] + sorted(exercise_db['BodyPart'].dropna().unique().tolist())
        selected_body_part = st.selectbox("Body Part", body_parts, key="core_body_part")
    
    with col2:
        equipment = ["All"] + sorted(exercise_db['Equipment'].dropna().unique().tolist())
        selected_equipment = st.selectbox("Equipment", equipment, key="core_equipment")
    
    with col3:
        search_term = st.text_input("Search exercises...", key="core_search")
    
    # Filter the database
    filtered_df = exercise_db.copy()
    
    if selected_body_part != "All":
        filtered_df = filtered_df[filtered_df['BodyPart'] == selected_body_part]
    
    if selected_equipment != "All":
        filtered_df = filtered_df[filtered_df['Equipment'] == selected_equipment]
    
    if search_term:
        filtered_df = filtered_df[filtered_df['Title'].str.contains(search_term, case=False, na=False)]
    
    # Display exercises
    st.write(f"Found {len(filtered_df)} exercises")
    
    # Create a scrollable container for exercise database
    with st.container():
        for _, exercise in filtered_df.head(20).iterrows():
            with st.container():
                st.markdown('<div class="exercise-db-card">', unsafe_allow_html=True)
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**{exercise.get('Title', 'Unknown Exercise')}**")
                    st.write(f"Body Part: {exercise.get('BodyPart', 'N/A')} | "
                            f"Equipment: {exercise.get('Equipment', 'N/A')} | "
                            f"Level: {exercise.get('Level', 'N/A')}")
                
                with col2:
                    if st.button("Add to Core", key=f"add_core_db_{exercise.name}"):
                        add_core_exercise(exercise.get('Title', ''))
                        st.success(f"Added '{exercise.get('Title', '')}' to core exercises")
                        st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)
    
    st.divider()
    
    # Manual add option
    st.write("**Add Custom Exercise:**")
    col1, col2 = st.columns([3, 1])
    with col1:
        new_exercise = st.text_input("Exercise name", key="new_core_exercise")
    with col2:
        if st.button("Add", key="add_core_exercise"):
            if new_exercise:
                add_core_exercise(new_exercise)
                st.success(f"Added {new_exercise}")
                st.rerun()

def workout_page():
    # Timer section with persistence
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Set Timer")

        # Timer preset
        preset_options = {
            "Stopwatch": 0,
            "30s": 30,
            "45s": 45,
            "1min": 60,
            "90s": 90,
            "2min": 120,
            "3min": 180,
            "5min": 300
        }

        selected_preset = st.selectbox(
            "Timer Preset",
            options=list(preset_options.keys()),
            index=0
        )

        if selected_preset != st.session_state.timer_preset:
            st.session_state.timer_preset = selected_preset
            st.session_state.timer_elapsed = 0
            st.session_state.timer_running = False
            st.session_state.timer_last_beep_second = -1

        timer_col1, timer_col2, timer_col3 = st.columns(3)

        with timer_col1:
            if st.button("Start", key="start_timer", disabled=st.session_state.timer_running):
                st.session_state.timer_running = True
                st.session_state.timer_start_timestamp = time.time() - st.session_state.timer_elapsed
                st.session_state.timer_last_beep_second = -1
                st.components.v1.html("<script>window.requestWakeLock && window.requestWakeLock();</script>", height=0)
                st.rerun()

        with timer_col2:
            if st.button("Pause", key="pause_timer", disabled=not st.session_state.timer_running):
                st.session_state.timer_running = False
                st.session_state.timer_elapsed = get_actual_elapsed_time('timer_running', 'timer_start_timestamp')
                st.rerun()

        with timer_col3:
            if st.button("Reset", key="reset_timer"):
                st.session_state.timer_running = False
                st.session_state.timer_elapsed = 0
                st.session_state.timer_last_beep_second = -1
                st.rerun()

        # Display timer with persistence handling
        if st.session_state.timer_running:
            actual_elapsed = get_actual_elapsed_time('timer_running', 'timer_start_timestamp')
            st.session_state.timer_elapsed = actual_elapsed

            # Handle countdown timers
            if selected_preset != "Stopwatch":
                remaining = preset_options[selected_preset] - st.session_state.timer_elapsed
                if remaining <= 0:
                    st.session_state.timer_running = False
                    st.markdown('<div class="timer-display">00:00 Complete</div>', unsafe_allow_html=True)
                    play_audio("timer")
                else:
                    st.markdown(f'<div class="timer-display">{format_time(remaining)}</div>', unsafe_allow_html=True)
                    
                    # Audio cues - fixed
                    remaining_seconds = int(remaining)
                    if remaining_seconds <= 10 and remaining_seconds > 0 and remaining_seconds != st.session_state.timer_last_beep_second:
                        play_audio("countdown")
                        st.session_state.timer_last_beep_second = remaining_seconds
                    
                    if remaining_seconds == 0 and st.session_state.timer_last_beep_second != 0:
                        play_audio("timer")
                        st.session_state.timer_last_beep_second = 0
                    
                    time.sleep(0.1)
                    st.rerun()
            else:
                st.markdown(f'<div class="timer-display">{format_time(st.session_state.timer_elapsed)}</div>', unsafe_allow_html=True)
                time.sleep(0.1)
                st.rerun()
        else:
            if selected_preset != "Stopwatch" and st.session_state.timer_elapsed == 0:
                st.markdown(f'<div class="timer-display">{format_time(preset_options[selected_preset])}</div>',
                          unsafe_allow_html=True)
            else:
                display_time = st.session_state.timer_elapsed
                if selected_preset != "Stopwatch":
                    display_time = max(0, preset_options[selected_preset] - st.session_state.timer_elapsed)
                st.markdown(f'<div class="timer-display">{format_time(display_time)}</div>', unsafe_allow_html=True)

    with col2:
        st.subheader("Workout Timer")

        timer_col1, timer_col2, timer_col3 = st.columns(3)
        with timer_col1:
            if st.button("Start", key="start_workout_timer", disabled=st.session_state.workout_timer_running):
                st.session_state.workout_timer_running = True
                st.session_state.workout_timer_start_timestamp = time.time() - st.session_state.workout_timer_elapsed
                st.components.v1.html("<script>window.requestWakeLock && window.requestWakeLock();</script>", height=0)
                st.rerun()

        with timer_col2:
            if st.button("Pause", key="pause_workout_timer", disabled=not st.session_state.workout_timer_running):
                st.session_state.workout_timer_running = False
                st.session_state.workout_timer_elapsed = get_actual_elapsed_time('workout_timer_running', 'workout_timer_start_timestamp')
                st.rerun()

        with timer_col3:
            if st.button("Reset", key="reset_workout_timer"):
                st.session_state.workout_timer_running = False
                st.session_state.workout_timer_elapsed = 0
                st.rerun()

        # Display workout timer with persistence
        if st.session_state.workout_timer_running:
            actual_elapsed = get_actual_elapsed_time('workout_timer_running', 'workout_timer_start_timestamp')
            st.session_state.workout_timer_elapsed = actual_elapsed
            st.markdown(f'<div class="timer-display">{format_time(st.session_state.workout_timer_elapsed)}</div>',
                       unsafe_allow_html=True)
            time.sleep(0.1)
            st.rerun()
        else:
            st.markdown(f'<div class="timer-display">{format_time(st.session_state.workout_timer_elapsed)}</div>',
                       unsafe_allow_html=True)

    # Rest of workout page remains the same
    st.divider()

    # Workout selection
    selected_day = st.selectbox(
        "Select Workout Day",
        ["dayA", "dayB", "dayC"],
        format_func=lambda x: {"dayA": "Day A - Full Body Focus",
                               "dayB": "Day B - Strength Focus",
                               "dayC": "Day C - Mobility Focus"}[x]
    )

    # Get workouts and completion status
    workouts = get_workouts(selected_day)
    completion = get_completion_status(selected_day)

    # Progress bar
    completed_count = sum(1 for i in range(len(workouts)) if completion.get(i, False))
    progress = completed_count / len(workouts) if len(workouts) > 0 else 0

    st.progress(progress)
    st.write(f"**{int(progress * 100)}% Complete** ({completed_count}/{len(workouts)})")

    # Exercise list
    for idx, row in workouts.iterrows():
        is_completed = completion.get(idx, False)

        with st.container():
            st.markdown(
                f'<div class="workout-card {"completed-card" if is_completed else ""}">',
                unsafe_allow_html=True
            )

            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"### {row['exercise_name']}")
                st.write(f"**{row['sets']} x {row['reps']}**")
                st.write(f"_{row['notes']}_")

            with col2:
                if st.button(
                    "Completed" if is_completed else "Mark Complete",
                    key=f"complete_{selected_day}_{idx}",
                    type="primary" if not is_completed else "secondary"
                ):
                    toggle_exercise_completion(selected_day, idx, not is_completed)
                    st.rerun()

                if st.button("Reset", key=f"reset_{selected_day}_{idx}"):
                    toggle_exercise_completion(selected_day, idx, False)
                    st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

    # Celebration section
    if progress == 1:
        st.success("Workout Complete! Excellent work!")
        play_audio("completion")
        if st.button("Log Workout & Reset", type="primary"):
            # Log the workout
            log_workout(selected_day, len(workouts), format_time(st.session_state.workout_timer_elapsed))

            # Reset completion for this day
            conn = sqlite3.connect('fittrack.db')
            c = conn.cursor()
            today = datetime.now().strftime("%Y-%m-%d")
            c.execute("DELETE FROM exercise_completion WHERE day = ? AND date = ?", (selected_day, today))
            conn.commit()
            conn.close()

            # Reset workout timer
            st.session_state.workout_timer_elapsed = 0
            st.session_state.workout_timer_running = False

            st.rerun()

def browse_replace_page():
    st.header("Browse & Replace Exercises")

    # Get current workout exercises for replacement
    col1, col2 = st.columns([2, 1])

    with col1:
        selected_day = st.selectbox(
            "Select Day for Replacement",
            ["dayA", "dayB", "dayC"],
            format_func=lambda x: {"dayA": "Day A", "dayB": "Day B", "dayC": "Day C"}[x],
            key="browse_day"
        )

    with col2:
        workouts = get_workouts(selected_day)
        exercise_to_replace = st.selectbox(
            "Exercise to Replace",
            options=[(row['id'], row['exercise_name']) for _, row in workouts.iterrows()],
            format_func=lambda x: x[1]
        )

    st.divider()

    # Filters
    col1, col2, col3 = st.columns(3)

    with col1:
        body_parts = ["All"] + sorted(exercise_db['BodyPart'].dropna().unique().tolist())
        selected_body_part = st.selectbox("Body Part", body_parts)

    with col2:
        equipment = ["All"] + sorted(exercise_db['Equipment'].dropna().unique().tolist())
        selected_equipment = st.selectbox("Equipment", equipment)

    with col3:
        search_term = st.text_input("Search exercises...")

    # Filter the database
    filtered_df = exercise_db.copy()

    if selected_body_part != "All":
        filtered_df = filtered_df[filtered_df['BodyPart'] == selected_body_part]

    if selected_equipment != "All":
        filtered_df = filtered_df[filtered_df['Equipment'] == selected_equipment]

    if search_term:
        filtered_df = filtered_df[filtered_df['Title'].str.contains(search_term, case=False, na=False)]

    # Display exercises
    st.write(f"Found {len(filtered_df)} exercises")

    # Create a scrollable container
    with st.container():
        for _, exercise in filtered_df.head(50).iterrows():
            with st.container():
                st.markdown('<div class="exercise-db-card">', unsafe_allow_html=True)

                col1, col2 = st.columns([3, 1])

                with col1:
                    st.markdown(f"**{exercise.get('Title', 'Unknown Exercise')}**")
                    st.write(f"Body Part: {exercise.get('BodyPart', 'N/A')} | "
                            f"Equipment: {exercise.get('Equipment', 'N/A')} | "
                            f"Level: {exercise.get('Level', 'N/A')}")

                with col2:
                    if st.button("Replace", key=f"replace_{exercise.name}"):
                        if exercise_to_replace:
                            notes = f"{exercise.get('Type', 'Exercise')} - {exercise.get('Level', 'All levels')}"
                            replace_exercise(exercise_to_replace[0], exercise.get('Title', ''), notes)
                            st.success(f"Replaced '{exercise_to_replace[1]}' with '{exercise.get('Title', '')}'")
                            st.rerun()

                st.markdown('</div>', unsafe_allow_html=True)

def edit_page():
    st.header("Edit Workouts")

    selected_day = st.selectbox(
        "Select Day to Edit",
        ["dayA", "dayB", "dayC"],
        format_func=lambda x: {"dayA": "Day A", "dayB": "Day B", "dayC": "Day C"}[x]
    )

    workouts = get_workouts(selected_day)

    # Display current exercises for reordering and deletion
    st.subheader("Current Exercises")

    for idx, row in workouts.iterrows():
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

            with col1:
                st.write(f"**{row['exercise_order'] + 1}. {row['exercise_name']}**")
                st.write(f"{row['sets']} sets x {row['reps']} - {row['notes']}")

            with col2:
                # Up button
                if row['exercise_order'] > 0:
                    if st.button("Up", key=f"up_{row['id']}"):
                        update_exercise_order(selected_day, row['id'], row['exercise_order'] - 1)
                        st.rerun()

            with col3:
                # Down button
                if row['exercise_order'] < len(workouts) - 1:
                    if st.button("Down", key=f"down_{row['id']}"):
                        update_exercise_order(selected_day, row['id'], row['exercise_order'] + 1)
                        st.rerun()

            with col4:
                # Delete button
                if st.button("Delete", key=f"delete_{row['id']}"):
                    delete_exercise(row['id'])
                    st.rerun()
            st.divider()

    # Add new exercise
    st.subheader("Add New Exercise")

    with st.form("add_exercise_form"):
        col1, col2 = st.columns(2)
        with col1:
            new_name = st.text_input("Exercise Name")
            new_notes = st.text_input("Notes", value="Focus on proper form")
        with col2:
            new_sets = st.number_input("Sets", min_value=1, max_value=10, value=3)
            new_reps = st.text_input("Reps", value="10-12")

        submitted = st.form_submit_button("Add Exercise")
        if submitted:
            if new_name:
                add_exercise(selected_day, new_name, new_sets, new_reps, new_notes)
                st.success(f"Added {new_name} to {selected_day}")
                st.rerun()

    # Replace exercise manually
    st.subheader("Replace Exercise Manually")

    with st.form("replace_exercise_form"):
        exercise_to_replace_id = st.selectbox(
            "Exercise to Replace",
            options=[(row['id'], f"{row['exercise_order'] + 1}. {row['exercise_name']}") for _, row in workouts.iterrows()],
            format_func=lambda x: x[1]
        )[0]

        st.write("Enter new exercise details:")
        col1, col2 = st.columns(2)
        with col1:
            replace_name = st.text_input("New Exercise Name")
            replace_notes = st.text_input("New Notes")
        with col2:
            replace_sets = st.number_input("New Sets", min_value=1, max_value=10, value=3)
            replace_reps = st.text_input("New Reps", value="10-12")

        replace_submitted = st.form_submit_button("Replace Exercise")
        if replace_submitted:
            if replace_name:
                replace_exercise_manually(exercise_to_replace_id, replace_name, replace_sets, replace_reps, replace_notes)
                st.success(f"Exercise replaced successfully in {selected_day}")
                st.rerun()
            else:
                st.error("New exercise name cannot be empty.")

def calendar_page():
    st.header("Workout Calendar")

    # Get workout history
    history = get_workout_history(limit=365)
    workout_dates = set(history['date'].tolist()) if not history.empty else set()

    # Month navigation
    today = datetime.now()
    if 'display_month' not in st.session_state:
        st.session_state.display_month = today.month
    if 'display_year' not in st.session_state:
        st.session_state.display_year = today.year

    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if st.button("Previous"):
            st.session_state.display_month -= 1
            if st.session_state.display_month == 0:
                st.session_state.display_month = 12
                st.session_state.display_year -= 1
            st.rerun()

    with col3:
        if st.button("Next"):
            st.session_state.display_month += 1
            if st.session_state.display_month == 13:
                st.session_state.display_month = 1
                st.session_state.display_year += 1
            st.rerun()

    display_year = st.session_state.display_year
    display_month = st.session_state.display_month
    display_date_obj = datetime(display_year, display_month, 1)

    with col2:
        st.markdown(f"<h2 style='text-align: center'>{display_date_obj.strftime('%B %Y')}</h2>", unsafe_allow_html=True)

    # Create calendar
    cal = calendar.monthcalendar(display_year, display_month)

    # Day headers
    days_header = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    cols = st.columns(7)
    for i, day_name in enumerate(days_header):
        cols[i].markdown(f"<div style='text-align: center; font-weight: bold;'>{day_name}</div>", unsafe_allow_html=True)

    # Calendar days
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].markdown('<div class="calendar-day"></div>', unsafe_allow_html=True)
            else:
                date_str = f"{display_year:04d}-{display_month:02d}-{day:02d}"
                is_today = (display_year == today.year and display_month == today.month and day == today.day)
                is_workout = date_str in workout_dates

                style_class = "calendar-day"
                if is_today:
                    style_class += " today"
                elif is_workout:
                    style_class += " workout-day"

                cols[i].markdown(f'<div class="{style_class}">{day}</div>', unsafe_allow_html=True)

def progress_page():
    st.header("Your Progress")

    # Get stats
    total, this_week, streak = get_stats()

    # Display stats
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('<div class="stat-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-value">{total}</div>', unsafe_allow_html=True)
        st.markdown('<div class="stat-label">Total Workouts</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="stat-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-value">{this_week}</div>', unsafe_allow_html=True)
        st.markdown('<div class="stat-label">This Week</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="stat-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="stat-value">{streak}</div>', unsafe_allow_html=True)
        st.markdown('<div class="stat-label">Day Streak</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Workout history
    st.subheader("Recent Workout History")

    history = get_workout_history(limit=20)

    if not history.empty:
        for _, workout in history.iterrows():
            day_name = {"dayA": "Day A", "dayB": "Day B", "dayC": "Day C", "Cardio & Core": "Cardio & Core"}.get(workout['day'], workout['day'])
            st.write(f"**{day_name}** - {workout['date']}")
            st.write(f"Completed {workout['exercises_completed']} exercises in {workout.get('duration', 'N/A')}")
            st.divider()
    else:
        st.info("No workout history yet. Complete your first workout to see it here!")

    # Export data option
    if st.button("Export Workout Data"):
        conn = sqlite3.connect('fittrack.db')
        all_history = pd.read_sql_query("SELECT * FROM workout_history ORDER BY timestamp DESC", conn)
        conn.close()

        csv = all_history.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"fittrack_export_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

def guide_page():
    st.header("Workout Guide")

    st.markdown("""
    ### Program Overview
    This 4-component fitness program focuses on comprehensive training with emphasis on proper form and progressive overload.

    #### Day A - Full Body Focus
    - Compound movements for overall strength
    - Balanced push/pull exercises
    - Core stability work

    #### Day B - Strength Focus
    - Higher intensity strength training
    - Unilateral movements for balance
    - Targeted muscle group work

    #### Day C - Mobility Focus
    - Movement quality and flexibility
    - Active recovery exercises
    - Corrective movement patterns

    #### Cardio & Core
    - 15 minutes of light cardio for cardiovascular health
    - 5 minutes of interval core training for functional strength
    - Customizable core exercises to target your specific needs

    ### General Guidelines
    - Focus on proper form over weight
    - Rest 45-60 seconds between sets
    - Progress gradually week to week
    - Listen to your body and adjust as needed

    ### Features of FitTrack Pro
    - **Persistent Storage**: All your workouts, completions, and history are saved in a SQLite database
    - **Exercise Database**: Access to thousands of exercises (when megaGymDataset.csv is loaded)
    - **Smart Replacements**: Easily swap exercises while maintaining your workout structure
    - **Progress Tracking**: Monitor your consistency with detailed statistics
    - **Flexible Editing**: Add, remove, or reorder exercises as needed
    - **Interval Timer**: Custom interval timer for core workouts with work/rest cycles
    - **Mobile Optimized**: Enhanced audio system and persistence features for mobile use

    ### Mobile App Tips
    1. **Add to Home Screen**: Save this page to your phone's home screen for quick access
    2. **Enable Notifications**: Allow notifications for timer alerts
    3. **Keep Screen Active**: Use the "Keep Screen On" button during workouts
    4. **Volume Up**: Ensure your volume is up and ringer is on for audio cues
    5. **Stay in App**: Keep the app in foreground for best timer performance

    ### Tips for Success
    1. **Consistency is key** - Aim for 3-4 workouts per week
    2. **Track your progress** - Use the calendar to monitor consistency
    3. **Progressive overload** - Gradually increase weight or reps
    4. **Proper nutrition** - Support your training with good nutrition
    5. **Rest and recovery** - Allow adequate rest between sessions
    6. **Mix it up** - Use all workout types for balanced fitness
    """)

if __name__ == "__main__":
    main()