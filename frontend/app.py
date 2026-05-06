import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import os, sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
SAMPLE_PATH = os.path.join(BACKEND_DIR, "data", "samples", "sample.log")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

st.set_page_config(page_title="Log Analyzer Dashboard", page_icon="🔍", layout="wide", initial_sidebar_state="expanded")
LEVEL_NAMES = {0:"DEBUG",1:"INFO",2:"WARNING",3:"ERROR",4:"CRITICAL"}

st.markdown("""<style>
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#0B3D3D,#0D4F4F)!important}
section[data-testid="stSidebar"] *{color:#E0F2F1!important}
.stApp{background:#F0F2F5}
#MainMenu,footer,header{visibility:hidden}
iframe{border:none!important}
</style>""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🟢 Log Analyzer")
    st.caption("Enterprise Infrastructure")
    st.divider()
    st.page_link("app.py", label="📊 Overview")
    st.page_link("pages/1_anomalies.py", label="⚠️ Anomalies")
    st.page_link("pages/2_performance.py", label="⚡ Performance")
    st.page_link("pages/3_explore.py", label="🔍 Explore")
    st.divider()
    st.page_link("pages/3_explore.py", label="📋 Review Logs")

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
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:'Inter',sans-serif}body{background:#F0F2F5}
@keyframes pulse{0%,100%{opacity:.6}50%{opacity:1}}
@keyframes slideUp{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)}}
.hero{background:linear-gradient(135deg,#0B3D3D,#0D4F4F 40%,#0D6B6B);border-radius:8px;padding:48px;position:relative;overflow:hidden}
.hero::before{content:'';position:absolute;top:-50%;right:-20%;width:500px;height:500px;background:radial-gradient(circle,rgba(255,255,255,.04),transparent 70%);border-radius:50%}
.hero h1{font-size:36px;font-weight:900;color:#fff;margin-bottom:8px;animation:slideUp .6s ease;position:relative;z-index:1}
.hero p{font-size:16px;color:#B2DFDB;max-width:600px;line-height:1.6;animation:slideUp .6s ease .1s both;position:relative;z-index:1}
.status{display:inline-flex;align-items:center;gap:6px;background:rgba(16,185,129,.15);border:1px solid rgba(16,185,129,.3);padding:6px 14px;border-radius:20px;margin-bottom:20px;position:relative;z-index:1}
.status .dot{width:8px;height:8px;background:#10B981;border-radius:50%;animation:pulse 2s infinite}
.status span{font-family:'Space Grotesk';font-size:11px;font-weight:600;color:#10B981;text-transform:uppercase;letter-spacing:.8px}
.pipeline{display:flex;gap:0;margin-top:32px;position:relative;z-index:1}
.stage{flex:1;padding:14px 16px;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1)}
.stage:first-child{border-radius:6px 0 0 6px}.stage:last-child{border-radius:0 6px 6px 0}
.stage:not(:last-child)::after{content:'->';position:absolute;right:-8px;top:50%;transform:translateY(-50%);color:#80CBC4;font-size:16px;z-index:2;font-weight:700}
.stage{position:relative}
.stage .num{font-family:'Space Grotesk';font-size:9px;color:#80CBC4;font-weight:700;letter-spacing:1px;text-transform:uppercase;margin-bottom:3px}
.stage .name{font-size:13px;font-weight:700;color:#fff}.stage .desc{font-size:10px;color:#B2DFDB;margin-top:2px}
.features{display:flex;gap:12px;margin-top:20px}
.feat{flex:1;background:#fff;border:1px solid #D1D5DB;border-radius:6px;padding:18px;text-align:center}
.feat .icon{width:40px;height:40px;border-radius:10px;display:flex;align-items:center;justify-content:center;margin:0 auto 10px;font-size:20px}
.feat h3{font-size:12px;font-weight:700;color:#191c1e;margin-bottom:3px}.feat p{font-size:10px;color:#707978;line-height:1.4}
</style></head><body>
<div class="hero">
<div class="status"><div class="dot"></div><span>System Ready — All Modules Online</span></div>
<h1>Log Analyzer Dashboard</h1>
<p>Enterprise-grade log analysis with AI anomaly detection, Drain3 template mining, and memory-efficient streaming.</p>
<div class="pipeline">
<div class="stage"><div class="num">Stage 1</div><div class="name">Ingestion</div><div class="desc">Stream parser</div></div>
<div class="stage"><div class="num">Stage 2</div><div class="name">Drain3 Parse</div><div class="desc">Template mining</div></div>
<div class="stage"><div class="num">Stage 3</div><div class="name">Deduplication</div><div class="desc">MinHash LSH</div></div>
<div class="stage"><div class="num">Stage 4</div><div class="name">Anomaly AI</div><div class="desc">Isolation Forest</div></div>
<div class="stage"><div class="num">Stage 5</div><div class="name">Storage</div><div class="desc">Parquet output</div></div>
</div></div>
<div class="features">
<div class="feat"><div class="icon" style="background:#CCFBF1;color:#0D4F4F">🧠</div><h3>Memory Efficient</h3><p>Constant RAM regardless of file size</p></div>
<div class="feat"><div class="icon" style="background:#FEE2E2;color:#991B1B">⚠️</div><h3>Anomaly Detection</h3><p>Unsupervised Isolation Forest</p></div>
<div class="feat"><div class="icon" style="background:#EDE9FE;color:#7C3AED">📦</div><h3>10× Compression</h3><p>Parquet + MinHash dedup</p></div>
<div class="feat"><div class="icon" style="background:#FEF3C7;color:#92642a">🔍</div><h3>Template Mining</h3><p>Drain3 v4 AI patterns</p></div>
</div></body></html>""", height=480, scrolling=False)

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
if metrics is None: st.metric("Total Records",f"{len(df):,}"); st.stop()
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
        d = d.replace("&lt;*&gt;","<span style='background:#CCFBF1;color:#0D4F4F;padding:1px 4px;border-radius:3px;font-size:11px;font-weight:600'>&lt;*&gt;</span>")
        tpl_rows += f'<tr style="border-bottom:1px solid #eee"><td style="padding:11px 16px;font-family:Space Grotesk,monospace;font-size:12px;color:#374151">{d}</td><td style="padding:11px 16px;width:180px"><div style="background:#eee;height:10px;border-radius:5px;overflow:hidden"><div style="width:{bar_w}%;background:#0D4F4F;height:10px;border-radius:5px"></div></div></td><td style="padding:11px 16px;text-align:right;font-weight:700;color:#222;font-size:13px">{pct:.1f}%</td></tr>'

