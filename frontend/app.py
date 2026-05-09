import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import os
from components.ui_utils import apply_custom_styles, render_sidebar

st.set_page_config(page_title="Log Analyzer | Enterprise Intelligence", layout="wide", initial_sidebar_state="expanded")
apply_custom_styles()
render_sidebar("overview")
LEVEL_NAMES = {0:"DEBUG",1:"INFO",2:"WARNING",3:"ERROR",4:"CRITICAL"}

# Paths
FRONTEND_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(FRONTEND_DIR, "..", "backend"))
SAMPLE_PATH = os.path.join(BACKEND_DIR, "data", "samples", "sample.log")
import sys
sys.path.append(FRONTEND_DIR) # Ensure components can be imported easily
sys.path.append(BACKEND_DIR)  # Ensure backend can be imported

# Sidebar handled by ui_utils

def load_and_run():
    lines = st.session_state.get("raw_lines")
    if not lines: return
    from components.pipeline_runner import run_pipeline_with_metrics
    out = os.path.join(BACKEND_DIR, "data", "processed")
    os.makedirs(out, exist_ok=True)
    m = run_pipeline_with_metrics(lines, out)
    st.session_state["metrics"] = m
    st.session_state["df"] = pd.DataFrame([
        {k:v for k,v in r.items() if k not in ("features","parameters")} for r in m["results_df"]
    ])

