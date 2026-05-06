import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

st.set_page_config(page_title="Explore | Log Analyzer", page_icon="🔍", layout="wide")
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
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px">
            <span style="background:{d_lb};color:{d_lc};padding:4px 12px;border-radius:4px;font-size:10px;font-weight:700">{d_lv}</span>
            <span style="color:#DC2626;font-size:12px;font-weight:700">⚠ Score: {d_sc:.2f}</span>
        </div>
        <div style="margin-bottom:16px">
            <div style="font-family:'Space Grotesk';font-size:9px;color:#888;text-transform:uppercase;font-weight:700;letter-spacing:.8px;margin-bottom:4px">Cluster ID</div>
            <div style="font-size:18px;font-weight:800;color:#222">{d_cl}</div>
        </div>
        <div style="margin-bottom:16px">
            <div style="font-family:'Space Grotesk';font-size:9px;color:#888;text-transform:uppercase;font-weight:700;letter-spacing:.8px;margin-bottom:4px">Full Raw Log</div>
            <div style="background:#1E293B;color:#A5F3FC;padding:12px;border-radius:4px;font-family:'Space Grotesk',monospace;font-size:11px;line-height:1.5;word-break:break-all">{d_raw}</div>
        </div>
        <div>
            <div style="font-family:'Space Grotesk';font-size:9px;color:#888;text-transform:uppercase;font-weight:700;letter-spacing:.8px;margin-bottom:4px">Parsed Template</div>
            <div style="background:#F9FAFB;border:1px solid #D1D5DB;padding:12px;border-radius:4px;font-family:'Space Grotesk',monospace;font-size:11px;color:#374151">{d_tpl}</div>
        </div>"""
else:
    detail = '<div style="color:#888;text-align:center;padding:40px">No entries match filters</div>'

html = f"""<!DOCTYPE html>
<html><head>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box;font-family:'Inter',sans-serif}}
body{{background:#F0F2F5;padding:16px}}
.card{{background:#fff;border:1px solid #D1D5DB;border-radius:4px;overflow:hidden}}
table{{width:100%;border-collapse:collapse}}
th{{text-align:left;font-family:'Space Grotesk';font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:#707978;padding:10px 14px;border-bottom:2px solid #D1D5DB;background:#F9FAFB}}
tr:hover{{background:#f0fffe!important}}
</style></head><body>

<div style="font-size:11px;color:#888;margin-bottom:12px;font-weight:500">{len(filt):,} logs found</div>

<div style="display:flex;gap:16px">
    <!-- Table -->
    <div class="card" style="flex:3">
        <table>
            <thead><tr><th>Message</th><th style="text-align:center">Level</th><th style="text-align:center">Cluster</th><th style="text-align:right">Score</th></tr></thead>
            <tbody>{rows}</tbody>
        </table>
        <div style="display:flex;justify-content:space-between;padding:10px 14px;background:#F9FAFB;border-top:1px solid #D1D5DB">
            <span style="font-size:10px;color:#888">Rows per page: 15</span>
            <span style="font-size:10px;color:#888">1–{min(15,len(filt))} of {len(filt):,}</span>
        </div>
    </div>
    
    <!-- Detail Panel -->
    <div style="flex:2;background:#fff;border:1px solid #D1D5DB;border-radius:4px;padding:20px">
        <div style="font-family:'Space Grotesk';font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:#404848;margin-bottom:16px">Log Details</div>
        {detail}
    </div>
</div>



</body></html>"""

components.html(html, height=800, scrolling=True)