lv_bars = ""
lv_clr = {"DEBUG":"#0D4F4F","INFO":"#0D4F4F","WARNING":"#92642a","ERROR":"#DC2626","CRITICAL":"#991B1B"}
for l in ["DEBUG","INFO","WARNING","ERROR","CRITICAL"]:
    cnt = lv_counts.get(l,0); pct = max(cnt/mx_lv*100,2) if mx_lv else 2
    lv_bars += f'<div style="display:flex;align-items:center;margin:5px 0"><div style="width:65px;font-family:Space Grotesk;font-size:11px;color:#555;font-weight:600;text-transform:uppercase;letter-spacing:.5px">{l}</div><div style="flex:1;background:#eee;height:13px;border-radius:2px;overflow:hidden;margin:0 10px"><div style="width:{pct}%;background:{lv_clr[l]};height:13px;border-radius:2px"></div></div><div style="width:70px;text-align:right;font-size:12px;font-weight:700;color:#222">{cnt:,}</div></div>'

# Before/After data
raw_lines = I["total_lines"]
after_lines = O["total_records"]
removed = raw_lines - after_lines
raw_mb = O["raw_size_mb"]; pq_mb = O["parquet_size_mb"]
saved_pct = ((raw_mb - pq_mb)/raw_mb*100) if raw_mb > 0 else 0

