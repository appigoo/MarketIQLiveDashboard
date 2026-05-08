import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import time
import json
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MarketIQ | Live Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS INJECTION ─────────────────────────────────────────────────────────────
def inject_css():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600;700&family=Noto+Sans+TC:wght@300;400;500;700&display=swap');

:root {
  --bg-primary:   #070b14;
  --bg-card:      #0d1526;
  --bg-card2:     #0a1020;
  --border:       rgba(0,212,255,0.15);
  --border-bright:rgba(0,212,255,0.40);
  --cyan:   #00d4ff;
  --gold:   #ffd700;
  --green:  #00ff88;
  --red:    #ff4757;
  --orange: #ff9f43;
  --text-primary: #e8f4f8;
  --text-dim:     #6b8a9e;
  --text-muted:   #3d5a6e;
}

/* ── GLOBAL ── */
html, body, [data-testid="stAppViewContainer"] {
  background: var(--bg-primary) !important;
  font-family: 'Noto Sans TC', sans-serif;
  color: var(--text-primary);
}
[data-testid="stAppViewContainer"]::before {
  content:'';
  position:fixed; inset:0;
  background-image:
    linear-gradient(rgba(0,212,255,0.03) 1px, transparent 1px),
    linear-gradient(90deg,rgba(0,212,255,0.03) 1px,transparent 1px);
  background-size:40px 40px;
  pointer-events:none; z-index:0;
}
[data-testid="stHeader"]        { background: transparent !important; }
[data-testid="stSidebar"]       { background: #0a1020 !important; border-right:1px solid var(--border); }
[data-testid="stSidebar"] *     { color: var(--text-primary) !important; }
.block-container                { padding: 1.5rem 2rem !important; max-width:100% !important; }
div[data-testid="stVerticalBlock"] { gap: 0.5rem; }

/* ── HIDE STREAMLIT CHROME ── */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"]  { display: none; }

/* ── HEADER BAND ── */
.iq-header {
  display:flex; align-items:center; justify-content:space-between;
  padding:14px 0 18px;
  border-bottom:1px solid var(--border);
  margin-bottom:20px;
}
.iq-logo {
  font-family:'IBM Plex Mono',monospace;
  font-size:24px; font-weight:700;
  color:var(--cyan); letter-spacing:4px;
  text-shadow:0 0 20px rgba(0,212,255,0.4);
}
.iq-logo span { color:var(--gold); }
.iq-badge {
  font-family:'IBM Plex Mono',monospace; font-size:10px;
  color:rgba(0,212,255,0.6); border:1px solid var(--border-bright);
  padding:3px 10px; border-radius:2px; letter-spacing:2px;
  text-transform:uppercase; margin-left:14px;
}
.iq-right { display:flex; align-items:center; gap:18px; }
.iq-live {
  display:flex; align-items:center; gap:8px;
  font-family:'IBM Plex Mono',monospace; font-size:11px;
  color:var(--green); letter-spacing:1px;
}
.iq-pulse {
  width:8px; height:8px; background:var(--green);
  border-radius:50%; box-shadow:0 0 8px var(--green);
  animation:pulse 1.5s ease infinite; display:inline-block;
}
@keyframes pulse {
  0%,100%{opacity:1;transform:scale(1)}
  50%{opacity:0.4;transform:scale(0.7)}
}
.iq-clock {
  font-family:'IBM Plex Mono',monospace; font-size:13px;
  color:var(--text-dim); letter-spacing:1px;
}
.iq-refresh {
  font-family:'IBM Plex Mono',monospace; font-size:10px;
  color:var(--gold); border:1px solid rgba(255,215,0,0.3);
  padding:4px 12px; border-radius:2px; letter-spacing:1px;
}

/* ── SCORE RING ── */
.score-wrap {
  background:var(--bg-card);
  border:1px solid var(--border-bright);
  border-radius:4px; padding:20px;
  position:relative; overflow:hidden;
  box-shadow:0 0 24px rgba(0,212,255,0.12),inset 0 0 40px rgba(0,212,255,0.03);
}
.score-wrap::before {
  content:''; position:absolute; top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,transparent,var(--cyan),transparent);
}
.score-inner { display:flex; align-items:center; gap:20px; }
.score-ring-svg { flex-shrink:0; }
.score-ring-svg svg { transform:rotate(-90deg); }
.score-ring-svg .s-track { fill:none; stroke:rgba(0,212,255,0.1); stroke-width:6; }
.score-ring-svg .s-fill  {
  fill:none; stroke:var(--cyan); stroke-width:6; stroke-linecap:round;
  stroke-dasharray:251.2; transition:stroke-dashoffset 0.8s ease;
  filter:drop-shadow(0 0 6px var(--cyan));
}
.score-num-label {
  font-family:'IBM Plex Mono',monospace; font-size:9px;
  color:var(--text-dim); letter-spacing:1px; margin-top:2px;
}

/* ── SUMMARY CARD ── */
.summary-card {
  background:var(--bg-card); border:1px solid var(--border);
  border-radius:4px; padding:18px 22px;
  position:relative; overflow:hidden; height:100%;
}
.summary-card::before {
  content:''; position:absolute; top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,var(--gold),transparent);
}
.summary-label {
  font-family:'IBM Plex Mono',monospace; font-size:10px;
  color:var(--gold); letter-spacing:2px; margin-bottom:10px;
  text-transform:uppercase;
}
.summary-body { font-size:13px; line-height:1.85; color:var(--text-primary); opacity:0.88; }
.hl  { color:var(--cyan);   font-weight:500; }
.wn  { color:var(--orange); font-weight:500; }
.rk  { color:var(--red);    font-weight:500; }

/* ── SIGNAL TAGS ── */
.sig-tags { display:flex; flex-wrap:wrap; gap:7px; margin-top:12px; }
.sig-tag {
  font-family:'IBM Plex Mono',monospace; font-size:9px;
  padding:3px 9px; border-radius:2px; letter-spacing:1px;
}
.sig-green  { background:rgba(0,255,136,0.08); border:1px solid rgba(0,255,136,0.3); color:var(--green); }
.sig-red    { background:rgba(255,71,87,0.08);  border:1px solid rgba(255,71,87,0.3);  color:var(--red); }
.sig-orange { background:rgba(255,159,67,0.08); border:1px solid rgba(255,159,67,0.3); color:var(--orange); }
.sig-cyan   { background:rgba(0,212,255,0.06);  border:1px solid var(--border-bright); color:var(--cyan); }

/* ── SECTION LABEL ── */
.sec-label {
  font-family:'IBM Plex Mono',monospace; font-size:10px;
  color:var(--text-muted); letter-spacing:3px; text-transform:uppercase;
  display:flex; align-items:center; gap:10px;
  margin:18px 0 10px;
}
.sec-label::after { content:''; flex:1; height:1px; background:var(--border); }

/* ── TICKER CARD ── */
.tc {
  background:var(--bg-card); border:1px solid var(--border);
  border-radius:4px; padding:12px 14px;
  position:relative; overflow:hidden;
  transition:border-color 0.2s, box-shadow 0.2s;
  cursor:default;
}
.tc:hover { border-color:var(--border-bright); box-shadow:0 0 20px rgba(0,212,255,0.15); }

.tc.up      { border-left:2px solid var(--green); }
.tc.dn      { border-left:2px solid var(--red); }
.tc.nt      { border-left:2px solid var(--text-muted); }
.tc.danger  { border-left:2px solid var(--red); background:rgba(255,71,87,0.04); }

/* Glow overlays for signal state */
.tc.sig-buy  { box-shadow:0 0 22px rgba(0,255,136,0.12),inset 0 0 28px rgba(0,255,136,0.04); }
.tc.sig-sell { box-shadow:0 0 22px rgba(255,71,87,0.12),inset 0 0 28px rgba(255,71,87,0.04); }
.tc.sig-watch{ box-shadow:0 0 18px rgba(255,159,67,0.10),inset 0 0 22px rgba(255,159,67,0.03); }

.tc-sym  { font-family:'IBM Plex Mono',monospace; font-size:12px; font-weight:600; color:var(--cyan); letter-spacing:1px; margin-bottom:3px; }
.tc-name { font-size:9px; color:var(--text-muted); margin-bottom:9px; }
.tc-price{ font-family:'IBM Plex Mono',monospace; font-size:17px; font-weight:600; color:var(--text-primary); line-height:1; margin-bottom:3px; }
.tc-chg  { font-family:'IBM Plex Mono',monospace; font-size:11px; font-weight:500; }
.tc-chg.pos { color:var(--green); }
.tc-chg.neg { color:var(--red); }
.tc-chg.neu { color:var(--text-dim); }
.tc-vol  { font-family:'IBM Plex Mono',monospace; font-size:8px; color:var(--text-muted); margin-top:5px; }

