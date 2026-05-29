import streamlit as st
import threading
import time
import queue
import json
import os
import requests
import numpy as np
import plotly.graph_objects as go
import websocket
from collections import deque
import base64

BASE_DIR = os.path.dirname(__file__)
LOGO_NAMES = ["logo.jpg", "logo.jpeg", "logo.png"]


def find_logo_path():
    for name in LOGO_NAMES:
        candidate = os.path.join(BASE_DIR, name)
        if os.path.exists(candidate):
            return candidate
    return None


def render_logo():
    logo_path = find_logo_path()
    if not logo_path:
        st.warning(f"Logo file not found. Checked: {', '.join(LOGO_NAMES)}")
        return

    try:
        with open(logo_path, "rb") as f:
            image_bytes = f.read()
        
        theme = st.session_state.get("theme", "dark")
        text_color = "#000000" if theme == "light" else "#FFFFFF"

        b64 = base64.b64encode(image_bytes).decode('utf-8')
        st.markdown(f"""
        <div style="display:flex;align-items:center;justify-content:center;flex-direction:column;margin:8px 0;">
            <img src="data:image/png;base64,{b64}" 
                 style="max-width:28vw;min-width:80px;height:auto;border-radius:8px;box-shadow:0 6px 18px rgba(0,0,0,0.12);"/>
            <div style="text-align:center;margin-top:8px;">
                <p style="color: {text_color}; font-size: clamp(14px, 1.6vw, 20px); font-weight: 600; letter-spacing: 0.5px; margin: 0;">CHINHOYI UNIVERSITY OF TECHNOLOGY</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    except Exception as exc:
        st.warning(f"Unable to load logo: {exc}")


def apply_custom_styles(theme="light"):
    if theme == "light":
        styles = """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Poppins:wght@500;600;700&display=swap');
            
            :root {
                --primary-color: #2E86AB;
                --success-color: #06A77D;
                --warning-color: #F77F00;
                --danger-color: #D62828;
                --light-bg: #F8F9FA;
                --dark-bg: #1a1a1a;
                --text-primary: #2C3E50;
                --text-secondary: #7F8C8D;
                --border-color: #ECF0F1;
            }
            
            * {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
            }
            
            .main { background-color: #FFFFFF; }
            
            .metric-card {
                background: linear-gradient(135deg, #F5F7FA 0%, #F8F9FA 100%);
                padding: 20px;
                border-radius: 12px;
                border: 1.5px solid #E0E7FF;
                box-shadow: 0 2px 8px rgba(46, 134, 171, 0.08);
                margin: 10px 0;
                transition: all 0.3s ease;
            }
            
            .metric-card:hover {
                box-shadow: 0 6px 16px rgba(46, 134, 171, 0.15);
                border-color: #2E86AB;
                transform: translateY(-2px);
            }
            
            .metric-label {
                color: #7F8C8D;
                font-size: 11px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 10px;
            }
            
            .metric-value {
                color: #2E86AB;
                font-size: 32px;
                font-weight: 700;
                line-height: 1;
                font-family: 'Poppins', sans-serif;
            }
            
            h1 {
                color: #2C3E50;
                font-size: 2.5rem;
                font-weight: 700;
                margin-bottom: 10px;
                letter-spacing: -0.5px;
                font-family: 'Poppins', sans-serif;
            }
            
            h2 {
                color: #2C3E50;
                font-size: 1.5rem;
                font-weight: 700;
                margin-top: 20px;
                margin-bottom: 15px;
                border-bottom: 2.5px solid #2E86AB;
                padding-bottom: 10px;
                font-family: 'Poppins', sans-serif;
            }
            
            .stButton > button {
                background: linear-gradient(135deg, #2E86AB 0%, #1D5580 100%);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 28px;
                font-weight: 700;
                font-size: 14px;
                transition: all 0.3s ease;
                box-shadow: 0 4px 12px rgba(46, 134, 171, 0.25);
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .stButton > button:hover {
                background: linear-gradient(135deg, #1D5580 0%, #134160 100%);
                box-shadow: 0 6px 20px rgba(46, 134, 171, 0.35);
                transform: translateY(-3px);
            }
            
            [data-testid="stSidebar"] {
                background-color: #F8F9FA;
                border-right: 1px solid #E8E8E8;
            }
            
            .stInfo { background: linear-gradient(135deg, #E3F2FD 0%, #F3F7FF 100%); border-left: 4px solid #2E86AB; border-radius: 6px; }
            .stSuccess { background: linear-gradient(135deg, #E8F5E9 0%, #F1F8F4 100%); border-left: 4px solid #06A77D; border-radius: 6px; }
            .stError { background: linear-gradient(135deg, #FFEBEE 0%, #FFF3F5 100%); border-left: 4px solid #D62828; border-radius: 6px; }
        </style>
        """
    else:
        styles = """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Poppins:wght@500;600;700&display=swap');
            
            :root {
                --primary-color: #64B5F6;
                --success-color: #4CAF50;
                --warning-color: #FFB74D;
                --danger-color: #EF5350;
                --light-bg: #121212;
                --dark-bg: #1a1a1a;
                --text-primary: #E0E0E0;
                --text-secondary: #9E9E9E;
                --border-color: #424242;
            }
            
            * {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
            }
            
            .main { background-color: #121212; }
            
            .metric-card {
                background: linear-gradient(135deg, #1E1E1E 0%, #252525 100%);
                padding: 20px;
                border-radius: 12px;
                border: 1.5px solid #2A3F5F;
                box-shadow: 0 4px 12px rgba(100, 181, 246, 0.1);
                margin: 10px 0;
                transition: all 0.3s ease;
            }
            
            .metric-card:hover {
                box-shadow: 0 6px 20px rgba(100, 181, 246, 0.2);
                border-color: #64B5F6;
                transform: translateY(-2px);
            }
            
            .metric-label {
                color: #9E9E9E;
                font-size: 11px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 10px;
            }
            
            .metric-value {
                color: #64B5F6;
                font-size: 32px;
                font-weight: 700;
                line-height: 1;
                font-family: 'Poppins', sans-serif;
            }
            
            h1 {
                color: #E8E8E8;
                font-size: 2.5rem;
                font-weight: 700;
                margin-bottom: 10px;
                letter-spacing: -0.5px;
                font-family: 'Poppins', sans-serif;
            }
            
            h2 {
                color: #E8E8E8;
                font-size: 1.5rem;
                font-weight: 700;
                margin-top: 20px;
                margin-bottom: 15px;
                border-bottom: 2.5px solid #64B5F6;
                padding-bottom: 10px;
                font-family: 'Poppins', sans-serif;
            }
            
            .stButton > button {
                background: linear-gradient(135deg, #64B5F6 0%, #42A5F5 100%);
                color: #121212;
                border: none;
                border-radius: 8px;
                padding: 12px 28px;
                font-weight: 700;
                font-size: 14px;
                transition: all 0.3s ease;
                box-shadow: 0 4px 12px rgba(100, 181, 246, 0.35);
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .stButton > button:hover {
                background: linear-gradient(135deg, #42A5F5 0%, #2196F3 100%);
                box-shadow: 0 6px 20px rgba(100, 181, 246, 0.45);
                transform: translateY(-3px);
            }
            
            [data-testid="stSidebar"] {
                background-color: #1E1E1E;
                border-right: 1px solid #2A2A2A;
            }
            
            .stInfo { background: linear-gradient(135deg, #1a237e 0%, #1e3a5f 100%); border-left: 4px solid #64B5F6; border-radius: 6px; color: #E0E0E0; }
            .stSuccess { background: linear-gradient(135deg, #1b5e20 0%, #1f7c2c 100%); border-left: 4px solid #4CAF50; border-radius: 6px; color: #E0E0E0; }
            .stError { background: linear-gradient(135deg, #b71c1c 0%, #c62828 100%); border-left: 4px solid #EF5350; border-radius: 6px; color: #E0E0E0; }
            
            .stTextInput input, .stNumberInput input {
                background-color: #1E1E1E !important;
                color: #E0E0E0 !important;
                border: 1.5px solid #2A3F5F !important;
            }
        </style>
        """
    st.markdown(styles, unsafe_allow_html=True)


def set_toast(text: str, kind: str = "info", duration: float = 4.0):
    st.session_state["toast"] = {"text": text, "type": kind, "expiry": time.time() + float(duration)}


def find_backend_base(ports=(8000, 8001)):
    for p in ports:
        try:
            resp = requests.get(f"http://127.0.0.1:{p}/", timeout=0.4)
            if resp.status_code in (200, 404):
                return f"http://127.0.0.1:{p}", f"ws://127.0.0.1:{p}/ws"
        except Exception:
            continue
    return "http://127.0.0.1:8000", "ws://127.0.0.1:8000/ws"


# URL Routing Logic
env_api = os.getenv("DASHBOARD_API_URL")
if env_api:
    API_URL = env_api.rstrip("/")
    if API_URL.startswith("https://"):
        WS_URL = API_URL.replace("https://", "wss://") + "/ws"
    else:
        WS_URL = API_URL.replace("http://", "ws://") + "/ws"
else:
    API_URL, WS_URL = find_backend_base()


def ws_thread(q: queue.Queue):
    def on_message(ws, message):
        try:
            data = json.loads(message)
            q.put(data)
        except Exception:
            pass

    def on_error(ws, error):
        pass

    def on_close(ws, close_status_code, close_msg):
        pass

    while True:
        try:
            ws = websocket.WebSocketApp(WS_URL, on_message=on_message, on_error=on_error, on_close=on_close)
            ws.run_forever()
        except Exception:
            time.sleep(1)


def render_dashboard():
    acc_buffer = np.zeros(4096)
    sample_rate = 2048

    history_len = st.session_state.get("history_len", 200)
    amp_history = deque(maxlen=history_len)
    time_history = deque(maxlen=history_len)

    if "bal_radius_cm" not in st.session_state: st.session_state["bal_radius_cm"] = 5.0
    if "sensitivity" not in st.session_state: st.session_state["sensitivity"] = 1.0
    if "rotor_mass_kg" not in st.session_state: st.session_state["rotor_mass_kg"] = 1.0
    if "accel_per_unit_g" not in st.session_state: st.session_state["accel_per_unit_g"] = 1.0

    toast_slot = st.empty()
    placeholder = st.empty()
    last_rpm = 0.0

    q = st.session_state.get("ws_queue")
    if q is None: return

    updated = False
    while not q.empty():
        data = q.get_nowait()
        arr = np.array(data.get("acc", []), dtype=float)
        sample_rate = int(data.get("sample_rate", sample_rate))
        acc_buffer = np.roll(acc_buffer, -len(arr))
        acc_buffer[-len(arr) :] = arr
        last_rpm = float(data.get("rpm", last_rpm))
        updated = True

    if not updated and st.session_state.get("local_running", False):
        sim_rpm = float(st.session_state.get("local_rpm", last_rpm))
        last_rpm = sim_rpm
        n = int(sample_rate * 0.1)
        t = np.arange(n) / sample_rate
        rotor_hz = max(0.1, sim_rpm / 60.0)
        signal = 1.0 * np.sin(2 * np.pi * rotor_hz * t) + 0.3 * np.sin(2 * np.pi * 2 * rotor_hz * t)
        arr = (signal + np.random.normal(scale=0.05, size=n)).astype(float)
        acc_buffer = np.roll(acc_buffer, -len(arr))
        acc_buffer[-len(arr) :] = arr
        updated = True

    n = len(acc_buffer)
    freqs = np.fft.rfftfreq(n, 1.0 / sample_rate)
    fft_complex = np.fft.rfft(acc_buffer)
    fft = np.abs(fft_complex)

    rotor_hz = max(0.1, last_rpm / 60.0)
    idx = int(np.argmin(np.abs(freqs - rotor_hz))) if len(freqs) > 0 else 0
    amp_at_rotor = float(fft[idx]) if idx < len(fft) else 0.0
    phase_at_rotor = float(np.angle(fft_complex[idx])) if idx < len(fft_complex) else 0.0

    if updated:
        amp_history.append(amp_at_rotor)
        time_history.append(time.time())

    recommended_mass_g = amp_at_rotor * float(st.session_state.get("sensitivity", 1.0))
    measured_deg = (np.degrees(phase_at_rotor) + 360.0) % 360.0
    recommended_angle_deg = (measured_deg + 180.0) % 360.0

    rotor_mass_kg = float(st.session_state.get("rotor_mass_kg", 1.0))
    accel_per_unit_g = float(st.session_state.get("accel_per_unit_g", 1.0))
    amp_m_s2 = amp_at_rotor * accel_per_unit_g * 9.81
    r_m = float(st.session_state.get("bal_radius_cm", 5.0)) / 100.0
    omega = 2.0 * np.pi * rotor_hz
    recommended_mass_physics_g = 0.0
    if r_m > 0 and omega > 0:
        recommended_mass_physics_g = max(0.0, ((amp_m_s2 * rotor_mass_kg) / (r_m * (omega ** 2))) * 1000.0)

    with placeholder.container():
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        with metric_col1:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Current RPM</div><div class="metric-value">{last_rpm:.0f}</div></div>', unsafe_allow_html=True)
        with metric_col2:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Rotor Amplitude</div><div class="metric-value">{amp_at_rotor:.3f}</div></div>', unsafe_allow_html=True)
        with metric_col3:
            st.markdown(f'<div class="metric-card"><div class="metric-label">Rotor Frequency</div><div class="metric-value">{rotor_hz:.2f} Hz</div></div>', unsafe_allow_html=True)
        with metric_col4:
            status_color = "#06A77D" if st.session_state.get("local_running", False) else "#D62828"
            status_text = "RUNNING" if st.session_state.get("local_running", False) else "STOPPED"
            st.markdown(f'<div class="metric-card"><div class="metric-label">Machine Status</div><div style="color: {status_color}; font-weight: 700; font-size: 16px;">{status_text}</div></div>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 📈 Real-Time Analysis")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig = go.Figure(go.Scatter(y=acc_buffer, mode="lines", name="Acceleration (g)", line=dict(color="#2E86AB", width=2)))
            fig.update_layout(title="Time-Domain Signal", xaxis_title="Sample", yaxis_title="Acceleration (g)", height=300, template="plotly_white", margin=dict(l=40,r=40,t=40,b=40))
            st.plotly_chart(fig, use_container_width=True, config={"responsive": True})

        with col2:
            fig2 = go.Figure(go.Scatter(x=freqs, y=fft, mode="lines", name="Magnitude", line=dict(color="#F77F00", width=2), fill="tozeroy", fillcolor="rgba(247, 127, 0, 0.2)"))
            fig2.update_layout(title="Frequency Domain (FFT)", xaxis_title="Frequency (Hz)", yaxis_title="Magnitude", height=300, template="plotly_white", margin=dict(l=40,r=40,t=40,b=40))
            st.plotly_chart(fig2, use_container_width=True, config={"responsive": True})
        
        st.markdown("---")
        st.markdown("### ⚖️ Balancing Recommendations")
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown("#### 📐 Proportional Recommendation")
            fig4 = go.Figure()
            theta = np.linspace(0, 360, 361)
            fig4.add_trace(go.Scatterpolar(r=[1.0] * len(theta), theta=theta, mode="lines", line=dict(color="#2E86AB", width=2)))
            fig4.add_trace(go.Scatterpolar(r=[1.0], theta=[measured_deg], mode="markers+text", marker=dict(size=15, color="#D62828"), text=["Imbalance"], textposition="top center"))
            fig4.add_trace(go.Scatterpolar(r=[1.0], theta=[recommended_angle_deg], mode="markers+text", marker=dict(size=max(6, min(28, recommended_mass_g * 3)), color="#06A77D"), text=[f"{recommended_mass_g:.2f}g"], textposition="bottom center"))
            fig4.update_layout(polar=dict(radialaxis=dict(visible=False, range=[0, 1.2])), showlegend=False, height=260, margin=dict(l=40,r=40,t=40,b=40))
            st.plotly_chart(fig4, use_container_width=True)

        with c2:
            st.markdown("#### 🔬 Physics-Based Recommendation")
            fig5 = go.Figure()
            fig5.add_trace(go.Scatterpolar(r=[1.0] * len(theta), theta=theta, mode="lines", line=dict(color="#2E86AB", width=2)))
            fig5.add_trace(go.Scatterpolar(r=[1.0], theta=[measured_deg], mode="markers+text", marker=dict(size=15, color="#D62828"), text=["Imbalance"], textposition="top center"))
            fig5.add_trace(go.Scatterpolar(r=[1.0], theta=[recommended_angle_deg], mode="markers+text", marker=dict(size=max(6, min(28, recommended_mass_physics_g * 0.25)), color="#06A77D"), text=[f"{recommended_mass_physics_g:.2f}g"], textposition="bottom center"))
            fig5.update_layout(polar=dict(radialaxis=dict(visible=False, range=[0, 1.2])), showlegend=False, height=260, margin=dict(l=40,r=40,t=40,b=40))
            st.plotly_chart(fig5, use_container_width=True)

    toast = st.session_state.get("toast")
    if toast:
        if time.time() > toast.get("expiry", 0):
            st.session_state.pop("toast", None)
            toast_slot.empty()
        else:
            cls = "stSuccess" if toast.get("type") == "success" else ("stError" if toast.get("type") == "error" else "stInfo")
            toast_slot.markdown(f'<div class="{cls}" style="padding:12px;border-radius:8px;margin-bottom:8px;">{toast.get("text")}</div>', unsafe_allow_html=True)


def main():
    st.set_page_config(layout="wide", page_title="Rotor Balancing Machine Dashboard")
    render_logo()
    
    if "theme" not in st.session_state: st.session_state["theme"] = "dark"
    apply_custom_styles(st.session_state["theme"])
    
    with st.sidebar:
        col_theme1, col_theme2 = st.columns(2)
        with col_theme1:
            if st.button("☀️ Light" if st.session_state["theme"] == "light" else "Light", use_container_width=True):
                st.session_state["theme"] = "light"
                st.rerun()
        with col_theme2:
            if st.button("🌙 Dark" if st.session_state["theme"] == "dark" else "Dark", use_container_width=True):
                st.session_state["theme"] = "dark"
                st.rerun()
        st.markdown("---")
    
    st.title("🔄 Rotor Balancing Machine")
    
    if "token" not in st.session_state:
        st.session_state["token"] = None
        st.session_state["username"] = None

    with st.sidebar:
        st.markdown("### 🔐 Authentication")
        hide_until = st.session_state.get("hide_auth_until", 0)
        
        if hide_until and time.time() < hide_until:
            st.info("Finalizing authentication...")
        else:
            auth_mode = st.radio("Mode", ["Login", "Signup"], label_visibility="collapsed")
            username = st.text_input("Username", placeholder="Enter username", label_visibility="collapsed")
            password = st.text_input("Password", type="password", placeholder="Enter password", label_visibility="collapsed")
            
            col_auth1, col_auth2 = st.columns(2)
            with col_auth1:
                if st.button(auth_mode, use_container_width=True):
                    if not username or not password:
                        set_toast("Please enter both username and password", "error")
                    else:
                        # Safety Block: Pause core dashboard loops briefly during database transaction
                        st.session_state["hide_auth_until"] = time.time() + 3.5
                        try:
                            resp = requests.post(f"{API_URL}/{auth_mode.lower()}", json={"username": username, "password": password}, timeout=5)
                            data = resp.json()
                            if resp.status_code == 200 and data:
                                st.session_state["token"] = data.get("access_token")
                                st.session_state["username"] = username
                                set_toast(f"{auth_mode} successful!", "success")
                                st.rerun()
                            else:
                                set_toast(data.get("detail", "Authentication failed."), "error")
                                st.session_state["hide_auth_until"] = 0
                        except Exception as e:
                            set_toast(f"Auth network error: {e}", "error")
                            st.session_state["hide_auth_until"] = 0

        if st.session_state.get("token"):
            st.markdown(f"**✓ Logged in:** {st.session_state.get('username')}")
            if st.button("Logout", use_container_width=True):
                st.session_state["token"] = None
                st.session_state["username"] = None
                st.rerun()
            st.markdown("---")

    token = st.session_state.get("token")
    if not token:
        st.warning("Please log in or sign up in the sidebar to view the live engine monitor metrics.")
        st.stop()

    if "ws_queue" not in st.session_state:
        st.session_state["ws_queue"] = queue.Queue()
        t = threading.Thread(target=ws_thread, args=(st.session_state["ws_queue"],), daemon=True)
        t.start()

    headers = {"Authorization": f"Bearer {token}"}
    if "local_running" not in st.session_state: st.session_state["local_running"] = False
    if "local_rpm" not in st.session_state: st.session_state["local_rpm"] = 30.0

    st.markdown("### 🎮 Machine Controls")
    ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns(4)
    with ctrl_col1:
        if st.button("▶️ Start", use_container_width=True):
            st.session_state["local_running"] = True
            try: requests.post(f"{API_URL}/start", headers=headers, timeout=3)
            except Exception: pass
    with ctrl_col2:
        if st.button("⏹️ Stop", use_container_width=True):
            st.session_state["local_running"] = False
            try: requests.post(f"{API_URL}/stop", headers=headers, timeout=3)
            except Exception: pass
    with ctrl_col3:
        rpm = st.slider("Set RPM", min_value=10, max_value=100, value=int(st.session_state["local_rpm"]), step=5)
    with ctrl_col4:
        if st.button("✓ Apply Speed", use_container_width=True):
            st.session_state["local_rpm"] = float(rpm)
            try: requests.post(f"{API_URL}/set_speed/{rpm}", headers=headers, timeout=3)
            except Exception: pass

    render_dashboard()

    # Dynamic refresh sleep interval
    time.sleep(0.6)
    st.rerun()


if __name__ == "__main__":
    main()
    