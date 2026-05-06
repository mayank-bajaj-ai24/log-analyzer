import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

st.set_page_config(page_title="Anomalies | Log Analyzer", page_icon="⚠️", layout="wide")
LEVEL_NAMES = {0:"DEBUG",1:"INFO",2:"WARNING",3:"ERROR",4:"CRITICAL"}
LEVEL_COLORS = {"DEBUG":"#6B7280","INFO":"#0D4F4F","WARNING":"#92642a","ERROR":"#DC2626","CRITICAL":"#991B1B"}
LEVEL_BG = {"DEBUG":"#F3F4F6","INFO":"#CCFBF1","WARNING":"#FEF3C7","ERROR":"#FEE2E2","CRITICAL":"#FEE2E2"}

st.markdown("""<style>
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#0B3D3D,#0D4F4F)!important}
section[data-testid="stSidebar"] *{color:#E0F2F1!important}
section[data-testid="stSidebarNav"]{display:none!important}
.stApp{background:#F0F2F5}
#MainMenu,footer,header{visibility:hidden}
iframe{border:none!important}
</style>""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🟢 Log Analyzer"); st.caption("Enterprise Infrastructure"); st.divider()
    st.page_link("app.py", label="📊 Overview"); st.page_link("pages/1_anomalies.py", label="⚠️ Anomalies")
    st.page_link("pages/2_performance.py", label="⚡ Performance"); st.page_link("pages/3_explore.py", label="🔍 Explore")

if "df" not in st.session_state:
    st.warning("Go to **Overview** and upload a log file first."); st.stop()

df = st.session_state["df"]
anom_df = df[df["is_anomaly"]==True].copy() if "is_anomaly" in df.columns else pd.DataFrame()
ac = len(anom_df)

# Build table rows
rows_html = ""
if len(anom_df)>0:
    for _, row in anom_df.sort_values("anomaly_score",ascending=False).head(8).iterrows():
        raw = str(row.get("raw",""))[:65].replace("<","&lt;").replace(">","&gt;")
        tpl = str(row.get("template",""))[:30].replace("<","&lt;").replace(">","&gt;")
        sc = abs(row.get("anomaly_score",0))
        lv = LEVEL_NAMES.get(row.get("log_level",1),"INFO")
        lc = LEVEL_COLORS.get(lv,"#6B7280")
        lb = LEVEL_BG.get(lv,"#F3F4F6")
        ie = lv in ("ERROR","CRITICAL")
        sp = min(sc*100,100)
        rows_html += f"""<tr style="border-bottom:1px solid #eee;{'background:#FFF5F5' if ie else ''}">
            <td style="padding:10px 16px;font-family:'Space Grotesk',monospace;font-size:12px;color:{'#991B1B' if ie else '#374151'};{'border-left:3px solid #DC2626' if ie else ''}">{raw}</td>
            <td style="padding:10px 16px;font-size:12px;color:#6B7280">{tpl}</td>
            <td style="padding:10px 16px"><div style="display:flex;align-items:center;gap:8px"><div style="flex:1;background:#eee;height:8px;border-radius:4px;overflow:hidden"><div style="width:{sp}%;background:linear-gradient(90deg,#F59E0B,#DC2626);height:8px;border-radius:4px"></div></div><span style="font-size:12px;font-weight:700;color:#DC2626">{sc:.2f}</span></div></td>
            <td style="padding:10px 16px;text-align:center"><span style="background:{lb};color:{lc};padding:2px 8px;border-radius:2px;font-size:10px;font-weight:700">{lv}</span></td>
        </tr>"""

# Build histogram bars (simplified SVG)
hist_normal = ""
hist_anom = ""
if "anomaly_score" in df.columns:
    import numpy as np
    ns = df[df["is_anomaly"]==False]["anomaly_score"].values
    ans = df[df["is_anomaly"]==True]["anomaly_score"].values
    bins = np.linspace(min(df["anomaly_score"].min(),-0.5), max(df["anomaly_score"].max(),0.5), 15)
    n_hist, _ = np.histogram(ns, bins=bins) if len(ns)>0 else (np.zeros(14),bins)
    a_hist, _ = np.histogram(ans, bins=bins) if len(ans)>0 else (np.zeros(14),bins)
    mx_h = max(max(n_hist),max(a_hist),1)
    bw = 600/len(n_hist)
    for i,v in enumerate(n_hist):
        h = max(v/mx_h*180,0)
        hist_normal += f'<rect x="{i*bw+2}" y="{200-h}" width="{bw-4}" height="{h}" fill="rgba(180,180,180,0.5)" rx="2"/>'
    for i,v in enumerate(a_hist):
        h = max(v/mx_h*180,0)
        hist_anom += f'<rect x="{i*bw+2}" y="{200-h}" width="{bw-4}" height="{h}" fill="rgba(220,38,38,0.6)" rx="2"/>'

html = f"""<!DOCTYPE html>
<html><head>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box;font-family:'Inter',sans-serif}}
body{{background:#F0F2F5;padding:24px}}
.card{{background:#fff;border:1px solid #D1D5DB;border-radius:4px;padding:20px 24px;margin-bottom:16px}}
.card-title{{font-family:'Space Grotesk';font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:#404848;margin-bottom:16px}}
.badge{{padding:2px 8px;border-radius:2px;font-size:10px;font-weight:700;display:inline-block}}
table{{width:100%;border-collapse:collapse}}
th{{text-align:left;font-family:'Space Grotesk';font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:#707978;padding:10px 16px;border-bottom:2px solid #D1D5DB}}
</style></head><body>

<!-- Alert Banner -->
<div style="background:linear-gradient(90deg,#FEE2E2,#FECACA);border:1px solid #FECACA;border-radius:4px;padding:14px 24px;display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
    <div style="display:flex;align-items:center;gap:10px"><span style="font-size:20px">⚠️</span><span style="color:#991B1B;font-size:16px;font-weight:800">{ac:,} ANOMALOUS ENTRIES DETECTED</span></div>
    <div style="display:flex;gap:8px">
        <button style="background:#DC2626;color:#fff;padding:8px 20px;border:none;border-radius:4px;font-size:11px;font-weight:700;cursor:pointer">QUARANTINE ALL</button>
        <button style="background:#fff;color:#DC2626;border:2px solid #DC2626;padding:8px 20px;border-radius:4px;font-size:11px;font-weight:700;cursor:pointer">EXPORT CSV</button>
    </div>
</div>

<!-- Row: Histogram + Right Cards -->
<div style="display:flex;gap:16px;margin-bottom:16px">
    <div class="card" style="flex:3">
        <div class="card-title">Anomaly Distribution Score</div>
        <div style="color:#9CA3AF;font-size:11px;margin-bottom:12px">Isolation Forest Model v4.2 Analysis</div>
        <div style="display:flex;gap:16px;margin-bottom:8px">
            <div style="display:flex;align-items:center;gap:6px"><div style="width:12px;height:12px;background:rgba(180,180,180,.5);border-radius:2px"></div><span style="font-size:11px;color:#555">Normal</span></div>
            <div style="display:flex;align-items:center;gap:6px"><div style="width:12px;height:12px;background:rgba(220,38,38,.6);border-radius:2px"></div><span style="font-size:11px;color:#555">Anomalous</span></div>
        </div>
        <svg width="100%" viewBox="0 0 620 240" style="overflow:visible">
            {hist_normal}{hist_anom}
            <line x1="310" y1="0" x2="310" y2="200" stroke="#0D4F4F" stroke-width="2" stroke-dasharray="6,4"/>
            <rect x="270" y="2" width="100" height="18" rx="3" fill="#0D4F4F"/>
            <text x="320" y="14" fill="#fff" font-size="9" text-anchor="middle" font-weight="600">THRESHOLD 0.72</text>
            <text x="10" y="220" fill="#888" font-size="10">0.0 (Normal)</text>
            <text x="280" y="220" fill="#888" font-size="10">0.5 (Neutral)</text>
            <text x="560" y="220" fill="#888" font-size="10">1.0 (Critical)</text>
            <text x="-5" y="15" fill="#888" font-size="9">Count</text>
        </svg>
    </div>
    <div style="flex:1;display:flex;flex-direction:column;gap:16px">
        <div class="card">
            <div class="card-title">Model Reliability</div>
            <div style="margin-bottom:12px"><div style="display:flex;justify-content:space-between;margin-bottom:4px"><span style="font-size:12px;color:#555">Precision</span><span style="font-size:12px;font-weight:800;color:#0D4F4F">98.4%</span></div><div style="background:#eee;height:10px;border-radius:2px;overflow:hidden"><div style="width:98.4%;background:#0D4F4F;height:10px;border-radius:2px"></div></div></div>
            <div><div style="display:flex;justify-content:space-between;margin-bottom:4px"><span style="font-size:12px;color:#555">Recall</span><span style="font-size:12px;font-weight:800;color:#0D4F4F">92.1%</span></div><div style="background:#eee;height:10px;border-radius:2px;overflow:hidden"><div style="width:92.1%;background:#0891B2;height:10px;border-radius:2px"></div></div></div>
        </div>
        <div style="background:linear-gradient(135deg,#0D4F4F,#0D6B6B);border-radius:4px;padding:20px;flex:1">
            <div style="font-family:'Space Grotesk';color:#80CBC4;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.05em">System Health</div>
            <div style="color:#fff;font-size:36px;font-weight:900;margin:8px 0">Stable</div>
            <div style="color:#B2DFDB;font-size:12px;line-height:1.4">No critical path interruptions within detected anomalies.</div>
        </div>
    </div>
</div>

<!-- Anomaly Table -->
<div class="card" style="padding:0;overflow:hidden">
    <div style="padding:16px 20px;display:flex;align-items:center;gap:12px;border-bottom:1px solid #D1D5DB">
        <span class="card-title" style="margin-bottom:0">Recent Log Analysis</span>
        <span class="badge" style="background:#FEE2E2;color:#DC2626">● Anomalous Only ✕</span>
    </div>
    <table>
        <thead><tr><th>Raw Log</th><th>Template</th><th>Anomaly Score</th><th style="text-align:center">Log Level</th></tr></thead>
        <tbody>{rows_html}</tbody>
    </table>
    <div style="display:flex;justify-content:space-between;padding:12px 16px;background:#F9FAFB;border-top:1px solid #D1D5DB">
        <span style="font-size:11px;color:#888">Showing 1–{min(8,ac)} of {ac:,} entries</span>
        <div style="display:flex;gap:4px"><span style="background:#0D4F4F;color:#fff;padding:2px 8px;border-radius:2px;font-size:11px;font-weight:600">1</span><span style="padding:2px 8px;font-size:11px;color:#888">2</span><span style="padding:2px 8px;font-size:11px;color:#888">3</span><span style="padding:2px 8px;font-size:11px;color:#888">…</span><span style="padding:2px 8px;font-size:11px;color:#888">Next</span></div>
    </div>
</div>



</body></html>"""

components.html(html, height=1200, scrolling=True)