# ═══════════ LANDING PAGE ═══════════
if "metrics" not in st.session_state and "df" not in st.session_state:
    components.html("""<!DOCTYPE html><html><head>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Space+Grotesk:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:'Inter',sans-serif}
body{background:transparent; padding: 20px;}

@keyframes gradient-bg { 0% {background-position: 0% 50%;} 50% {background-position: 100% 50%;} 100% {background-position: 0% 50%;} }
@keyframes float1 { 0% {transform: translate(0, 0) scale(1);} 50% {transform: translate(20px, -20px) scale(1.1);} 100% {transform: translate(0, 0) scale(1);} }
@keyframes float2 { 0% {transform: translate(0, 0) scale(1);} 50% {transform: translate(-20px, 20px) scale(1.2);} 100% {transform: translate(0, 0) scale(1);} }

.hero {
    background: linear-gradient(-45deg, #0F172A, #1E1B4B, #064E3B, #0F172A);
    background-size: 400% 400%;
    animation: gradient-bg 15s ease infinite;
    border-radius: 24px;
    padding: 80px 60px;
    position: relative;
    overflow: hidden;
    color: white;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5), inset 0 0 0 1px rgba(255, 255, 255, 0.1);
}

.orb-1 { position: absolute; top: -20%; right: -10%; width: 500px; height: 500px; background: radial-gradient(circle, rgba(16, 185, 129, 0.2) 0%, transparent 70%); animation: float1 8s ease-in-out infinite; pointer-events: none; }
.orb-2 { position: absolute; bottom: -30%; left: -10%; width: 600px; height: 600px; background: radial-gradient(circle, rgba(139, 92, 246, 0.15) 0%, transparent 70%); animation: float2 10s ease-in-out infinite; pointer-events: none; }

.badge {
    display: inline-flex; align-items: center; gap: 8px;
    background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.2);
    color: #10B981; padding: 6px 16px; border-radius: 100px; font-size: 12px; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 24px;
    backdrop-filter: blur(4px);
}

.hero h1 {
    font-family: 'Space Grotesk', sans-serif; font-size: 64px; font-weight: 800; line-height: 1.1;
    margin-bottom: 24px; letter-spacing: -0.02em;
    background: linear-gradient(to right, #FFFFFF, #E2E8F0);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}

.gradient-text {
    background: linear-gradient(to right, #10B981, #06B6D4);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}

.hero p { font-size: 18px; color: #94A3B8; max-width: 600px; line-height: 1.6; margin-bottom: 40px; }

.grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 24px; margin-top: 40px; position: relative; z-index: 10; }

.stat-card {
    background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.05);
    padding: 24px; border-radius: 16px; backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); position: relative; overflow: hidden;
}
.stat-card::before {
    content: ''; position: absolute; top: 0; left: -100%; width: 50%; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.05), transparent); transition: all 0.5s ease;
}
.stat-card:hover { transform: translateY(-5px); border-color: rgba(16, 185, 129, 0.3); box-shadow: 0 10px 30px -10px rgba(16, 185, 129, 0.2); }
.stat-card:hover::before { left: 100%; }
.stat-card .label { display: flex; align-items: center; gap: 6px; color: #64748B; font-size: 11px; font-weight: 700; text-transform: uppercase; margin-bottom: 8px; letter-spacing: 0.05em; }
.stat-card .value { color: white; font-family: 'Space Grotesk', sans-serif; font-size: 20px; font-weight: 700; }
</style></head><body>
<div class="hero">
    <div class="orb-1"></div>
    <div class="orb-2"></div>
    <div class="badge"><span class="material-icons" style="font-size:14px">auto_awesome</span> Next-Gen Observability</div>
    <h1>Enterprise Log <br><span class="gradient-text">Intelligence.</span></h1>
    <p>Unlock deep insights from your distributed infrastructure with AI-driven anomaly detection and high-performance pipeline architecture.</p>
    
    <div class="grid">
        <div class="stat-card">
            <div class="label"><span class="material-icons" style="font-size:14px; color:#10B981">radar</span> Detection Engine</div>
            <div class="value">Isolation Forest</div>
        </div>
        <div class="stat-card">
            <div class="label"><span class="material-icons" style="font-size:14px; color:#8B5CF6">account_tree</span> Mining Logic</div>
            <div class="value">Drain3 AI Parser</div>
        </div>
        <div class="stat-card">
            <div class="label"><span class="material-icons" style="font-size:14px; color:#06B6D4">view_column</span> Data Schema</div>
            <div class="value">Apache Parquet</div>
        </div>
        <div class="stat-card">
            <div class="label"><span class="material-icons" style="font-size:14px; color:#F59E0B">compress</span> Compression</div>
            <div class="value">50x Reduction</div>
        </div>
    </div>
</div>
</body></html>""", height=620, scrolling=False)

    st.markdown("""<div style="text-align:center;margin:8px 0"><span style="font-family:'Space Grotesk',sans-serif;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;color:#707978">UPLOAD LOG FILE TO BEGIN ANALYSIS</span></div>""", unsafe_allow_html=True)
    uploaded = st.file_uploader("Upload log file", type=["log","txt","parquet","csv"], label_visibility="collapsed")
    _, cb, _ = st.columns([2,1,2])
    with cb: sample_clicked = st.button("🧪 Use Sample File", use_container_width=True, type="primary")
    if sample_clicked and os.path.exists(SAMPLE_PATH):
        with open(SAMPLE_PATH,"r",encoding="utf-8",errors="replace") as f: c=f.read()
        st.session_state["raw_lines"]=c.strip().split("\n")
        with st.spinner("⚙️ Running pipeline..."): load_and_run()
        st.rerun()
    if uploaded:
        rb=uploaded.read()
        if uploaded.name.endswith(".parquet"):
            import io; st.session_state["df"]=pd.read_parquet(io.BytesIO(rb)); st.session_state["metrics"]=None; st.rerun()
        else:
            st.session_state["raw_lines"]=rb.decode("utf-8",errors="replace").strip().split("\n")
            with st.spinner("⚙️ Running pipeline..."): load_and_run()
            st.rerun()
    st.stop()

if "raw_lines" in st.session_state and "metrics" not in st.session_state:
    with st.spinner("Running pipeline..."): load_and_run(); st.rerun()