html = f"""<!DOCTYPE html><html><head>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box;font-family:'Inter',sans-serif}}body{{background:#F0F2F5;color:#191c1e}}
.card{{background:#fff;border:1px solid #D1D5DB;border-radius:4px;padding:18px 22px;margin-bottom:14px}}
.ct{{font-family:'Space Grotesk';font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:#404848;margin-bottom:14px}}
.badge{{padding:2px 8px;border-radius:2px;font-size:10px;font-weight:700;display:inline-block}}
table{{width:100%;border-collapse:collapse}}
th{{text-align:left;font-family:Space Grotesk;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:#707978;padding:10px 16px;border-bottom:2px solid #D1D5DB}}
</style></head><body>

<!-- TOP: 4 Quick Stats -->
<div style="display:flex;gap:12px;margin-bottom:14px">
<div style="flex:1;background:linear-gradient(135deg,#0D4F4F,#0D6B6B);border-radius:4px;padding:16px 20px"><div style="font-family:Space Grotesk;font-size:9px;color:#80CBC4;font-weight:700;text-transform:uppercase;letter-spacing:1px">Lines Ingested</div><div style="font-size:28px;font-weight:900;color:#fff;margin-top:4px">{I['total_lines']:,}</div></div>
<div style="flex:1;background:#fff;border:1px solid #D1D5DB;border-radius:4px;padding:16px 20px"><div style="font-family:Space Grotesk;font-size:9px;color:#707978;font-weight:700;text-transform:uppercase;letter-spacing:1px">Unique After Dedup</div><div style="font-size:28px;font-weight:900;color:#0D4F4F;margin-top:4px">{O['total_records']:,}</div></div>
<div style="flex:1;background:#fff;border:1px solid #D1D5DB;border-radius:4px;padding:16px 20px"><div style="font-family:Space Grotesk;font-size:9px;color:#707978;font-weight:700;text-transform:uppercase;letter-spacing:1px">Anomalies Found</div><div style="font-size:28px;font-weight:900;color:#DC2626;margin-top:4px">{O['anomaly_count']:,}</div></div>
<div style="flex:1;background:#fff;border:1px solid #D1D5DB;border-radius:4px;padding:16px 20px"><div style="font-family:Space Grotesk;font-size:9px;color:#707978;font-weight:700;text-transform:uppercase;letter-spacing:1px">Processing Time</div><div style="font-size:28px;font-weight:900;color:#0891B2;margin-top:4px">{O['elapsed_seconds']:.2f}<span style="font-size:14px;color:#999">s</span></div></div>
</div>

<!-- ROW: Pipeline Summary + Log Levels -->
<div style="display:flex;gap:14px;margin-bottom:14px">
<div class="card" style="flex:3"><div class="ct">Pipeline Summary Stats</div>
<div style="display:flex;align-items:center;gap:24px">
<div style="position:relative;width:140px;height:140px;flex-shrink:0">
<svg viewBox="0 0 36 36" style="width:140px;height:140px;transform:rotate(-90deg)"><path d="M18 2.0845a15.9155 15.9155 0 0 1 0 31.831a15.9155 15.9155 0 0 1 0-31.831" fill="none" stroke="#E5E7EB" stroke-width="3"/><path d="M18 2.0845a15.9155 15.9155 0 0 1 0 31.831a15.9155 15.9155 0 0 1 0-31.831" fill="none" stroke="#0D4F4F" stroke-width="3" stroke-dasharray="{O['dedup_reduction_pct']}, 100"/></svg>
<div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center"><div style="font-size:22px;font-weight:800;color:#0D4F4F">{O['dedup_reduction_pct']:.1f}%</div><div style="font-size:8px;color:#707978;text-transform:uppercase;font-weight:600;letter-spacing:.5px">DEDUP REDUCTION</div></div>
</div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:14px 36px;flex:1">
<div><div style="font-family:Space Grotesk;font-size:10px;color:#707978;text-transform:uppercase;font-weight:600;letter-spacing:.5px">Lines Ingested</div><div style="font-size:26px;font-weight:800;color:#191c1e">{I['total_lines']:,}</div></div>
<div><div style="font-family:Space Grotesk;font-size:10px;color:#707978;text-transform:uppercase;font-weight:600;letter-spacing:.5px">Templates Extracted</div><div style="font-size:26px;font-weight:800;color:#191c1e">{I['total_lines']:,}</div></div>
<div><div style="font-family:Space Grotesk;font-size:10px;color:#707978;text-transform:uppercase;font-weight:600;letter-spacing:.5px">Unique Entries</div><div style="font-size:26px;font-weight:800;color:#191c1e">{O['total_records']:,}</div></div>
<div><div style="font-family:Space Grotesk;font-size:10px;color:#707978;text-transform:uppercase;font-weight:600;letter-spacing:.5px">Anomalies</div><div style="font-size:26px;font-weight:800;color:#DC2626">{O['anomaly_count']:,}</div></div>
</div></div></div>
<div class="card" style="flex:2"><div class="ct">Log Level Distribution</div>{lv_bars}</div>
</div>

<!-- ROW: Before vs After Comparison -->
<div class="card">
<div class="ct">📊 Before vs After Processing Comparison</div>
<div style="display:flex;gap:20px;align-items:stretch">
<div style="flex:1;background:#FEF2F2;border:1px solid #FECACA;border-radius:6px;padding:18px;text-align:center">
<div style="font-family:Space Grotesk;font-size:10px;color:#991B1B;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px">❌ Before Processing</div>
<div style="font-size:32px;font-weight:900;color:#991B1B">{raw_lines:,}</div>
<div style="font-size:11px;color:#DC2626;margin-bottom:6px">raw log lines</div>
<div style="font-size:24px;font-weight:800;color:#991B1B">{raw_mb:.4f} MB</div>
<div style="font-size:11px;color:#DC2626">uncompressed size</div>
</div>
<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px;width:80px">
<div style="font-size:28px">-></div>
<div style="background:#0D4F4F;color:#fff;padding:6px 12px;border-radius:20px;font-size:10px;font-weight:700">5-STAGE</div>
<div style="font-size:28px">-></div>
</div>
<div style="flex:1;background:#ECFDF5;border:1px solid #A7F3D0;border-radius:6px;padding:18px;text-align:center">
<div style="font-family:Space Grotesk;font-size:10px;color:#065F46;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px">✅ After Processing</div>
<div style="font-size:32px;font-weight:900;color:#065F46">{after_lines:,}</div>
<div style="font-size:11px;color:#059669;margin-bottom:6px">unique deduplicated entries</div>
<div style="font-size:24px;font-weight:800;color:#065F46">{pq_mb:.4f} MB</div>
<div style="font-size:11px;color:#059669">Parquet compressed</div>
</div>
<div style="flex:1;display:flex;flex-direction:column;gap:10px">
<div style="background:#fff;border:1px solid #D1D5DB;border-radius:6px;padding:14px;text-align:center;flex:1"><div style="font-family:Space Grotesk;font-size:9px;color:#707978;font-weight:700;text-transform:uppercase;letter-spacing:1px">Lines Removed</div><div style="font-size:24px;font-weight:900;color:#7C3AED;margin-top:4px">{removed:,}</div></div>
<div style="background:#fff;border:1px solid #D1D5DB;border-radius:6px;padding:14px;text-align:center;flex:1"><div style="font-family:Space Grotesk;font-size:9px;color:#707978;font-weight:700;text-transform:uppercase;letter-spacing:1px">Storage Saved</div><div style="font-size:24px;font-weight:900;color:#059669;margin-top:4px">{saved_pct:.1f}%</div></div>
<div style="background:#fff;border:1px solid #D1D5DB;border-radius:6px;padding:14px;text-align:center;flex:1"><div style="font-family:Space Grotesk;font-size:9px;color:#707978;font-weight:700;text-transform:uppercase;letter-spacing:1px">Compression</div><div style="font-size:24px;font-weight:900;color:#0D4F4F;margin-top:4px">{O['compression_ratio']:.1f}×</div></div>
</div>
</div></div>

<!-- ROW: Templates -->
<div class="card"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px"><div class="ct" style="margin-bottom:0">Top Log Templates AI</div><div style="display:flex;gap:8px;align-items:center"><span class="badge" style="background:#CCFBF1;color:#0D4F4F">AI MODEL: DRAIN3_V4</span><span class="material-icons" style="font-size:18px;color:#707978">settings</span></div></div>
<table><thead><tr><th>Template Pattern</th><th>Frequency</th><th style="text-align:right">Occurrence Rate</th></tr></thead><tbody>{tpl_rows}</tbody></table></div>

<!-- ROW: Storage Cards -->
<div style="display:flex;gap:14px">
<div class="card" style="flex:1;display:flex;align-items:center;gap:14px"><span class="material-icons" style="font-size:30px;color:#707978">description</span><div><div style="font-family:Space Grotesk;font-size:10px;color:#707978;text-transform:uppercase;font-weight:700;letter-spacing:.5px">Raw File Size</div><div style="font-size:30px;font-weight:900;color:#191c1e">{raw_mb:.2f}<span style="font-size:13px;color:#707978"> MB</span></div><span class="badge" style="background:#FEE2E2;color:#991B1B">UNCOMPRESSED</span></div></div>
<div style="flex:1;background:linear-gradient(135deg,#0D4F4F,#0D6B6B);border-radius:4px;padding:18px 22px;display:flex;align-items:center;gap:14px"><span class="material-icons" style="font-size:30px;color:#80CBC4">arrow_forward</span><div><div style="font-family:Space Grotesk;font-size:10px;color:#80CBC4;text-transform:uppercase;font-weight:700;letter-spacing:.5px">Parquet Output</div><div style="font-size:30px;font-weight:900;color:#fff">{pq_mb:.4f}<span style="font-size:13px;color:#B2DFDB"> MB</span></div><span class="badge" style="background:rgba(255,255,255,.2);color:#fff">{O['compression_ratio']:.1f}× SMALLER</span></div></div>
<div class="card" style="flex:1;display:flex;align-items:center;gap:14px"><span class="material-icons" style="font-size:30px;color:#707978">memory</span><div><div style="font-family:Space Grotesk;font-size:10px;color:#707978;text-transform:uppercase;font-weight:700;letter-spacing:.5px">Peak Memory Usage</div><div style="font-size:30px;font-weight:900;color:#191c1e">{O['peak_ram_mb']:.1f}<span style="font-size:13px;color:#707978"> MB</span></div><span style="font-size:11px;color:#059669;font-weight:600">✅ Within safe limits</span></div></div>
</div>

</body></html>"""

components.html(html, height=1250, scrolling=True)

if st.button("🔄 Upload a different file"):
    for k in ["raw_lines","filename","raw_size","metrics","df"]: st.session_state.pop(k,None)
    st.rerun()
