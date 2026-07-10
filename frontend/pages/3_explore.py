import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from components.ui_utils import apply_custom_styles, render_sidebar

st.set_page_config(page_title="Explore | Log Analyzer", layout="wide")
apply_custom_styles()
render_sidebar("explore")

LEVEL_NAMES = {0:"DEBUG",1:"INFO",2:"WARNING",3:"ERROR",4:"CRITICAL"}
LEVEL_COLORS = {"DEBUG":"#94A3B8","INFO":"#10B981","WARNING":"#F59E0B","ERROR":"#EF4444","CRITICAL":"#7F1D1D"}
LEVEL_BG = {"DEBUG":"#F1F5F9","INFO":"#ECFDF5","WARNING":"#FFFBEB","ERROR":"#FEF2F2","CRITICAL":"#FEF2F2"}

# Sidebar handled by ui_utils

if "df" not in st.session_state:
    st.markdown("""
    <div style="display:flex; justify-content:center; align-items:center; height:60vh;">
        <div style="background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%); border-radius: 24px; padding: 60px; text-align: center; max-width: 600px; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5), inset 0 0 0 1px rgba(255,255,255,0.05);">
            <div style="width: 80px; height: 80px; background: rgba(255,255,255,0.05); border-radius: 50%; display: flex; justify-content: center; align-items: center; margin: 0 auto 30px auto;">
                <span class="material-icons" style="font-size: 40px; color: #10B981;">manage_search</span>
            </div>
            <h2 style="font-family: 'Space Grotesk', sans-serif; font-size: 32px; font-weight: 700; color: white; margin-bottom: 16px;">Log Explorer Offline</h2>
            <p style="font-family: 'Inter', sans-serif; font-size: 16px; color: #94A3B8; line-height: 1.6;">Awaiting data stream. Please return to the Dashboard Overview and upload a log file to initialize data exploration.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

df = st.session_state["df"].copy()
if "log_level" in df.columns:
    df["level_name"] = df["log_level"].map(LEVEL_NAMES)

# Filters (native Streamlit for interactivity)
f1,f2,f3,f4 = st.columns(4)
with f1: lf = st.selectbox("Log Level",["All"]+list(LEVEL_NAMES.values()))
with f2:
    opts = ["All"]+(sorted([str(c) for c in df["cluster_id"].unique()]) if "cluster_id" in df.columns else [])
    cf = st.selectbox("Cluster ID", opts)
with f3: af = st.selectbox("Anomaly Status",["All","Flagged","Normal"])
with f4: sq = st.text_input("🔍 Search", placeholder="e.g. error, timeout")

filt = df.copy()
if lf!="All" and "level_name" in filt.columns: filt=filt[filt["level_name"]==lf]
if cf!="All" and "cluster_id" in filt.columns: filt=filt[filt["cluster_id"]==int(cf)]
if af=="Flagged" and "is_anomaly" in filt.columns: filt=filt[filt["is_anomaly"]==True]
elif af=="Normal" and "is_anomaly" in filt.columns: filt=filt[filt["is_anomaly"]==False]
if sq:
    m=filt["raw"].str.contains(sq,case=False,na=False)
    if "template" in filt.columns: m=m|filt["template"].str.contains(sq,case=False,na=False)
    filt=filt[m]

ddf = filt.head(15).reset_index(drop=True)

# Table rows
rows = ""
for i,row in ddf.iterrows():
    msg = str(row.get("raw",""))[:55].replace("<","&lt;").replace(">","&gt;")
    lv = LEVEL_NAMES.get(row.get("log_level",1),"INFO")
    lc = LEVEL_COLORS.get(lv,"#6B7280"); lb = LEVEL_BG.get(lv,"#F3F4F6")
    cl = row.get("cluster_id","-"); sc = row.get("anomaly_score",0)
    ie = lv in ("ERROR","CRITICAL")
    bg = "#FFF5F5" if ie else ("#F9FAFB" if i%2 else "#fff")
    rows += f"""<tr style="background:{bg};border-bottom:1px solid #eee;cursor:pointer" onclick="showDetail({i})">
        <td style="padding:10px 14px;font-family:'Space Grotesk',monospace;font-size:12px;color:{'#991B1B' if ie else '#374151'}">{msg}</td>
        <td style="padding:10px 14px;text-align:center"><span style="background:{lb};color:{lc};padding:2px 8px;border-radius:2px;font-size:9px;font-weight:700">{lv}</span></td>
        <td style="padding:10px 14px;text-align:center;font-size:12px;color:#6B7280">{cl}</td>
        <td style="padding:10px 14px;text-align:right;font-size:12px;font-weight:700;color:{'#DC2626' if abs(sc)>.5 else '#374151'}">{sc:.2f}</td>
    </tr>"""

# Detail panel
first = ddf.iloc[0] if len(ddf)>0 else None
if first is not None:
    d_lv = LEVEL_NAMES.get(first.get("log_level",1),"INFO")
    d_lc = LEVEL_COLORS.get(d_lv,"#6B7280"); d_lb = LEVEL_BG.get(d_lv,"#F3F4F6")
    d_sc = first.get("anomaly_score",0)
    d_raw = str(first.get("raw","")).replace("<","&lt;").replace(">","&gt;")
    d_tpl = str(first.get("template","")).replace("<","&lt;").replace(">","&gt;")
    d_tpl = d_tpl.replace("&lt;*&gt;","<span style='background:#CCFBF1;color:#0D4F4F;padding:1px 5px;border-radius:3px;font-weight:700'>&lt;*&gt;</span>")
    d_cl = first.get("cluster_id","N/A")
    detail = f"""
        <div style="display:flex; align-items:center; gap:12px; margin-bottom:24px;">
            <span style="background:{d_lb}; color:{d_lc}; padding:6px 16px; border-radius:8px; font-size:11px; font-weight:800; border: 1px solid rgba(0,0,0,0.05);">{d_lv}</span>
            <div style="height: 20px; width: 1px; background: #E2E8F0;"></div>
            <span style="color:#EF4444; font-size:13px; font-weight:700;">AI Score: {d_sc:.2f}</span>
        </div>
        
        <div style="margin-bottom:20px;">
            <div style="font-size:10px; color:#64748B; text-transform:uppercase; font-weight:700; letter-spacing:0.05em; margin-bottom:8px;">Cluster Context</div>
            <div style="font-size:16px; font-weight:800; color:#0F172A; display:flex; align-items:center; gap:6px;">
                <span class="material-icons" style="font-size:18px; color:#6366F1;">group_work</span>
                Node Cluster #{d_cl}
            </div>
        </div>

        <div style="margin-bottom:20px;">
            <div style="font-size:10px; color:#64748B; text-transform:uppercase; font-weight:700; letter-spacing:0.05em;">Trace Payload</div>
            <div class="code-block">{d_raw}</div>
        </div>

        <div>
            <div style="font-size:10px; color:#64748B; text-transform:uppercase; font-weight:700; letter-spacing:0.05em;">Semantic Template</div>
            <div style="background:#F8FAFC; border:1px solid #E2E8F0; padding:16px; border-radius:12px; font-family:'Inter',monospace; font-size:12px; color:#334155; margin-top:12px; line-height:1.6;">{d_tpl}</div>
        </div>"""
else:
    detail = '<div style="color:#888;text-align:center;padding:40px">No entries match filters</div>'

html = f"""<!DOCTYPE html>
<html><head>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box;font-family:'Inter',sans-serif}}
body{{background:transparent; padding:0; color:#1E293B;}}
.card{{background:#fff; border: 1px solid #E2E8F0; border-radius:16px; overflow:hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);}}
.section-title{{font-family:'Space Grotesk'; font-size:14px; font-weight:700; color:#0F172A; text-transform:uppercase; letter-spacing:0.05em; display:flex; align-items:center; gap:8px;}}
table{{width:100%; border-collapse:collapse;}}
th{{text-align:left; font-size:11px; font-weight:700; color:#64748B; text-transform:uppercase; padding:16px; border-bottom:2px solid #F1F5F9; background:#F8FAFC;}}
td{{padding:14px 16px; border-bottom:1px solid #F1F5F9; font-size:13px; color:#334155;}}
tr:hover{{background:#F0FDF4!important; cursor:pointer;}}
.detail-panel {{ background: white; border: 1px solid #E2E8F0; border-radius: 16px; padding: 24px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05); position: sticky; top: 0; }}
.code-block {{ background: #0F172A; color: #10B981; padding: 16px; border-radius: 12px; font-family: 'Inter', monospace; font-size: 12px; line-height: 1.6; white-space: pre-wrap; word-break: break-all; margin-top: 12px; border: 1px solid #1E293B; }}
</style></head><body>

<div style="font-family:'Space Grotesk'; font-size:12px; color:#64748B; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:16px;">{len(filt):,} logs indexed in current view</div>

<div style="display:flex; gap:24px; align-items: flex-start;">
    <!-- Table -->
    <div class="card" style="flex:3;">
        <table>
            <thead><tr><th>Log Message</th><th style="text-align:center;">Level</th><th style="text-align:center;">Cluster</th><th style="text-align:right;">AI Score</th></tr></thead>
            <tbody>{rows}</tbody>
        </table>
        <div style="padding:16px; background:#F8FAFC; border-top:1px solid #F1F5F9; display:flex; justify-content:space-between; align-items:center;">
            <span style="font-size:12px; color:#64748B; font-weight:500;">Viewing top 15 results</span>
            <div style="display:flex; gap:8px;"><span style="background:#0F172A; color:#fff; padding:4px 12px; border-radius:6px; font-size:11px; font-weight:700;">1</span><span style="color:#64748B; padding:4px 12px; font-size:11px; font-weight:600;">2</span><span style="color:#64748B; padding:4px 12px; font-size:11px; font-weight:600;">3</span></div>
        </div>
    </div>
    
    <!-- Detail Panel -->
    <div style="flex:2;">
        <div class="detail-panel">
            <div class="section-title" style="margin-bottom:20px;"><span class="material-icons" style="color: #10B981;">visibility</span> Diagnostic Data</div>
            {detail}
        </div>
    </div>
</div>

</body></html>"""

components.html(html, height=900, scrolling=True)