# ═══════════ OVERVIEW DASHBOARD ═══════════
metrics = st.session_state.get("metrics")
df = st.session_state["df"]
if metrics is None: 
    st.markdown(f"""
    <div class="glass-card" style="text-align: center; padding: 3rem;">
        <h2 style="color: #64748B;">No Metrics Available</h2>
        <p>Total Records: <span style="color: #10B981; font-weight: 800; font-size: 1.5rem;">{len(df):,}</span></p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

O = metrics["output"]; I = metrics["input"]

# Prepare data
lv_counts = {}
if "log_level" in df.columns:
    lc = df["log_level"].map(LEVEL_NAMES).value_counts()
    for l in ["DEBUG","INFO","WARNING","ERROR","CRITICAL"]: lv_counts[l] = lc.get(l,0)
mx_lv = max(lv_counts.values()) if lv_counts else 1

tpl_rows = ""
if "template" in df.columns:
    top = df["template"].value_counts().head(5)
    mx_t = top.max() if len(top) else 1; total_t = top.sum()
    for t, cnt in top.items():
        pct = cnt/total_t*100; bar_w = max(cnt/mx_t*100,3)
        d = (t[:70]+"…" if len(t)>70 else t).replace("<","&lt;").replace(">","&gt;")
        d = d.replace("&lt;*&gt;","<span style='background:#F1F5F9;color:#64748B;padding:2px 6px;border-radius:4px;font-size:10px;font-weight:600;border:1px solid #E2E8F0'>&lt;*&gt;</span>")
        tpl_rows += f"""
        <tr style="border-bottom: 1px solid #F1F5F9;">
            <td style="padding: 16px; font-family: 'Inter', monospace; font-size: 13px; color: #334155;">{d}</td>
            <td style="padding: 16px; width: 200px;">
                <div style="background: #F1F5F9; height: 8px; border-radius: 100px; overflow: hidden;">
                    <div style="width: {bar_w}%; background: #10B981; height: 8px; border-radius: 100px;"></div>
                </div>
            </td>
            <td style="padding: 16px; text-align: right; font-weight: 700; color: #0F172A; font-size: 14px;">{pct:.1f}%</td>
        </tr>"""

lv_bars = ""
lv_clr = {"DEBUG":"#94A3B8","INFO":"#10B981","WARNING":"#F59E0B","ERROR":"#EF4444","CRITICAL":"#7F1D1D"}
for l in ["DEBUG","INFO","WARNING","ERROR","CRITICAL"]:
    cnt = lv_counts.get(l,0); pct = max(cnt/mx_lv*100,2) if mx_lv else 2
    lv_bars += f"""
    <div style="margin-bottom: 16px;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
            <span style="font-size: 11px; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em;">{l}</span>
            <span style="font-size: 12px; font-weight: 700; color: #0F172A;">{cnt:,}</span>
        </div>
        <div style="background: #F1F5F9; height: 6px; border-radius: 100px; overflow: hidden;">
            <div style="width: {pct}%; background: {lv_clr[l]}; height: 6px; border-radius: 100px;"></div>
        </div>
    </div>"""

# Metrics calc
raw_mb = O["raw_size_mb"]; pq_mb = O["parquet_size_mb"]
saved_pct = ((raw_mb - pq_mb)/raw_mb*100) if raw_mb > 0 else 0
raw_str = f"{raw_mb:.4f} MB" if raw_mb < 0.01 else f"{raw_mb:.2f} MB"
pq_str = f"{pq_mb:.4f} MB" if pq_mb < 0.01 else f"{pq_mb:.2f} MB"

stages_html = ""
for idx, s in enumerate(metrics.get("stages", [])):
    stages_html += f"""
    <div style="display: flex; align-items: stretch; margin-bottom: 0px;">
        <div style="display: flex; flex-direction: column; align-items: center; margin-right: 20px;">
            <div style="width: 28px; height: 28px; border-radius: 50%; background: #EEF2FF; border: 2px solid #6366F1; display: flex; align-items: center; justify-content: center; font-weight: 700; color: #4F46E5; font-size: 12px; z-index: 2;">{idx+1}</div>
            <div style="flex: 1; width: 2px; background: #E0E7FF; margin-top: -4px; margin-bottom: -4px; z-index: 1;"></div>
        </div>
        <div style="flex: 1; background: #fff; border: 1px solid #E2E8F0; border-radius: 12px; padding: 16px; margin-bottom: 16px; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px; align-items: center;">
                <div style="font-family: 'Space Grotesk'; font-weight: 700; color: #0F172A; font-size: 15px;">{s['name']}</div>
                <div style="background: #F1F5F9; padding: 4px 10px; border-radius: 6px; font-weight: 700; color: #6366F1; font-size: 12px; border: 1px solid #E2E8F0;">RAM: {s.get('ram_mb', 0)} MB</div>
            </div>
            <div style="font-size: 13px; color: #64748B; margin-bottom: 12px; font-weight: 500;">{s.get('description', '')}</div>
            <div style="background: #F8FAFC; padding: 12px; border-radius: 8px; display: flex; justify-content: space-between; border: 1px solid #F1F5F9;">
                <div style="font-size: 12px;"><span style="color: #64748B; font-weight: 600; margin-right: 4px;">Lines In:</span><span style="font-weight: 700; color: #0F172A;">{s.get('lines_in', '-'):,}</span></div>
                <div style="font-size: 12px;"><span style="color: #64748B; font-weight: 600; margin-right: 4px;">Lines Out:</span><span style="font-weight: 700; color: #0F172A;">{s.get('lines_out', '-'):,}</span></div>
                <div style="font-size: 12px;"><span style="color: #64748B; font-weight: 600; margin-right: 4px;">Data Loss:</span><span style="font-weight: 700; color: #059669; background: #D1FAE5; padding: 2px 8px; border-radius: 4px;">{s.get('data_loss', 'None')}</span></div>
            </div>
        </div>
    </div>
    """

html = f"""<!DOCTYPE html><html><head>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box;font-family:'Inter',sans-serif}}
body{{background:transparent; color:#1E293B; padding: 20px;}}
.grid-4 {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 24px; }}
.card {{ background: white; border-radius: 16px; border: 1px solid #E2E8F0; padding: 24px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
.stat-title {{ font-size: 12px; font-weight: 600; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; }}
.stat-value {{ font-family: 'Space Grotesk', sans-serif; font-size: 32px; font-weight: 800; color: #0F172A; }}
.emerald-card {{ background: #0F172A; color: white; border: none; }}
.emerald-card .stat-title {{ color: #94A3B8; }}
.emerald-card .stat-value {{ color: #10B981; }}
.flex-row {{ display: flex; gap: 20px; margin-bottom: 24px; }}
.flex-3 {{ flex: 3; }} .flex-2 {{ flex: 2; }}
.section-title {{ font-family: 'Space Grotesk', sans-serif; font-size: 16px; font-weight: 700; color: #0F172A; margin-bottom: 20px; display: flex; align-items: center; gap: 8px; }}
table {{ width: 100%; border-collapse: collapse; }}
th {{ text-align: left; font-size: 11px; font-weight: 700; color: #64748B; text-transform: uppercase; padding: 16px; border-bottom: 2px solid #F1F5F9; }}
</style></head><body>

<!-- Top KPI Row -->
<div class="grid-4">
    <div class="card emerald-card">
        <div class="stat-title">Lines Ingested</div>
        <div class="stat-value">{I['total_lines']:,}</div>
    </div>
    <div class="card">
        <div class="stat-title">Deduplicated</div>
        <div class="stat-value">{O['total_records']:,}</div>
    </div>
    <div class="card">
        <div class="stat-title">AI Anomalies</div>
        <div class="stat-value" style="color: #EF4444;">{O['anomaly_count']:,}</div>
    </div>
    <div class="card">
        <div class="stat-title">Execution</div>
        <div class="stat-value" style="color: #6366F1;">{O['elapsed_seconds']:.2f}s</div>
    </div>
</div>

<!-- Main Content Row -->
<div class="flex-row">
    <div class="card flex-3">
        <div class="section-title"><span class="material-icons" style="color: #10B981;">analytics</span> Pipeline Efficiency</div>
        <div style="display: flex; align-items: center; gap: 40px;">
            <div style="position: relative; width: 160px; height: 160px;">
                <svg viewBox="0 0 36 36" style="width: 160px; height: 160px; transform: rotate(-90deg);">
                    <circle cx="18" cy="18" r="16" fill="none" stroke="#F1F5F9" stroke-width="3"/>
                    <circle cx="18" cy="18" r="16" fill="none" stroke="#10B981" stroke-width="3" 
                            stroke-dasharray="{O['dedup_reduction_pct']}, 100" stroke-linecap="round"/>
                </svg>
                <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%,-50%); text-align: center;">
                    <div style="font-family: 'Space Grotesk'; font-size: 28px; font-weight: 800; color: #0F172A;">{O['dedup_reduction_pct']:.1f}%</div>
                    <div style="font-size: 9px; color: #64748B; font-weight: 700; text-transform: uppercase;">Reduction</div>
                </div>
            </div>
            <div style="flex: 1; display: grid; grid-template-columns: 1fr 1fr; gap: 24px;">
                <div><div class="stat-title">Raw Size</div><div style="font-size: 20px; font-weight: 700;">{raw_str}</div></div>
                <div><div class="stat-title">Optimized</div><div style="font-size: 20px; font-weight: 700; color: #10B981;">{pq_str}</div></div>
                <div><div class="stat-title">Saved Space</div><div style="font-size: 20px; font-weight: 700; color: #6366F1;">{saved_pct:.1f}%</div></div>
                <div><div class="stat-title">Compression</div><div style="font-size: 20px; font-weight: 700; color: #8B5CF6;">{O['compression_ratio']:.1f}×</div></div>
            </div>
        </div>
    </div>
    <div class="card flex-2">
        <div class="section-title"><span class="material-icons" style="color: #F59E0B;">bar_chart</span> Level Distribution</div>
        {lv_bars}
    </div>
</div>

<!-- Pipeline Transparency Report -->
<div class="card" style="margin-bottom: 24px;">
    <div class="section-title"><span class="material-icons" style="color: #6366F1;">account_tree</span> Pipeline Transparency & Memory Trace</div>
    <div style="font-size: 13px; color: #64748B; margin-bottom: 24px; line-height: 1.5;">Step-by-step breakdown of how the Log Analyzer achieves maximum compression and memory efficiency without compromising raw data integrity.</div>
    <div>{stages_html}</div>
</div>

<!-- Template Table -->
<div class="card" style="padding: 0; overflow: hidden;">
    <div style="padding: 24px; border-bottom: 1px solid #F1F5F9; display: flex; justify-content: space-between; align-items: center;">
        <div class="section-title" style="margin-bottom: 0;"><span class="material-icons" style="color: #8B5CF6;">hub</span> Top Log Templates AI</div>
        <div style="background: #F1F5F9; padding: 6px 12px; border-radius: 8px; font-size: 11px; font-weight: 700; color: #64748B; border: 1px solid #E2E8F0;">DRAIN3 V4 ENGINE</div>
    </div>
    <table>
        <thead><tr><th>Template Pattern</th><th>Frequency</th><th style="text-align: right;">Occurence Rate</th></tr></thead>
        <tbody>{tpl_rows}</tbody>
    </table>
</div>

</body></html>"""

components.html(html, height=2200, scrolling=True)

if st.button("🔄 Upload a different file"):
    for k in ["raw_lines","filename","raw_size","metrics","df"]: st.session_state.pop(k,None)
    st.rerun()
