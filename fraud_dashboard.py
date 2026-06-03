"""
Fraud Detection Dashboard — Streamlit Frontend (v5 — Dark Theme)
Run with: streamlit run fraud_dashboard.py
Make sure your FastAPI server is running on http://127.0.0.1:8000
"""

import streamlit as st
import requests
import re
from datetime import datetime

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="FraudShield — Detection System",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [class*="css"], .stApp {
    font-family: 'Inter', sans-serif !important;
    background: #0a0a0f !important;
    color: #e2e8f0 !important;
}

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 2.5rem 3rem 2.5rem !important; max-width: 100% !important; }

/* ── NAV ── */
.nav-bar {
    display: flex; align-items: center; justify-content: space-between;
    padding: 24px 0 28px 0;
    border-bottom: 1px solid #1e1e2e;
    margin-bottom: 36px;
}
.nav-logo { display: flex; align-items: center; gap: 12px; }
.nav-logo-icon {
    width: 40px; height: 40px;
    background: linear-gradient(135deg, #3b82f6, #8b5cf6);
    border-radius: 10px; display: flex; align-items: center; justify-content: center;
    font-size: 18px; box-shadow: 0 0 20px rgba(139,92,246,0.4);
}
.nav-logo-text { font-size: 20px; font-weight: 700; color: #f1f5f9; letter-spacing: -0.5px; }
.nav-logo-text span { color: #818cf8; }
.nav-status {
    display: flex; align-items: center; gap: 8px;
    background: rgba(16,185,129,0.1);
    border: 1px solid rgba(16,185,129,0.3);
    border-radius: 99px; padding: 6px 16px;
    font-size: 11px; font-family: 'JetBrains Mono', monospace;
    font-weight: 600; color: #10b981; letter-spacing: 1px;
}
.nav-status-dot { width: 6px; height: 6px; border-radius: 50%; background: #10b981; animation: blink 2s ease-in-out infinite; }
.nav-status.offline { background: rgba(239,68,68,0.1); border-color: rgba(239,68,68,0.3); color: #ef4444; }
.nav-status-dot.offline { background: #ef4444; animation: none; }
@keyframes blink { 0%,100%{opacity:1;} 50%{opacity:0.3;} }

/* ── SECTION LABEL ── */
.sec-label {
    font-size: 10px; font-weight: 600; letter-spacing: 2px; text-transform: uppercase;
    color: #4b5563; margin-bottom: 12px;
    display: flex; align-items: center; gap: 10px;
}
.sec-label::after { content: ''; flex: 1; height: 1px; background: #1e1e2e; border-radius: 99px; }

/* ── PANEL ── */
.panel {
    background: #0f0f1a;
    border: 1px solid #1e1e2e;
    border-radius: 16px;
    padding: 24px 26px;
}

/* ── STREAMLIT INPUTS ── */
.stTextInput input, .stNumberInput input {
    background: #0a0a0f !important;
    border: 1px solid #1e1e2e !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 13px !important;
    padding: 10px 14px !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.15) !important;
    background: #0f0f1a !important;
}
.stSelectbox > div > div {
    background: #0a0a0f !important;
    border: 1px solid #1e1e2e !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 13px !important;
}
label, .stNumberInput label, .stTextInput label, .stSelectbox label {
    font-size: 10px !important; font-weight: 600 !important;
    letter-spacing: 1.5px !important; text-transform: uppercase !important;
    color: #6b7280 !important; margin-bottom: 5px !important;
    font-family: 'Inter', sans-serif !important;
}
.stCheckbox label {
    font-size: 13px !important; text-transform: none !important;
    letter-spacing: 0 !important; color: #94a3b8 !important; font-weight: 400 !important;
}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {
    background: #0f0f1a !important;
    border-bottom: 1px solid #1e1e2e !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    color: #4b5563 !important;
    font-size: 13px !important; font-weight: 500 !important;
    padding: 10px 20px !important;
    background: transparent !important;
    border-bottom: 2px solid transparent !important;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    color: #818cf8 !important;
    border-bottom: 2px solid #818cf8 !important;
    background: transparent !important;
}
.stTabs [data-baseweb="tab-highlight"] { background: transparent !important; }
.stTabs [data-baseweb="tab-border"] { display: none !important; }

/* ── SUBMIT BUTTON ── */
.stFormSubmitButton > button {
    background: linear-gradient(135deg, #3b82f6, #8b5cf6) !important;
    border: none !important; border-radius: 10px !important; color: #fff !important;
    font-family: 'Inter', sans-serif !important; font-size: 14px !important;
    font-weight: 600 !important; padding: 12px !important; width: 100% !important;
    box-shadow: 0 0 24px rgba(139,92,246,0.3) !important; letter-spacing: 0.3px !important;
    transition: all 0.2s !important;
}
.stFormSubmitButton > button:hover {
    box-shadow: 0 0 32px rgba(139,92,246,0.5) !important;
    transform: translateY(-1px) !important;
}

/* ── PRIMARY BUTTON ── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #3b82f6, #8b5cf6) !important;
    border: none !important; border-radius: 10px !important; color: #fff !important;
    font-family: 'Inter', sans-serif !important; font-size: 14px !important;
    font-weight: 600 !important; padding: 12px !important;
    box-shadow: 0 0 24px rgba(139,92,246,0.3) !important;
}

/* ── FILE UPLOADER ── */
.stFileUploader {
    background: #0f0f1a !important;
    border: 1.5px dashed #1e1e2e !important;
    border-radius: 12px !important; padding: 8px !important;
}
.stFileUploader:hover { border-color: #3b82f6 !important; }
.stFileUploader label {
    font-size: 13px !important; font-weight: 500 !important;
    text-transform: none !important; letter-spacing: 0 !important;
    color: #94a3b8 !important;
}
[data-testid="stFileUploaderDropzone"] {
    background: transparent !important; border: none !important; padding: 16px !important;
}

/* ── PREVIEW BOX ── */
.preview-box {
    background: #070710; border: 1px solid #1e1e2e; border-radius: 10px;
    padding: 14px 16px; margin-top: 12px;
    font-family: 'JetBrains Mono', monospace; font-size: 12px;
    color: #64748b; line-height: 1.8; max-height: 180px; overflow-y: auto;
    white-space: pre-wrap; word-break: break-word;
}
.preview-label {
    font-size: 10px; font-weight: 600; letter-spacing: 2px; text-transform: uppercase;
    color: #4b5563; margin-bottom: 8px; font-family: 'Inter', sans-serif;
}

/* ── FIELD CHIPS ── */
.fields-wrap { margin-top: 16px; }
.fields-title {
    font-size: 10px; font-weight: 600; letter-spacing: 2px; text-transform: uppercase;
    color: #4b5563; margin-bottom: 10px; font-family: 'Inter', sans-serif;
}
.chips-row { display: flex; flex-wrap: wrap; gap: 8px; }
.chip {
    border-radius: 8px; padding: 7px 12px;
    border: 1px solid #1e1e2e; background: #0a0a0f;
}
.chip.found { border-color: rgba(59,130,246,0.4); background: rgba(59,130,246,0.08); }
.chip.missing { opacity: 0.4; }
.chip-label { font-size: 9px; font-weight: 600; letter-spacing: 1.5px; text-transform: uppercase; color: #4b5563; margin-bottom: 3px; }
.chip-val { font-family: 'JetBrains Mono', monospace; font-weight: 600; color: #94a3b8; font-size: 12px; }
.chip.found .chip-val { color: #60a5fa; }
.count-badge {
    display: inline-block; background: linear-gradient(135deg, #3b82f6, #8b5cf6);
    color: #fff; border-radius: 99px; padding: 1px 9px; font-size: 10px;
    margin-left: 8px; vertical-align: middle;
}

/* ── DIVIDER ── */
.divider { height: 1px; background: #1e1e2e; border-radius: 99px; margin: 18px 0; }

/* ── DECISION ── */
.decision-wrap {
    border-radius: 12px; padding: 20px 22px; margin-bottom: 20px;
    display: flex; align-items: center; gap: 16px;
}
.decision-wrap.block  { background: rgba(225,29,72,0.08); border: 1px solid rgba(225,29,72,0.25); }
.decision-wrap.review { background: rgba(217,119,6,0.08); border: 1px solid rgba(217,119,6,0.25); }
.decision-wrap.allow  { background: rgba(22,163,74,0.08); border: 1px solid rgba(22,163,74,0.25); }
.decision-icon { font-size: 36px; line-height: 1; }
.decision-sublabel { font-size: 10px; font-weight: 600; letter-spacing: 3px; text-transform: uppercase; color: #4b5563; margin-bottom: 4px; }
.decision-value { font-size: 32px; font-weight: 800; letter-spacing: -1px; line-height: 1; }
.decision-value.block  { color: #f43f5e; }
.decision-value.review { color: #f59e0b; }
.decision-value.allow  { color: #22c55e; }

/* ── SCORE ── */
.score-header { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 10px; }
.score-label { font-size: 10px; font-weight: 600; letter-spacing: 2px; text-transform: uppercase; color: #4b5563; }
.score-value { font-family: 'JetBrains Mono', monospace; font-size: 20px; font-weight: 700; color: #e2e8f0; }
.score-track { background: #1e1e2e; border-radius: 99px; height: 8px; overflow: hidden; margin-bottom: 6px; }
.score-fill { height: 100%; border-radius: 99px; }
.score-fill.red   { background: linear-gradient(90deg, #f43f5e, #fb7185); box-shadow: 0 0 10px rgba(244,63,94,0.5); }
.score-fill.amber { background: linear-gradient(90deg, #f59e0b, #fbbf24); box-shadow: 0 0 10px rgba(245,158,11,0.5); }
.score-fill.green { background: linear-gradient(90deg, #22c55e, #4ade80); box-shadow: 0 0 10px rgba(34,197,94,0.5); }
.score-ticks { display: flex; justify-content: space-between; font-family: 'JetBrains Mono', monospace; font-size: 9px; color: #374151; }

/* ── STAT CARDS ── */
.stat-row { display: flex; gap: 10px; margin: 18px 0; }
.stat-card { flex: 1; background: #0a0a0f; border: 1px solid #1e1e2e; border-radius: 10px; padding: 14px; text-align: center; }
.stat-val { font-size: 18px; font-weight: 700; color: #e2e8f0; line-height: 1.2; }
.stat-lbl { font-size: 9px; font-weight: 600; letter-spacing: 1.5px; text-transform: uppercase; color: #4b5563; margin-top: 5px; }

/* ── PILLS ── */
.pill-section { margin-bottom: 12px; }
.pill-heading { font-size: 9px; font-weight: 600; letter-spacing: 2px; text-transform: uppercase; color: #374151; margin-bottom: 7px; }
.pill-row { display: flex; flex-wrap: wrap; gap: 6px; }
.pill { border-radius: 6px; padding: 4px 10px; font-size: 11px; font-family: 'JetBrains Mono', monospace; font-weight: 500; }
.pill-rule   { background: rgba(139,92,246,0.15); border: 1px solid rgba(139,92,246,0.3); color: #a78bfa; }
.pill-reason { background: #0f0f1a; border: 1px solid #1e1e2e; color: #64748b; }

/* ── ACTION BOX ── */
.action-box {
    background: rgba(59,130,246,0.08); border: 1px solid rgba(59,130,246,0.2);
    border-radius: 10px; padding: 12px 16px; font-size: 13px; color: #93c5fd;
    font-weight: 500; display: flex; gap: 10px; align-items: flex-start; line-height: 1.6;
}

/* ── EMPTY STATE ── */
.empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 360px; gap: 14px; }
.empty-icon { font-size: 52px; opacity: 0.15; }
.empty-text { font-family: 'JetBrains Mono', monospace; font-size: 10px; letter-spacing: 2px; text-transform: uppercase; color: #374151; text-align: center; line-height: 2.4; }

/* ── BANNERS ── */
.banner { border-radius: 10px; padding: 14px 18px; font-size: 13px; font-weight: 500; display: flex; gap: 10px; align-items: flex-start; line-height: 1.6; }
.banner.warn { background: rgba(217,119,6,0.1); border: 1px solid rgba(217,119,6,0.3); color: #fbbf24; }
.banner.err  { background: rgba(225,29,72,0.1); border: 1px solid rgba(225,29,72,0.3); color: #fb7185; }
.banner.info { background: rgba(59,130,246,0.1); border: 1px solid rgba(59,130,246,0.3); color: #93c5fd; }

/* ── EXPANDER / DASHBOARD ── */
details summary {
    background: #0f0f1a !important; border: 1px solid #1e1e2e !important;
    border-radius: 12px !important; padding: 14px 20px !important;
    color: #6b7280 !important; font-weight: 500 !important;
    font-size: 13px !important; cursor: pointer;
}
details[open] summary { border-radius: 12px 12px 0 0 !important; }
details > div {
    background: #0f0f1a !important; border: 1px solid #1e1e2e !important;
    border-top: none !important; border-radius: 0 0 12px 12px !important; padding: 24px !important;
}

/* ── DASH METRICS ── */
.dash-metric { background: #0a0a0f; border: 1px solid #1e1e2e; border-radius: 12px; padding: 18px; text-align: center; }
.dash-metric-val { font-size: 28px; font-weight: 700; color: #e2e8f0; }
.dash-metric-lbl { font-size: 9px; font-weight: 600; letter-spacing: 2px; text-transform: uppercase; color: #4b5563; margin-top: 6px; }

/* ── TXN LIST ── */
.txn-list { display: flex; flex-direction: column; gap: 3px; }
.txn-row {
    display: flex; align-items: center; gap: 12px;
    padding: 10px 14px; border-radius: 8px;
    background: #0a0a0f; border: 1px solid #1e1e2e;
    transition: border-color 0.15s;
}
.txn-row:hover { border-color: #2d2d42; }
.txn-id { font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #475569; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.txn-score { font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #6b7280; width: 60px; text-align: right; }
.txn-badge { font-family: 'JetBrains Mono', monospace; font-size: 10px; font-weight: 700; padding: 3px 10px; border-radius: 5px; width: 66px; text-align: center; letter-spacing: 0.5px; }
.txn-badge.BLOCK  { background: rgba(244,63,94,0.12); color: #f43f5e; border: 1px solid rgba(244,63,94,0.25); }
.txn-badge.REVIEW { background: rgba(245,158,11,0.12); color: #f59e0b; border: 1px solid rgba(245,158,11,0.25); }
.txn-badge.ALLOW  { background: rgba(34,197,94,0.12); color: #22c55e; border: 1px solid rgba(34,197,94,0.25); }
.txn-time { font-family: 'JetBrains Mono', monospace; font-size: 10px; color: #374151; white-space: nowrap; }

/* scrollbar */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #1e1e2e; border-radius: 99px; }
</style>
""", unsafe_allow_html=True)


# ── HELPERS ─────────────────────────────────────────────
def check_api():
    try:
        return requests.get(f"{API_BASE}/health", timeout=3).status_code == 200
    except:
        return False

def predict(payload):
    try:
        r = requests.post(f"{API_BASE}/predict", json=payload, timeout=10)
        return r.json(), r.status_code
    except Exception as e:
        return {"error": str(e)}, 500

def get_metrics():
    try:
        return requests.get(f"{API_BASE}/metrics", timeout=5).json()
    except:
        return None

def get_recent(limit=12):
    try:
        return requests.get(f"{API_BASE}/transactions/recent?limit={limit}", timeout=5).json()
    except:
        return []


# ── SAMPLE SLIPS ────────────────────────────────────────
SAMPLE_SLIPS = {
    "✅ Normal Transaction": """PAYMENT RECEIPT
Transaction ID: TXN-NORMAL-001
Date: 2026-06-03
Time: 12:30
Amount: 85.00
Merchant Category: grocery
Country: IN
Card Present: yes
International: no
Device Change: no
Transactions Last 1H: 1
Transactions Last 24H: 3
Avg Amount 7D: 95.00
Distance From Home: 2
Account Age: 730
Failed Attempts: 0""",

    "⚠️ Suspicious": """DIGITAL PAYMENT SLIP
Transaction ID: TXN-SUSP-001
Date: 2026-06-03
Time: 23:45
Amount: 420.00
Merchant: entertainment
Country Code: GB
Card Present: no
International: yes
Device Change: yes
Transactions Last 1H: 3
Transactions Last 24H: 9
Avg Amount 7D: 90.00
Distance From Home: 320
Account Age: 18
Failed Attempts: 1""",

    "🚫 High Risk Fraud": """WIRE TRANSFER RECEIPT
Transaction ID: TXN-FRAUD-001
Date: 2026-06-03
Time: 02:15
Amount: 4800.00
Merchant Category: travel
Country Code: SG
Card Present: no
International: yes
Device Change: yes
Transactions Last 1H: 9
Transactions Last 24H: 22
Avg Amount 7D: 110.00
Distance From Home: 580
Account Age: 5
Failed Attempts: 3""",
}


# ── SLIP PARSER ─────────────────────────────────────────
def parse_slip(text: str):
    lines = text.split("\n")
    t = text.lower()

    def find(patterns):
        for pat in patterns:
            for line in lines:
                m = re.search(pat, line, re.IGNORECASE)
                if m:
                    return m.group(1).strip() if m.lastindex else None
        return None

    def find_num(patterns, default=None):
        v = find(patterns)
        if v is None: return default
        try: return float(re.sub(r"[$,₹€£]", "", v))
        except: return default

    def find_int(patterns, default=0):
        v = find_num(patterns, default)
        return int(round(v)) if v is not None else default

    def find_bool(patterns):
        v = find(patterns)
        if v is None: return None
        return 1 if re.search(r"yes|true|1", v, re.IGNORECASE) else 0

    def detect_merchant(text):
        for c in ["grocery","restaurant","gas","retail","travel","entertainment","healthcare"]:
            if c in text: return c
        if re.search(r"food|eat|dine|cafe|coffee", text): return "restaurant"
        if re.search(r"fuel|petrol|diesel", text): return "gas"
        if re.search(r"flight|hotel|airline|booking", text): return "travel"
        if re.search(r"movie|cinema|game|stream", text): return "entertainment"
        if re.search(r"hospital|clinic|pharma|doctor", text): return "healthcare"
        return "retail"

    def detect_country(text):
        for k, v in {"india":"IN","indian":"IN"," in ":"IN","us ":"US","usa":"US","united states":"US","uk":"GB","gb":"GB","united kingdom":"GB","germany":"DE","singapore":"SG"," sg ":"SG"}.items():
            if k in text: return v
        m = find([r"country[\s:]+([A-Za-z]{2,})", r"country code[\s:]+([A-Za-z]{2,})"])
        return m.upper()[:2] if m else "IN"

    def extract_time(text):
        m = re.search(r"(\d{1,2}):(\d{2})\s*(AM|PM)?", text, re.IGNORECASE)
        if not m: return datetime.now().hour
        h = int(m.group(1))
        ampm = (m.group(3) or "").upper()
        if ampm == "PM" and h < 12: h += 12
        if ampm == "AM" and h == 12: h = 0
        return h

    txn_id  = find([r"transaction\s*id[\s:]+([A-Za-z0-9\-_]+)", r"txn[\s:#]+([A-Za-z0-9\-_]+)", r"ref[\s:#]+([A-Za-z0-9\-_]+)"]) or f"TXN-{int(datetime.now().timestamp()) % 100000000}"
    amount  = find_num([r"amount[\s:]+([0-9,.$₹€£]+)", r"total[\s:]+([0-9,.$₹€£]+)", r"paid[\s:]+([0-9,.$₹€£]+)"], 100.0)
    hour    = extract_time(text)
    merchant = detect_merchant(t)
    country  = detect_country(t)
    txn_1h  = find_int([r"transactions?\s*(?:last|past|in)\s*1\s*h(?:our)?[\s:]+(\d+)"], 1)
    txn_24h = find_int([r"transactions?\s*(?:last|past|in)\s*24\s*h(?:ours?)?[\s:]+(\d+)"], 3)
    avg_amt = find_num([r"avg.{0,15}amount.{0,10}7d?[\s:]+([0-9,.$₹€£]+)"], amount)
    dist    = find_num([r"distance.{0,10}home[\s:]+([0-9.]+)", r"distance[\s:]+([0-9.]+)"], 10.0)
    acc_age = find_num([r"account\s*age[\s:]+([0-9.]+)"], 365.0)
    failed  = find_int([r"failed\s*(?:attempts?|tries?)[\s:]+(\d+)"], 0)
    card_p  = find_bool([r"card\s*present[\s:]+(yes|no|true|false|1|0)"])
    is_intl = find_bool([r"international[\s:]+(yes|no|true|false|1|0)"])
    dev_ch  = find_bool([r"device\s*(?:change|changed)[\s:]+(yes|no|true|false|1|0)"])

    payload = {
        "transaction_id": txn_id, "amount": amount,
        "hour_of_day": hour, "day_of_week": datetime.now().weekday(),
        "merchant_category": merchant, "country_code": country,
        "card_present": card_p if card_p is not None else 1,
        "transactions_last_1h": txn_1h, "transactions_last_24h": txn_24h,
        "avg_amount_last_7d": avg_amt, "distance_from_home_km": dist,
        "account_age_days": acc_age, "failed_attempts_last_24h": failed,
        "is_international": is_intl if is_intl is not None else 0,
        "device_change": dev_ch if dev_ch is not None else 0,
    }

    found_keys = set()
    for line in lines:
        ll = line.lower()
        if re.search(r"amount|total|sum|paid", ll): found_keys.add("amount")
        if re.search(r"txn|transaction|ref", ll): found_keys.add("transaction_id")
        if re.search(r"time|hour", ll): found_keys.add("hour_of_day")
        if re.search(r"merchant|category", ll): found_keys.add("merchant_category")
        if re.search(r"country|nation", ll): found_keys.add("country_code")
        if re.search(r"1h|1 hour", ll): found_keys.add("transactions_last_1h")
        if re.search(r"24h|24 hour", ll): found_keys.add("transactions_last_24h")
        if re.search(r"distance", ll): found_keys.add("distance_from_home_km")
        if re.search(r"account age|acc.*age", ll): found_keys.add("account_age_days")
        if re.search(r"failed", ll): found_keys.add("failed_attempts_last_24h")
        if re.search(r"card present", ll): found_keys.add("card_present")
        if re.search(r"international", ll): found_keys.add("is_international")
        if re.search(r"device", ll): found_keys.add("device_change")

    field_display = [
        ("transaction_id","TXN ID",txn_id),
        ("amount","Amount",f"${amount}"),
        ("hour_of_day","Hour",f"{hour}:00"),
        ("merchant_category","Merchant",merchant),
        ("country_code","Country",country),
        ("transactions_last_1h","TXN / 1h",str(txn_1h)),
        ("transactions_last_24h","TXN / 24h",str(txn_24h)),
        ("distance_from_home_km","Distance",f"{dist}km"),
        ("account_age_days","Acc. Age",f"{int(acc_age)}d"),
        ("failed_attempts_last_24h","Failed",str(failed)),
        ("card_present","Card Present","Yes" if payload["card_present"] else "No"),
        ("is_international","Intl","Yes" if payload["is_international"] else "No"),
        ("device_change","Device Change","Yes" if payload["device_change"] else "No"),
    ]
    return payload, found_keys, field_display


# ── RESULT RENDERER ─────────────────────────────────────
def render_result(result, status_code, txn_id=""):
    if status_code != 200:
        err = result.get("detail", str(result))
        cls = "warn" if "UNIQUE" in err else "err"
        msg = "⚠ Transaction ID already used — change it and try again." if "UNIQUE" in err else f"✕ {err[:200]}"
        st.markdown(f'<div class="banner {cls}">{msg}</div>', unsafe_allow_html=True)
        return

    decision   = result["decision"]
    score      = result["fraud_score"]
    confidence = result["confidence"]
    reasons    = result.get("reasons", [])
    rules      = result.get("rule_triggers", [])
    action     = result.get("recommended_action", "")
    ms         = result.get("processing_ms", 0)
    tid        = result.get("transaction_id", txn_id)
    dec_lower  = decision.lower()
    icon       = {"BLOCK": "🚫", "REVIEW": "⚠️", "ALLOW": "✅"}.get(decision, "")

    st.markdown(f"""
    <div class="decision-wrap {dec_lower}">
        <div class="decision-icon">{icon}</div>
        <div>
            <div class="decision-sublabel">Decision</div>
            <div class="decision-value {dec_lower}">{decision}</div>
        </div>
    </div>""", unsafe_allow_html=True)

    pct = int(score * 100)
    bar_cls = "red" if score > 0.6 else ("amber" if score > 0.3 else "green")
    st.markdown(f"""
    <div class="score-header">
        <span class="score-label">Fraud Probability</span>
        <span class="score-value">{score:.6f}</span>
    </div>
    <div class="score-track"><div class="score-fill {bar_cls}" style="width:{pct}%"></div></div>
    <div class="score-ticks"><span>0.0 Safe</span><span>0.3 Review</span><span>0.6 Block</span><span>1.0</span></div>
    """, unsafe_allow_html=True)

    conf_colors = {"HIGH": "#22c55e", "MEDIUM": "#f59e0b", "LOW": "#f43f5e"}
    conf_color  = conf_colors.get(confidence, "#6b7280")
    st.markdown(f"""
    <div class="stat-row">
        <div class="stat-card">
            <div class="stat-val" style="color:{conf_color}">{confidence}</div>
            <div class="stat-lbl">Confidence</div>
        </div>
        <div class="stat-card">
            <div class="stat-val">{ms:.1f}<span style="font-size:12px;font-weight:500;color:#4b5563">ms</span></div>
            <div class="stat-lbl">Latency</div>
        </div>
        <div class="stat-card">
            <div class="stat-val" style="font-size:12px;color:#6b7280;font-family:'JetBrains Mono',monospace">{tid[:14]}</div>
            <div class="stat-lbl">TXN ID</div>
        </div>
    </div>""", unsafe_allow_html=True)

    if rules:
        pills = "".join([f'<span class="pill pill-rule">{r}</span>' for r in rules])
        st.markdown(f'<div class="pill-section"><div class="pill-heading">Triggered Rules</div><div class="pill-row">{pills}</div></div>', unsafe_allow_html=True)

    if reasons:
        pills = "".join([f'<span class="pill pill-reason">{r}</span>' for r in reasons])
        st.markdown(f'<div class="pill-section"><div class="pill-heading">Risk Signals</div><div class="pill-row">{pills}</div></div>', unsafe_allow_html=True)

    st.markdown(f'<div class="action-box"><span>→</span><span>{action}</span></div>', unsafe_allow_html=True)


# ── NAV BAR ─────────────────────────────────────────────
api_ok   = check_api()
dot_cls  = "nav-status-dot" + ("" if api_ok else " offline")
stat_cls = "nav-status" + ("" if api_ok else " offline")
stat_txt = "SYSTEM ONLINE" if api_ok else "API OFFLINE"

st.markdown(f"""
<div class="nav-bar">
    <div class="nav-logo">
        <div class="nav-logo-icon">🛡️</div>
        <div class="nav-logo-text">Fraud<span>Shield</span></div>
    </div>
    <div class="{stat_cls}">
        <div class="{dot_cls}"></div>
        {stat_txt}
    </div>
</div>""", unsafe_allow_html=True)

if not api_ok:
    st.markdown("""
    <div class="banner err">
        ⚠ API server is not running. Start it with:&nbsp;
        <code style="background:rgba(255,255,255,0.06);padding:2px 8px;border-radius:5px;">
        uvicorn src.api.main:app --reload --port 8000
        </code>
    </div><br>""", unsafe_allow_html=True)
    st.stop()


# ── TABS ────────────────────────────────────────────────
tab_upload, tab_manual = st.tabs(["📄  Upload Slip", "✏️  Manual Entry"])


# ══════════════════════════════════════════════════════
# TAB 1 — UPLOAD SLIP
# ══════════════════════════════════════════════════════
with tab_upload:
    left_up, right_up = st.columns([1.05, 1], gap="large")

    with left_up:
        st.markdown('<div class="sec-label">Upload Payment Slip</div>', unsafe_allow_html=True)
        st.markdown('<div class="panel">', unsafe_allow_html=True)

        sample_choice = st.selectbox(
            "Try a sample slip",
            ["— select —"] + list(SAMPLE_SLIPS.keys()),
            key="sample_select"
        )

        uploaded_file = st.file_uploader(
            "Drop your slip here or click to browse",
            type=["txt", "pdf", "jpg", "jpeg", "png"],
            key="slip_upload",
            help="Supports .txt, .pdf, .jpg, .png"
        )

        slip_text   = None
        source_note = None

        if sample_choice != "— select —":
            slip_text   = SAMPLE_SLIPS[sample_choice]
            source_note = ("info", f"Loaded sample: {sample_choice}")
        elif uploaded_file is not None:
            ext = uploaded_file.name.rsplit(".", 1)[-1].lower()
            if ext == "txt":
                slip_text = uploaded_file.read().decode("utf-8", errors="replace")
            elif ext in ("jpg", "jpeg", "png"):
                source_note = ("info", f"🖼️ Image uploaded ({uploaded_file.name}). For OCR run: python slip_parser.py --file \"{uploaded_file.name}\". Using demo extraction.")
                slip_text = "Transaction ID: TXN-IMG-001\nAmount: 1200.00\nDate: 2026-06-03\nTime: 14:30\nMerchant: retail\nCountry: IN\nCard Present: yes"
            elif ext == "pdf":
                source_note = ("info", f"📄 PDF uploaded ({uploaded_file.name}). For full parsing run: python slip_parser.py --file \"{uploaded_file.name}\". Using demo extraction.")
                slip_text = "PAYMENT RECEIPT\nTransaction ID: TXN-PDF-001\nAmount: 3500.00\nDate: 2026-06-03\nTime: 02:15\nMerchant Category: travel\nCountry Code: SG\nCard Present: no\nInternational: yes\nDevice Change: yes\nTransactions Last 1H: 7\nTransactions Last 24H: 20\nAvg Amount 7D: 150\nDistance From Home: 480\nAccount Age: 12\nFailed Attempts: 2"

        if source_note:
            st.markdown(f'<div class="banner {source_note[0]}" style="margin-top:12px;">{source_note[1]}</div>', unsafe_allow_html=True)

        if slip_text:
            st.markdown('<div class="preview-label" style="margin-top:16px;">Raw Content</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="preview-box">{slip_text[:600]}{"..." if len(slip_text)>600 else ""}</div>', unsafe_allow_html=True)

            payload, found_keys, field_display = parse_slip(slip_text)

            chips_html = "".join([
                f'<div class="chip {"found" if key in found_keys else "missing"}"><div class="chip-label">{label}</div><div class="chip-val">{val}</div></div>'
                for key, label, val in field_display
            ])

            st.markdown(f"""
            <div class="fields-wrap">
                <div class="fields-title">Extracted Fields <span class="count-badge">{len(found_keys)}</span></div>
                <div class="chips-row">{chips_html}</div>
            </div>""", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("🔍  Analyse Transaction", use_container_width=True, key="upload_analyse_btn", type="primary"):
                st.session_state["upload_result"] = predict(payload)
                st.session_state["upload_txn_id"] = payload["transaction_id"]

        st.markdown('</div>', unsafe_allow_html=True)

    with right_up:
        st.markdown('<div class="sec-label">Risk Assessment</div>', unsafe_allow_html=True)
        st.markdown('<div class="panel">', unsafe_allow_html=True)

        if "upload_result" in st.session_state:
            render_result(st.session_state["upload_result"][0], st.session_state["upload_result"][1], st.session_state.get("upload_txn_id",""))
        else:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-icon">🛡️</div>
                <div class="empty-text">Upload a slip and click<br>Analyse Transaction</div>
            </div>""", unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════
# TAB 2 — MANUAL ENTRY
# ══════════════════════════════════════════════════════
with tab_manual:
    left, right = st.columns([1.05, 1], gap="large")

    with left:
        st.markdown('<div class="sec-label">Transaction Details</div>', unsafe_allow_html=True)
        st.markdown('<div class="panel">', unsafe_allow_html=True)

        with st.form("predict_form", clear_on_submit=False):
            txn_id = st.text_input("Transaction ID", value=f"TXN-{datetime.now().strftime('%H%M%S%f')[:10]}")
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                amount   = st.number_input("Amount ($)", min_value=0.0, value=250.0, step=10.0)
                hour     = st.number_input("Hour of Day (0–23)", min_value=0, max_value=23, value=14)
                dow      = st.number_input("Day of Week (0=Mon)", min_value=0, max_value=6, value=1)
                merchant = st.selectbox("Merchant Category", ["grocery","restaurant","gas","retail","travel","entertainment","healthcare"])
                country  = st.selectbox("Country", ["IN","US","GB","DE","SG"])
            with c2:
                txn_1h  = st.number_input("Transactions (last 1h)", min_value=0, value=1)
                txn_24h = st.number_input("Transactions (last 24h)", min_value=0, value=3)
                avg_amt = st.number_input("Avg Amount last 7d ($)", min_value=0.0, value=200.0)
                dist    = st.number_input("Distance from Home (km)", min_value=0.0, value=5.0)
                age     = st.number_input("Account Age (days)", min_value=0.0, value=365.0)
                failed  = st.number_input("Failed Attempts (24h)", min_value=0, value=0)

            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            st.markdown('<div style="font-size:10px;font-weight:600;letter-spacing:2px;color:#4b5563;text-transform:uppercase;margin-bottom:10px;">Flags</div>', unsafe_allow_html=True)
            fc1, fc2, fc3 = st.columns(3)
            with fc1: card_present  = st.checkbox("💳 Card Present", value=True)
            with fc2: is_intl       = st.checkbox("🌍 International", value=False)
            with fc3: device_change = st.checkbox("📱 Device Change", value=False)

            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("🔍  Analyse Transaction", use_container_width=True)

        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="sec-label">Risk Assessment</div>', unsafe_allow_html=True)
        st.markdown('<div class="panel">', unsafe_allow_html=True)

        if submitted:
            payload = {
                "transaction_id": txn_id, "amount": amount,
                "hour_of_day": hour, "day_of_week": dow,
                "merchant_category": merchant, "country_code": country,
                "card_present": int(card_present),
                "transactions_last_1h": txn_1h, "transactions_last_24h": txn_24h,
                "avg_amount_last_7d": avg_amt, "distance_from_home_km": dist,
                "account_age_days": age, "failed_attempts_last_24h": failed,
                "is_international": int(is_intl), "device_change": int(device_change),
            }
            with st.spinner("Analysing..."):
                result, status_code = predict(payload)
            render_result(result, status_code, txn_id)
        else:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-icon">🛡️</div>
                <div class="empty-text">Fill in the details and<br>click Analyse</div>
            </div>""", unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)


# ── DASHBOARD ───────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)

with st.expander("📊  Live Dashboard — Metrics & Recent Transactions"):
    dl, dr = st.columns([1, 1.1], gap="large")

    with dl:
        st.markdown('<div class="sec-label">System Metrics</div>', unsafe_allow_html=True)
        metrics = get_metrics()

        if metrics:
            m1, m2, m3 = st.columns(3)
            with m1:
                st.markdown(f'<div class="dash-metric"><div class="dash-metric-val">{metrics.get("total_transactions",0)}</div><div class="dash-metric-lbl">Total TXNs</div></div>', unsafe_allow_html=True)
            with m2:
                fr = metrics.get("fraud_rate_pct", 0)
                fc = "#f43f5e" if fr > 20 else ("#f59e0b" if fr > 5 else "#22c55e")
                st.markdown(f'<div class="dash-metric"><div class="dash-metric-val" style="color:{fc}">{fr:.1f}%</div><div class="dash-metric-lbl">Fraud Rate</div></div>', unsafe_allow_html=True)
            with m3:
                st.markdown(f'<div class="dash-metric"><div class="dash-metric-val">{metrics.get("avg_latency_ms",0):.0f}<span style="font-size:14px;color:#4b5563">ms</span></div><div class="dash-metric-lbl">Avg Latency</div></div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            dd = metrics.get("decision_distribution", {})
            m4, m5, m6 = st.columns(3)
            with m4:
                st.markdown(f'<div class="dash-metric"><div class="dash-metric-val" style="color:#22c55e">{dd.get("ALLOW",{}).get("count",0)}</div><div class="dash-metric-lbl">✅ Allowed</div></div>', unsafe_allow_html=True)
            with m5:
                st.markdown(f'<div class="dash-metric"><div class="dash-metric-val" style="color:#f59e0b">{dd.get("REVIEW",{}).get("count",0)}</div><div class="dash-metric-lbl">⚠️ Review</div></div>', unsafe_allow_html=True)
            with m6:
                st.markdown(f'<div class="dash-metric"><div class="dash-metric-val" style="color:#f43f5e">{dd.get("BLOCK",{}).get("count",0)}</div><div class="dash-metric-lbl">🚫 Blocked</div></div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(f"""
            <div style="display:flex;flex-wrap:wrap;gap:20px;font-family:'JetBrains Mono',monospace;font-size:11px;color:#374151;">
                <span>p95 <b style="color:#6b7280">{metrics.get("p95_latency_ms",0):.0f}ms</b></span>
                <span>p99 <b style="color:#6b7280">{metrics.get("p99_latency_ms",0):.0f}ms</b></span>
                <span>errors <b style="color:#f43f5e">{metrics.get("error_count",0)}</b></span>
                <span>uptime <b style="color:#6b7280">{int(metrics.get("uptime_seconds",0))}s</b></span>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#374151;font-size:13px;padding:16px 0;">Could not fetch metrics.</div>', unsafe_allow_html=True)

    with dr:
        st.markdown('<div class="sec-label">Recent Transactions</div>', unsafe_allow_html=True)
        recent = get_recent(12)

        if recent:
            rows = "".join([f"""
            <div class="txn-row">
                <span class="txn-id">{txn.get("transaction_id","")}</span>
                <span class="txn-score">{float(txn.get("fraud_score",0)):.4f}</span>
                <span class="txn-badge {txn.get("decision","ALLOW")}">{txn.get("decision","ALLOW")}</span>
                <span class="txn-time">{txn.get("created_at","")[:16].replace("T"," ")}</span>
            </div>""" for txn in recent])
            st.markdown(f'<div class="txn-list">{rows}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#374151;font-size:13px;padding:16px 0;">No transactions yet. Run a prediction first.</div>', unsafe_allow_html=True)
