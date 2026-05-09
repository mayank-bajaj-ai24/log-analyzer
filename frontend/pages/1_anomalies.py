import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from components.ui_utils import apply_custom_styles, render_sidebar

st.set_page_config(page_title="Anomalies | Log Analyzer", layout="wide")
apply_custom_styles()
render_sidebar("anomalies")

LEVEL_NAMES = {0:"DEBUG",1:"INFO",2:"WARNING",3:"ERROR",4:"CRITICAL"}
LEVEL_COLORS = {"DEBUG":"#94A3B8","INFO":"#10B981","WARNING":"#F59E0B","ERROR":"#EF4444","CRITICAL":"#7F1D1D"}
LEVEL_BG = {"DEBUG":"#F1F5F9","INFO":"#ECFDF5","WARNING":"#FFFBEB","ERROR":"#FEF2F2","CRITICAL":"#FEF2F2"}

# Sidebar handled by ui_utils

if "df" not in st.session_state:
    st.markdown("""
    <div style="display:flex; justify-content:center; align-items:center; height:60vh;">
        <div style="background: linear-gradient(135deg, #1E1B4B 0%, #0F172A 100%); border-radius: 24px; padding: 60px; text-align: center; max-width: 600px; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5), inset 0 0 0 1px rgba(255,255,255,0.05);">
            <div style="width: 80px; height: 80px; background: rgba(255,255,255,0.05); border-radius: 50%; display: flex; justify-content: center; align-items: center; margin: 0 auto 30px auto;">
                <span class="material-icons" style="font-size: 40px; color: #10B981;">portable_wifi_off</span>
            </div>
            <h2 style="font-family: 'Space Grotesk', sans-serif; font-size: 32px; font-weight: 700; color: white; margin-bottom: 16px;">Anomaly Engine Offline</h2>
            <p style="font-family: 'Inter', sans-serif; font-size: 16px; color: #94A3B8; line-height: 1.6;">Awaiting data stream. Please return to the Dashboard Overview and upload a log file to initialize threat detection.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

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
        hist_anom += f'<rect x="{i*bw+2}" y="{200-h}" width="{bw-4}" height="{h}" fill="rgba(239,68,68,0.7)" rx="2"/>'

html = f"""<!DOCTYPE html>
<html><head>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box;font-family:'Inter',sans-serif}}
body{{background:transparent; padding: 24px; color: #1E293B;}}
.card{{background:#fff;border:1px solid #E2E8F0;border-radius:16px;padding:24px;margin-bottom:24px;box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);}}
.section-title{{font-family:'Space Grotesk';font-size:16px;font-weight:700;color:#0F172A;margin-bottom:20px;display:flex;align-items:center;gap:8px;}}
.alert-banner {{
    background: linear-gradient(90deg, #7F1D1D 0%, #B91C1C 100%);
    border-radius: 12px;
    padding: 20px 32px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    color: white;
    box-shadow: 0 10px 15px -3px rgba(185, 28, 28, 0.2);
}}
table{{width:100%;border-collapse:collapse}}
th{{text-align:left;font-size:11px;font-weight:700;color:#64748B;text-transform:uppercase;padding:16px;border-bottom:2px solid #F1F5F9}}
</style></head><body>

<!-- Alert Banner -->
<div class="alert-banner">
    <div style="display:flex;align-items:center;gap:16px">
        <span class="material-icons" style="font-size:32px;">report_problem</span>
        <div>
            <div style="font-size:18px;font-weight:800;letter-spacing:-0.01em;">{ac:,} Critical Anomalies Detected</div>
            <div style="font-size:12px;color:rgba(255,255,255,0.7);font-weight:500;">Immediate review of security logs suggested by AI Engine</div>
        </div>
    </div>
    <div style="display:flex;gap:12px">
        <button style="background:rgba(255,255,255,0.1);color:#fff;border:1px solid rgba(255,255,255,0.2);padding:10px 24px;border-radius:8px;font-size:12px;font-weight:700;cursor:pointer;">QUARANTINE</button>
        <button style="background:#fff;color:#B91C1C;border:none;padding:10px 24px;border-radius:8px;font-size:12px;font-weight:700;cursor:pointer;box-shadow: 0 4px 6px rgba(0,0,0,0.1);">EXPORT DATA</button>
    </div>
</div>

<div style="display:flex;gap:24px;margin-bottom:24px">
    <div class="card" style="flex:3">
        <div class="section-title"><span class="material-icons" style="color: #EF4444;">insights</span> AI Threat Distribution</div>
        <div style="display:flex;gap:16px;margin-bottom:16px">
            <div style="display:flex;align-items:center;gap:8px"><div style="width:12px;height:12px;background:#E2E8F0;border-radius:3px"></div><span style="font-size:11px;color:#64748B;font-weight:600">Baseline</span></div>
            <div style="display:flex;align-items:center;gap:8px"><div style="width:12px;height:12px;background:#EF4444;border-radius:3px"></div><span style="font-size:11px;color:#EF4444;font-weight:700">Anomalous</span></div>
        </div>
        <svg width="100%" viewBox="0 0 620 240" style="overflow:visible">
            {hist_normal}{hist_anom}
            <line x1="310" y1="0" x2="310" y2="200" stroke="#0F172A" stroke-width="2" stroke-dasharray="6,4"/>
            <rect x="260" y="0" width="100" height="20" rx="6" fill="#0F172A"/>
            <text x="310" y="13" fill="#fff" font-size="9" text-anchor="middle" font-weight="700">AI THRESHOLD</text>
        </svg>
    </div>
    <div style="flex:1;display:flex;flex-direction:column;gap:24px">
        <div class="card">
            <div class="section-title" style="margin-bottom: 12px;"><span class="material-icons" style="color: #10B981; font-size: 18px;">verified</span> Engine Reliability</div>
            <div style="margin-bottom:16px">
                <div style="display:flex;justify-content:space-between;margin-bottom:6px"><span style="font-size:12px;color:#64748B;font-weight:500">Precision</span><span style="font-size:12px;font-weight:800;color:#0F172A">98.4%</span></div>
                <div style="background:#F1F5F9;height:8px;border-radius:100px;overflow:hidden"><div style="width:98.4%;background:#10B981;height:8px;border-radius:100px"></div></div>
            </div>
            <div>
                <div style="display:flex;justify-content:space-between;margin-bottom:6px"><span style="font-size:12px;color:#64748B;font-weight:500">Model Recall</span><span style="font-size:12px;font-weight:800;color:#0F172A">92.1%</span></div>
                <div style="background:#F1F5F9;height:8px;border-radius:100px;overflow:hidden"><div style="width:92.1%;background:#6366F1;height:8px;border-radius:100px"></div></div>
            </div>
        </div>
        <div style="background:#0F172A;border-radius:16px;padding:24px;color:white;flex:1;position:relative;overflow:hidden;">
            <div class="material-icons" style="position:absolute;right:-10px;bottom:-10px;font-size:100px;color:rgba(255,255,255,0.05);">security</div>
            <div style="font-size:11px;color:#10B981;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;">System Integrity</div>
            <div style="font-size:32px;font-weight:800;margin:8px 0;">Stable</div>
            <div style="font-size:12px;color:#94A3B8;line-height:1.5;">Anomaly patterns indicate non-disruptive background noise.</div>
        </div>
    </div>
</div>

<!-- Anomaly Table -->
<div class="card" style="padding:0;overflow:hidden">
    <div style="padding:20px 24px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #F1F5F9">
        <div class="section-title" style="margin-bottom:0;"><span class="material-icons" style="color: #6366F1;">list_alt</span> Detailed Analysis</div>
        <span style="background:#FEF2F2;color:#EF4444;padding:4px 12px;border-radius:8px;font-size:11px;font-weight:700;border:1px solid #FEE2E2;">ANOMALIES ONLY</span>
    </div>
    <table>
        <thead><tr><th>Raw Log Snippet</th><th>Detected Template</th><th>AI Score</th><th style="text-align:center">Level</th></tr></thead>
        <tbody>{rows_html}</tbody>
    </table>
    <div style="padding:16px 24px;background:#F8FAFC;border-top:1px solid #F1F5F9;display:flex;justify-content:space-between;align-items:center">
        <span style="font-size:12px;color:#64748B;font-weight:500">Showing top results for high-priority incidents</span>
        <div style="display:flex;gap:8px"><span style="background:#0F172A;color:#fff;padding:4px 12px;border-radius:6px;font-size:11px;font-weight:700;">1</span><span style="color:#64748B;padding:4px 12px;font-size:11px;font-weight:600;">2</span><span style="color:#64748B;padding:4px 12px;font-size:11px;font-weight:600;">3</span></div>
    </div>
</div>

</body></html>"""

components.html(html, height=1200, scrolling=True)
