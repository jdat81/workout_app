import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import time
import calendar
import json
import base64
import os

# =========================
# CONFIG
# =========================
APP_DB = "fittrack.db"
EXERCISE_CSV_PRIMARY = Path("/Users/johndattoma/Downloads/workout app/megaGymDataset.csv")
EXERCISE_CSV_FALLBACK = Path("megaGymDataset.csv")

st.set_page_config(
    page_title="FitTrack Pro",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================
# GLOBAL CSS + JS (Audio, Wake Lock, Apple Music, Sticky Header)
# =========================
st.markdown("""
<style>
:root{
  --bg:#0b1020; --card:#0f1530; --muted:#9aa3b2; --text:#e6ebf4; --brand:#7aa2ff; --brand-2:#22c55e; --warn:#f59e0b; --ok:#10b981;
  --border: #1f2747;
}
html,body,.main{
  background: var(--bg);
  color: var(--text);
  font-family: -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Inter,system-ui,sans-serif;
}
.block-container{padding-top:1rem; padding-bottom:3rem;}
h1,h2,h3{letter-spacing:.2px}
.stTabs [data-baseweb="tab-list"]{gap:.5rem}
.stTabs [data-baseweb="tab"]{
  background: var(--card); color: var(--text); border: 1px solid var(--border);
  border-radius:10px; padding:.6rem 1rem; font-weight:600
}
.stTabs [aria-selected="true"]{outline: 2px solid var(--brand); color: white}
.card{
  background: var(--card); border:1px solid var(--border);
  border-radius:16px; padding:1.0rem; box-shadow: 0 10px 30px rgba(0,0,0,.25)
}
.btn .stButton>button{
  width:100%; height:3rem; border-radius:12px; border:1px solid var(--border);
  background:linear-gradient(180deg,#1a2346,#0f1735); color:#fff; font-weight:600
}
.btn .stButton>button:hover{filter:brightness(1.15)}
.stat{
  text-align:center; border-radius:16px; padding:1rem; background:var(--card); border:1px solid var(--border)
}
.stat .value{font-size:2.2rem; font-weight:800; color: var(--brand)}
.stat .label{color: var(--muted)}
.timer{
  font-variant-numeric: tabular-nums; text-align:center; font-size:4rem; font-weight:800;
  padding:1rem 1.25rem; border-radius:14px; background:#0b1433; border:1px dashed var(--border)
}
.timer.work{border-color: var(--ok); box-shadow: inset 0 0 0 1px rgba(16,185,129,.25)}
.timer.rest{border-color: var(--warn); box-shadow: inset 0 0 0 1px rgba(245,158,11,.25)}
.badge{display:inline-block; padding:.35rem .6rem; border-radius:999px; font-weight:700; font-size:.85rem}
.badge.ok{background:rgba(16,185,129,.15); color:#86efac; border:1px solid rgba(16,185,129,.35)}
.badge.warn{background:rgba(245,158,11,.15); color:#fde68a; border:1px solid rgba(245,158,11,.35)}
.progress-wrap{background:#0b1433;border-radius:12px;border:1px solid var(--border);padding:.3rem}
.progress-bar{height:12px;border-radius:8px;background:linear-gradient(90deg,var(--brand),#8b5cf6)}
.exercise{border:1px solid var(--border); border-radius:12px; padding:1rem; background:#0a1230}
.exercise.done{background:rgba(16,185,129,.12); border-color:rgba(16,185,129,.35)}
.calendar-day{padding:.6rem; text-align:center; border-radius:8px; border:1px solid var(--border); background:#0a1230}
.calendar-day.today{outline:2px solid var(--brand)}
.calendar-day.workout{outline:2px solid var(--ok)}
hr{border-color:var(--border)}
.small{color:var(--muted); font-size:.95rem}
.success{color:#86efac}
.warn{color:#fde68a}
</style>

<script>
// ----- Simple Audio System with WebAudio + vibration fallback -----
class SimpleAudioSystem {
  constructor(){
    this.audioContext = null;
    this.initialized = false;
  }
  async init(){
    if(this.initialized) return true;
    try{
      const Ctx = window.AudioContext || window.webkitAudioContext;
      if(Ctx){
        this.audioContext = new Ctx();
        if(this.audioContext.state === 'suspended'){
          await this.audioContext.resume();
        }
        this.initialized = true;
        console.log('Audio initialized');
        return true;
      }
    }catch(e){ console.log('WebAudio not available', e); }
    this.initialized = true;
    return false;
  }
  async play(type){
    if(!this.initialized) await this.init();
    if(this.audioContext && this.audioContext.state === 'running'){
      this._beep(type);
    } else {
      this._fallback(type);
    }
  }
  _beep(type){
    const map = { countdown:820, transition:980, completion:1200, timer:900 };
    const dur = type==='completion'?0.35:0.2;
    const osc = this.audioContext.createOscillator();
    const gain = this.audioContext.createGain();
    osc.connect(gain); gain.connect(this.audioContext.destination);
    osc.frequency.value = map[type] || 800;
    osc.type = 'sine';
    const t = this.audioContext.currentTime;
    gain.gain.setValueAtTime(0, t);
    gain.gain.linearRampToValueAtTime(0.35, t+.01);
    gain.gain.exponentialRampToValueAtTime(0.001, t+dur);
    osc.start(t); osc.stop(t+dur);
    if(type==='completion'){
      setTimeout(()=>this._beep('completion'), 260);
    }
  }
  _fallback(type){
    if('vibrate' in navigator){
      const pat = {countdown:[80], transition:[140], completion:[80,80,80], timer:[120]};
      navigator.vibrate(pat[type] || [80]);
    }
    document.body.style.outline = '3px solid rgba(122,162,255,.65)';
    setTimeout(()=>{document.body.style.outline='none';}, 180);
  }
}
window.__fitAudio = new SimpleAudioSystem();
document.addEventListener('click', ()=>window.__fitAudio.init(), {once:true});
document.addEventListener('touchstart', ()=>window.__fitAudio.init(), {once:true});

window.playCountdownBeep = () => window.__fitAudio.play('countdown');
window.playTransitionBeep = () => window.__fitAudio.play('transition');
window.playTimerBeep = () => window.__fitAudio.play('timer');
window.playCompletionBeep = () => window.__fitAudio.play('completion');

window.openAppleMusic = () => {
  const isiOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
  const isMac = navigator.platform.indexOf('Mac')>-1;
  if(isiOS){ window.location.href='music://'; setTimeout(()=>{ window.open('https://apps.apple.com/app/apple-music/id1108187390','_blank'); },1500); }
  else if(isMac){ window.location.href='music://'; }
  else { window.open('https://music.apple.com','_blank'); }
};
window.requestWakeLock = async() => {
  try{
    if('wakeLock' in navigator){
      const wl = await navigator.wakeLock.request('screen');
      wl.addEventListener('release', ()=>console.log('Wake lock released'));
      return wl;
    }
  }catch(e){ console.log('WakeLock fail', e); }
  return null;
};
</script>
""", unsafe_allow_html=True)

# =========================
# DB INIT & HELPERS
# =========================
def db_conn():
    return sqlite3.connect(APP_DB)

def init_database():
    conn = db_conn()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS workouts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        day TEXT NOT NULL,
        exercise_name TEXT NOT NULL,
        sets INTEGER,
        reps TEXT,
        notes TEXT,
        exercise_order INTEGER
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS workout_history(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        day TEXT NOT NULL,
        exercises_completed INTEGER,
        duration TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS exercise_completion(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        day TEXT NOT NULL,
        exercise_index INTEGER,
        completed BOOLEAN,
        date TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS core_exercises(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exercise_name TEXT NOT NULL,
        exercise_order INTEGER
    )""")
    # NEW: user profile
    c.execute("""CREATE TABLE IF NOT EXISTS user_profile(
        id INTEGER PRIMARY KEY CHECK (id=1),
        name TEXT,
        units TEXT,
        height_cm REAL,
        weight_kg REAL,
        goal TEXT,
        theme TEXT,
        created_at TEXT,
        updated_at TEXT
    )""")
    conn.commit()
    # seed defaults
    c.execute("SELECT COUNT(*) FROM workouts")
    if c.fetchone()[0] == 0:
        populate_default_workouts(conn)
    c.execute("SELECT COUNT(*) FROM core_exercises")
    if c.fetchone()[0] == 0:
        populate_default_core_exercises(conn)
    conn.close()

def populate_default_workouts(conn):
    default = {
        "dayA":[
            ("Dynamic Warm-up",1,"5-8 min","Light cardio + mobility"),
            ("Seated Machine Chest Press",3,"10-12","Smooth tempo"),
            ("Chest-Supported Cable Row",3,"10-12","Squeeze back"),
            ("Reverse Lunges",3,"10-12 each","Upright torso"),
            ("Seated Calf Raise",2,"12-15","Pause at top"),
            ("Seated Machine Shoulder Press",3,"10-12","Full ROM"),
            ("Wall Sit",3,"30-45s","Flat back"),
            ("Pallof Press",2,"10 each","Resist rotation"),
            ("Cool-down",1,"5-10 min","Stretch major groups")
        ],
        "dayB":[
            ("Movement Prep",1,"5-8 min","Mobility + activation"),
            ("Seated Dumbbell Press",3,"10-12","Controlled"),
            ("Machine Lat Pulldown",3,"10-12","To chest"),
            ("Forward Lunges",3,"10-12 each","Stable knee"),
            ("Hip Adduction Machine",2,"12-15","Pause"),
            ("Seated Lateral Raise",2,"12-15","To shoulder"),
            ("Face Pull",2,"12-15","ER and scap"),
            ("Triceps Pushdown",2,"12-15","Lockout"),
            ("Seated Bicep Curl",2,"12-15","No swing"),
            ("Modified Plank",2,"30-45s","Neutral spine")
        ],
        "dayC":[
            ("Gentle Movement",1,"5-8 min","Walk or easy cardio"),
            ("Pec Deck Machine",3,"12-15","Smooth arc"),
            ("Seated Cable Row",3,"10-12","Posture"),
            ("Lateral Lunges",3,"10-12 each","Sit back"),
            ("Standing Calf Raise",2,"15-20","Controlled"),
            ("Seated Cable Fly",3,"12-15","Wide arc"),
            ("Reverse Pec Deck",2,"12-15","Scaps"),
            ("Curtsy Lunges",3,"10-12 each","Control"),
            ("Seated Knee Raises",2,"10-12","Core tight"),
            ("Mobility Flow",1,"10 min","Full body")
        ]
    }
    c = conn.cursor()
    for day, exs in default.items():
        for i,(n,s,r,notes) in enumerate(exs):
            c.execute("INSERT INTO workouts(day,exercise_name,sets,reps,notes,exercise_order) VALUES(?,?,?,?,?,?)",
                      (day,n,s,r,notes,i))
    conn.commit()

def populate_default_core_exercises(conn):
    core = ["Bird-Dogs","Plank","Right Side Plank","Left Side Plank"]
    c = conn.cursor()
    for i, name in enumerate(core):
        c.execute("INSERT INTO core_exercises(exercise_name,exercise_order) VALUES(?,?)",(name,i))
    conn.commit()

# CRUD helpers
def get_workouts(day):
    conn = db_conn()
    df = pd.read_sql_query("SELECT * FROM workouts WHERE day=? ORDER BY exercise_order", conn, params=(day,))
    conn.close()
    return df

def get_core_exercises():
    conn = db_conn()
    df = pd.read_sql_query("SELECT * FROM core_exercises ORDER BY exercise_order", conn)
    conn.close()
    return df

def add_core_exercise(name):
    conn = db_conn()
    c = conn.cursor()
    c.execute("SELECT MAX(exercise_order) FROM core_exercises")
    maxo = c.fetchone()[0] or -1
    c.execute("INSERT INTO core_exercises(exercise_name,exercise_order) VALUES(?,?)", (name, maxo+1))
    conn.commit(); conn.close()

def delete_core_exercise(eid):
    conn = db_conn(); conn.execute("DELETE FROM core_exercises WHERE id=?", (eid,)); conn.commit(); conn.close()

def get_completion_status(day):
    conn = db_conn()
    today = datetime.now().strftime("%Y-%m-%d")
    df = pd.read_sql_query("SELECT exercise_index,completed FROM exercise_completion WHERE day=? AND date=?",
                           conn, params=(day,today))
    conn.close()
    return {int(r['exercise_index']): bool(r['completed']) for _,r in df.iterrows()}

def toggle_exercise_completion(day, idx, completed):
    conn = db_conn(); c=conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("SELECT id FROM exercise_completion WHERE day=? AND exercise_index=? AND date=?",(day,idx,today))
    row = c.fetchone()
    if row: c.execute("UPDATE exercise_completion SET completed=? WHERE id=?", (completed,row[0]))
    else:   c.execute("INSERT INTO exercise_completion(day,exercise_index,completed,date) VALUES(?,?,?,?)",
                      (day,idx,completed,today))
    conn.commit(); conn.close()

def log_workout(day, done, duration):
    conn = db_conn()
    conn.execute("INSERT INTO workout_history(date,day,exercises_completed,duration) VALUES(?,?,?,?)",
                 (datetime.now().strftime("%Y-%m-%d"),day,done,duration))
    conn.commit(); conn.close()

def get_workout_history(limit=100):
    conn = db_conn()
    df = pd.read_sql_query("SELECT * FROM workout_history ORDER BY timestamp DESC LIMIT ?", conn, params=(limit,))
    conn.close()
    return df

def get_stats():
    conn = db_conn(); c=conn.cursor()
    c.execute("SELECT COUNT(*) FROM workout_history"); total = c.fetchone()[0]
    week_ago = (datetime.now()-timedelta(days=7)).strftime("%Y-%m-%d")
    c.execute("SELECT COUNT(*) FROM workout_history WHERE date>=?", (week_ago,)); this_week = c.fetchone()[0]
    c.execute("SELECT DISTINCT date FROM workout_history ORDER BY date DESC"); dates = [d[0] for d in c.fetchall()]
    streak = 0
    if dates:
        last = datetime.strptime(dates[0], "%Y-%m-%d").date()
        if (datetime.now().date()-last).days <= 1:
            streak = 1
            for i in range(1,len(dates)):
                d = datetime.strptime(dates[i], "%Y-%m-%d").date()
                if (last-d).days == 1: streak+=1; last=d
                else: break
    conn.close()
    return total, this_week, streak

def add_exercise(day,name,sets,reps,notes):
    conn = db_conn(); c=conn.cursor()
    c.execute("SELECT MAX(exercise_order) FROM workouts WHERE day=?", (day,))
    maxo = c.fetchone()[0] or -1
    c.execute("INSERT INTO workouts(day,exercise_name,sets,reps,notes,exercise_order) VALUES(?,?,?,?,?,?)",
              (day,name,sets,reps,notes,maxo+1))
    conn.commit(); conn.close()

def delete_exercise(ex_id):
    conn = db_conn(); conn.execute("DELETE FROM workouts WHERE id=?", (ex_id,)); conn.commit(); conn.close()

def update_exercise_order(day, ex_id, new_order):
    conn = db_conn(); c=conn.cursor()
    c.execute("SELECT exercise_order FROM workouts WHERE id=?", (ex_id,))
    cur = c.fetchone()[0]
    c.execute("SELECT id FROM workouts WHERE day=? AND exercise_order=?", (day,new_order))
    swap = c.fetchone()
    if swap: c.execute("UPDATE workouts SET exercise_order=? WHERE id=?", (cur, swap[0]))
    c.execute("UPDATE workouts SET exercise_order=? WHERE id=?", (new_order, ex_id))
    conn.commit(); conn.close()

def replace_exercise(ex_id,new_name,new_notes=None):
    conn=db_conn(); c=conn.cursor()
    if new_notes is not None:
        c.execute("UPDATE workouts SET exercise_name=?, notes=? WHERE id=?", (new_name,new_notes,ex_id))
    else:
        c.execute("UPDATE workouts SET exercise_name=? WHERE id=?", (new_name,ex_id))
    conn.commit(); conn.close()

def replace_exercise_manually(ex_id, name, sets, reps, notes):
    conn=db_conn()
    conn.execute("UPDATE workouts SET exercise_name=?, sets=?, reps=?, notes=? WHERE id=?",
                 (name,sets,reps,notes,ex_id))
    conn.commit(); conn.close()

# Profile
def load_profile():
    conn = db_conn()
    df = pd.read_sql_query("SELECT * FROM user_profile WHERE id=1", conn)
    conn.close()
    return df.iloc[0].to_dict() if not df.empty else None

def save_profile(data: dict):
    now = datetime.now().isoformat(timespec='seconds')
    conn = db_conn(); c=conn.cursor()
    c.execute("SELECT id FROM user_profile WHERE id=1")
    if c.fetchone():
        c.execute("""UPDATE user_profile SET name=?, units=?, height_cm=?, weight_kg=?, goal=?, theme=?, updated_at=? WHERE id=1""",
                  (data.get('name'), data.get('units'), data.get('height_cm'), data.get('weight_kg'),
                   data.get('goal'), data.get('theme'), now))
    else:
        c.execute("""INSERT INTO user_profile(id,name,units,height_cm,weight_kg,goal,theme,created_at,updated_at)
                     VALUES(1,?,?,?,?,?,?,?,?)""",
                  (data.get('name'), data.get('units'), data.get('height_cm'), data.get('weight_kg'),
                   data.get('goal'), data.get('theme'), now, now))
    conn.commit(); conn.close()

# =========================
# EXERCISE DB LOADING
# =========================
@st.cache_data(show_spinner=False)
def load_exercise_database():
    path = EXERCISE_CSV_PRIMARY if EXERCISE_CSV_PRIMARY.exists() else EXERCISE_CSV_FALLBACK
    if path.exists():
        try:
            df = pd.read_csv(path)
            if 'Unnamed: 0' in df.columns: df = df.drop(columns=['Unnamed: 0'])
            # Normalize expected columns
            rename_map = {c:c for c in df.columns}
            # Make sure we have these logical names:
            for need in ['Title','BodyPart','Equipment','Level','Type']:
                if need not in df.columns:
                    # try best-effort mapping
                    for c in df.columns:
                        if need.lower() in c.lower():
                            rename_map[c] = need
            df = df.rename(columns=rename_map)
            for need in ['Title','BodyPart','Equipment','Level','Type']:
                if need not in df.columns:
                    df[need] = None
            return df, True, str(path)
        except Exception as e:
            st.error(f"Error loading exercise database: {e}")
            return pd.DataFrame(), False, str(path)
    # tiny default
    return pd.DataFrame({
        'Title':['Push-ups','Squats','Plank','Lunges','Burpees'],
        'BodyPart':['Chest','Legs','Core','Legs','Full Body'],
        'Equipment':['Body Only']*5,
        'Level':['Beginner','Beginner','Beginner','Beginner','Intermediate'],
        'Type':['Strength']*4+['Cardio']
    }), False, "DEFAULT"
exercise_db, db_loaded, db_path_used = load_exercise_database()

# =========================
# TIMER UTILS (no freeze; use epoch math)
# =========================
def init_timer_state():
    ss = st.session_state
    for k,v in {
        'timer_running':False,'timer_start_ts':None,'timer_elapsed':0.0,'timer_preset':'Stopwatch','timer_beep_last':-1,
        'wo_running':False,'wo_start_ts':None,'wo_elapsed':0.0,
        'int_running':False,'int_start_ts':None,'int_elapsed':0.0,'int_set':1,'int_phase':'WORK','int_idx':0,
        'int_done':False,'int_beep_last':-1
    }.items():
        if k not in ss: ss[k]=v

def fmt_time(sec: float)->str:
    sec = max(0,int(sec))
    return f"{sec//60:02d}:{sec%60:02d}"

def actual_elapsed(flag_key, start_key):
    ss = st.session_state
    if not ss.get(flag_key) or ss.get(start_key) is None: return 0.0
    return time.time() - float(ss[start_key])

def play_sound(kind:str):
    st.components.v1.html(f"""
    <script>(async()=>{{try{{await window.__fitAudio.play('{kind}')}}catch(e){{console.log(e)}}}})();</script>
    """, height=0)

# =========================
# PAGES
# =========================
def page_workout():
    st.subheader("Timers")
    colA,colB = st.columns(2, gap="large")
    with colA:
        with st.container(border=True):
            st.markdown("#### Countdown / Stopwatch")
            presets = {"Stopwatch":0,"30s":30,"45s":45,"1min":60,"90s":90,"2min":120,"3min":180,"5min":300}
            sel = st.selectbox("Preset", list(presets.keys()), index=list(presets.keys()).index(st.session_state.timer_preset))
            if sel != st.session_state.timer_preset:
                st.session_state.timer_preset = sel
                st.session_state.timer_elapsed = 0.0
                st.session_state.timer_running = False
                st.session_state.timer_beep_last = -1
            c1,c2,c3 = st.columns(3)
            with c1:
                if st.button("Start", use_container_width=True, key="t_start", disabled=st.session_state.timer_running):
                    st.session_state.timer_running = True
                    st.session_state.timer_start_ts = time.time() - st.session_state.timer_elapsed
                    st.components.v1.html("<script>window.requestWakeLock && window.requestWakeLock();</script>", height=0)
                    st.rerun()
            with c2:
                if st.button("Pause", use_container_width=True, key="t_pause", disabled=not st.session_state.timer_running):
                    st.session_state.timer_running = False
                    st.session_state.timer_elapsed = actual_elapsed('timer_running','timer_start_ts')
                    st.rerun()
            with c3:
                if st.button("Reset", use_container_width=True, key="t_reset"):
                    st.session_state.timer_running = False
                    st.session_state.timer_elapsed = 0.0
                    st.session_state.timer_beep_last = -1
                    st.rerun()
            # display
            if st.session_state.timer_running:
                el = actual_elapsed('timer_running','timer_start_ts')
                st.session_state.timer_elapsed = el
                if sel!="Stopwatch":
                    remaining = presets[sel] - el
                    if remaining <= 0:
                        st.session_state.timer_running=False
                        st.markdown(f"<div class='timer'>00:00</div>", unsafe_allow_html=True)
                        play_sound("timer")
                    else:
                        st.markdown(f"<div class='timer'>{fmt_time(remaining)}</div>", unsafe_allow_html=True)
                        remain_int = int(remaining)
                        if 0<remain_int<=10 and remain_int!=st.session_state.timer_beep_last:
                            play_sound("countdown"); st.session_state.timer_beep_last = remain_int
                        if remain_int==0 and st.session_state.timer_beep_last!=0:
                            play_sound("timer"); st.session_state.timer_beep_last=0
                        time.sleep(0.1); st.rerun()
                else:
                    st.markdown(f"<div class='timer'>{fmt_time(el)}</div>", unsafe_allow_html=True)
                    time.sleep(0.1); st.rerun()
            else:
                if sel!="Stopwatch" and st.session_state.timer_elapsed==0:
                    st.markdown(f"<div class='timer'>{fmt_time(presets[sel])}</div>", unsafe_allow_html=True)
                else:
                    disp = st.session_state.timer_elapsed if sel=="Stopwatch" else max(0,presets[sel]-st.session_state.timer_elapsed)
                    st.markdown(f"<div class='timer'>{fmt_time(disp)}</div>", unsafe_allow_html=True)

    with colB:
        with st.container(border=True):
            st.markdown("#### Workout Stopwatch")
            c1,c2,c3 = st.columns(3)
            with c1:
                if st.button("Start", use_container_width=True, key="wo_start", disabled=st.session_state.wo_running):
                    st.session_state.wo_running=True
                    st.session_state.wo_start_ts = time.time() - st.session_state.wo_elapsed
                    st.components.v1.html("<script>window.requestWakeLock && window.requestWakeLock();</script>", height=0)
                    st.rerun()
            with c2:
                if st.button("Pause", use_container_width=True, key="wo_pause", disabled=not st.session_state.wo_running):
                    st.session_state.wo_running=False
                    st.session_state.wo_elapsed = actual_elapsed('wo_running','wo_start_ts')
                    st.rerun()
            with c3:
                if st.button("Reset", use_container_width=True, key="wo_reset"):
                    st.session_state.wo_running=False; st.session_state.wo_elapsed=0.0; st.rerun()
            if st.session_state.wo_running:
                el = actual_elapsed('wo_running','wo_start_ts')
                st.session_state.wo_elapsed = el
                st.markdown(f"<div class='timer'>{fmt_time(el)}</div>", unsafe_allow_html=True)
                time.sleep(0.1); st.rerun()
            else:
                st.markdown(f"<div class='timer'>{fmt_time(st.session_state.wo_elapsed)}</div>", unsafe_allow_html=True)

    st.divider()

    # Workout Flow
    st.markdown("### Today’s Workout")
    day = st.selectbox("Select Plan", ["dayA","dayB","dayC"], format_func=lambda x: {"dayA":"Day A — Full Body","dayB":"Day B — Strength","dayC":"Day C — Mobility"}[x])
    workouts = get_workouts(day)
    completion = get_completion_status(day)
    done = sum(1 for i in range(len(workouts)) if completion.get(i, False))
    pct = int(100 * (done/len(workouts) if len(workouts)>0 else 0))
    st.markdown("<div class='progress-wrap'><div class='progress-bar' style='width:%d%%'></div></div>"%pct, unsafe_allow_html=True)
    st.caption(f"**{pct}% Complete** — {done} / {len(workouts)}")

    for idx, row in workouts.iterrows():
        comp = completion.get(idx, False)
        with st.container():
            st.markdown(f"<div class='exercise {'done' if comp else ''}'>", unsafe_allow_html=True)
            c1,c2 = st.columns([3,1])
            with c1:
                st.markdown(f"**{row['exercise_name']}**  \n{row['sets']} × {row['reps']}  \n<span class='small'>{row['notes']}</span>", unsafe_allow_html=True)
            with c2:
                colx, coly = st.columns(2)
                with colx:
                    if st.button("Done" if not comp else "Undo", key=f"ex_done_{day}_{idx}"):
                        toggle_exercise_completion(day, idx, not comp); st.rerun()
                with coly:
                    if st.button("Reset", key=f"ex_reset_{day}_{idx}"):
                        toggle_exercise_completion(day, idx, False); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    if len(workouts)>0 and done==len(workouts):
        st.success("Workout Complete! Logging and celebrating 🎉")
        play_sound("completion")
        if st.button("Log Workout & Reset"):
            dur = fmt_time(st.session_state.wo_elapsed)
            log_workout(day, len(workouts), dur)
            # clear today's completion for next time (optional)
            conn=db_conn(); today=datetime.now().strftime("%Y-%m-%d")
            conn.execute("DELETE FROM exercise_completion WHERE day=? AND date=?", (day,today))
            conn.commit(); conn.close()
            st.session_state.wo_elapsed=0; st.session_state.wo_running=False
            st.rerun()

def page_cardio_core():
    st.markdown("### 20-Minute Cardio & Core")
    st.caption("Light cardio (15) + Core intervals (5). Sounds fixed. Timers don’t freeze.")
    core = get_core_exercises()
    exercise_list = core['exercise_name'].tolist()
    if not exercise_list:
        st.error("No core exercises saved. Add some in **Edit**."); return

    st.markdown("#### Audio test")
    c1,c2,c3 = st.columns(3)
    with c1:
        if st.button("Countdown beep"): play_sound("countdown")
    with c2:
        if st.button("Transition beep"): play_sound("transition")
    with c3:
        if st.button("Completion beep"): play_sound("completion")

    st.divider()
    st.markdown("#### Intervals — 4× (60s work + 10s rest)")
    # controls
    a,b,c = st.columns(3)
    with a:
        if st.button("Start", key="int_start", disabled=st.session_state.int_running):
            st.session_state.int_running=True
            st.session_state.int_start_ts=time.time()
            st.session_state.int_elapsed=0.0
            st.session_state.int_set=1; st.session_state.int_phase="WORK"; st.session_state.int_idx=0
            st.session_state.int_done=False; st.session_state.int_beep_last=-1
            st.components.v1.html("<script>window.requestWakeLock && window.requestWakeLock();</script>", height=0)
            st.rerun()
    with b:
        if st.button("Pause", key="int_pause", disabled=not st.session_state.int_running):
            st.session_state.int_running=False
            st.session_state.int_elapsed = actual_elapsed('int_running','int_start_ts')
            st.rerun()
    with c:
        if st.button("Reset", key="int_reset"):
            st.session_state.int_running=False; st.session_state.int_elapsed=0.0
            st.session_state.int_set=1; st.session_state.int_phase="WORK"; st.session_state.int_idx=0
            st.session_state.int_done=False; st.session_state.int_beep_last=-1
            st.rerun()

    if st.session_state.int_running and not st.session_state.int_done:
        el = actual_elapsed('int_running','int_start_ts')
        st.session_state.int_elapsed = el
        total_work = 4*60; total_rest = 3*10; total = total_work + total_rest  # 310s
        cycle = 70

        if el < total:
            # compute set/phase/remaining
            which_cycle = int(el // cycle)
            in_cycle_t = el - which_cycle*cycle
            current_set = which_cycle + 1
            if current_set>4: current_set=4
            if in_cycle_t < 60:
                phase = "WORK"
                remaining = 60 - in_cycle_t
                idx = which_cycle % max(1,len(exercise_list))
            else:
                phase = "REST"
                remaining = 70 - in_cycle_t
                idx = which_cycle % max(1,len(exercise_list))
        else:
            st.session_state.int_done=True; st.session_state.int_running=False
            remaining = 0; phase="WORK"; current_set=4; idx=3

        if not st.session_state.int_done:
            st.session_state.int_set=current_set; st.session_state.int_phase=phase; st.session_state.int_idx=idx
            badge = "ok" if phase=="WORK" else "warn"
            st.markdown(f"<span class='badge {badge}'>Set {current_set}/4 — {phase}</span>", unsafe_allow_html=True)
            if phase=="WORK":
                st.markdown(f"**Current:** {exercise_list[idx]}")
            cls = "work" if phase=="WORK" else "rest"
            st.markdown(f"<div class='timer {cls}'>{fmt_time(remaining)}</div>", unsafe_allow_html=True)

            remain_int = int(remaining)
            if 0<remain_int<=10 and remain_int!=st.session_state.int_beep_last:
                play_sound("countdown"); st.session_state.int_beep_last = remain_int
            if remain_int==0 and st.session_state.int_beep_last!=0:
                if current_set==4 and phase=="WORK": play_sound("completion")
                else: play_sound("transition")
                st.session_state.int_beep_last=0

            time.sleep(0.1); st.rerun()
    elif st.session_state.int_done:
        st.success("Core intervals complete! Logged as Cardio & Core.")
        st.markdown("<div class='timer'>DONE</div>", unsafe_allow_html=True)
        if st.button("Log Workout"):
            log_workout("Cardio & Core", 1, "20:00")
            st.success("Logged."); st.rerun()
    else:
        st.markdown("<span class='badge ok'>Ready — Set 1/4</span>", unsafe_allow_html=True)
        st.markdown(f"**First up:** {exercise_list[0]}")
        st.markdown("<div class='timer work'>01:00</div>", unsafe_allow_html=True)

    st.divider()
    st.markdown("#### Manage Core List")
    for _,r in core.iterrows():
        c1,c2 = st.columns([5,1])
        with c1:
            st.write(f"{r['exercise_order']+1}. {r['exercise_name']}")
        with c2:
            if st.button("Delete", key=f"del_core_{r['id']}"):
                delete_core_exercise(r['id']); st.rerun()

    st.markdown("**Add from DB**")
    c1,c2,c3 = st.columns(3)
    with c1:
        bp = ["All"] + sorted(exercise_db['BodyPart'].dropna().unique().tolist())
        sel_bp = st.selectbox("Body Part", bp, key="core_bp")
    with c2:
        eq = ["All"] + sorted(exercise_db['Equipment'].dropna().unique().tolist())
        sel_eq = st.selectbox("Equipment", eq, key="core_eq")
    with c3:
        term = st.text_input("Search", key="core_term")

    fdf = exercise_db.copy()
    if sel_bp!="All": fdf = fdf[fdf['BodyPart']==sel_bp]
    if sel_eq!="All": fdf = fdf[fdf['Equipment']==sel_eq]
    if term: fdf = fdf[fdf['Title'].str.contains(term, case=False, na=False)]
    st.caption(f"Found {len(fdf)}")
    for _,ex in fdf.head(20).iterrows():
        cc1,cc2 = st.columns([4,1])
        with cc1:
            st.markdown(f"**{ex.get('Title','(Unnamed)')}** — {ex.get('BodyPart','?')} | {ex.get('Equipment','?')} | {ex.get('Level','?')}")
        with cc2:
            if st.button("Add", key=f"core_add_{ex.name}"):
                add_core_exercise(ex.get('Title','')); st.success("Added"); st.rerun()

    st.markdown("**Add custom**")
    name = st.text_input("Exercise name", key="core_custom")
    if st.button("Add Custom"):
        if name.strip():
            add_core_exercise(name.strip()); st.success("Added"); st.rerun()

def page_browse_replace():
    st.markdown("### Browse & Replace Exercises")
    c1,c2 = st.columns([2,1])
    with c1:
        day = st.selectbox("Day", ["dayA","dayB","dayC"], format_func=lambda x: {"dayA":"Day A","dayB":"Day B","dayC":"Day C"}[x], key="br_day")
    with c2:
        w = get_workouts(day)
        choice = st.selectbox("Exercise to replace",
                              options=[(row['id'], row['exercise_name']) for _,row in w.iterrows()],
                              format_func=lambda x: x[1] if isinstance(x,tuple) else x)

    st.markdown("---")
    c1,c2,c3 = st.columns(3)
    with c1:
        bp = ["All"] + sorted(exercise_db['BodyPart'].dropna().unique().tolist())
        sel_bp = st.selectbox("Body Part", bp)
    with c2:
        eq = ["All"] + sorted(exercise_db['Equipment'].dropna().unique().tolist())
        sel_eq = st.selectbox("Equipment", eq)
    with c3:
        term = st.text_input("Search")

    fdf = exercise_db.copy()
    if sel_bp!="All": fdf = fdf[fdf['BodyPart']==sel_bp]
    if sel_eq!="All": fdf = fdf[fdf['Equipment']==sel_eq]
    if term: fdf = fdf[fdf['Title'].str.contains(term, case=False, na=False)]

    st.caption(f"Found {len(fdf)} (source: {db_path_used})")
    for _,ex in fdf.head(50).iterrows():
        d1,d2 = st.columns([4,1])
        with d1:
            st.markdown(f"**{ex.get('Title','?')}** — {ex.get('BodyPart','?')} | {ex.get('Equipment','?')} | {ex.get('Level','?')}")
        with d2:
            if st.button("Replace", key=f"rep_{ex.name}"):
                notes = f"{ex.get('Type','Exercise')} — {ex.get('Level','All levels')}"
                replace_exercise(choice[0], ex.get('Title',''), notes)
                st.success(f"Replaced with '{ex.get('Title','')}'"); st.rerun()

def page_edit():
    st.markdown("### Edit Workouts")
    day = st.selectbox("Day", ["dayA","dayB","dayC"], format_func=lambda x: {"dayA":"Day A","dayB":"Day B","dayC":"Day C"}[x])
    ws = get_workouts(day)
    st.markdown("#### Current")
    for _,row in ws.iterrows():
        e1,e2,e3,e4 = st.columns([4,1,1,1])
        with e1:
            st.write(f"**{row['exercise_order']+1}. {row['exercise_name']}** — {row['sets']}×{row['reps']}  \n_{row['notes']}_")
        with e2:
            if row['exercise_order']>0 and st.button("Up", key=f"up_{row['id']}"):
                update_exercise_order(day, row['id'], row['exercise_order']-1); st.rerun()
        with e3:
            if row['exercise_order']<len(ws)-1 and st.button("Down", key=f"down_{row['id']}"):
                update_exercise_order(day, row['id'], row['exercise_order']+1); st.rerun()
        with e4:
            if st.button("Delete", key=f"del_{row['id']}"):
                delete_exercise(row['id']); st.rerun()
        st.divider()

    st.markdown("#### Add New")
    with st.form("add_ex"):
        c1,c2 = st.columns(2)
        with c1:
            name = st.text_input("Name")
            notes = st.text_input("Notes", value="Focus on form")
        with c2:
            sets = st.number_input("Sets",1,10,3)
            reps = st.text_input("Reps", value="10-12")
        if st.form_submit_button("Add"):
            if name.strip():
                add_exercise(day, name.strip(), sets, reps, notes.strip())
                st.success("Added"); st.rerun()

    st.markdown("#### Replace (Manual)")
    with st.form("rep_manual"):
        ex_id = st.selectbox("Pick exercise", options=[(row['id'], f"{row['exercise_order']+1}. {row['exercise_name']}") for _,row in ws.iterrows()],
                             format_func=lambda x: x[1])[0]
        c1,c2 = st.columns(2)
        with c1:
            new_name = st.text_input("New name")
            new_notes = st.text_input("New notes")
        with c2:
            new_sets = st.number_input("New sets",1,10,3)
            new_reps = st.text_input("New reps", value="10-12")
        if st.form_submit_button("Replace"):
            if new_name.strip():
                replace_exercise_manually(ex_id, new_name.strip(), new_sets, new_reps.strip(), new_notes.strip())
                st.success("Replaced"); st.rerun()

def page_calendar():
    st.markdown("### Calendar")
    hist = get_workout_history(limit=365)
    days = set(hist['date'].tolist()) if not hist.empty else set()
    today = datetime.now()
    if 'cal_month' not in st.session_state: st.session_state.cal_month = today.month
    if 'cal_year' not in st.session_state: st.session_state.cal_year = today.year
    c1,c2,c3 = st.columns([1,2,1])
    with c1:
        if st.button("◀ Prev"):
            st.session_state.cal_month -= 1
            if st.session_state.cal_month==0: st.session_state.cal_month=12; st.session_state.cal_year-=1
            st.rerun()
    with c3:
        if st.button("Next ▶"):
            st.session_state.cal_month += 1
            if st.session_state.cal_month==13: st.session_state.cal_month=1; st.session_state.cal_year+=1
            st.rerun()
    with c2:
        st.markdown(f"#### {datetime(st.session_state.cal_year, st.session_state.cal_month, 1).strftime('%B %Y')}")

    cal = calendar.monthcalendar(st.session_state.cal_year, st.session_state.cal_month)
    hdr = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
    cols = st.columns(7)
    for i,dn in enumerate(hdr): cols[i].markdown(f"**{dn}**")
    for wk in cal:
        cols = st.columns(7)
        for i, d in enumerate(wk):
            if d==0:
                cols[i].markdown("<div class='calendar-day'>&nbsp;</div>", unsafe_allow_html=True)
            else:
                ds = f"{st.session_state.cal_year:04d}-{st.session_state.cal_month:02d}-{d:02d}"
                classes = "calendar-day"
                if ds in days: classes += " workout"
                if ds == datetime.now().strftime("%Y-%m-%d"): classes += " today"
                cols[i].markdown(f"<div class='{classes}'>{d}</div>", unsafe_allow_html=True)

def page_progress():
    st.markdown("### Progress")
    t,w,s = get_stats()
    a,b,c = st.columns(3)
    with a:
        st.markdown("<div class='stat'><div class='value'>%d</div><div class='label'>Total Workouts</div></div>"%t, unsafe_allow_html=True)
    with b:
        st.markdown("<div class='stat'><div class='value'>%d</div><div class='label'>This Week</div></div>"%w, unsafe_allow_html=True)
    with c:
        st.markdown("<div class='stat'><div class='value'>%d</div><div class='label'>Day Streak</div></div>"%s, unsafe_allow_html=True)

    st.markdown("#### Recent History")
    hist = get_workout_history(limit=20)
    if hist.empty:
        st.info("No workout history yet.")
    else:
        for _,r in hist.iterrows():
            dn = {"dayA":"Day A","dayB":"Day B","dayC":"Day C","Cardio & Core":"Cardio & Core"}.get(r['day'], r['day'])
            st.write(f"**{dn}** — {r['date']} • {r.get('duration','N/A')} • {r['exercises_completed']} exercises")
            st.divider()
    if not hist.empty and st.button("Export CSV"):
        conn=db_conn()
        df = pd.read_sql_query("SELECT * FROM workout_history ORDER BY timestamp DESC", conn); conn.close()
        st.download_button("Download", data=df.to_csv(index=False), file_name=f"fittrack_export_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")

def page_profile():
    st.markdown("### Your Profile")
    prof = load_profile() or {}
    with st.form("profile_form", clear_on_submit=False):
        c1,c2,c3 = st.columns(3)
        with c1:
            name = st.text_input("Name", value=prof.get("name",""))
            units = st.selectbox("Units", ["metric","imperial"], index=(0 if prof.get("units","metric")=="metric" else 1))
        with c2:
            height_cm = st.number_input("Height (cm)", 0.0, 300.0, float(prof.get("height_cm") or 0.0), step=0.5)
            weight_kg = st.number_input("Weight (kg)", 0.0, 500.0, float(prof.get("weight_kg") or 0.0), step=0.1)
        with c3:
            goal = st.text_input("Training Goal", value=prof.get("goal",""))
            theme = st.selectbox("Theme", ["auto","dark"], index=(1 if prof.get("theme","dark")=="dark" else 0))
        if st.form_submit_button("Save Profile"):
            save_profile({"name":name.strip(),"units":units,"height_cm":height_cm,"weight_kg":weight_kg,"goal":goal.strip(),"theme":theme})
            st.success("Profile saved ✔")

    st.markdown("#### Quick Utilities")
    c1,c2,c3 = st.columns(3)
    with c1:
        if st.button("Open Apple Music"):
            st.components.v1.html("<script>window.openAppleMusic && window.openAppleMusic();</script>", height=0)
            st.toast("Attempting to open Apple Music…")
    with c2:
        if st.button("Allow Notifications"):
            st.components.v1.html("""
            <script>
            if('Notification' in window){
              Notification.requestPermission().then(p=>{
                if(p==='granted'){ new Notification('FitTrack Pro', {body:'Notifications enabled ✅'}); }
              });
            }
            </script>""", height=0)
            st.info("Notification request sent.")
    with c3:
        if st.button("Keep Screen On"):
            st.components.v1.html("<script>window.requestWakeLock && window.requestWakeLock();</script>", height=0)
            st.info("Wake lock requested.")

def page_guide():
    st.markdown("### Guide")
    st.markdown("""
- **Three-day split** plus **Cardio & Core**.  
- Rest **45–60s** between sets. Add load slowly.  
- Green badges = **Work**. Yellow = **Rest**.  
- Timers keep true time even after tab switches.  
- Sounds: test once (tap) to grant audio.  
- DB path in use: `""" + db_path_used + """`  
""")

# =========================
# MAIN
# =========================
def main():
    init_database()
    init_timer_state()

    if db_loaded:
        st.caption(f"✅ Loaded {len(exercise_db)} exercises from: **{db_path_used}**")
    else:
        st.warning("⚠ Could not find your dataset at the specified path. Using a small fallback list.")

    tabs = st.tabs(["🏋️ Workout","🫀 Cardio & Core","🔁 Browse & Replace","✏️ Edit","📅 Calendar","📈 Progress","👤 Profile","📘 Guide"])
    with tabs[0]: page_workout()
    with tabs[1]: page_cardio_core()
    with tabs[2]: page_browse_replace()
    with tabs[3]: page_edit()
    with tabs[4]: page_calendar()
    with tabs[5]: page_progress()
    with tabs[6]: page_profile()
    with tabs[7]: page_guide()

if __name__ == "__main__":
    main()