/* ── BREATHING DOT ── */
.bdot {
  position:absolute; top:10px; right:10px;
  width:10px; height:10px; border-radius:50%;
}
.bdot.green {
  background:var(--green); box-shadow:0 0 6px var(--green);
  animation:breatheG 2s ease-in-out infinite;
}
.bdot.red {
  background:var(--red); box-shadow:0 0 6px var(--red);
  animation:breatheR 0.8s ease-in-out infinite;
}
.bdot.orange {
  background:var(--orange); box-shadow:0 0 6px var(--orange);
  animation:breatheO 3s ease-in-out infinite;
}
.bdot.grey { background:var(--text-muted); }

@keyframes breatheG {
  0%,100%{opacity:1;transform:scale(1);box-shadow:0 0 6px 0 #00ff88,0 0 0 0 rgba(0,255,136,0.4)}
  50%{opacity:0.5;transform:scale(1.35);box-shadow:0 0 12px 4px #00ff88,0 0 20px 8px rgba(0,255,136,0.2)}
}
@keyframes breatheR {
  0%,100%{opacity:1;transform:scale(1);box-shadow:0 0 6px 0 #ff4757,0 0 0 0 rgba(255,71,87,0.4)}
  50%{opacity:0.4;transform:scale(1.45);box-shadow:0 0 14px 5px #ff4757,0 0 24px 10px rgba(255,71,87,0.2)}
}
@keyframes breatheO {
  0%,100%{opacity:1;box-shadow:0 0 8px var(--orange)}
  50%{opacity:0.55;box-shadow:0 0 16px var(--orange)}
}

/* ── MINI SPARKLINE ── */
.tc-spark { position:absolute; bottom:0; right:0; width:58px; height:28px; opacity:0.38; }

/* ── CHART CARD ── */
.chart-card {
  background:var(--bg-card); border:1px solid var(--border);
  border-radius:4px; padding:14px 18px; position:relative; overflow:hidden;
}
.chart-card::before {
  content:''; position:absolute; top:0;left:0;right:0;height:1px;
  background:linear-gradient(90deg,transparent,var(--cyan),transparent); opacity:0.5;
}
.chart-hdr { display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; }
.chart-title{ font-family:'IBM Plex Mono',monospace; font-size:11px; color:var(--cyan); letter-spacing:2px; text-transform:uppercase; }
.chart-val  { font-family:'IBM Plex Mono',monospace; font-size:11px; }

/* ── ALERT ROW ── */
.al-row {
  background:var(--bg-card); border:1px solid var(--border);
  border-radius:4px; padding:13px 16px; margin-bottom:8px;
  position:relative; overflow:hidden;
  animation:slideIn 0.3s ease;
}
@keyframes slideIn{from{opacity:0;transform:translateX(-8px)}to{opacity:1;transform:translateX(0)}}
.al-row.al-red    { border-left:3px solid var(--red);    box-shadow:-3px 0 14px rgba(255,71,87,0.15); }
.al-row.al-green  { border-left:3px solid var(--green);  box-shadow:-3px 0 14px rgba(0,255,136,0.15); }
.al-row.al-orange { border-left:3px solid var(--orange); box-shadow:-3px 0 14px rgba(255,159,67,0.15); }
.al-time  { font-family:'IBM Plex Mono',monospace; font-size:10px; color:var(--text-muted); }
.al-title { font-size:13px; font-weight:500; margin:4px 0; }
.al-body  { font-size:11px; color:var(--text-dim); line-height:1.7; }
.al-opp   { color:var(--green); font-weight:500; }
.al-risk  { color:var(--red);   font-weight:500; }
.al-adv   { color:var(--cyan);  font-weight:500; }

/* ── SIDEBAR ── */
.sb-card {
  background:var(--bg-card2); border:1px solid var(--border);
  border-radius:4px; padding:14px; margin-bottom:12px;
}
.sb-title {
  font-family:'IBM Plex Mono',monospace; font-size:10px; color:var(--cyan);
  letter-spacing:2px; text-transform:uppercase;
  margin-bottom:12px; padding-bottom:8px; border-bottom:1px solid var(--border);
}

/* dim bar */
.dim-bar-wrap { margin-bottom:7px; display:flex; align-items:center; gap:8px; }
.dim-bar-label { font-family:'IBM Plex Mono',monospace; font-size:9px; color:var(--text-dim); width:52px; letter-spacing:0.5px; }
.dim-bar-track { flex:1; height:4px; background:rgba(255,255,255,0.05); border-radius:2px; overflow:hidden; }
.dim-bar-fill  { height:100%; border-radius:2px; transition:width 0.8s ease; }
.dim-bar-val   { font-family:'IBM Plex Mono',monospace; font-size:9px; width:22px; text-align:right; }

/* legend rows */
.leg-row { display:flex; align-items:center; gap:10px; margin-bottom:10px; }
.leg-dot { width:10px; height:10px; border-radius:50%; flex-shrink:0; }
.leg-dot.green  { background:var(--green);  box-shadow:0 0 7px var(--green);  animation:breatheG 2s ease-in-out infinite; }
.leg-dot.red    { background:var(--red);    box-shadow:0 0 7px var(--red);    animation:breatheR 0.8s ease-in-out infinite; }
.leg-dot.orange { background:var(--orange); box-shadow:0 0 7px var(--orange); animation:breatheO 3s ease-in-out infinite; }
.leg-dot.grey   { background:var(--text-muted); }
.leg-name { font-size:12px; }
.leg-sub  { font-family:'IBM Plex Mono',monospace; font-size:9px; color:var(--text-muted); }

/* Streamlit widget overrides */
.stTextInput > div > div > input,
.stNumberInput > div > div > input {
  background: #070b14 !important;
  border: 1px solid var(--border) !important;
  color: var(--text-primary) !important;
  font-family: 'IBM Plex Mono', monospace !important;
  border-radius: 3px !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
  border-color: var(--border-bright) !important;
  box-shadow: none !important;
}
.stButton > button {
  background: linear-gradient(135deg,rgba(0,212,255,0.15),rgba(0,212,255,0.05)) !important;
  border: 1px solid var(--border-bright) !important;
  color: var(--cyan) !important;
  font-family: 'IBM Plex Mono', monospace !important;
  letter-spacing: 2px !important;
  border-radius: 3px !important;
  width: 100% !important;
}
.stButton > button:hover {
  background: rgba(0,212,255,0.2) !important;
  box-shadow: 0 0 16px rgba(0,212,255,0.25) !important;
}
.stToggle > label { color: var(--text-primary) !important; font-size:12px !important; }
div[data-testid="stMetric"] { background:transparent !important; }
.stSelectbox > div > div { background:#070b14 !important; border:1px solid var(--border) !important; color:var(--text-primary) !important; }

/* plotly chart background */
.js-plotly-plot .plotly { background:transparent !important; }

hr { border-color: var(--border) !important; margin: 8px 0 !important; }

/* ── AI PROMPT BUTTONS ── */
.ai-prompt-wrap {
  margin-top: 14px;
  padding: 16px 22px 18px;
  background: var(--bg-card2);
  border: 1px solid var(--border);
  border-radius: 4px;
  position: relative;
  overflow: hidden;
}
.ai-prompt-wrap::before {
  content:''; position:absolute; top:0;left:0;right:0;height:1px;
  background:linear-gradient(90deg,transparent,rgba(255,215,0,0.4),transparent);
}
.ai-prompt-label {
  font-family:'IBM Plex Mono',monospace; font-size:10px;
  color:var(--gold); letter-spacing:2px; text-transform:uppercase;
  margin-bottom:12px;
}
.ai-btn-row {
  display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 10px;
}
.ai-btn {
  display: flex; align-items: center; gap: 8px;
  padding: 9px 18px; border-radius: 3px;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 12px; font-weight: 600;
  letter-spacing: 1px; cursor: pointer;
  border: 1px solid; transition: all 0.2s;
  text-decoration: none; white-space: nowrap;
}
.ai-btn:hover { transform: translateY(-1px); }

.ai-btn-claude {
  background: rgba(204,120,92,0.12);
  border-color: rgba(204,120,92,0.45);
  color: #cc785c;
}
.ai-btn-claude:hover {
  background: rgba(204,120,92,0.22);
  box-shadow: 0 0 16px rgba(204,120,92,0.25);
}
.ai-btn-chatgpt {
  background: rgba(16,163,127,0.12);
  border-color: rgba(16,163,127,0.45);
  color: #10a37f;
}
.ai-btn-chatgpt:hover {
  background: rgba(16,163,127,0.22);
  box-shadow: 0 0 16px rgba(16,163,127,0.25);
}
.ai-btn-gemini {
  background: rgba(66,133,244,0.12);
  border-color: rgba(66,133,244,0.45);
  color: #4285f4;
}
.ai-btn-gemini:hover {
  background: rgba(66,133,244,0.22);
  box-shadow: 0 0 16px rgba(66,133,244,0.25);
}
.ai-btn-grok {
  background: rgba(255,255,255,0.06);
  border-color: rgba(255,255,255,0.25);
  color: #e8f4f8;
}
.ai-btn-grok:hover {
  background: rgba(255,255,255,0.12);
  box-shadow: 0 0 16px rgba(255,255,255,0.12);
}
.ai-hint {
  font-family:'IBM Plex Mono',monospace; font-size:9px;
  color:var(--text-muted); letter-spacing:0.5px; margin-top:8px;
}
.ai-hint span { color: var(--cyan); }

/* prompt preview box */
.prompt-preview {
  margin-top: 12px;
  background: var(--bg-primary);
  border: 1px solid var(--border);
  border-radius: 3px;
  padding: 12px 14px;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10px;
  color: var(--text-dim);
  line-height: 1.7;
  max-height: 160px;
  overflow-y: auto;
  white-space: pre-wrap;
  letter-spacing: 0.3px;
}
</style>
""", unsafe_allow_html=True)

# ── CONSTANTS ─────────────────────────────────────────────────────────────────
TICKERS = {
    "大盤指數 ETF":   ["SPY","QQQ","DIA","IWM"],
    "恐慌/做空":      ["^VIX","UVXY","SQQQ"],
    "債券/美元/商品": ["TLT","DX-Y.NYB","GLD","USO"],
    "板塊/信用":      ["HYG","XLF","XLK","ARKK"],
    "龍頭個股":       ["NVDA","AAPL","MSFT","AMZN","META","GOOGL","TSLA",
                       "AVGO","TSM","WMT","LLY","JPM","V","MA"],
}

TICKER_NAMES = {
    "SPY":"S&P 500 ETF","QQQ":"Nasdaq 100 ETF","DIA":"道瓊斯 ETF","IWM":"羅素2000 ETF",
    "^VIX":"恐慌指數","UVXY":"VIX期貨 2x","SQQQ":"納指3x做空",
    "TLT":"20Y 美債 ETF","DX-Y.NYB":"美元指數","GLD":"黃金 ETF","USO":"原油 ETF",
    "HYG":"高收益債 ETF","XLF":"金融板塊 ETF","XLK":"科技板塊 ETF","ARKK":"ARK創新 ETF",
    "NVDA":"Nvidia","AAPL":"Apple","MSFT":"Microsoft","AMZN":"Amazon",
    "META":"Meta","GOOGL":"Alphabet","TSLA":"Tesla","AVGO":"Broadcom",
    "TSM":"TSMC","WMT":"Walmart","LLY":"Eli Lilly","JPM":"JPMorgan",
    "V":"Visa","MA":"Mastercard",
}

DISPLAY_SYM = {t: t.replace("^","").replace("-Y.NYB","") for t in sum(TICKERS.values(),[])}

ALL_TICKERS = sum(TICKERS.values(), [])

ALERT_DEFS = [
    {"id":"vix_up",    "name":"🔴 VIX 急升",    "cond":"VIX >15% 單日漲幅",  "color":"red"},
    {"id":"vix_dn",    "name":"🟢 VIX 急跌",    "cond":"VIX >10% 單日跌幅",  "color":"green"},
    {"id":"spy_dn",    "name":"🔴 大盤急跌",     "cond":"SPY < -2%",          "color":"red"},
    {"id":"spy_up",    "name":"🟢 大盤急漲",     "cond":"SPY > +2%",          "color":"green"},
    {"id":"uvxy_up",   "name":"🔴 恐慌爆發",     "cond":"UVXY >20%",          "color":"red"},
    {"id":"tlt_div",   "name":"🟡 債股背離",     "cond":"TLT↑ + SPY↓",       "color":"orange"},
    {"id":"dxy_up",    "name":"🟡 美元衝擊",     "cond":"DXY >+1%",           "color":"orange"},
    {"id":"gld_up",    "name":"🟡 黃金避險",     "cond":"GLD >+1.5%",         "color":"orange"},
    {"id":"xlk_dn",    "name":"🔴 科技領跌",     "cond":"XLK < -2%",          "color":"red"},
    {"id":"hyg_dn",    "name":"🟡 信用收縮",     "cond":"HYG < -1%",          "color":"orange"},
    {"id":"mega_dn",   "name":"🔴 龍頭崩跌",     "cond":"NVDA/AAPL < -4%",   "color":"red"},
    {"id":"all_bull",  "name":"🟢 全面機會",     "cond":"VIX<15+SPY均線+HYG穩","color":"green"},
]

ALERT_CONTENT = {
    "vix_up": {
        "opp":"短線可買 Put 或做多 UVXY；若 VIX 超過 30，考慮反手抄底 NVDA / QQQ Call，往往更賺錢。",
        "risk":"波動極端放大，方向一錯幾小時內可大虧；UVXY 和 Options 有時間衰減與高槓桿，追高最容易被瞬間反殺。",
        "adv":"觀察 VIX 是否突破 30/40 極端區，超過考慮分批建倉優質股 Call；突破 20 前勿輕易追多科技股。"
    },
    "vix_dn": {
        "opp":"恐慌消退，風險偏好回升，QQQ / SPY 短線反彈概率大；做多 TQQQ 或買 SPY Call 勝率提升。",
        "risk":"假跌後反彈，VIX 可能二次急升；不宜重倉，需確認 SPY 站穩均線才入場。",
        "adv":"等 VIX 回落至 20 以下，配合 SPY 放量突破確認再入場，分批建倉降低風險。"
    },
    "spy_dn": {
        "opp":"短線做空機會（買 SPY Put / 做多 SQQQ）；若跌至強支撐，可考慮分批佈局長線。",
        "risk":"急跌可能是開端而非結束，抄底時機難判；止損必須嚴格，否則越攤越虧。",
        "adv":"先觀察成交量，放量下跌避免抄底；縮量下跌可考慮小倉試探，止損設前低下方 0.5%。"
    },
    "spy_up": {
        "opp":"動能交易做多 QQQ / TQQQ；板塊輪動中尋找滯漲股補漲機會，金融/能源值得關注。",
        "risk":"單日急漲後次日回撤概率高；追高成本大，若無持續資金跟進易被套在高位。",
        "adv":"不追高，等當日收盤確認；次日回測不破高點才加倉，用 Call Spread 降低權利金成本。"
    },
    "uvxy_up": {
        "opp":"市場極端恐慌通常是短期底部訊號；UVXY 因 VIX 期貨結構長期必跌，極端高位可做空。",
        "risk":"做空 UVXY 需足夠保證金，極端行情可繼續飆升數倍；倉位管理極重要，切忌重倉。",
        "adv":"不建議追多 UVXY；可小倉做多優質股 Call，等 VIX 回落後收益更穩，風險更低。"
    },
    "tlt_div": {
        "opp":"資金從股市流入債市，防守型配置（GLD / TLT）短線佔優；可做多 TLT 或 GLD 對沖。",
        "risk":"若因聯儲加息預期改變導致，股市下行壓力可持續數週甚至數月，不可輕視。",
        "adv":"減少進攻型倉位，增加 GLD / TLT 對沖比例；等 SPY 重回均線再重新佈局股票多倉。"
    },
    "dxy_up": {
        "opp":"美元強勢時，金融股（XLF）短線可能受惠；可關注 XLF 是否同步走強作確認。",
        "risk":"美元急升對黃金、科技股、新興市場打壓明顯；NVDA / AAPL 等跨國收入企業受損。",
        "adv":"迴避 GLD 和高估值科技股；聚焦美國內需型標的，等 DXY 穩定後再評估科技股入場機會。"
    },
    "gld_up": {
        "opp":"避險情緒升溫，GLD 短線動能強；可順勢做多 GLD 或 GDX（金礦股 ETF）放大收益。",
        "risk":"黃金急升若因地緣政治，事件解除後可能快速回落；不宜重倉追高，需設好止損。",
        "adv":"已持倉可持有；新入場者等小幅回調確認支撐後再買，止損設近期低點下方 1%。"
    },
    "xlk_dn": {
        "opp":"科技股急跌後若 NVDA / MSFT 基本面未變，中長線佈局機會；可掃描超賣個股逢低吸納。",
        "risk":"科技板塊佔 QQQ 比重極高，XLK 持續弱勢會拖垮整體大盤；不能輕視連鎖反應。",
        "adv":"暫停科技股新多倉；等 XLK 回測 20 日均線獲支撐再評估入場，以 Call Spread 控制成本。"
    },
    "hyg_dn": {
        "opp":"高收益債走弱是市場壓力前兆，可提前佈局防守（TLT / GLD）或做空（SQQQ）。",
        "risk":"HYG 下跌預示企業違約風險上升，若持續下跌將引發更大拋售潮；早期預警勿忽視。",
        "adv":"減少高 Beta 股票倉位，增加現金比例；這是早期預警信號，比大盤崩跌早 1-2 週出現。"
    },
    "mega_dn": {
        "opp":"龍頭股急跌若非基本面惡化，往往是最好的低吸機會；可分批建倉 Call 或股票。",
        "risk":"龍頭帶頭下跌會引發板塊性連鎖反應；若同時 VIX 急升，下跌可能遠未結束。",
        "adv":"先確認是否有負面消息；無消息面利空則考慮小倉低吸，止損設前低下方，跌破不戀戰。"
    },
    "all_bull": {
        "opp":"三項同時達標是最清晰的做多環境；QQQ / SPY 趨勢多倉，龍頭股（NVDA / AAPL）加倉。",
        "risk":"過度樂觀時市場往往已在高位；VIX 極低時 Options 權利金昂貴，買 Call 需注意成本。",
        "adv":"順勢做多為主，適當用 Call Spread 代替裸 Call 降低成本；設好移動止盈，不要戀戰高位。"
    },
}

# ── SESSION STATE ─────────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "data": {},
        "hist": {},
        "alert_log": [],
        "alert_cooldown": {},
        "last_fetch": 0,
        "alert_enabled": {a["id"]: True for a in ALERT_DEFS},
        "all_alerts_on": True,
        "tg_token": "",
        "tg_chat_id": "",
        "refresh_interval": 60,
        "cooldown_min": 30,
        "fetch_count": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# ── DATA FETCH ────────────────────────────────────────────────────────────────
def fetch_single(ticker):
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="7d", interval="1d", auto_adjust=True)
        if hist.empty:
            return ticker, None, None
        # flatten MultiIndex if present
        if isinstance(hist.columns, pd.MultiIndex):
            hist.columns = hist.columns.get_level_values(0)
        close = hist["Close"].dropna()
        vol   = hist["Volume"].dropna()
        if len(close) < 2:
            return ticker, None, None
        price   = float(close.iloc[-1])
        prev    = float(close.iloc[-2])
        chg_pct = (price - prev) / prev * 100
        volume  = float(vol.iloc[-1]) if len(vol) else 0
        ma5  = float(close.tail(5).mean())  if len(close) >= 5  else price
        ma20 = float(close.tail(20).mean()) if len(close) >= 20 else price
        spark = list(close.tail(7).values)
        return ticker, {
            "price": price, "prev": prev, "chg": chg_pct,
            "volume": volume, "ma5": ma5, "ma20": ma20,
        }, spark
    except Exception:
        return ticker, None, None

@st.cache_data(ttl=58)
def fetch_all_cached(_count):
    data, hist = {}, {}
    with ThreadPoolExecutor(max_workers=12) as ex:
        futures = {ex.submit(fetch_single, t): t for t in ALL_TICKERS}
        for f in as_completed(futures):
            ticker, d, spark = f.result()
            if d:
                data[ticker] = d
                hist[ticker] = spark
    return data, hist

# ── SIGNAL LOGIC ──────────────────────────────────────────────────────────────
def get_signal(ticker, d):
    if not d:
        return "grey", "normal"
    chg = d["chg"]
    # Special inverse logic for fear instruments
    if ticker in ["^VIX","UVXY"]:
        if chg > 8:   return "red",   "sell"
        if chg < -8:  return "green",  "buy"
        if chg > 4:   return "orange", "watch"
        return "grey", "normal"
    if ticker == "SQQQ":
        if chg > 3:   return "red",   "sell"
        if chg < -3:  return "green",  "buy"
        return "grey", "normal"
    # Normal logic
    if chg >= 2.0:   return "green",  "buy"
    if chg <= -2.0:  return "red",    "sell"
    if chg >= 0.8:   return "green",  "buy"
    if chg <= -0.8:  return "red",    "sell"
    if abs(chg) >= 0.4: return "orange","watch"
    return "grey", "normal"

# ── MARKET SCORE ──────────────────────────────────────────────────────────────
def calc_market_score(data):
    scores = {}
    d = data

    def g(t): return d.get(t, {})

    # 1. Trend: SPY & QQQ vs MA
    spy = g("SPY"); qqq = g("QQQ")
    trend = 5.0
    if spy:
        if spy["price"] > spy["ma20"]: trend += 1.5
        if spy["chg"] > 0:             trend += 0.5
    if qqq:
        if qqq["price"] > qqq["ma20"]: trend += 1.5
        if qqq["chg"] > 0:             trend += 1.0
    trend = min(10, trend)
    scores["趨勢方向"] = trend

    # 2. Fear: VIX
    vix = g("^VIX")
    fear = 5.0
    if vix:
        v = vix["price"]
        if   v < 13: fear = 9.0
        elif v < 17: fear = 7.5
        elif v < 20: fear = 5.5
        elif v < 25: fear = 4.0
        elif v < 30: fear = 2.5
        else:        fear = 1.0
    scores["恐慌程度"] = fear

    # 3. Rotation: XLK vs XLF vs IWM
    xlk = g("XLK"); xlf = g("XLF"); iwm = g("IWM")
    rot = 5.0
    if xlk and xlk["chg"] > 1: rot += 1.5
    if xlf and xlf["chg"] > 0: rot += 1.0
    if iwm and iwm["chg"] > 0: rot += 1.0
    if xlk and xlk["chg"] < -1: rot -= 2.0
    rot = max(0, min(10, rot))
    scores["資金輪動"] = rot

    # 4. Bond-Stock: TLT vs SPY
    tlt = g("TLT")
    bond = 5.0
    if tlt and spy:
        if tlt["chg"] > 0.5 and spy["chg"] < 0: bond = 3.0  # diverge
        elif tlt["chg"] < 0 and spy["chg"] > 0: bond = 7.5  # healthy
        elif tlt["chg"] > 0 and spy["chg"] > 0: bond = 6.0
        else: bond = 4.5
    scores["債股關係"] = bond

    # 5. Dollar: DXY
    dxy = g("DX-Y.NYB")
    dollar = 5.0
    if dxy:
        if dxy["chg"] > 1.0:  dollar = 3.0
        elif dxy["chg"] > 0.5: dollar = 4.0
        elif dxy["chg"] < -0.5: dollar = 7.0
        else: dollar = 5.5
    scores["美元影響"] = dollar

    # 6. Credit: HYG
    hyg = g("HYG")
    credit = 5.0
    if hyg:
        if hyg["chg"] > 0.3:  credit = 8.0
        elif hyg["chg"] > 0:  credit = 6.5
        elif hyg["chg"] < -1: credit = 2.0
        elif hyg["chg"] < -0.5: credit = 3.5
    scores["信用風險"] = credit

    # 7. Mega leadership: NVDA + AAPL
    nvda = g("NVDA"); aapl = g("AAPL")
    mega = 5.0
    if nvda:
        if nvda["chg"] > 2: mega += 2.0
        elif nvda["chg"] > 0: mega += 0.5
        elif nvda["chg"] < -3: mega -= 2.5
        elif nvda["chg"] < -1: mega -= 1.0
    if aapl:
        if aapl["chg"] > 1: mega += 1.5
        elif aapl["chg"] < -2: mega -= 1.5
    mega = max(0, min(10, mega))
    scores["龍頭健康"] = mega

    weights = [0.20, 0.18, 0.14, 0.12, 0.12, 0.12, 0.12]
    vals    = list(scores.values())
    total   = sum(w * v for w, v in zip(weights, vals)) * 10
    total   = max(0, min(100, total))
    return round(total), scores

def get_market_status(score):
    if   score >= 80: return "🚀 強勢做多", "green"
    elif score >= 65: return "📈 謹慎偏多", "cyan"
    elif score >= 50: return "⚖️ 中性觀望", "orange"
    elif score >= 35: return "⚠️ 防守偏空", "orange"
    else:             return "🔴 極端風險", "red"

def build_analysis(data, score, scores):
    d = data
    def g(t): return d.get(t, {})
    spy  = g("SPY");  vix = g("^VIX"); tlt = g("TLT")
    xlk  = g("XLK");  hyg = g("HYG"); gld = g("GLD")
    nvda = g("NVDA"); dxy = g("DX-Y.NYB")

    lines = []

    # Trend
    if spy:
        trend_word = "站穩" if spy["price"] > spy.get("ma20", spy["price"]) else "跌破"
        lines.append(f'大盤 <span class="hl">SPY {trend_word} 20 日均線</span>，'
                     f'當日漲跌 <span class="{"hl" if spy["chg"]>0 else "rk"}">'
                     f'{"▲" if spy["chg"]>0 else "▼"}{abs(spy["chg"]):.2f}%</span>。')

    # VIX
    if vix:
        v = vix["price"]
        if v < 15:
            vix_comment = f'VIX 報 <span class="hl">{v:.1f}</span>，市場情緒貪婪，做多環境佳。'
        elif v < 20:
            vix_comment = f'VIX 報 <span class="wn">{v:.1f}</span>，中性偏高，市場存在分歧，需謹慎。'
        elif v < 30:
            vix_comment = f'VIX 報 <span class="rk">{v:.1f}</span>，恐慌升溫，建議降低倉位。'
        else:
            vix_comment = f'VIX 報 <span class="rk">{v:.1f}</span>，市場極端恐慌！逢低機會臨近但風險極大。'
        lines.append(vix_comment)

    # TLT / Bond-Stock
    if tlt and spy:
        if tlt["chg"] > 0.4 and spy["chg"] < 0:
            lines.append('⚠️ <span class="wn">債股背離警示</span>：TLT 上漲同時 SPY 下跌，資金向避險資產轉移，需提高警覺。')
        elif tlt["chg"] < 0 and spy["chg"] > 0:
            lines.append('債券回落、股市上漲，<span class="hl">風險偏好健康</span>，利於做多。')

    # XLK / Tech leadership
    if xlk:
        if xlk["chg"] > 1.5:
            lines.append(f'科技板塊 XLK <span class="hl">強勢領漲 +{xlk["chg"]:.1f}%</span>，大盤動能充足。')
        elif xlk["chg"] < -1.5:
            lines.append(f'科技板塊 XLK <span class="rk">領跌 {xlk["chg"]:.1f}%</span>，警惕連鎖拋售。')

    # GLD / Safe haven
    if gld and gld["chg"] > 1.2:
        lines.append(f'黃金 GLD <span class="wn">急升 +{gld["chg"]:.1f}%</span>，避險需求升溫，地緣或通脹壓力值得關注。')

    # Credit HYG
    if hyg:
        if hyg["chg"] > 0.2:
            lines.append('高收益債 HYG 穩定，<span class="hl">企業信用風險可控</span>，市場流動性正常。')
        elif hyg["chg"] < -0.8:
            lines.append('⚠️ 高收益債 HYG 下跌，<span class="rk">信用風險上升</span>，或預示更大拋售。')

    # DXY
    if dxy and abs(dxy["chg"]) > 0.5:
        word = "走強" if dxy["chg"] > 0 else "走弱"
        impact = "對黃金及科技股形成壓力" if dxy["chg"] > 0 else "利好黃金及新興市場"
        lines.append(f'美元 DXY <span class="wn">{word} {dxy["chg"]:+.2f}%</span>，{impact}。')

    # NVDA leading indicator
    if nvda:
        if nvda["chg"] > 3:
            lines.append(f'AI 龍頭 NVDA <span class="hl">爆發 +{nvda["chg"]:.1f}%</span>，半導體板塊情緒高漲。')
        elif nvda["chg"] < -3:
            lines.append(f'NVDA <span class="rk">重挫 {nvda["chg"]:.1f}%</span>，AI 板塊承壓，需警惕科技股連鎖下跌。')

    # Summary conclusion
    if score >= 70:
        lines.append(f'<b>整體評估：</b>市場評分 <span class="hl">{score}/100</span>，<span class="hl">順勢偏多為主</span>，倉位可維持七至八成。')
    elif score >= 50:
        lines.append(f'<b>整體評估：</b>市場評分 <span class="wn">{score}/100</span>，建議<span class="wn">半倉中性觀望</span>，等待明確方向。')
    else:
        lines.append(f'<b>整體評估：</b>市場評分 <span class="rk">{score}/100</span>，建議<span class="rk">輕倉防守</span>，現金為王。')

    return " ".join(lines)

def build_tags(data, score):
    d = data
    tags = []
    spy = d.get("SPY",{}); vix_d = d.get("^VIX",{}); hyg = d.get("HYG",{}); xlk = d.get("XLK",{})
    if spy and spy["price"] > spy.get("ma20", 0): tags.append(("✅ 大盤站均線","sig-green"))
    else: tags.append(("⚠️ 大盤跌破均線","sig-red"))
    if vix_d:
        v = vix_d["price"]
        if v < 15:   tags.append(("😊 VIX 低位貪婪","sig-green"))
        elif v < 20: tags.append(("😐 VIX 中性偏高","sig-orange"))
        else:        tags.append(("😱 VIX 恐慌區","sig-red"))
    if xlk and xlk["chg"] > 1: tags.append(("💹 科技強勢","sig-cyan"))
    elif xlk and xlk["chg"] < -1: tags.append(("📉 科技承壓","sig-red"))
    if hyg and hyg["chg"] > 0: tags.append(("✅ 信用穩定","sig-green"))
    elif hyg and hyg["chg"] < -0.5: tags.append(("⚠️ 信用收縮","sig-orange"))
    gld = d.get("GLD",{})
    if gld and gld["chg"] > 1.2: tags.append(("🔶 黃金避險升溫","sig-orange"))
    return tags

# ── AI PROMPT BUILDER ────────────────────────────────────────────────────────
def build_ai_prompt(data, score, scores, status_text):
    d = data
    def g(t): return d.get(t, {})
    def fmt(t):
        dd = g(t)
        sym = DISPLAY_SYM.get(t, t)
        if not dd: return f"• {sym}: 數據載入中"
        p = dd["price"]; c = dd["chg"]
        sign = "▲" if c > 0 else ("▼" if c < 0 else "▶")
        return f"• {sym}: ${p:,.2f} ({sign}{abs(c):.2f}%)"

    dim_lines = "\n".join([f"• {k}：{v:.1f}/10" for k,v in scores.items()])

    etf_lines  = "\n".join([fmt(t) for t in TICKERS["大盤指數 ETF"]])
    fear_lines = "\n".join([fmt(t) for t in TICKERS["恐慌/做空"]])
    bond_lines = "\n".join([fmt(t) for t in TICKERS["債券/美元/商品"]])
    sec_lines  = "\n".join([fmt(t) for t in TICKERS["板塊/信用"]])
    mega_lines = "\n".join([fmt(t) for t in TICKERS["龍頭個股"]])

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    prompt = f"""請作為頂級美股交易分析師，根據以下【即時市場數據】給我一份深度分析報告。

═══════════════════════════════════
📊 MarketIQ 即時數據 — {now_str}
市場綜合評分：{score}/100（{status_text}）
═══════════════════════════════════

【大盤指數 ETF】
{etf_lines}

【恐慌 / 做空指標】
{fear_lines}

【債券 / 美元 / 商品】
{bond_lines}

【板塊 / 信用】
{sec_lines}

【龍頭個股】
{mega_lines}

【七維度量化評分】
{dim_lines}

═══════════════════════════════════
請根據以上數據，提供：

1️⃣ 【市場結構判斷】
   當前處於什麼市場格局？牛市/熊市/震盪？關鍵支撐阻力在哪？

2️⃣ 【最大機會】
   現在最值得關注的做多/做空機會是什麼？具體標的？

3️⃣ 【最大風險】
   當前最需要警惕的風險訊號是什麼？可能觸發什麼連鎖反應？

4️⃣ 【未來 24-48 小時走勢預判】
   最可能的走勢路徑？需要關注的關鍵事件？

5️⃣ 【具體操作建議】
   - 標的：
   - 方向（做多/做空）：
   - 建議倉位（%）：
   - 入場價區間：
   - 止損位：
   - 目標位：

6️⃣ 【板塊輪動提示】
   哪些板塊資金正在流入/流出？如何佈局？

請用繁體中文回答，分析要有深度、有數據支撐、有明確結論。"""

    return prompt

# ── ALERT CHECK ───────────────────────────────────────────────────────────────
def check_alerts(data, enabled, cooldown_min):
    triggered = []
    now = datetime.now()
    cd_seconds = cooldown_min * 60
    d = data
    def g(t): return d.get(t, {})
    def cooled(aid):
        last = st.session_state.alert_cooldown.get(aid)
        return (not last) or ((now - last).total_seconds() > cd_seconds)
    def fire(aid, title, extra=""):
        if enabled.get(aid, True) and cooled(aid):
            st.session_state.alert_cooldown[aid] = now
            triggered.append({"id":aid,"title":title,"time":now.strftime("%H:%M:%S"),"extra":extra})

    vix = g("^VIX"); spy = g("SPY"); uvxy = g("UVXY")
    tlt = g("TLT"); dxy = g("DX-Y.NYB"); gld = g("GLD")
    xlk = g("XLK"); hyg = g("HYG"); nvda = g("NVDA"); aapl = g("AAPL")

    if vix and vix["chg"] > 15:  fire("vix_up",  f'VIX 急升 +{vix["chg"]:.1f}% → {vix["price"]:.2f}')
    if vix and vix["chg"] < -10: fire("vix_dn",  f'VIX 急跌 {vix["chg"]:.1f}% → {vix["price"]:.2f}')
    if spy and spy["chg"] < -2:  fire("spy_dn",  f'SPY 急跌 {spy["chg"]:.1f}% → ${spy["price"]:.2f}')
    if spy and spy["chg"] > 2:   fire("spy_up",  f'SPY 急漲 +{spy["chg"]:.1f}% → ${spy["price"]:.2f}')
    if uvxy and uvxy["chg"] > 20: fire("uvxy_up", f'UVXY 恐慌爆發 +{uvxy["chg"]:.1f}%')
    if tlt and spy and tlt["chg"] > 0.4 and spy["chg"] < -0.5:
        fire("tlt_div", f'TLT +{tlt["chg"]:.1f}% / SPY {spy["chg"]:.1f}% — 債股背離')
    if dxy and dxy["chg"] > 1:   fire("dxy_up",  f'DXY 急升 +{dxy["chg"]:.1f}% → {dxy["price"]:.2f}')
    if gld and gld["chg"] > 1.5: fire("gld_up",  f'GLD 急升 +{gld["chg"]:.1f}% → ${gld["price"]:.2f}')
    if xlk and xlk["chg"] < -2:  fire("xlk_dn",  f'XLK 領跌 {xlk["chg"]:.1f}%')
    if hyg and hyg["chg"] < -1:  fire("hyg_dn",  f'HYG 信用收縮 {hyg["chg"]:.1f}%')
    if nvda and nvda["chg"] < -4: fire("mega_dn", f'NVDA 崩跌 {nvda["chg"]:.1f}%')
    elif aapl and aapl["chg"] < -4: fire("mega_dn", f'AAPL 崩跌 {aapl["chg"]:.1f}%')
    # Bull signal
    vix_ok = vix and vix["price"] < 15
    spy_ok  = spy and spy["price"] > spy.get("ma20", 0)
    hyg_ok  = hyg and hyg["chg"] > -0.3
    if vix_ok and spy_ok and hyg_ok:
        fire("all_bull", "🟢 全面做多信號：VIX<15 + SPY站均線 + HYG穩定")

    return triggered

# ── TELEGRAM ──────────────────────────────────────────────────────────────────
def send_telegram(token, chat_id, alert):
    if not token or not chat_id:
        return False
    ac = ALERT_CONTENT.get(alert["id"], {})
    icon = "🔴" if ALERT_DEFS[[a["id"] for a in ALERT_DEFS].index(alert["id"])]["color"]=="red" else (
           "🟢" if ALERT_DEFS[[a["id"] for a in ALERT_DEFS].index(alert["id"])]["color"]=="green" else "🟡")
    msg = (
        f"{icon} *MarketIQ 警報* — {alert['time']}\n\n"
        f"*{alert['title']}*\n\n"
        f"📈 *【機會】*\n{ac.get('opp','')}\n\n"
        f"⚠️ *【風險】*\n{ac.get('risk','')}\n\n"
        f"💡 *【建議】*\n{ac.get('adv','')}"
    )
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        resp = requests.post(url, json={
            "chat_id": chat_id, "text": msg,
            "parse_mode": "Markdown"
        }, timeout=8)
        return resp.status_code == 200
    except Exception:
        return False

# ── SPARKLINE SVG ─────────────────────────────────────────────────────────────
def make_spark(values, color):
    if not values or len(values) < 2:
        return ""
    mn, mx = min(values), max(values)
    rng = mx - mn or 1
    W, H = 58, 28
    pts = []
    for i, v in enumerate(values):
        x = i / (len(values)-1) * W
        y = H - (v - mn) / rng * H
        pts.append(f"{x:.1f},{y:.1f}")
    return (f'<svg class="tc-spark" viewBox="0 0 {W} {H}">'
            f'<polyline points="{" ".join(pts)}" fill="none" '
            f'stroke="{color}" stroke-width="1.5"/></svg>')

# ── TICKER CARD HTML ──────────────────────────────────────────────────────────
def ticker_card_html(ticker, d, spark):
    sym   = DISPLAY_SYM.get(ticker, ticker)
    name  = TICKER_NAMES.get(ticker, "")
    if not d:
        return (f'<div class="tc nt">'
                f'<div class="bdot grey"></div>'
                f'<div class="tc-sym">{sym}</div>'
                f'<div class="tc-name">{name}</div>'
                f'<div class="tc-price">—</div>'
                f'<div class="tc-chg neu">載入中...</div>'
                f'</div>')

    price = d["price"]
    chg   = d["chg"]
    vol   = d["volume"]
    dot_color, sig = get_signal(ticker, d)
    is_fear = ticker in ["^VIX","UVXY","SQQQ"]

    card_cls = "tc "
    if sig == "buy":  card_cls += "up sig-buy"
    elif sig == "sell": card_cls += ("danger sig-sell" if is_fear else "dn sig-sell")
    elif sig == "watch": card_cls += "nt sig-watch"
    else: card_cls += ("nt" if chg >= 0 else "dn")
    if chg > 0 and sig == "normal": card_cls += " up"

    chg_cls = "pos" if chg > 0 else ("neg" if chg < 0 else "neu")
    chg_sym = "▲" if chg > 0 else ("▼" if chg < 0 else "▶")
    price_fmt = f"{price:,.2f}" if price > 10 else f"{price:.4f}"
    if price > 1000: price_fmt = f"{price:,.0f}"
    vol_fmt = f"{vol/1e6:.1f}M" if vol > 1e6 else (f"{vol/1e3:.0f}K" if vol > 1e3 else "—")

    sig_label = ""
    if sig == "buy"  and not is_fear: sig_label = " · 🟢 買入機會"
    if sig == "sell" and not is_fear: sig_label = " · 🔴 下跌風險"
    if sig == "buy"  and is_fear:     sig_label = " · 🔴 危險"
    if sig == "sell" and is_fear:     sig_label = " · 🟢 機會"
    if sig == "watch": sig_label = " · 🟡 觀察"

    spark_color = "#00ff88" if chg >= 0 else "#ff4757"
    spark_svg = make_spark(spark or [], spark_color)

    return (f'<div class="{card_cls}">'
            f'<div class="bdot {dot_color}"></div>'
            f'<div class="tc-sym">{sym}</div>'
            f'<div class="tc-name">{name}</div>'
            f'<div class="tc-price">${price_fmt}</div>'
            f'<div class="tc-chg {chg_cls}">{chg_sym} {abs(chg):.2f}%</div>'
            f'<div class="tc-vol">VOL {vol_fmt}{sig_label}</div>'
            f'{spark_svg}'
            f'</div>')

def render_group(label, tickers, data, hist, cols):
    st.markdown(f'<div class="sec-label">{label}</div>', unsafe_allow_html=True)
    grid_cols = st.columns(cols)
    for i, t in enumerate(tickers):
        with grid_cols[i % cols]:
            html = ticker_card_html(t, data.get(t), hist.get(t))
            st.markdown(html, unsafe_allow_html=True)

# ── CHART SVG ─────────────────────────────────────────────────────────────────
def chart_card_html(ticker, data, hist):
    sym  = DISPLAY_SYM.get(ticker, ticker)
    d    = data.get(ticker,{})
    vals = hist.get(ticker,[])
    if not d or not vals:
        return f'<div class="chart-card"><div class="chart-title">{sym}</div><div style="color:var(--text-muted);font-size:11px;margin-top:20px">數據載入中...</div></div>'
    chg = d["chg"]
    price = d["price"]
    chg_str = f'{"▲" if chg>0 else "▼"}{abs(chg):.2f}%'
    val_color = "var(--green)" if chg>=0 else "var(--red)"
    line_color = "#00ff88" if chg>=0 else "#ff4757"
    grad_id = f"gc{ticker.replace('^','').replace('-','')}"

    # Build SVG path
    W,H = 300,70
    mn = min(vals); mx = max(vals); rng = mx-mn or 1
    pts = []
    for i,v in enumerate(vals):
        x = i/(len(vals)-1)*W
        y = H - (v-mn)/rng*H*0.85 - H*0.05
        pts.append(f"{x:.0f},{y:.0f}")
    pts_str = " ".join(pts)
    poly_pts = f"0,{H} {pts_str} {W},{H}"

    svg = (f'<svg viewBox="0 0 {W} {H}" style="width:100%;height:70px">'
           f'<defs><linearGradient id="{grad_id}" x1="0" y1="0" x2="0" y2="1">'
           f'<stop offset="0%" stop-color="{line_color}" stop-opacity="0.3"/>'
           f'<stop offset="100%" stop-color="{line_color}" stop-opacity="0"/>'
           f'</linearGradient></defs>'
           f'<polygon points="{poly_pts}" fill="url(#{grad_id})"/>'
           f'<polyline points="{pts_str}" fill="none" stroke="{line_color}" stroke-width="2" '
           f'filter="drop-shadow(0 0 3px {line_color})"/>'
           f'</svg>')

    return (f'<div class="chart-card">'
            f'<div class="chart-hdr">'
            f'<div class="chart-title">{sym} 7D</div>'
            f'<div class="chart-val" style="color:{val_color}">${price:,.2f} {chg_str}</div>'
            f'</div>{svg}</div>')

# ── ALERT ROW HTML ────────────────────────────────────────────────────────────
def alert_row_html(alert):
    ac = ALERT_CONTENT.get(alert["id"],{})
    idx = [a["id"] for a in ALERT_DEFS].index(alert["id"])
    color = ALERT_DEFS[idx]["color"]
    icon  = {"red":"🔴","green":"🟢","orange":"🟡"}.get(color,"⚪")
    badge_style = {
        "red":    "background:rgba(255,71,87,0.1);border:1px solid rgba(255,71,87,0.35);color:#ff4757",
        "green":  "background:rgba(0,255,136,0.1);border:1px solid rgba(0,255,136,0.35);color:#00ff88",
        "orange": "background:rgba(255,159,67,0.1);border:1px solid rgba(255,159,67,0.35);color:#ff9f43",
    }.get(color,"")
    label = {"red":"危險","green":"機會","orange":"警示"}.get(color,"通知")

    return (f'<div class="al-row al-{color}">'
            f'<div class="al-time">{alert["time"]}</div>'
            f'<div style="margin:4px 0 6px">'
            f'<span class="al-badge" style="{badge_style}">{icon} {label}</span>'
            f'</div>'
            f'<div class="al-title">{alert["title"]}</div>'
            f'<div class="al-body">'
            f'<span class="al-opp">【機會】</span>{ac.get("opp","")}<br>'
            f'<span class="al-risk">【風險】</span>{ac.get("risk","")}<br>'
            f'<span class="al-adv">【建議】</span>{ac.get("adv","")}'
            f'</div>'
            f'</div>')

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown('<div class="sb-card"><div class="sb-title">📱 Telegram 設定</div>', unsafe_allow_html=True)
        st.session_state.tg_token   = st.text_input("Bot Token",   value=st.session_state.tg_token,   type="password", label_visibility="visible")
        st.session_state.tg_chat_id = st.text_input("Chat ID",     value=st.session_state.tg_chat_id, label_visibility="visible")
        if st.button("✅ 測試 Telegram 連接"):
            test = {"id":"vix_up","title":"MarketIQ 連接測試 🎉","time":datetime.now().strftime("%H:%M:%S")}
            ok = send_telegram(st.session_state.tg_token, st.session_state.tg_chat_id, test)
            st.success("✅ 發送成功！") if ok else st.error("❌ 發送失敗，請檢查 Token / Chat ID")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="sb-card"><div class="sb-title">⚙️ 刷新設定</div>', unsafe_allow_html=True)
        st.session_state.refresh_interval = st.number_input("刷新間隔（秒）", min_value=30, max_value=300, value=st.session_state.refresh_interval, step=10)
        st.session_state.cooldown_min     = st.number_input("警報冷卻（分鐘）", min_value=5, max_value=120, value=st.session_state.cooldown_min, step=5)
        st.markdown('</div>', unsafe_allow_html=True)

        # Alert toggles
        st.markdown('<div class="sb-card"><div class="sb-title">🔔 警報開關</div>', unsafe_allow_html=True)

        # Master toggle
        master = st.toggle("⚡ 一鍵全開 / 全關", value=st.session_state.all_alerts_on, key="master_toggle")
        if master != st.session_state.all_alerts_on:
            st.session_state.all_alerts_on = master
            for a in ALERT_DEFS:
                st.session_state.alert_enabled[a["id"]] = master

        on_count = sum(1 for a in ALERT_DEFS if st.session_state.alert_enabled.get(a["id"], True))
        st.caption(f"{on_count} / {len(ALERT_DEFS)} 已啟用")
        st.markdown("---")

        for a in ALERT_DEFS:
            val = st.toggle(f"{a['name']}", value=st.session_state.alert_enabled.get(a["id"], True), key=f"tog_{a['id']}", help=a["cond"])
            st.session_state.alert_enabled[a["id"]] = val

        st.markdown('</div>', unsafe_allow_html=True)

        # Legend
        st.markdown("""
<div class="sb-card">
<div class="sb-title">💡 呼吸燈圖例</div>
<div class="leg-row"><div class="leg-dot green"></div><div><div class="leg-name" style="color:#00ff88">買入機會</div><div class="leg-sub">慢速呼吸 2s</div></div></div>
<div class="leg-row"><div class="leg-dot red"></div><div><div class="leg-name" style="color:#ff4757">下跌風險</div><div class="leg-sub">急促呼吸 0.8s</div></div></div>
<div class="leg-row"><div class="leg-dot orange"></div><div><div class="leg-name" style="color:#ff9f43">中性觀察</div><div class="leg-sub">緩慢 3s</div></div></div>
<div class="leg-row"><div class="leg-dot grey"></div><div><div class="leg-name" style="color:#6b8a9e">正常無信號</div><div class="leg-sub">靜止暗灰</div></div></div>
</div>
""", unsafe_allow_html=True)

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    init_state()
    inject_css()
    render_sidebar()

    # ── HEADER ──
    now_str = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    st.markdown(f"""
<div class="iq-header">
  <div style="display:flex;align-items:center">
    <div class="iq-logo">MARKET<span>IQ</span></div>
    <div class="iq-badge">LIVE MONITOR</div>
  </div>
  <div class="iq-right">
    <div class="iq-live"><span class="iq-pulse"></span>LIVE</div>
    <div class="iq-clock">{now_str}</div>
    <div class="iq-refresh">↻ AUTO {st.session_state.refresh_interval}s</div>
  </div>
</div>""", unsafe_allow_html=True)

    # ── FETCH DATA ──
    st.session_state.fetch_count += 1
    with st.spinner("⟳ 載入市場數據..."):
        data, hist = fetch_all_cached(st.session_state.fetch_count)
    st.session_state.data = data
    st.session_state.hist = hist

    # ── SCORE ──
    score, scores = calc_market_score(data)
    status_text, status_color = get_market_status(score)
    analysis_html = build_analysis(data, score, scores)
    tags = build_tags(data, score)
    dashoffset = 251.2 * (1 - score / 100)

    # ── SCORE BANNER ──
    col_score, col_summary = st.columns([1, 2.8])

    with col_score:
        score_color = {"green":"#00ff88","cyan":"#00d4ff","orange":"#ff9f43","red":"#ff4757"}.get(status_color,"#00d4ff")
        bars_html = "".join([
            f'<div class="dim-bar-wrap">'
            f'<div class="dim-bar-label">{k}</div>'
            f'<div class="dim-bar-track"><div class="dim-bar-fill" style="width:{v*10}%;background:var(--cyan)"></div></div>'
            f'<div class="dim-bar-val" style="color:var(--cyan)">{v:.1f}</div>'
            f'</div>'
            for k, v in scores.items()
        ])
        st.markdown(f"""
<div class="score-wrap">
  <div class="score-inner">
    <div class="score-ring-svg">
      <svg viewBox="0 0 90 90" width="90" height="90">
        <circle class="s-track" cx="45" cy="45" r="40"/>
        <circle class="s-fill" cx="45" cy="45" r="40"
          style="stroke:{score_color};stroke-dashoffset:{dashoffset:.1f}"/>
      </svg>
      <div style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;margin-top:-90px">
        <div style="font-family:'IBM Plex Mono',monospace;font-size:26px;font-weight:700;color:{score_color};text-shadow:0 0 12px {score_color}">{score}</div>
        <div class="score-num-label">/ 100</div>
      </div>
    </div>
    <div style="flex:1">
      <div style="font-family:'IBM Plex Mono',monospace;font-size:10px;color:var(--text-dim);letter-spacing:2px;text-transform:uppercase;margin-bottom:6px">MARKET SCORE</div>
      <div style="font-size:18px;font-weight:700;color:{score_color};margin-bottom:10px">{status_text}</div>
      {bars_html}
    </div>
  </div>
</div>""", unsafe_allow_html=True)

    with col_summary:
        tags_html = "".join([f'<span class="sig-tag {cls}">{t}</span>' for t,cls in tags])
        st.markdown(f"""
<div class="summary-card">
  <div class="summary-label">🧠 深度市場分析 — {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>
  <div class="summary-body">{analysis_html}</div>
  <div class="sig-tags">{tags_html}</div>
</div>""", unsafe_allow_html=True)

    # ── AI PROMPT SECTION ──
    ai_prompt = build_ai_prompt(data, score, scores, status_text)
    # Safely encode prompt for JS — store in a data attribute, read via JS
    import json as _json
    prompt_json = _json.dumps(ai_prompt)   # produces a valid JS string literal

    ai_component_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{
    background: transparent;
    font-family: 'IBM Plex Mono', monospace;
    padding: 0;
  }}
  .wrap {{
    background: #0a1020;
    border: 1px solid rgba(0,212,255,0.15);
    border-radius: 4px;
    padding: 16px 20px 18px;
    position: relative;
    overflow: hidden;
  }}
  .wrap::before {{
    content:'';
    position:absolute; top:0; left:0; right:0; height:1px;
    background: linear-gradient(90deg, transparent, rgba(255,215,0,0.4), transparent);
  }}
  .label {{
    font-size: 10px; color: #ffd700;
    letter-spacing: 2px; text-transform: uppercase;
    margin-bottom: 14px;
  }}
  .btn-row {{ display:flex; gap:10px; flex-wrap:wrap; margin-bottom:12px; }}
  .btn {{
    display: flex; align-items: center; gap: 8px;
    padding: 10px 20px; border-radius: 3px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px; font-weight: 600; letter-spacing: 1px;
    cursor: pointer; border: 1px solid;
    transition: all 0.2s; background: transparent;
  }}
  .btn:hover {{ transform: translateY(-1px); }}
  .btn-claude  {{ border-color:rgba(204,120,92,0.5); color:#cc785c; background:rgba(204,120,92,0.08); }}
  .btn-claude:hover  {{ background:rgba(204,120,92,0.18); box-shadow:0 0 16px rgba(204,120,92,0.25); }}
  .btn-chatgpt {{ border-color:rgba(16,163,127,0.5);  color:#10a37f; background:rgba(16,163,127,0.08); }}
  .btn-chatgpt:hover {{ background:rgba(16,163,127,0.18); box-shadow:0 0 16px rgba(16,163,127,0.25); }}
  .btn-gemini  {{ border-color:rgba(66,133,244,0.5);  color:#4285f4; background:rgba(66,133,244,0.08); }}
  .btn-gemini:hover  {{ background:rgba(66,133,244,0.18); box-shadow:0 0 16px rgba(66,133,244,0.25); }}
  .btn-grok    {{ border-color:rgba(255,255,255,0.2);  color:#e8f4f8; background:rgba(255,255,255,0.04); }}
  .btn-grok:hover    {{ background:rgba(255,255,255,0.10); box-shadow:0 0 16px rgba(255,255,255,0.10); }}
  .hint {{ font-size:9px; color:#3d5a6e; letter-spacing:0.5px; line-height:1.6; }}
  .hint span {{ color:#00d4ff; }}
  .toast {{
    display:none;
    margin-top: 12px;
    padding: 10px 16px;
    border-radius: 3px;
    font-size: 11px;
    border: 1px solid rgba(255,255,255,0.1);
    background: #0d1526;
    transition: opacity 0.3s;
  }}
</style>
</head>
<body>
<div class="wrap">
  <div class="label">🤖 一鍵帶數據詢問 AI 分析師</div>
  <div class="btn-row">
    <button class="btn btn-claude"  onclick="go('claude')">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2"/><rect x="9" y="8" width="2" height="8" rx="1"/><rect x="13" y="8" width="2" height="8" rx="1"/></svg>
      Claude
    </button>
    <button class="btn btn-chatgpt" onclick="go('chatgpt')">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2a10 10 0 1 0 0 20A10 10 0 0 0 12 2zm0 4a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3zm0 4.5c2 0 6 1 6 3v.5H6V13.5c0-2 4-3 6-3z"/></svg>
      ChatGPT
    </button>
    <button class="btn btn-gemini"  onclick="go('gemini')">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12,2 22,8 22,16 12,22 2,16 2,8"/><line x1="12" y1="2" x2="12" y2="22"/><line x1="2" y1="8" x2="22" y2="8"/><line x1="2" y1="16" x2="22" y2="16"/></svg>
      Gemini
    </button>
    <button class="btn btn-grok"    onclick="go('grok')">
      <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
      Grok
    </button>
  </div>
  <div class="hint">點擊按鈕 → <span>Prompt 自動複製到剪貼板</span> → 新分頁開啟 AI 網頁 → 輸入框按 <span>Ctrl+V</span>（Mac: ⌘+V）貼上即可</div>
  <div class="toast" id="toast"></div>
</div>

<script>
const PROMPT = {prompt_json};
const URLS = {{
  claude:  'https://claude.ai/new',
  chatgpt: 'https://chatgpt.com/',
  gemini:  'https://gemini.google.com/app',
  grok:    'https://grok.com/'
}};
const NAMES  = {{claude:'Claude', chatgpt:'ChatGPT', gemini:'Gemini', grok:'Grok'}};
const COLORS = {{claude:'#cc785c', chatgpt:'#10a37f', gemini:'#4285f4', grok:'#aad4f8'}};

function go(ai) {{
  const toast = document.getElementById('toast');
  const doOpen = () => {{
    toast.style.color  = COLORS[ai];
    toast.style.display = 'block';
    toast.textContent = '✅ Prompt 已複製！正在跳轉到 ' + NAMES[ai] + '... 請在輸入框按 Ctrl+V';
    setTimeout(() => {{ toast.style.display = 'none'; }}, 3500);
    window.open(URLS[ai], '_blank');
  }};

  if (navigator.clipboard && window.isSecureContext) {{
    navigator.clipboard.writeText(PROMPT).then(doOpen).catch(() => fallback(doOpen));
  }} else {{
    fallback(doOpen);
  }}
}}

function fallback(cb) {{
  const ta = document.createElement('textarea');
  ta.value = PROMPT;
  ta.style.cssText = 'position:fixed;top:-9999px;left:-9999px;opacity:0';
  document.body.appendChild(ta);
  ta.focus(); ta.select();
  try {{ document.execCommand('copy'); }} catch(e) {{}}
  document.body.removeChild(ta);
  cb();
}}
</script>
</body>
</html>"""

    components.html(ai_component_html, height=130, scrolling=False)

    # ── TICKER GROUPS ──
    render_group("📊 大盤指數 ETF",   TICKERS["大盤指數 ETF"],   data, hist, 4)
    render_group("😱 恐慌 / 做空指標", TICKERS["恐慌/做空"],      data, hist, 3)
    render_group("💵 債券 / 美元 / 商品", TICKERS["債券/美元/商品"], data, hist, 4)
    render_group("🏦 板塊 / 信用",     TICKERS["板塊/信用"],      data, hist, 4)
    render_group("🏆 龍頭個股 (1/2)",  TICKERS["龍頭個股"][:7],   data, hist, 7)
    render_group("🏆 龍頭個股 (2/2)",  TICKERS["龍頭個股"][7:],   data, hist, 7)

    # ── CHARTS ──
    st.markdown('<div class="sec-label">📈 走勢圖（7日）</div>', unsafe_allow_html=True)
    chart_tickers = ["SPY","^VIX","GLD","QQQ","TLT","NVDA"]
    c1,c2,c3 = st.columns(3)
    for i, t in enumerate(chart_tickers):
        with [c1,c2,c3][i%3]:
            st.markdown(chart_card_html(t, data, hist), unsafe_allow_html=True)

    # ── DIMENSION ANALYSIS ──
    st.markdown('<div class="sec-label">🧬 七維度分析</div>', unsafe_allow_html=True)
    dim_cols = st.columns(7)
    dim_icons = ["📈","😱","🔄","🏦","💵","💳","🏆"]
    dim_colors = []
    for i, (name, val) in enumerate(scores.items()):
        with dim_cols[i]:
            col = "#00ff88" if val>=7 else ("#ff9f43" if val>=5 else "#ff4757")
            dim_colors.append(col)
            pct = val*10
            st.markdown(f"""
<div style="background:var(--bg-card2);border:1px solid var(--border);border-radius:4px;
     padding:12px 10px;text-align:center;transition:border-color 0.2s">
  <div style="font-size:18px;margin-bottom:6px">{dim_icons[i]}</div>
  <div style="font-family:'IBM Plex Mono',monospace;font-size:8px;color:var(--text-dim);
       letter-spacing:1px;text-transform:uppercase;margin-bottom:6px">{name}</div>
  <div style="font-family:'IBM Plex Mono',monospace;font-size:22px;font-weight:700;
       color:{col};text-shadow:0 0 10px {col}">{val:.1f}</div>
  <div style="width:100%;height:3px;background:rgba(255,255,255,0.05);
       border-radius:2px;overflow:hidden;margin-top:8px">
    <div style="width:{pct}%;height:100%;background:{col};border-radius:2px"></div>
  </div>
</div>""", unsafe_allow_html=True)

    # ── ALERT CHECK & LOG ──
    triggered = check_alerts(
        data,
        st.session_state.alert_enabled,
        st.session_state.cooldown_min
    )
    for alert in triggered:
        st.session_state.alert_log.insert(0, alert)
        send_telegram(st.session_state.tg_token, st.session_state.tg_chat_id, alert)

    # Keep last 20
    st.session_state.alert_log = st.session_state.alert_log[:20]

    # ── ALERT LOG ──
    st.markdown('<div class="sec-label">🔔 即時警報記錄</div>', unsafe_allow_html=True)
    if st.session_state.alert_log:
        for alert in st.session_state.alert_log:
            st.markdown(alert_row_html(alert), unsafe_allow_html=True)
    else:
        st.markdown("""
<div style="background:var(--bg-card);border:1px solid var(--border);border-radius:4px;
     padding:20px;text-align:center;color:var(--text-muted);
     font-family:'IBM Plex Mono',monospace;font-size:12px;letter-spacing:1px">
  ✅ 暫無警報 — 市場運行正常
</div>""", unsafe_allow_html=True)

    # ── AUTO REFRESH ──
    time.sleep(0.5)
    st.rerun()

if __name__ == "__main__":
    main()
