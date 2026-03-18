import json
import random
import re
from collections import Counter
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import requests
import streamlit as st
from groq import Groq


# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="T-HEXA CINEMA",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CONSTANTS
# ============================================================
API_BASE = "https://ophim1.com"
CDN_FALLBACK = "https://img.ophim1.com/uploads/movies/"
REQUEST_TIMEOUT = 15

HOME_ROWS = [
    ("🔥 Đang gây nghiện", "danh-sach", "phim-moi-cap-nhat"),
    ("🎞 Phim bộ đáng cày", "danh-sach", "phim-bo"),
    ("🍿 Phim lẻ cho buổi tối", "danh-sach", "phim-le"),
    ("📺 TV Shows nổi bật", "danh-sach", "tv-shows"),
    ("🧸 Hoạt hình & family time", "danh-sach", "hoat-hinh"),
    ("🪐 Viễn tưởng & phiêu lưu", "the-loai", "vien-tuong"),
    ("👻 Kinh dị nổi bật", "the-loai", "kinh-di"),
    ("💘 Tình cảm xem rất dính", "the-loai", "tinh-cam"),
    ("⚔️ Hành động cháy máy", "the-loai", "hanh-dong"),
    ("🌏 Hàn Quốc đang hot", "quoc-gia", "han-quoc"),
]

MENU_DATA = {
    "DANH_SACH": {
        "Phim Mới": "phim-moi-cap-nhat",
        "Phim Bộ": "phim-bo",
        "Phim Lẻ": "phim-le",
        "TV Shows": "tv-shows",
        "Hoạt Hình": "hoat-hinh",
        "Phim Vietsub": "phim-vietsub",
        "Thuyết Minh": "phim-thuyet-minh",
        "Lồng Tiếng": "phim-long-tieng",
        "Bộ Đang Chiếu": "phim-bo-dang-chieu",
        "Trọn Bộ": "phim-bo-hoan-thanh",
        "Sắp Chiếu": "phim-sap-chieu",
        "Chiếu Rạp": "phim-chieu-rap",
    },
    "THE_LOAI": {
        "Hành Động": "hanh-dong",
        "Tình Cảm": "tinh-cam",
        "Hài Hước": "hai-huoc",
        "Cổ Trang": "co-trang",
        "Tâm Lý": "tam-ly",
        "Hình Sự": "hinh-su",
        "Chiến Tranh": "chien-tranh",
        "Thể Thao": "the-thao",
        "Võ Thuật": "vo-thuat",
        "Viễn Tưởng": "vien-tuong",
        "Phiêu Lưu": "phieu-luu",
        "Khoa Học": "khoa-hoc",
        "Kinh Dị": "kinh-di",
        "Âm Nhạc": "am-nhac",
        "Thần Thoại": "than-thoai",
        "Tài Liệu": "tai-lieu",
        "Gia Đình": "gia-dinh",
        "Chính Kịch": "chinh-kich",
        "Bí Ẩn": "bi-an",
        "Học Đường": "hoc-duong",
        "Kinh Điển": "kinh-dien",
    },
    "QUOC_GIA": {
        "Trung Quốc": "trung-quoc",
        "Hàn Quốc": "han-quoc",
        "Nhật Bản": "nhat-ban",
        "Thái Lan": "thai-lan",
        "Âu Mỹ": "au-my",
        "Đài Loan": "dai-loan",
        "Hồng Kông": "hong-kong",
        "Ấn Độ": "an-do",
        "Anh": "anh",
        "Pháp": "phap",
        "Việt Nam": "viet-nam",
    },
}

MOOD_SHORTCUTS = [
    ("🌙 Chill đêm", "the-loai", "tinh-cam", "Mood: Chill & tình cảm"),
    ("⚡ Căng não", "the-loai", "bi-an", "Mood: Bí ẩn & lôi cuốn"),
    ("💀 Kích thích", "the-loai", "kinh-di", "Mood: Kinh dị & adrenaline"),
    ("🛋 Thư giãn", "the-loai", "hai-huoc", "Mood: Hài & dễ xem"),
    ("🚀 Hoành tráng", "the-loai", "vien-tuong", "Mood: Viễn tưởng đỉnh"),
    ("🔥 Cày series", "danh-sach", "phim-bo", "Mood: Cày nhiều tập"),
]

DEFAULT_STATE = {
    "route": "home",
    "current_movie_slug": None,
    "browse_type": "moi-cap-nhat",
    "browse_slug": "",
    "browse_title": "Khám phá điện ảnh",
    "browse_page": 1,
    "search_query": "",
    "favorites": [],
    "watch_later": [],
    "watch_history": [],
    "continue_watching": {},
    "chat_history": [],
    "selected_episode_map": {},
    "hero_seed": 13,
    "sort_mode": "Mặc định",
    "library_tab_index": 0,
    "landing_mood": "",
    "prev_route": "home",
    "notification": None,
    "theme": "dark",
    "combo_danhmuc": [],
    "combo_theloai": [],
    "combo_quocgia": [],
    "combo_page": 1,
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# STYLES — Cinema Noir × Neon Edge
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Lexend:wght@300;400;500;600;700;800;900&family=Be+Vietnam+Pro:ital,wght@0,300;0,400;0,500;0,600;0,700;1,300;1,400&display=swap');

:root {
  --bg:        #0e1117;
  --bg2:       #161b27;
  --surface:   rgba(255,255,255,0.06);
  --surface2:  rgba(255,255,255,0.11);
  --border:    rgba(255,255,255,0.10);
  --border2:   rgba(255,255,255,0.20);
  --text:      #eef1f8;
  --muted:     #9aa3b8;
  --muted2:    #c4cad9;
  --primary:   #7b6ff0;
  --primary2:  #22d3ee;
  --accent:    #f43f5e;
  --gold:      #fbbf24;
  --green:     #10d9a0;
  --glow-p:    rgba(123,111,240,0.30);
  --glow-b:    rgba(34,211,238,0.22);
  --ff-display: 'Lexend', sans-serif;
  --ff-body:   'Be Vietnam Pro', sans-serif;
  --radius:    18px;
  --radius-lg: 26px;
  --radius-xl: 34px;
  --shadow:    0 32px 80px rgba(0,0,0,0.5);
  --shadow-sm: 0 8px 30px rgba(0,0,0,0.3);
}

*, *::before, *::after { box-sizing: border-box; }

html, body {
  background: #0e1117 !important;
  background-color: #0e1117 !important;
  font-family: var(--ff-body);
  color: #eef1f8;
  -webkit-font-smoothing: antialiased;
}

/* Force dark on every Streamlit container layer */
.stApp,
.main,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewBlockContainer"],
[data-testid="stMainBlockContainer"],
[data-testid="stMain"],
[data-testid="stVerticalBlock"],
[data-testid="stHorizontalBlock"],
section.main,
div.main,
.block-container,
[class*="appview"],
[class*="main"] {
  background: #0e1117 !important;
  background-color: #0e1117 !important;
  color: #eef1f8 !important;
}

/* Catch any rogue white divs */
div[data-testid]:not([data-testid="stSidebar"]):not([data-testid="stChatMessage"]) {
  background-color: transparent !important;
}

[class*="st-"] { color: #eef1f8; }

.stApp {
  background: #0e1117 !important;
  background-color: #0e1117 !important;
  min-height: 100vh;
}

[data-testid="stHeader"], [data-testid="stToolbar"] { display: none !important; }
footer, header { visibility: hidden; }

.block-container {
  max-width: 1520px;
  padding: 1rem 2rem 4rem;
}

/* ── SIDEBAR ─────────────────────────────── */
section[data-testid="stSidebar"] {
  background: #12161f !important;
  border-right: 1px solid var(--border2);
}
section[data-testid="stSidebar"] * { color: var(--text) !important; }
section[data-testid="stSidebar"] .stButton > button {
  background: rgba(255,255,255,0.07) !important;
  border: 1px solid var(--border2) !important;
  color: var(--text) !important;
  font-family: var(--ff-body) !important;
  font-weight: 500 !important;
  font-size: 0.9rem !important;
  border-radius: var(--radius) !important;
  transition: all 0.2s ease !important;
  min-height: 2.6rem !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
  background: rgba(123,111,240,0.18) !important;
  border-color: var(--primary) !important;
  color: #fff !important;
  transform: translateX(3px) !important;
}

/* ── TOP BAR SHELL ───────────────────────── */
.topbar {
  display: flex;
  align-items: center;
  gap: 16px;
  background: rgba(13,19,32,0.85);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  padding: 12px 20px;
  margin-bottom: 14px;
  box-shadow: 0 4px 30px rgba(0,0,0,0.3);
  position: sticky;
  top: 0;
  z-index: 100;
}

.brand-logo {
  width: 46px; height: 46px;
  border-radius: 14px;
  background: linear-gradient(135deg, var(--primary), var(--primary2));
  display: grid; place-items: center;
  font-family: var(--ff-display);
  font-size: 1.1rem; font-weight: 800;
  color: #fff;
  flex-shrink: 0;
  box-shadow: 0 8px 24px var(--glow-p);
}

.brand-text { line-height: 1.2; }
.brand-name {
  font-family: var(--ff-display);
  font-size: 1.1rem; font-weight: 800;
  letter-spacing: -0.3px; color: #fff;
}
.brand-tagline { font-size: 0.76rem; color: var(--muted); font-weight: 400; }

/* ── COLUMN ALIGNMENT — uniform row heights ── */
[data-testid="stHorizontalBlock"] {
  align-items: center !important;
  gap: 10px !important;
}
[data-testid="column"] {
  display: flex !important;
  flex-direction: column !important;
  justify-content: center !important;
  gap: 0 !important;
}
/* Remove extra margin Streamlit adds above/below widgets */
[data-testid="column"] > div { width: 100% !important; }
[data-testid="column"] .stButton { width: 100% !important; margin: 0 !important; }
[data-testid="column"] .stButton > button {
  width: 100% !important;
  height: 2.65rem !important;
  margin: 0 !important;
}
/* Input same height as buttons */
[data-testid="column"] .stTextInput { margin: 0 !important; }
[data-testid="column"] .stTextInput > label { display: none !important; }
[data-testid="column"] .stTextInput > div { margin: 0 !important; }
[data-testid="column"] .stTextInput > div > div {
  height: 2.65rem !important;
  min-height: 2.65rem !important;
}
[data-testid="column"] .stTextInput > div > div > input {
  height: 100% !important;
  padding: 0 14px !important;
  line-height: 2.65rem !important;
}
/* Popover same height */
[data-testid="column"] div[data-testid="stPopover"] { width: 100% !important; margin: 0 !important; }
[data-testid="column"] div[data-testid="stPopover"] > button {
  width: 100% !important;
  height: 2.65rem !important;
  margin: 0 !important;
}

/* ── BUTTONS — force dark on ALL button types ── */
button, .stButton > button,
div[data-testid="stPopover"] > button,
div[data-testid="stPopoverButton"] > button {
  font-family: var(--ff-body) !important;
  font-weight: 600 !important;
  font-size: 0.88rem !important;
  color: #eef1f8 !important;
  background: #1e2535 !important;
  border: 1px solid rgba(255,255,255,0.15) !important;
  border-radius: var(--radius) !important;
  min-height: 2.6rem !important;
  transition: all 0.18s ease !important;
  box-shadow: none !important;
  white-space: nowrap !important;
}
button:hover, .stButton > button:hover,
div[data-testid="stPopover"] > button:hover {
  background: #26304a !important;
  border-color: rgba(123,111,240,0.5) !important;
  color: #fff !important;
  transform: translateY(-1px) !important;
}
/* all text/icons inside buttons */
button *, .stButton > button *,
div[data-testid="stPopover"] > button * {
  color: #eef1f8 !important;
}

.primary-btn .stButton > button {
  background: linear-gradient(135deg, var(--primary), var(--primary2)) !important;
  border: none !important;
  color: #fff !important;
  font-weight: 700 !important;
  box-shadow: 0 6px 22px var(--glow-p) !important;
}
.primary-btn .stButton > button:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 12px 32px var(--glow-p) !important;
}

/* Popover panel */
div[data-baseweb="popover"], [data-baseweb="popover"] {
  background: #141926 !important;
  border: 1px solid rgba(255,255,255,0.15) !important;
  border-radius: var(--radius-lg) !important;
  box-shadow: 0 24px 60px rgba(0,0,0,0.6) !important;
}
div[data-baseweb="popover"] *, [data-baseweb="popover"] * {
  color: #eef1f8 !important;
  background-color: transparent !important;
}
/* popover inner buttons */
div[data-baseweb="popover"] button {
  background: #1e2535 !important;
  border: 1px solid rgba(255,255,255,0.1) !important;
  color: #eef1f8 !important;
  margin: 2px 0 !important;
}

/* ── INPUTS ──────────────────────────────── */
.stTextInput > div > div > input,
.stTextInput > div > div,
.stTextArea textarea,
[data-baseweb="input"] input,
[data-baseweb="input"],
[data-baseweb="base-input"] {
  font-family: var(--ff-body) !important;
  font-size: 0.92rem !important;
  color: #eef1f8 !important;
  -webkit-text-fill-color: #eef1f8 !important;
  background: #1a2032 !important;
  background-color: #1a2032 !important;
  border: 1px solid rgba(255,255,255,0.18) !important;
  border-radius: var(--radius) !important;
  font-weight: 400 !important;
}
.stTextInput > div > div > input::placeholder,
.stTextArea textarea::placeholder { color: var(--muted) !important; opacity: 1 !important; }
.stTextInput > div > div > input:focus,
[data-baseweb="input"]:focus-within { border-color: var(--primary) !important; }

/* ── SELECTBOX ───────────────────────────── */
.stSelectbox > div > div, .stMultiSelect > div > div,
[data-baseweb="select"] > div,
[data-baseweb="select"] {
  background: #1a2032 !important;
  background-color: #1a2032 !important;
  border: 1px solid rgba(255,255,255,0.18) !important;
  border-radius: var(--radius) !important;
  color: #eef1f8 !important;
}
[data-baseweb="select"] * { color: #eef1f8 !important; }
[data-baseweb="select"] svg { fill: var(--muted2) !important; }
div[role="listbox"] {
  background: #141926 !important;
  border: 1px solid rgba(255,255,255,0.15) !important;
  border-radius: var(--radius) !important;
}
div[role="option"] { color: #eef1f8 !important; background: transparent !important; }
div[role="option"]:hover { background: rgba(123,111,240,0.18) !important; }

/* ── TABS ────────────────────────────────── */
button[role="tab"] {
  font-family: var(--ff-body) !important;
  font-weight: 600 !important;
  font-size: 0.88rem !important;
  color: var(--muted2) !important;
  background: transparent !important;
  border: none !important;
  border-bottom: 2px solid transparent !important;
  border-radius: 0 !important;
  padding: 10px 18px !important;
}
button[role="tab"][aria-selected="true"] {
  color: var(--text) !important;
  border-bottom-color: var(--primary) !important;
}
[data-testid="stTabs"] > div:first-child {
  border-bottom: 1px solid var(--border) !important;
  gap: 0 !important;
}

/* ── CHAT ────────────────────────────────── */
.stChatMessage, [data-testid="stChatMessage"] {
  background: rgba(255,255,255,0.04) !important;
  border-radius: 16px !important;
  border: 1px solid var(--border) !important;
}
[data-testid="stChatMessageContent"] { color: var(--text) !important; }
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] span,
[data-testid="stMarkdownContainer"] div { color: var(--text) !important; line-height: 1.8; }
[data-testid="stMarkdownContainer"] strong { color: #ffffff !important; }
p, span, div, label { color: var(--text); }
.stCaption, [data-testid="stCaptionContainer"] { color: var(--muted2) !important; }

/* ── COMPONENTS ──────────────────────────── */

/* HERO */
.hero-wrap {
  position: relative;
  min-height: 500px;
  border-radius: var(--radius-xl);
  overflow: hidden;
  border: 1px solid var(--border2);
  box-shadow: var(--shadow);
  margin-bottom: 4px;
}
.hero-bg {
  position: absolute; inset: 0;
  width: 100%; height: 100%;
  object-fit: cover;
  filter: saturate(1.05) brightness(0.85);
}
.hero-scrim {
  position: absolute; inset: 0;
  background:
    linear-gradient(90deg, var(--hero-scrim-strong, rgba(8,12,20,0.95)) 0%, var(--hero-scrim-mid, rgba(8,12,20,0.72)) 42%, rgba(0,0,0,0.18) 75%, rgba(0,0,0,0.45) 100%),
    linear-gradient(0deg, var(--hero-scrim-strong, rgba(8,12,20,0.75)) 0%, transparent 55%);
}
.hero-inner {
  position: relative; z-index: 2;
  padding: 42px 40px;
  max-width: 640px;
}
.hero-pills {
  display: flex; gap: 8px; flex-wrap: wrap;
  margin-bottom: 18px;
}
.pill {
  display: inline-flex; align-items: center;
  padding: 5px 12px;
  border-radius: 999px;
  font-size: 0.75rem; font-weight: 700;
  font-family: var(--ff-display);
  letter-spacing: 0.3px;
}
.pill-primary { background: linear-gradient(135deg, var(--primary), var(--primary2)); color: #fff; }
.pill-glass { background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.2); color: #fff; }
.pill-gold { background: rgba(245,200,66,0.18); border: 1px solid rgba(245,200,66,0.35); color: var(--gold); }

.hero-title {
  font-family: var(--ff-display);
  font-size: clamp(2.2rem, 4vw, 3.6rem);
  font-weight: 800;
  line-height: 1.02;
  letter-spacing: -1.5px;
  color: #fff;
  margin-bottom: 14px;
  text-shadow: 0 2px 20px rgba(0,0,0,0.4);
}
.hero-desc {
  font-size: 0.97rem;
  line-height: 1.8;
  color: rgba(240,244,255,0.82);
  margin-bottom: 20px;
  font-weight: 300;
}
.hero-score {
  font-size: 0.85rem;
  color: var(--muted2);
  font-style: italic;
}

/* MOVIE CARD */
.mcard {
  position: relative;
  height: 400px;
  border-radius: var(--radius-lg);
  overflow: hidden;
  border: 1px solid var(--border);
  background: #0d1320;
  transition: transform 0.22s cubic-bezier(.22,1,.36,1), box-shadow 0.22s ease, border-color 0.22s ease;
  cursor: pointer;
}
.mcard:hover {
  transform: translateY(-8px) scale(1.01);
  box-shadow: 0 28px 60px rgba(0,0,0,0.55), 0 0 0 1px rgba(108,99,255,0.3);
  border-color: rgba(108,99,255,0.4);
}
.mcard img { width: 100%; height: 100%; object-fit: cover; }
.mcard-overlay {
  position: absolute; inset: 0;
  background: linear-gradient(180deg, transparent 30%, rgba(8,12,20,0.96) 100%);
  padding: 12px;
  display: flex; flex-direction: column;
  justify-content: space-between;
}
.mcard-top { display: flex; justify-content: space-between; align-items: flex-start; }
.mcard-bottom {}
.mcard-name {
  font-family: var(--ff-display);
  font-size: 0.98rem; font-weight: 700;
  line-height: 1.3; color: #fff;
  display: -webkit-box;
  -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
  margin-bottom: 6px;
  text-shadow: 0 2px 10px rgba(0,0,0,0.5);
}
.mcard-meta {
  font-size: 0.78rem; color: var(--muted2);
  display: -webkit-box;
  -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
  margin-bottom: 8px; font-weight: 400;
}
.mcard-tags { display: flex; gap: 6px; flex-wrap: wrap; }

.badge {
  display: inline-flex; align-items: center;
  padding: 4px 9px; border-radius: 999px;
  font-size: 0.7rem; font-weight: 700;
  font-family: var(--ff-display);
  backdrop-filter: blur(8px);
}
.badge-default { background: rgba(0,0,0,0.6); border: 1px solid rgba(255,255,255,0.15); color: #fff; }
.badge-hot { background: linear-gradient(135deg,#ff4d6d,#ff8c5a); color: #fff; }
.badge-rank { background: linear-gradient(135deg, var(--gold), #ffa05a); color: #1a1200; }
.badge-score { background: rgba(245,200,66,0.15); border: 1px solid rgba(245,200,66,0.3); color: var(--gold); }
.badge-quality { background: rgba(0,229,160,0.15); border: 1px solid rgba(0,229,160,0.3); color: var(--green); }

/* SECTION HEADING */
.sh {
  font-family: var(--ff-display);
  font-size: 1.15rem; font-weight: 800;
  color: #eef1f8 !important;
  letter-spacing: -0.3px;
  margin: 28px 0 14px;
  display: flex; align-items: center; gap: 10px;
}
.sh-line {
  flex: 1; height: 1px;
  background: linear-gradient(90deg, rgba(255,255,255,0.18), transparent);
}
.sh-sub {
  font-family: var(--ff-body);
  font-size: 0.88rem; color: #9aa3b8 !important;
  margin: -10px 0 16px; font-weight: 400;
}

/* GLASS CARD */
.glass {
  background: #1a2235 !important;
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: var(--radius-lg);
  padding: 18px;
}
.glass * { color: #eef1f8 !important; }
.glass-sm { border-radius: var(--radius); padding: 14px; }

/* STAT TILE */
.stat {
  background: #1a2235 !important;
  border: 1px solid rgba(255,255,255,0.10);
  border-radius: var(--radius-lg);
  padding: 16px;
  text-align: center;
}
.stat-val {
  font-family: var(--ff-display);
  font-size: 1.6rem; font-weight: 800;
  background: linear-gradient(135deg, #7b6ff0, #22d3ee);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  display: block;
}
.stat-label { font-size: 0.78rem; color: #9aa3b8 !important; margin-top: 4px; font-weight: 500; display: block; }

/* BANNER */
.banner {
  background: linear-gradient(135deg, rgba(123,111,240,0.20), rgba(34,211,238,0.10)) !important;
  border: 1px solid rgba(123,111,240,0.35);
  border-radius: var(--radius-lg);
  padding: 18px 20px;
}
.banner-title {
  font-family: var(--ff-display);
  font-weight: 800; font-size: 1rem;
  color: #fff !important; margin-bottom: 6px; display: block;
}
.banner-sub { font-size: 0.85rem; color: #c4cad9 !important; font-weight: 400; line-height: 1.6; display: block; }

/* WATCH SHELL */
.player {
  position: relative;
  padding-bottom: 56.25%;
  border-radius: var(--radius-xl);
  overflow: hidden;
  border: 1px solid var(--border2);
  box-shadow: var(--shadow), 0 0 80px rgba(108,99,255,0.12);
  background: #000;
}
.player iframe {
  position: absolute; inset: 0;
  width: 100%; height: 100%; border: none;
}

/* POSTER */
.poster-wrap {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  padding: 10px;
  box-shadow: var(--shadow);
}
.poster-wrap img { border-radius: var(--radius-lg); width: 100%; }

/* INFO GRID */
.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px; margin-top: 16px;
}
.info-cell {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 12px;
}
.info-label { font-size: 0.72rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.6px; font-weight: 600; margin-bottom: 4px; }
.info-val { font-size: 0.9rem; font-weight: 700; color: var(--text); font-family: var(--ff-display); }

/* DETAIL */
.detail-title {
  font-family: var(--ff-display);
  font-size: clamp(1.8rem, 3.5vw, 2.8rem);
  font-weight: 800;
  line-height: 1.05;
  letter-spacing: -1px;
  color: #fff;
  margin-bottom: 8px;
}
.detail-sub { font-size: 0.9rem; color: var(--muted2); margin-bottom: 14px; }
.detail-desc { font-size: 0.95rem; line-height: 1.85; color: var(--muted2); font-weight: 300; }

/* EMPTY */
.empty {
  text-align: center;
  border: 1px dashed var(--border2);
  border-radius: var(--radius-xl);
  padding: 48px 24px;
  color: var(--muted);
  font-weight: 400;
  font-size: 0.95rem;
}
.empty-icon { font-size: 2.5rem; margin-bottom: 12px; opacity: 0.5; }

/* NOTIFICATION */
.notif {
  background: rgba(0,229,160,0.12);
  border: 1px solid rgba(0,229,160,0.3);
  border-radius: var(--radius);
  padding: 10px 16px;
  font-size: 0.88rem;
  color: var(--green);
  font-weight: 600;
  margin-bottom: 12px;
}

/* CONTINUE CARD */
.cont-card {
  position: relative; height: 360px;
  border-radius: var(--radius-lg); overflow: hidden;
  border: 1px solid var(--border);
  background: #0d1320;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.cont-card:hover { transform: translateY(-5px); box-shadow: 0 20px 50px rgba(0,0,0,0.45); }
.cont-card img { width: 100%; height: 100%; object-fit: cover; }
.cont-overlay {
  position: absolute; inset: 0;
  background: linear-gradient(0deg, rgba(8,12,20,0.97) 30%, rgba(8,12,20,0.3) 70%);
  padding: 12px; display: flex; flex-direction: column; justify-content: space-between;
}

/* PROGRESS BAR hint */
.ep-progress {
  height: 3px; background: var(--border);
  border-radius: 2px; margin-top: 8px; overflow: hidden;
}
.ep-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--primary), var(--primary2));
  border-radius: 2px;
}

/* MOOD CHIP */
.mood-chip {
  display: inline-flex; align-items: center; gap: 6px;
  background: var(--surface); border: 1px solid var(--border2);
  border-radius: 999px; padding: 8px 14px;
  font-size: 0.84rem; font-weight: 600; color: var(--text);
  cursor: pointer; transition: all 0.18s ease;
  white-space: nowrap;
}
.mood-chip:hover {
  background: var(--surface2);
  border-color: var(--primary);
  transform: translateY(-2px);
  box-shadow: 0 8px 20px var(--glow-p);
}

/* DIVIDER */
.divider { height: 1px; background: linear-gradient(90deg, transparent, var(--border2), transparent); margin: 22px 0; }

/* SCROLL ROW */
code { color: var(--green) !important; background: rgba(0,229,160,0.08) !important; border: 1px solid rgba(0,229,160,0.15); padding: 2px 6px; border-radius: 6px; }

[data-testid="stWidgetLabel"] { color: var(--muted) !important; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# HELPERS
# ============================================================
def normalize_text(text: Optional[str]) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def strip_html(text: Optional[str]) -> str:
    raw = str(text or "")
    raw = re.sub(r"<br\s*/?>", "\n", raw, flags=re.I)
    raw = re.sub(r"</p>", "\n", raw, flags=re.I)
    raw = re.sub(r"<.*?>", "", raw)
    return normalize_text(raw)


def route_to(route: str, slug: Optional[str] = None):
    st.session_state.prev_route = st.session_state.route
    st.session_state.route = route
    if slug is not None:
        st.session_state.current_movie_slug = slug


def set_browse(filter_type: str, filter_slug: str, title: str, page: int = 1):
    st.session_state.browse_type = filter_type
    st.session_state.browse_slug = filter_slug
    st.session_state.browse_title = title
    st.session_state.browse_page = page
    route_to("browse")


def handle_search_submit():
    query = normalize_text(st.session_state.get("search_input", ""))
    if query:
        st.session_state.search_query = query
        set_browse("tim-kiem", query, f'🔍 Kết quả: "{query}"', 1)


def build_image_url(thumb_url: Optional[str], path_img: str = CDN_FALLBACK) -> str:
    thumb_url = str(thumb_url or "")
    if not thumb_url:
        return "https://placehold.co/800x1200/0d1320/6c63ff?text=T-HEXA"
    if thumb_url.startswith("http://") or thumb_url.startswith("https://"):
        return thumb_url
    return f"{path_img}{thumb_url}"


def quality_badge(item: dict) -> str:
    return normalize_text(item.get("quality") or "HD")


def movie_meta_line(item: dict) -> str:
    parts = []
    for key in ["year", "lang", "episode_current", "time"]:
        value = normalize_text(item.get(key))
        if value:
            parts.append(value)
    if not parts:
        origin = normalize_text(item.get("origin_name"))
        if origin:
            parts.append(origin)
    return " · ".join(parts) if parts else "Điện ảnh chọn lọc"


def deterministic_score(slug: str) -> float:
    base = sum(ord(c) for c in slug) % 20
    return round(8.1 + base / 20, 1)


def score_reason(slug: str) -> str:
    reasons = [
        "cuốn ngay từ vài phút đầu",
        "có vibe xem là dính",
        "hợp để cày liền nhiều tập",
        "đẹp phần nhìn và giữ mood tốt",
        "nhịp kể dễ giữ chân người xem",
        "có năng lượng giải trí rất mạnh",
    ]
    idx = sum(ord(c) for c in slug) % len(reasons)
    return reasons[idx]


def is_saved(collection_key: str, slug: str) -> bool:
    return any(x.get("slug") == slug for x in st.session_state.get(collection_key, []))


def upsert_collection(collection_key: str, item: dict):
    items = [x for x in st.session_state[collection_key] if x.get("slug") != item.get("slug")]
    st.session_state[collection_key] = [item] + items


def remove_from_collection(collection_key: str, slug: str):
    st.session_state[collection_key] = [
        x for x in st.session_state[collection_key] if x.get("slug") != slug
    ]


def pack_movie(item: dict, path_img: str = CDN_FALLBACK) -> dict:
    return {
        "slug": item.get("slug"),
        "name": item.get("name"),
        "thumb_url": build_image_url(item.get("thumb_url") or item.get("poster_url"), path_img),
        "meta": movie_meta_line(item),
        "year": item.get("year"),
        "quality": item.get("quality"),
        "lang": item.get("lang"),
        "episode_current": item.get("episode_current"),
    }


def remember_watch_event(movie_item: dict, selected_episode: Optional[str] = None):
    if not movie_item:
        return
    packed = {
        "slug": movie_item.get("slug"),
        "name": movie_item.get("name"),
        "thumb_url": build_image_url(movie_item.get("thumb_url") or movie_item.get("poster_url")),
        "meta": movie_meta_line(movie_item),
        "watched_at": datetime.now().strftime("%d/%m %H:%M"),
        "episode": selected_episode or "",
    }
    st.session_state.watch_history = [
        x for x in st.session_state.watch_history if x.get("slug") != packed["slug"]
    ]
    st.session_state.watch_history.insert(0, packed)
    st.session_state.watch_history = st.session_state.watch_history[:30]


def save_continue(movie: dict, episode_label: str, embed_link: str):
    st.session_state.continue_watching[movie.get("slug")] = {
        "slug": movie.get("slug"),
        "name": movie.get("name"),
        "thumb_url": build_image_url(movie.get("thumb_url") or movie.get("poster_url")),
        "episode": episode_label,
        "embed_link": embed_link,
        "updated_at": datetime.now().strftime("%d/%m %H:%M"),
        "meta": movie_meta_line(movie),
    }


def parse_episode_map(episodes: List[dict]) -> Dict[str, str]:
    out = {}
    for server in episodes or []:
        server_name = server.get("server_name", "Server")
        for ep in server.get("server_data", []):
            ep_name = normalize_text(ep.get("name") or "?")
            label = f"{server_name} • Tập {ep_name}"
            out[label] = ep.get("link_embed", "")
    return out


def sort_items(items: List[dict], mode: str) -> List[dict]:
    if mode == "A → Z":
        return sorted(items, key=lambda x: normalize_text(x.get("name")).lower())
    if mode == "Z → A":
        return sorted(items, key=lambda x: normalize_text(x.get("name")).lower(), reverse=True)
    if mode == "Điểm T-HEXA":
        return sorted(items, key=lambda x: deterministic_score(str(x.get("slug", ""))), reverse=True)
    if mode == "Mới nhất":
        return sorted(items, key=lambda x: str(x.get("year") or "0"), reverse=True)
    return items


def extract_episode_index(label: str) -> int:
    found = re.search(r"Tập\s+(\d+)", label or "")
    return int(found.group(1)) if found else -1


def next_episode_label(labels: List[str], current_label: str) -> Optional[str]:
    if current_label not in labels:
        return None
    idx = labels.index(current_label)
    return labels[idx + 1] if idx + 1 < len(labels) else None


def previous_episode_label(labels: List[str], current_label: str) -> Optional[str]:
    if current_label not in labels:
        return None
    idx = labels.index(current_label)
    return labels[idx - 1] if idx - 1 >= 0 else None


def top_keywords_from_collections() -> Tuple[List[str], List[str]]:
    slugs = []
    for item in st.session_state.favorites[:6]:
        if item.get("slug"):
            slugs.append(item["slug"])
    for item in st.session_state.watch_history[:6]:
        if item.get("slug"):
            slugs.append(item["slug"])

    cat_counter, country_counter = Counter(), Counter()
    for slug in slugs[:6]:
        detail = get_movie_detail(slug)
        movie = (detail or {}).get("movie", {})
        for cat in movie.get("category", [])[:3]:
            if cat.get("slug"):
                cat_counter[(cat.get("name", ""), cat.get("slug"))] += 1
        for country in movie.get("country", [])[:2]:
            if country.get("slug"):
                country_counter[(country.get("name", ""), country.get("slug"))] += 1

    top_categories = [slug for _, slug in [k for k, _ in cat_counter.most_common(2)]]
    top_countries = [slug for _, slug in [k for k, _ in country_counter.most_common(1)]]
    return top_categories, top_countries


def infer_time_greeting() -> Tuple[str, str]:
    hour = datetime.now().hour
    if 5 <= hour < 11:
        return "Buổi sáng điện ảnh", "Hợp với những phim nhẹ, đẹp mood và không quá nặng đầu."
    if 11 <= hour < 17:
        return "Buổi chiều thư giãn", "Ưu tiên nhịp xem dễ vào, đủ cuốn để bạn khó rời mắt."
    if 17 <= hour < 22:
        return "Giờ vàng giải trí", "Lúc này nên ưu tiên các phim có lực hút mạnh và phần nhìn đã mắt."
    return "Đêm nay xem gì", "Thời điểm hoàn hảo cho những bộ phim dính, bí ẩn hoặc rất giàu cảm xúc."


def show_notification(msg: str):
    st.session_state.notification = msg


# ============================================================
# DATA ACCESS
# ============================================================
@st.cache_data(ttl=600, show_spinner=False)
def fetch_json(url: str):
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            return response.json()
    except Exception:
        return None
    return None


@st.cache_data(ttl=600, show_spinner=False)
def get_movies(filter_type: str, slug: str = "", page: int = 1) -> Tuple[List[dict], str]:
    if filter_type == "tim-kiem":
        url = f"{API_BASE}/v1/api/tim-kiem?keyword={slug}"
    elif filter_type == "danh-sach":
        if slug == "phim-moi-cap-nhat":
            url = f"{API_BASE}/danh-sach/phim-moi-cap-nhat?page={page}"
        else:
            url = f"{API_BASE}/v1/api/danh-sach/{slug}?page={page}"
    elif filter_type == "moi-cap-nhat":
        url = f"{API_BASE}/danh-sach/phim-moi-cap-nhat?page={page}"
    else:
        url = f"{API_BASE}/v1/api/{filter_type}/{slug}?page={page}"

    data = fetch_json(url)
    items: List[dict] = []
    path_img = CDN_FALLBACK
    if data:
        if isinstance(data, dict) and "items" in data:
            items = data.get("items", []) or []
            path_img = data.get("pathImage", CDN_FALLBACK) or CDN_FALLBACK
        elif isinstance(data, dict) and "data" in data and isinstance(data["data"], dict):
            items = data["data"].get("items", []) or []
            domain = data["data"].get("APP_DOMAIN_CDN_IMAGE", "https://img.ophim1.com")
            path_img = f"{domain}/uploads/movies/"
    return items, path_img


@st.cache_data(ttl=600, show_spinner=False)
def get_movie_detail(slug: str) -> Optional[dict]:
    if not slug:
        return None
    return fetch_json(f"{API_BASE}/phim/{slug}")


@st.cache_data(ttl=600, show_spinner=False)
def get_home_row(label: str, filter_type: str, slug: str):
    return get_movies(filter_type, slug, 1)


# ============================================================
# AI
# ============================================================
def get_groq_client():
    api_key = st.secrets.get("GROQ_API_KEY", "")
    if not api_key:
        return None, None
    try:
        return Groq(api_key=api_key), "llama-3.3-70b-versatile"
    except Exception:
        return None, None


def ask_cinema_ai(chat_history: List[dict]) -> dict:
    client, model_name = get_groq_client()
    if not client:
        return {
            "action": "text",
            "reply": "🔑 AI chưa được cấu hình. Thêm `GROQ_API_KEY` vào `st.secrets` để kích hoạt trợ lý điện ảnh.",
        }

    system_prompt = """
Bạn là T-HEXA CineMind — một trợ lý điện ảnh cực kỳ tinh tế, am hiểu tâm lý người xem,
biết biến gợi ý phim thành trải nghiệm đầy cảm xúc và cá nhân hóa cao.

Luôn phản hồi bằng JSON hợp lệ, một trong hai dạng:

1) Khi người dùng muốn tìm/gợi ý phim:
{
  "action": "search",
  "keyword": "từ khóa tìm kiếm ngắn, cụ thể",
  "reply": "đoạn tư vấn hấp dẫn, giàu hình ảnh, đúng mood"
}

2) Khi chỉ trò chuyện thông thường:
{
  "action": "text",
  "reply": "câu trả lời tự nhiên, lôi cuốn"
}

Quy tắc:
- Không trả markdown ngoài JSON.
- Ưu tiên 1 phim hoặc 1 từ khóa cụ thể để dễ tìm trong kho.
- Giọng sang, giàu cảm xúc, không máy móc. Viết như một người bạn thực sự am hiểu phim.
"""

    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history[-10:]:
        if msg.get("type") == "text":
            messages.append({"role": msg["role"], "content": msg["content"]})

    try:
        completion = client.chat.completions.create(
            model=model_name, messages=messages, temperature=0.72,
        )
        text = completion.choices[0].message.content.strip()
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
    except Exception:
        pass

    return {
        "action": "text",
        "reply": "Mình đang lắng nghe. Hãy nói rõ thể loại, cảm xúc hoặc mood bạn muốn, mình sẽ chọn cho bạn một bộ phim cực chuẩn.",
    }



# ============================================================
# THEME ENGINE
# ============================================================
THEMES = {
    "dark":   {"label": "🌌 Midnight",  "bg": "#0e1117", "bg2": "#161b27", "surface": "#1a2235", "surface2": "#212d42", "border": "rgba(255,255,255,0.10)", "border2": "rgba(255,255,255,0.20)", "text": "#eef1f8", "muted": "#9aa3b8", "muted2": "#c4cad9", "btn_bg": "#1e2535", "btn_bg2": "#26304a", "input_bg": "#1a2032", "sidebar_bg": "#12161f", "popover_bg": "#141926", "card_bg": "#0d1320"},
    "cinema": {"label": "🎬 Cinema",    "bg": "#0a0a0f", "bg2": "#111118", "surface": "#18181f", "surface2": "#22222c", "border": "rgba(255,200,50,0.12)", "border2": "rgba(255,200,50,0.28)", "text": "#f5ead0", "muted": "#a09070", "muted2": "#c8b898", "btn_bg": "#1e1c14", "btn_bg2": "#2a2710", "input_bg": "#16140e", "sidebar_bg": "#0d0c0a", "popover_bg": "#111008", "card_bg": "#0d0d12"},
    "amoled": {"label": "⚫ AMOLED",    "bg": "#000000", "bg2": "#080808", "surface": "#111111", "surface2": "#1a1a1a", "border": "rgba(255,255,255,0.07)", "border2": "rgba(255,255,255,0.14)", "text": "#f0f0f0", "muted": "#666666", "muted2": "#999999", "btn_bg": "#141414", "btn_bg2": "#1e1e1e", "input_bg": "#111111", "sidebar_bg": "#050505", "popover_bg": "#0a0a0a", "card_bg": "#080808"},
}

def apply_theme():
    t = THEMES.get(st.session_state.theme, THEMES["dark"])
    txt, muted, muted2 = t["text"], t["muted"], t["muted2"]

    hero_scrim = "linear-gradient(90deg,rgba(8,12,20,0.96) 0%,rgba(8,12,20,0.74) 42%,rgba(8,12,20,0.18) 75%,rgba(8,12,20,0.45) 100%),linear-gradient(0deg,rgba(8,12,20,0.76) 0%,transparent 55%)"

    st.markdown(f"""<style>
html,body,.stApp,[data-testid="stAppViewContainer"],[data-testid="stAppViewBlockContainer"],
[data-testid="stMainBlockContainer"],[data-testid="stMain"],[data-testid="stVerticalBlock"],
section.main,div.main,.main{{background:{t["bg"]}!important;background-color:{t["bg"]}!important;color:{txt}!important;}}
div[data-testid]:not([data-testid="stSidebar"]):not([data-testid="stChatMessage"]){{background-color:transparent!important;}}
p,span,div,label,h1,h2,h3,h4{{color:{txt};}}
[class*="st-"]{{color:{txt};}}
section[data-testid="stSidebar"],section[data-testid="stSidebar"]>div{{background:{t["sidebar_bg"]}!important;background-color:{t["sidebar_bg"]}!important;}}
section[data-testid="stSidebar"] *{{color:{txt}!important;}}
section[data-testid="stSidebar"] .stButton>button{{background:{t["btn_bg"]}!important;border-color:{t["border2"]}!important;color:{txt}!important;}}
section[data-testid="stSidebar"] .stButton>button:hover{{background:{t["btn_bg2"]}!important;}}
button,.stButton>button,div[data-testid="stPopover"]>button{{background:{t["btn_bg"]}!important;border-color:{t["border2"]}!important;color:{txt}!important;}}
button:hover,.stButton>button:hover,div[data-testid="stPopover"]>button:hover{{background:{t["btn_bg2"]}!important;}}
button *,.stButton>button *,div[data-testid="stPopover"]>button *{{color:{txt}!important;}}
.stTextInput>div>div>input,.stTextInput>div>div,.stTextArea textarea,[data-baseweb="input"] input,[data-baseweb="input"],[data-baseweb="base-input"]{{background:{t["input_bg"]}!important;background-color:{t["input_bg"]}!important;color:{txt}!important;-webkit-text-fill-color:{txt}!important;border-color:{t["border2"]}!important;}}
.stSelectbox>div>div,.stMultiSelect>div>div,[data-baseweb="select"]>div,[data-baseweb="select"]{{background:{t["input_bg"]}!important;background-color:{t["input_bg"]}!important;border-color:{t["border2"]}!important;color:{txt}!important;}}
[data-baseweb="select"] *{{color:{txt}!important;}}
div[role="listbox"]{{background:{t["popover_bg"]}!important;border-color:{t["border2"]}!important;}}
div[role="option"]{{color:{txt}!important;}}
div[data-baseweb="popover"],[data-baseweb="popover"]{{background:{t["popover_bg"]}!important;border-color:{t["border2"]}!important;}}
div[data-baseweb="popover"] *,[data-baseweb="popover"] *{{color:{txt}!important;}}
div[data-baseweb="popover"] button{{background:{t["btn_bg"]}!important;color:{txt}!important;}}
.glass{{background:{t["surface"]}!important;border-color:{t["border"]}!important;}}
.glass *{{color:{txt}!important;}}
.stat{{background:{t["surface"]}!important;border-color:{t["border"]}!important;}}
.stat-label{{color:{muted}!important;}}
.sh{{color:{txt}!important;}}
.sh-sub{{color:{muted}!important;}}
.info-cell{{background:{t["surface"]}!important;border-color:{t["border"]}!important;}}
.info-label{{color:{muted}!important;}}
.info-val{{color:{txt}!important;}}
.detail-sub,.detail-desc,.mcard-meta{{color:{muted2}!important;}}
.empty{{border-color:{t["border2"]}!important;color:{muted}!important;}}
button[role="tab"]{{color:{muted2}!important;}}
button[role="tab"][aria-selected="true"]{{color:{txt}!important;}}
[data-testid="stMarkdownContainer"] p,[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] span,[data-testid="stMarkdownContainer"] div{{color:{txt}!important;}}
/* Hero scrim theme-aware */
.hero-scrim{{background:{hero_scrim}!important;}}
/* Checkbox label color */
[data-testid="stCheckbox"] label,[data-testid="stCheckbox"] span{{color:{txt}!important;}}
[data-testid="stCheckbox"] {{color:{txt}!important;}}
/* Expander */
[data-testid="stExpander"]{{background:{t["surface"]}!important;border-color:{t["border2"]}!important;}}
[data-testid="stExpander"] *{{color:{txt}!important;}}
[data-testid="stExpander"] summary{{color:{txt}!important;background:{t["surface"]}!important;}}
</style>""", unsafe_allow_html=True)


# ============================================================
# COMBO FILTER HELPERS
# ============================================================
def get_combo_results(danhmuc_slugs, theloai_slugs, quocgia_slugs, page=1):
    """Fetch and intersect results from multiple filter dimensions."""
    import itertools
    all_sets = []

    # Collect slugs from each selected dimension
    fetch_tasks = []
    if danhmuc_slugs:
        for s in danhmuc_slugs:
            fetch_tasks.append(("danh-sach", s))
    if theloai_slugs:
        for s in theloai_slugs:
            fetch_tasks.append(("the-loai", s))
    if quocgia_slugs:
        for s in quocgia_slugs:
            fetch_tasks.append(("quoc-gia", s))

    if not fetch_tasks:
        return [], CDN_FALLBACK

    # If only one dimension selected, just return that list (no intersection needed)
    if len(danhmuc_slugs) + len(theloai_slugs) + len(quocgia_slugs) == 1:
        ft, sl = fetch_tasks[0]
        return get_movies(ft, sl, page)

    # For multi-dimension: fetch all, collect slug sets per dimension type, then intersect across types
    dim_slug_sets = {}  # "danh-sach" -> set of movie slugs, etc.
    path_img = CDN_FALLBACK
    slug_to_item = {}

    for ft, sl in fetch_tasks:
        items, pimg = get_movies(ft, sl, 1)
        if pimg != CDN_FALLBACK:
            path_img = pimg
        s = set(i.get("slug") for i in items if i.get("slug"))
        for item in items:
            if item.get("slug"):
                slug_to_item[item["slug"]] = item
        if ft not in dim_slug_sets:
            dim_slug_sets[ft] = s
        else:
            dim_slug_sets[ft] = dim_slug_sets[ft] | s  # union within same type

    # Intersect across different dimension types
    sets_list = list(dim_slug_sets.values())
    if not sets_list:
        return [], path_img
    result_slugs = sets_list[0]
    for s in sets_list[1:]:
        result_slugs = result_slugs & s

    results = [slug_to_item[sl] for sl in result_slugs if sl in slug_to_item]
    # Paginate manually
    per_page = 20
    start = (page - 1) * per_page
    return results[start:start + per_page], path_img



# ============================================================
# COMPONENTS
# ============================================================
def get_logo_html() -> str:
    """Load logo.png / logo.jpg from same directory as app.py, encode as base64."""
    import base64, pathlib
    app_dir = pathlib.Path(__file__).parent
    for name in [ "logo.jpg", "logo.jpeg", "logo.webp"]:
        p = app_dir / name
        if p.exists():
            data = base64.b64encode(p.read_bytes()).decode()
            ext = name.rsplit(".", 1)[-1].replace("jpg", "jpeg")
            return f'<img src="data:image/{ext};base64,{data}" style="width:46px;height:46px;border-radius:14px;object-fit:cover;box-shadow:0 8px 24px rgba(123,111,240,0.35);flex-shrink:0;">'
    # Fallback: gradient box with T
    return '<div style="width:46px;height:46px;border-radius:14px;background:linear-gradient(135deg,#7b6ff0,#22d3ee);display:grid;place-items:center;font-family:Lexend,sans-serif;font-size:1.1rem;font-weight:800;color:#fff;flex-shrink:0;box-shadow:0 8px 24px rgba(123,111,240,0.35);">T</div>'



def render_top_bar():
    c1, c2, c3, c4 = st.columns([1.4, 3.2, 1.0, 1.2])
    with c1:
        logo_html = get_logo_html()
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:12px;padding:8px 0;">
          {logo_html}
          <div class="brand-text">
            <div class="brand-name">T-HEXA CINEMA</div>
            <div class="brand-tagline">Premium streaming experience</div>
          </div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.text_input(
            "Tìm phim",
            placeholder="🔍  Tìm tên phim, diễn viên, thể loại, tâm trạng...",
            key="search_input",
            on_change=handle_search_submit,
            label_visibility="collapsed",
        )
    with c3:
        current = st.session_state.theme
        order = ["dark", "cinema", "amoled"]
        next_theme = order[(order.index(current) + 1) % len(order)]
        label = THEMES[current]["label"]
        if st.button(label, use_container_width=True, key="topbar_theme"):
            st.session_state.theme = next_theme
            st.rerun()
    with c4:
        cc1, cc2 = st.columns(2)
        with cc1:
            if st.button("🤖 AI", use_container_width=True):
                route_to("ai"); st.rerun()
        with cc2:
            if st.button("❤️ Tủ", use_container_width=True):
                route_to("library"); st.rerun()


def render_nav_strip():
    n = st.columns([1, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1])
    with n[0]:
        if st.button("🏠 Trang chủ", use_container_width=True):
            route_to("home"); st.rerun()
    with n[1]:
        with st.popover("📂 Danh sách ", use_container_width=True):
            cols = st.columns(2)
            for i, (name, slug) in enumerate(MENU_DATA["DANH_SACH"].items()):
                if cols[i % 2].button(name, key=f"ds_{slug}", use_container_width=True):
                    set_browse("danh-sach", slug, name); st.rerun()
    with n[2]:
        with st.popover("🎭 Thể loại ", use_container_width=True):
            cols = st.columns(2)
            for i, (name, slug) in enumerate(MENU_DATA["THE_LOAI"].items()):
                if cols[i % 2].button(name, key=f"tl_{slug}", use_container_width=True):
                    set_browse("the-loai", slug, f"Thể loại: {name}"); st.rerun()
    with n[3]:
        with st.popover("🌍 Quốc gia ", use_container_width=True):
            cols = st.columns(2)
            for i, (name, slug) in enumerate(MENU_DATA["QUOC_GIA"].items()):
                if cols[i % 2].button(name, key=f"qg_{slug}", use_container_width=True):
                    set_browse("quoc-gia", slug, f"Quốc gia: {name}"); st.rerun()
    with n[4]:
        st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
        if st.button("🔀 Lọc kết hợp", use_container_width=True):
            route_to("combo"); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with n[5]:
        if st.button("🕘 Tiếp tục xem", use_container_width=True):
            route_to("library")
            st.session_state.library_tab_index = 2
            st.rerun()
    with n[6]:
        if st.button("📜 Lịch sử", use_container_width=True):
            route_to("history"); st.rerun()


def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div class="brand-logo" style="width:52px;height:52px;font-size:1.3rem;margin:0 auto 16px;border-radius:16px;">T</div>
        """, unsafe_allow_html=True)

        st.markdown("**🎬 Điều hướng**")
        nav_items = [
            ("🏠 Trang chủ", "home"),
            ("🤖 Trợ lý AI", "ai"),
            ("❤️ Tủ phim", "library"),
            ("📜 Lịch sử", "history"),
        ]
        for label, r in nav_items:
            if st.button(label, use_container_width=True, key=f"sb_{r}"):
                route_to(r); st.rerun()

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown("**⚙️ Hiển thị**")

        # Theme info (switching done via top bar button)
        current_theme = THEMES.get(st.session_state.theme, THEMES["dark"])
        st.markdown(f"""
        <div style="background:{current_theme['surface']};border:1px solid {current_theme['border2']};
             border-radius:14px;padding:10px 14px;margin-bottom:10px;
             display:flex;align-items:center;justify-content:space-between;">
          <div>
            <div style="font-size:0.78rem;color:{current_theme['muted']};margin-bottom:2px;">Giao diện hiện tại</div>
            <div style="font-size:0.92rem;font-weight:700;color:{current_theme['text']};">{current_theme['label']}</div>
          </div>
          <div style="font-size:0.72rem;color:{current_theme['muted']};text-align:right;line-height:1.5;">
            Bấm nút<br>trên đầu<br>để đổi
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='font-size:0.8rem;margin-bottom:4px;'>📋 Sắp xếp kết quả</div>", unsafe_allow_html=True)
        st.selectbox(
            "Sắp xếp",
            ["Mặc định", "A → Z", "Z → A", "Điểm T-HEXA", "Mới nhất"],
            key="sort_mode",
            label_visibility="collapsed",
        )

        greeting, note = infer_time_greeting()
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="glass glass-sm">
          <div style="font-family:var(--ff-display);font-weight:800;font-size:0.92rem;color:#fff;margin-bottom:6px;">
            🌗 {greeting}
          </div>
          <div style="font-size:0.82rem;color:var(--muted2);line-height:1.65;">{note}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown("**📊 Không gian của bạn**")
        st.markdown(f"""
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:8px;">
          <div class="stat" style="padding:12px;">
            <div style="font-size:1rem;">❤️</div>
            <div class="stat-val" style="font-size:1.2rem;">{len(st.session_state.favorites)}</div>
            <div class="stat-label">Yêu thích</div>
          </div>
          <div class="stat" style="padding:12px;">
            <div style="font-size:1rem;">⏳</div>
            <div class="stat-val" style="font-size:1.2rem;">{len(st.session_state.watch_later)}</div>
            <div class="stat-label">Xem sau</div>
          </div>
          <div class="stat" style="padding:12px;">
            <div style="font-size:1rem;">👁</div>
            <div class="stat-val" style="font-size:1.2rem;">{len(st.session_state.watch_history)}</div>
            <div class="stat-label">Đã mở</div>
          </div>
          <div class="stat" style="padding:12px;">
            <div style="font-size:1rem;">▶️</div>
            <div class="stat-val" style="font-size:1.2rem;">{len(st.session_state.continue_watching)}</div>
            <div class="stat-label">Đang dở</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown("**⚡ Mở nhanh**")
        shortcuts = [
            ("Phim bộ đang chiếu", "danh-sach", "phim-bo-dang-chieu"),
            ("Phim lẻ", "danh-sach", "phim-le"),
            ("Kinh dị", "the-loai", "kinh-di"),
            ("Âu Mỹ", "quoc-gia", "au-my"),
            ("Sắp chiếu", "danh-sach", "phim-sap-chieu"),
        ]
        for title, ft, slug in shortcuts:
            if st.button(title, use_container_width=True, key=f"sbsc_{title}"):
                set_browse(ft, slug, title); st.rerun()


def render_movie_card(item: dict, path_img: str, key_prefix: str, rank: Optional[int] = None):
    slug = item.get("slug", "")
    name = item.get("name", "Không rõ tên")
    img = build_image_url(item.get("thumb_url") or item.get("poster_url"), path_img)
    score = deterministic_score(slug)
    meta = movie_meta_line(item)
    quality = quality_badge(item)
    is_fav = is_saved("favorites", slug)
    is_later = is_saved("watch_later", slug)

    if rank:
        top_badge = f'<span class="badge badge-rank">#{rank}</span>'
    else:
        top_badge = f'<span class="badge badge-hot">HOT</span>'

    st.markdown(f"""
    <div class="mcard">
      <img src="{img}" loading="lazy">
      <div class="mcard-overlay">
        <div class="mcard-top">
          {top_badge}
          <span class="badge badge-score">⭐ {score}</span>
        </div>
        <div class="mcard-bottom">
          <div class="mcard-name">{name}</div>
          <div class="mcard-meta">{meta}</div>
          <div class="mcard-tags">
            <span class="badge badge-quality">{quality}</span>
            <span class="badge badge-default">{normalize_text(item.get('lang') or 'Vietsub')}</span>
          </div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
        if st.button("▶ Xem ngay", key=f"w_{key_prefix}_{slug}", use_container_width=True):
            route_to("watch", slug); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        label = "❤️" if is_fav else "🤍"
        if st.button(label, key=f"f_{key_prefix}_{slug}", use_container_width=True):
            packed = pack_movie(item, path_img)
            if is_fav:
                remove_from_collection("favorites", slug)
            else:
                upsert_collection("favorites", packed)
            st.rerun()
    with c3:
        label2 = "⏳" if is_later else "➕"
        if st.button(label2, key=f"l_{key_prefix}_{slug}", use_container_width=True):
            packed = pack_movie(item, path_img)
            if is_later:
                remove_from_collection("watch_later", slug)
            else:
                upsert_collection("watch_later", packed)
            st.rerun()


def render_hero(item: dict, path_img: str, detail: Optional[dict] = None):
    if not item:
        return
    image = build_image_url(item.get("poster_url") or item.get("thumb_url"), path_img)
    name = item.get("name", "T-HEXA Spotlight")
    desc = strip_html((detail or {}).get("movie", {}).get("content") or "")
    if not desc:
        desc = "Một lựa chọn spotlight: hình ảnh bắt mắt, nhịp kể cuốn và dư vị rất khó quên sau khi credits chạy xong."
    desc = desc[:380] + ("…" if len(desc) > 380 else "")

    badges_data = [
        ("pill-primary", "🔥 Spotlight"),
        ("pill-glass", normalize_text(item.get("quality") or "HD")),
        ("pill-glass", normalize_text(item.get("lang") or "Vietsub")),
        ("pill-gold", f"⭐ {deterministic_score(item.get('slug', ''))}"),
    ]
    if item.get("year"):
        badges_data.append(("pill-glass", str(item.get("year"))))

    pills_html = "".join(f'<span class="pill {cls}">{txt}</span>' for cls, txt in badges_data)
    reason = score_reason(item.get("slug", ""))

    st.markdown(f"""
    <div class="hero-wrap">
      <img class="hero-bg" src="{image}">
      <div class="hero-scrim"></div>
      <div class="hero-inner">
        <div class="hero-pills">{pills_html}</div>
        <div class="hero-title">{name}</div>
        <div class="hero-desc">{desc}</div>
        <div class="hero-score">📌 Được đẩy lên spotlight vì {reason}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns([1.3, 1.2, 1, 1])
    with c1:
        st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
        if st.button("▶ Xem ngay", key=f"hero_w_{item.get('slug')}", use_container_width=True):
            route_to("watch", item.get("slug")); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        is_fav = is_saved("favorites", item.get("slug"))
        if st.button("💔 Bỏ thích" if is_fav else "❤️ Yêu thích", key="hero_fav", use_container_width=True):
            packed = pack_movie(item, path_img)
            if is_fav:
                remove_from_collection("favorites", item.get("slug"))
            else:
                upsert_collection("favorites", packed)
            st.rerun()
    with c3:
        if st.button("🎲 Đổi", use_container_width=True):
            st.session_state.hero_seed = random.randint(1, 99999); st.rerun()
    with c4:
        if st.button("🤖 Hỏi AI", use_container_width=True):
            route_to("ai")
            st.session_state.chat_history.append({
                "role": "user", "type": "text",
                "content": f"Kể mình nghe vì sao phim {name} đáng xem và hợp với kiểu khán giả nào",
            })
            st.rerun()


def render_collection_grid(title: str, items: List[dict], key_prefix: str, empty_text: str):
    st.markdown(f'<div class="sh">{title} <span class="sh-line"></span></div>', unsafe_allow_html=True)
    if not items:
        st.markdown(f"""
        <div class="empty">
          <div class="empty-icon">🎬</div>
          {empty_text}
        </div>
        """, unsafe_allow_html=True)
        return
    cols = st.columns(5)
    for i, item in enumerate(items):
        with cols[i % 5]:
            render_movie_card(item, "", f"{key_prefix}_{i}")


# ============================================================
# VIEWS
# ============================================================
def view_home():
    hero_items, hero_path = get_movies("moi-cap-nhat", "", 1)

    if hero_items:
        rnd = random.Random(st.session_state.hero_seed)
        featured = rnd.choice(hero_items[: min(12, len(hero_items))])
        featured_detail = get_movie_detail(featured.get("slug"))
        render_hero(featured, hero_path, featured_detail)

    # Mood shortcuts
    greeting, note = infer_time_greeting()
    st.markdown(f'<div class="sh">✨ Chọn mood xem tối nay <span class="sh-line"></span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sh-sub">{greeting} — {note}</div>', unsafe_allow_html=True)

    mood_cols = st.columns(6)
    for i, (label, ft, slug, title) in enumerate(MOOD_SHORTCUTS):
        with mood_cols[i]:
            if st.button(label, key=f"mood_{i}", use_container_width=True):
                st.session_state.landing_mood = title
                set_browse(ft, slug, title); st.rerun()

    # Stats — pure HTML, no st.columns to avoid white gap
    st.markdown(f"""
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:20px 0;">
      <div class="stat">
        <div style="font-size:1.4rem;">🎬</div>
        <div class="stat-val">{len(hero_items)}</div>
        <div class="stat-label">Phim đang lên sóng</div>
      </div>
      <div class="stat">
        <div style="font-size:1.4rem;">❤️</div>
        <div class="stat-val">{len(st.session_state.favorites)}</div>
        <div class="stat-label">Phim yêu thích</div>
      </div>
      <div class="stat">
        <div style="font-size:1.4rem;">⏳</div>
        <div class="stat-val">{len(st.session_state.watch_later)}</div>
        <div class="stat-label">Xem sau</div>
      </div>
      <div class="stat">
        <div style="font-size:1.4rem;">▶️</div>
        <div class="stat-val">{len(st.session_state.continue_watching)}</div>
        <div class="stat-label">Đang xem dở</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Personalized rows
    top_categories, top_countries = top_keywords_from_collections()
    personalized_rows = []
    if top_categories:
        personalized_rows.append(("✨ Dành riêng cho bạn", "the-loai", top_categories[0]))
    if len(top_categories) > 1:
        personalized_rows.append(("🎯 Gu của bạn đang nghiêng về", "the-loai", top_categories[1]))
    if top_countries:
        personalized_rows.append(("🌍 Khu vực bạn sẽ thích", "quoc-gia", top_countries[0]))

    if personalized_rows:
        st.markdown('<div class="sh">🎯 Cá nhân hóa cho bạn <span class="sh-line"></span></div>', unsafe_allow_html=True)
        st.markdown('<div class="sh-sub">Dựa trên lịch sử xem và danh sách yêu thích của bạn.</div>', unsafe_allow_html=True)
        for row_idx, (label, filter_type, slug) in enumerate(personalized_rows[:3]):
            items, path_img = get_movies(filter_type, slug, 1)
            items = sort_items(items[:5], st.session_state.sort_mode)
            if items:
                st.markdown(f'<div class="sh">{label} <span class="sh-line"></span></div>', unsafe_allow_html=True)
                cols = st.columns(5)
                for i, item in enumerate(items[:5]):
                    with cols[i]:
                        render_movie_card(item, path_img, f"personal_{row_idx}_{i}")

    # Top 10
    st.markdown('<div class="sh">🏆 Top 10 T-HEXA hôm nay <span class="sh-line"></span></div>', unsafe_allow_html=True)
    top10 = sort_items(hero_items[:10], "Điểm T-HEXA") if hero_items else []
    if top10:
        cols = st.columns(5)
        for i, item in enumerate(top10):
            with cols[i % 5]:
                render_movie_card(item, hero_path, f"top10_{i}", rank=i + 1)

    # Watch later strip
    if st.session_state.watch_later:
        st.markdown('<div class="sh">⏳ Chờ bạn bấm xem <span class="sh-line"></span></div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="banner" style="margin-bottom:16px;">
          <div class="banner-title">Danh sách xem sau — {len(st.session_state.watch_later)} phim</div>
          <div class="banner-sub">Những lựa chọn bạn từng thấy hấp dẫn nhưng chưa bấm vào. Bây giờ là lúc chọn một bộ và bắt đầu.</div>
        </div>
        """, unsafe_allow_html=True)
        cols = st.columns(5)
        for i, item in enumerate(st.session_state.watch_later[:5]):
            with cols[i]:
                render_movie_card(item, "", f"later_home_{i}")

    # Continue watching strip
    if st.session_state.continue_watching:
        st.markdown('<div class="sh">▶️ Tiếp tục xem <span class="sh-line"></span></div>', unsafe_allow_html=True)
        continue_items = list(st.session_state.continue_watching.values())[:5]
        cols = st.columns(5)
        for i, item in enumerate(continue_items):
            with cols[i]:
                st.markdown(f"""
                <div class="cont-card">
                  <img src="{item.get('thumb_url')}" loading="lazy">
                  <div class="cont-overlay">
                    <div>
                      <span class="badge badge-default">🕘 {item.get('updated_at')}</span>
                    </div>
                    <div>
                      <div class="mcard-name">{item.get('name')}</div>
                      <div class="mcard-meta">{item.get('episode')}</div>
                      <div class="ep-progress"><div class="ep-progress-fill" style="width:45%;"></div></div>
                    </div>
                  </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("▶ Tiếp tục", key=f"cont_home_{i}", use_container_width=True):
                    route_to("watch", item.get("slug")); st.rerun()

    # Home rows
    for row_idx, (label, filter_type, slug) in enumerate(HOME_ROWS):
        st.markdown(f'<div class="sh">{label} <span class="sh-line"></span></div>', unsafe_allow_html=True)
        items, path_img = get_home_row(label, filter_type, slug)
        items = sort_items(items[:10], st.session_state.sort_mode)
        if items:
            cols = st.columns(5)
            for i, item in enumerate(items[:10]):
                with cols[i % 5]:
                    render_movie_card(item, path_img, f"home_{row_idx}_{i}")
        else:
            st.markdown('<div class="empty"><div class="empty-icon">📭</div>Kệ phim này đang tạm vắng.</div>', unsafe_allow_html=True)


def view_browse():
    hcols = st.columns([3, 1, 1])
    with hcols[0]:
        st.markdown(f'<div class="sh">{st.session_state.browse_title} <span class="sh-line"></span></div>', unsafe_allow_html=True)
    with hcols[1]:
        st.caption(f"Trang {st.session_state.browse_page} · {st.session_state.sort_mode}")
    with hcols[2]:
        if st.button("🏠 Về trang chủ", use_container_width=True):
            route_to("home"); st.rerun()

    if st.session_state.landing_mood:
        st.markdown(f'<div class="sh-sub">{st.session_state.landing_mood}</div>', unsafe_allow_html=True)

    items, path_img = get_movies(
        st.session_state.browse_type,
        st.session_state.browse_slug,
        st.session_state.browse_page,
    )
    items = sort_items(items, st.session_state.sort_mode)

    if not items:
        st.markdown('<div class="empty"><div class="empty-icon">🔍</div>Không tìm thấy nội dung phù hợp.</div>', unsafe_allow_html=True)
        return

    cols = st.columns(5)
    for i, item in enumerate(items):
        with cols[i % 5]:
            render_movie_card(item, path_img, f"browse_{st.session_state.browse_page}_{i}")

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    nav = st.columns([1.2, 3, 1.2])
    with nav[0]:
        if st.session_state.browse_page > 1:
            if st.button("⬅ Trang trước", use_container_width=True):
                st.session_state.browse_page -= 1; st.rerun()
    with nav[1]:
        st.markdown(f"""
        <div class="glass" style="text-align:center;">
          <div style="font-family:var(--ff-display);font-weight:800;font-size:1.1rem;">Trang {st.session_state.browse_page}</div>
          <div style="font-size:0.82rem;color:var(--muted);margin-top:4px;">Tiếp tục lướt để khám phá thêm</div>
        </div>
        """, unsafe_allow_html=True)
    with nav[2]:
        if st.button("Trang sau ➡", use_container_width=True):
            st.session_state.browse_page += 1; st.rerun()


def view_watch():
    slug = st.session_state.current_movie_slug
    data = get_movie_detail(slug)

    top = st.columns([1, 4, 1, 1])
    with top[0]:
        if st.button("⬅ Quay lại", use_container_width=True):
            prev = st.session_state.prev_route or "home"
            route_to(prev); st.rerun()
    with top[2]:
        if st.button("🤖 Hỏi AI", use_container_width=True):
            route_to("ai")
            st.session_state.chat_history.append({
                "role": "user", "type": "text",
                "content": f"Kể mình nghe vì sao phim slug={slug} đáng xem",
            })
            st.rerun()
    with top[3]:
        if st.button("📚 Tủ phim", use_container_width=True):
            route_to("library"); st.rerun()

    if not data or not data.get("status"):
        st.error("Không tải được chi tiết phim. Vui lòng thử lại.")
        return

    mv = data.get("movie", {})
    episodes = data.get("episodes", [])
    ep_map = parse_episode_map(episodes)

    left, right = st.columns([1.0, 2.2], gap="large")

    with left:
        st.markdown('<div class="poster-wrap">', unsafe_allow_html=True)
        st.image(mv.get("thumb_url") or mv.get("poster_url"), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        a1, a2 = st.columns(2)
        with a1:
            fav = is_saved("favorites", mv.get("slug"))
            if st.button("💔 Bỏ thích" if fav else "❤️ Yêu thích", use_container_width=True):
                packed = pack_movie(mv, "")
                if fav:
                    remove_from_collection("favorites", mv.get("slug"))
                else:
                    upsert_collection("favorites", packed)
                st.rerun()
        with a2:
            later = is_saved("watch_later", mv.get("slug"))
            if st.button("🗑 Bỏ sau" if later else "⏳ Xem sau", use_container_width=True):
                packed = pack_movie(mv, "")
                if later:
                    remove_from_collection("watch_later", mv.get("slug"))
                else:
                    upsert_collection("watch_later", packed)
                st.rerun()

        countries = ", ".join([c.get("name", "") for c in mv.get("country", []) if c.get("name")]) or "—"
        cats = ", ".join([c.get("name", "") for c in mv.get("category", []) if c.get("name")]) or "—"
        st.markdown(f"""
        <div class="info-grid">
          <div class="info-cell"><div class="info-label">Chất lượng</div><div class="info-val">{normalize_text(mv.get('quality') or 'HD')}</div></div>
          <div class="info-cell"><div class="info-label">Ngôn ngữ</div><div class="info-val">{normalize_text(mv.get('lang') or 'Vietsub')}</div></div>
          <div class="info-cell"><div class="info-label">Năm phát hành</div><div class="info-val">{normalize_text(mv.get('year') or '—')}</div></div>
          <div class="info-cell"><div class="info-label">Thời lượng</div><div class="info-val">{normalize_text(mv.get('time') or '—')}</div></div>
          <div class="info-cell"><div class="info-label">Quốc gia</div><div class="info-val">{countries}</div></div>
          <div class="info-cell"><div class="info-label">Thể loại</div><div class="info-val">{cats}</div></div>
        </div>
        """, unsafe_allow_html=True)

        score = deterministic_score(mv.get("slug", ""))
        st.markdown(f"""
        <div class="glass" style="margin-top:16px;">
          <div style="font-family:var(--ff-display);font-weight:800;font-size:0.9rem;margin-bottom:6px;">💡 Vibe của phim này</div>
          <div style="font-size:0.82rem;color:var(--muted2);line-height:1.65;">
            Điểm T-HEXA <strong style="color:var(--gold);">{score}</strong> — {score_reason(mv.get('slug',''))}.
            Phù hợp để xem liền mạch.
          </div>
        </div>
        """, unsafe_allow_html=True)

    with right:
        title = mv.get("name", "Không rõ tên phim")
        origin = normalize_text(mv.get("origin_name"))
        score = deterministic_score(mv.get("slug", ""))
        sub_parts = [x for x in [origin, normalize_text(mv.get("episode_current")), normalize_text(mv.get("status"))] if x]

        st.markdown(f'<div class="detail-title">{title}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="detail-sub">{" · ".join(sub_parts)} · ⭐ {score}</div>', unsafe_allow_html=True)

        # Tags
        tags = []
        for cat in mv.get("category", [])[:4]:
            if cat.get("name"):
                tags.append(cat["name"])
        for country in mv.get("country", [])[:3]:
            if country.get("name"):
                tags.append(country["name"])
        if tags:
            st.markdown(
                '<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px;">'
                + "".join(f'<span class="pill pill-glass">{t}</span>' for t in tags)
                + "</div>",
                unsafe_allow_html=True,
            )

        desc = strip_html(mv.get("content", "Nội dung đang được cập nhật."))
        st.markdown(f'<div class="detail-desc">{desc}</div>', unsafe_allow_html=True)
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        if ep_map:
            labels = list(ep_map.keys())
            default_label = st.session_state.selected_episode_map.get(mv.get("slug"), labels[0])
            if default_label not in labels:
                default_label = labels[0]

            selected = st.selectbox(
                "Chọn tập phát",
                labels,
                index=labels.index(default_label),
                key=f"ep_select_{mv.get('slug')}",
            )
            st.session_state.selected_episode_map[mv.get("slug")] = selected
            embed_link = ep_map[selected]
            remember_watch_event(mv, selected)
            save_continue(mv, selected, embed_link)

            st.markdown(f"""
            <div class="player">
              <iframe src="{embed_link}" allowfullscreen allow="autoplay; fullscreen"></iframe>
            </div>
            """, unsafe_allow_html=True)
            st.caption(f"▶ Đang phát: {selected}")

            prev_label = previous_episode_label(labels, selected)
            next_label = next_episode_label(labels, selected)
            ep_idx = extract_episode_index(selected)

            ep_nav = st.columns([1.2, 1.2, 2.4])
            with ep_nav[0]:
                if prev_label:
                    if st.button("⏮ Tập trước", use_container_width=True):
                        st.session_state.selected_episode_map[mv.get("slug")] = prev_label; st.rerun()
            with ep_nav[1]:
                if next_label:
                    st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
                    if st.button("⏭ Tập tiếp", use_container_width=True):
                        st.session_state.selected_episode_map[mv.get("slug")] = next_label; st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
            with ep_nav[2]:
                ep_display = ep_idx if ep_idx > 0 else "•"
                total = normalize_text(mv.get("episode_total") or str(len(labels)))
                st.markdown(f"""
                <div class="glass" style="display:flex;align-items:center;justify-content:space-between;gap:12px;">
                  <div>
                    <div style="font-family:var(--ff-display);font-weight:800;font-size:0.9rem;">Tiến độ</div>
                    <div style="font-size:0.8rem;color:var(--muted2);margin-top:2px;">Tập {ep_display} / {total}</div>
                  </div>
                  <div class="pill pill-primary" style="font-size:1rem;padding:8px 14px;">{ep_display}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("⚠️ Phim này hiện chưa có link xem.")

        detail_tabs = st.tabs(["👥 Đoàn phim", "📊 Phân tích", "💡 Gợi ý nhanh"])
        with detail_tabs[0]:
            for label, key in [("Đạo diễn", "director"), ("Diễn viên", "actor"), ("Trạng thái", "status"), ("Tổng số tập", "episode_total"), ("Tập hiện tại", "episode_current")]:
                val = normalize_text(mv.get(key) or "—")
                st.markdown(f"""
                <div class="info-cell" style="margin-bottom:8px;">
                  <div class="info-label">{label}</div>
                  <div class="info-val">{val}</div>
                </div>
                """, unsafe_allow_html=True)

        with detail_tabs[1]:
            sc = deterministic_score(mv.get("slug", ""))
            st.markdown(f"""
            <div class="glass">
              <div style="font-family:var(--ff-display);font-weight:800;font-size:0.95rem;margin-bottom:10px;">Phân tích T-HEXA</div>
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
                <span style="color:var(--muted2);font-size:0.88rem;">Điểm tổng thể</span>
                <span class="pill pill-gold">⭐ {sc} / 10</span>
              </div>
              <div style="font-size:0.85rem;color:var(--muted2);line-height:1.7;">
                Phim này {score_reason(mv.get('slug',''))}. Dựa trên các yếu tố về thể loại, nhịp phim và tính giải trí,
                đây là lựa chọn <strong style="color:var(--text);">{'phù hợp cao' if sc >= 8.8 else 'phù hợp tốt'}</strong>
                cho buổi xem {'tập trung' if sc >= 8.8 else 'thư giãn'} hôm nay.
              </div>
            </div>
            """, unsafe_allow_html=True)

        with detail_tabs[2]:
            p1, p2, p3 = st.columns(3)
            with p1:
                if st.button("🎭 Cùng thể loại", use_container_width=True):
                    if mv.get("category"):
                        set_browse("the-loai", mv["category"][0].get("slug", ""), f"Cùng thể loại · {title}"); st.rerun()
            with p2:
                if st.button("🌍 Cùng quốc gia", use_container_width=True):
                    if mv.get("country"):
                        set_browse("quoc-gia", mv["country"][0].get("slug", ""), f"Cùng quốc gia · {title}"); st.rerun()
            with p3:
                if st.button("⏳ Xem tối nay", use_container_width=True):
                    upsert_collection("watch_later", pack_movie(mv, "")); st.rerun()

    # Related
    st.markdown('<div class="sh">🎬 Bạn có thể cũng sẽ mê <span class="sh-line"></span></div>', unsafe_allow_html=True)
    related_done = False
    if mv.get("category"):
        related_items, related_path = get_movies("the-loai", mv["category"][0].get("slug", ""), 1)
        related_items = [x for x in related_items if x.get("slug") != mv.get("slug")][:10]
        if related_items:
            related_done = True
            cols = st.columns(5)
            for i, item in enumerate(related_items):
                with cols[i % 5]:
                    render_movie_card(item, related_path, f"rel_{i}")
    if not related_done and mv.get("country"):
        related_items, related_path = get_movies("quoc-gia", mv["country"][0].get("slug", ""), 1)
        related_items = [x for x in related_items if x.get("slug") != mv.get("slug")][:10]
        if related_items:
            cols = st.columns(5)
            for i, item in enumerate(related_items):
                with cols[i % 5]:
                    render_movie_card(item, related_path, f"relc_{i}")


def view_ai():
    st.markdown('<div class="sh">🤖 T-HEXA CineMind <span class="sh-line"></span></div>', unsafe_allow_html=True)
    st.markdown('<div class="sh-sub">Gợi ý phim theo tâm trạng, kể nội dung cuốn, chọn phim đúng gu và tìm ngay trong kho.</div>', unsafe_allow_html=True)

    if not st.session_state.chat_history:
        st.session_state.chat_history = [{
            "role": "assistant", "type": "text",
            "content": "Chào bạn! Mình là **T-HEXA CineMind** ✨\n\nHãy thử hỏi mình:\n- *Mình muốn phim tình cảm buồn nhưng sang*\n- *Gợi ý phim kinh dị ít jumpscare*\n- *Kể mình nghe nội dung một phim thật bánh cuốn*",
        }]

    quick_cols = st.columns(4)
    quick_prompts = [
        ("🎭 Tình cảm sâu", "Gợi ý phim tình cảm đẹp, buồn, tinh tế và dễ nghiện"),
        ("👻 Kinh dị ám ảnh", "Gợi ý phim kinh dị ám ảnh nhưng không lạm dụng jumpscare"),
        ("😂 Giải trí cực đã", "Mình cần phim vui, cuốn, xem thư giãn cuối ngày"),
        ("🚀 Viễn tưởng đỉnh", "Phim viễn tưởng thật đã phần nhìn và có ý tưởng lớn"),
    ]
    for col, (label, prompt) in zip(quick_cols, quick_prompts):
        with col:
            if st.button(label, use_container_width=True):
                st.session_state.chat_history.append({"role": "user", "type": "text", "content": prompt})
                st.rerun()

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    for idx, message in enumerate(st.session_state.chat_history):
        with st.chat_message(message["role"]):
            if message.get("type") == "text":
                st.markdown(message["content"])
            elif message.get("type") == "movie_list":
                st.markdown(message["content"])
                cols = st.columns(4)
                for i, item in enumerate(message.get("data", [])[:4]):
                    with cols[i]:
                        render_movie_card(item, message.get("path_img", CDN_FALLBACK), f"chat_{idx}_{i}")

    if prompt := st.chat_input("Hỏi bất cứ điều gì về phim..."):
        st.session_state.chat_history.append({"role": "user", "type": "text", "content": prompt})
        st.rerun()

    if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "user":
        with st.spinner("CineMind đang suy nghĩ..."):
            payload = ask_cinema_ai(st.session_state.chat_history)

        if payload.get("action") == "search":
            keyword = normalize_text(payload.get("keyword"))
            reply = payload.get("reply", "Mình đã chọn được một gợi ý hợp gu cho bạn.")
            items, path_img = get_movies("tim-kiem", keyword, 1)
            if items:
                st.session_state.chat_history.append({
                    "role": "assistant", "type": "movie_list",
                    "content": reply, "data": items, "path_img": path_img,
                })
            else:
                st.session_state.chat_history.append({
                    "role": "assistant", "type": "text",
                    "content": reply + "\n\n*Mình chưa tìm thấy đúng tên trong kho, nhưng mood này rất hợp với mô tả của bạn.*",
                })
        else:
            st.session_state.chat_history.append({
                "role": "assistant", "type": "text",
                "content": payload.get("reply", "Mình đang ở đây để giúp bạn chọn một bộ phim thật xứng đáng."),
            })
        st.rerun()

    # Clear chat
    if st.session_state.chat_history and len(st.session_state.chat_history) > 1:
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        if st.button("🗑 Xóa cuộc trò chuyện", use_container_width=False):
            st.session_state.chat_history = []
            st.rerun()


def view_library():
    st.markdown('<div class="sh">❤️ Tủ phim cá nhân <span class="sh-line"></span></div>', unsafe_allow_html=True)

    continue_items = list(st.session_state.continue_watching.values())
    banners = st.columns(3)
    banner_data = [
        (len(st.session_state.favorites), "Phim yêu thích", "❤️", "Các lựa chọn bạn đã quyết định giữ lại."),
        (len(st.session_state.watch_later), "Phim xem sau", "⏳", "Watchlist thực thụ cho những buổi xem kế tiếp."),
        (len(continue_items), "Phim đang dở", "▶️", "Hệ thống ghi nhớ tập để quay lại đúng điểm dừng."),
    ]
    for col, (val, title, icon, sub) in zip(banners, banner_data):
        with col:
            st.markdown(f"""
            <div class="banner">
              <div style="font-size:1.8rem;margin-bottom:8px;">{icon}</div>
              <div class="banner-title">{val} {title}</div>
              <div class="banner-sub">{sub}</div>
            </div>
            """, unsafe_allow_html=True)

    tabs = st.tabs(["❤️ Yêu thích", "⏳ Xem sau", "▶️ Tiếp tục xem"])

    with tabs[0]:
        render_collection_grid(
            "Phim bạn đã chọn giữ lại",
            st.session_state.favorites,
            "lib_fav",
            "Bạn chưa có phim nào trong danh sách yêu thích.",
        )

    with tabs[1]:
        render_collection_grid(
            "Kệ phim chờ bạn bấm xem",
            st.session_state.watch_later,
            "lib_later",
            "Danh sách xem sau hiện đang trống.",
        )

    with tabs[2]:
        st.markdown('<div class="sh">Tiếp tục nơi bạn dừng lại <span class="sh-line"></span></div>', unsafe_allow_html=True)
        if not continue_items:
            st.markdown('<div class="empty"><div class="empty-icon">🎬</div>Chưa có phim nào trong mục tiếp tục xem.</div>', unsafe_allow_html=True)
        else:
            cols = st.columns(4)
            for i, item in enumerate(continue_items):
                with cols[i % 4]:
                    st.markdown(f"""
                    <div class="cont-card">
                      <img src="{item.get('thumb_url')}" loading="lazy">
                      <div class="cont-overlay">
                        <div>
                          <span class="badge badge-default">🕘 {item.get('updated_at')}</span>
                        </div>
                        <div>
                          <div class="mcard-name">{item.get('name')}</div>
                          <div class="mcard-meta">{item.get('episode')}</div>
                          <div class="ep-progress">
                            <div class="ep-progress-fill" style="width:50%;"></div>
                          </div>
                        </div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("▶ Mở lại", key=f"cont_{i}", use_container_width=True):
                        route_to("watch", item.get("slug")); st.rerun()


def view_history():
    st.markdown('<div class="sh">📜 Lịch sử mở phim <span class="sh-line"></span></div>', unsafe_allow_html=True)
    items = st.session_state.watch_history

    if not items:
        st.markdown('<div class="empty"><div class="empty-icon">🕐</div>Bạn chưa mở phim nào gần đây.</div>', unsafe_allow_html=True)
        return

    hcols = st.columns([4, 1])
    with hcols[0]:
        st.markdown('<div class="sh-sub">Lịch sử xem của bạn góp phần tạo lane cá nhân hóa trên trang chủ.</div>', unsafe_allow_html=True)
    with hcols[1]:
        if st.button("🗑 Xóa lịch sử", use_container_width=True):
            st.session_state.watch_history = []
            st.rerun()

    cols = st.columns(5)
    for i, item in enumerate(items):
        with cols[i % 5]:
            st.markdown(f"""
            <div class="mcard">
              <img src="{item.get('thumb_url')}" loading="lazy">
              <div class="mcard-overlay">
                <div class="mcard-top">
                  <span class="badge badge-default">🕒 {item.get('watched_at')}</span>
                  <span class="badge badge-default">{item.get('episode') or '—'}</span>
                </div>
                <div class="mcard-bottom">
                  <div class="mcard-name">{item.get('name')}</div>
                  <div class="mcard-meta">{item.get('meta')}</div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("▶ Xem lại", key=f"hist_{i}", use_container_width=True):
                route_to("watch", item.get("slug")); st.rerun()


def view_combo():
    t = THEMES.get(st.session_state.theme, THEMES["dark"])
    txt = t["text"]; surface = t["surface"]; border2 = t["border2"]
    muted = t["muted"]; muted2 = t["muted2"]

    st.markdown('<div class="sh">🔀 Lọc kết hợp <span class="sh-line"></span></div>', unsafe_allow_html=True)
    st.markdown('<div class="sh-sub">Chọn đồng thời nhiều danh mục, thể loại và quốc gia để tìm phim thật đúng gu.</div>', unsafe_allow_html=True)

    # ── Filter panels ─────────────────────────────────
    with st.expander("📂 Danh mục phim", expanded=True):
        st.markdown(f"<div style='font-size:0.8rem;color:{muted};margin-bottom:8px;'>Chọn một hoặc nhiều danh mục</div>", unsafe_allow_html=True)
        dm_names = list(MENU_DATA["DANH_SACH"].keys())
        dm_slugs = list(MENU_DATA["DANH_SACH"].values())
        dm_cols = st.columns(4)
        for i, (name, slug) in enumerate(zip(dm_names, dm_slugs)):
            with dm_cols[i % 4]:
                selected = slug in st.session_state.combo_danhmuc
                if st.checkbox(name, value=selected, key=f"cdm_{slug}"):
                    if slug not in st.session_state.combo_danhmuc:
                        st.session_state.combo_danhmuc.append(slug)
                else:
                    st.session_state.combo_danhmuc = [s for s in st.session_state.combo_danhmuc if s != slug]

    with st.expander("🎭 Thể loại", expanded=True):
        st.markdown(f"<div style='font-size:0.8rem;color:{muted};margin-bottom:8px;'>Chọn một hoặc nhiều thể loại</div>", unsafe_allow_html=True)
        tl_cols = st.columns(4)
        for i, (name, slug) in enumerate(MENU_DATA["THE_LOAI"].items()):
            with tl_cols[i % 4]:
                selected = slug in st.session_state.combo_theloai
                if st.checkbox(name, value=selected, key=f"ctl_{slug}"):
                    if slug not in st.session_state.combo_theloai:
                        st.session_state.combo_theloai.append(slug)
                else:
                    st.session_state.combo_theloai = [s for s in st.session_state.combo_theloai if s != slug]

    with st.expander("🌍 Quốc gia", expanded=True):
        st.markdown(f"<div style='font-size:0.8rem;color:{muted};margin-bottom:8px;'>Chọn một hoặc nhiều quốc gia</div>", unsafe_allow_html=True)
        qg_cols = st.columns(4)
        for i, (name, slug) in enumerate(MENU_DATA["QUOC_GIA"].items()):
            with qg_cols[i % 4]:
                selected = slug in st.session_state.combo_quocgia
                if st.checkbox(name, value=selected, key=f"cqg_{slug}"):
                    if slug not in st.session_state.combo_quocgia:
                        st.session_state.combo_quocgia.append(slug)
                else:
                    st.session_state.combo_quocgia = [s for s in st.session_state.combo_quocgia if s != slug]

    # ── Active filter summary ──────────────────────────
    active_labels = []
    for s in st.session_state.combo_danhmuc:
        for k, v in MENU_DATA["DANH_SACH"].items():
            if v == s: active_labels.append(f"📂 {k}")
    for s in st.session_state.combo_theloai:
        for k, v in MENU_DATA["THE_LOAI"].items():
            if v == s: active_labels.append(f"🎭 {k}")
    for s in st.session_state.combo_quocgia:
        for k, v in MENU_DATA["QUOC_GIA"].items():
            if v == s: active_labels.append(f"🌍 {k}")

    if active_labels:
        pills_html = "".join(f'<span class="pill pill-primary" style="font-size:0.75rem;">{l}</span>' for l in active_labels)
        st.markdown(f"""
        <div style="margin:14px 0 8px;display:flex;flex-wrap:wrap;gap:8px;align-items:center;">
          <span style="font-size:0.82rem;color:{muted};font-weight:600;">Đang lọc:</span>
          {pills_html}
        </div>
        """, unsafe_allow_html=True)

    # ── Action buttons ────────────────────────────────
    ac1, ac2 = st.columns([1.5, 4])
    with ac1:
        st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
        search_clicked = st.button("🔍 Tìm phim", use_container_width=True, key="combo_search")
        st.markdown('</div>', unsafe_allow_html=True)
    with ac2:
        total_sel = len(active_labels)
        if total_sel == 0:
            st.markdown(f"<div style='padding:10px;font-size:0.85rem;color:{muted};'>⬅ Chọn ít nhất một tiêu chí để tìm kiếm</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='padding:10px;font-size:0.85rem;color:{muted2};'>✅ Đã chọn <strong style='color:{txt};'>{total_sel}</strong> tiêu chí lọc</div>", unsafe_allow_html=True)

    # ── Results ───────────────────────────────────────
    has_any = st.session_state.combo_danhmuc or st.session_state.combo_theloai or st.session_state.combo_quocgia

    if search_clicked or (has_any and st.session_state.get("combo_searched")):
        if search_clicked:
            st.session_state.combo_page = 1
            st.session_state.combo_searched = True

        if not has_any:
            st.markdown('<div class="empty"><div class="empty-icon">🎯</div>Vui lòng chọn ít nhất một tiêu chí lọc.</div>', unsafe_allow_html=True)
            return

        with st.spinner("Đang tìm phim phù hợp..."):
            items, path_img = get_combo_results(
                st.session_state.combo_danhmuc,
                st.session_state.combo_theloai,
                st.session_state.combo_quocgia,
                st.session_state.combo_page,
            )

        items = sort_items(items, st.session_state.sort_mode)

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # Result header
        result_note = "Kết quả giao nhau giữa các bộ lọc" if len(active_labels) > 1 else "Kết quả bộ lọc"
        st.markdown(f'<div class="sh">🎯 {result_note} <span class="sh-line"></span></div>', unsafe_allow_html=True)

        if not items:
            st.markdown(f"""
            <div class="empty">
              <div class="empty-icon">🔍</div>
              Không tìm thấy phim nào khớp với tất cả bộ lọc đã chọn.<br>
              <span style="font-size:0.82rem;color:{muted};">Thử bỏ bớt một số tiêu chí để mở rộng kết quả.</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='sh-sub'>Tìm thấy {len(items)} phim · Trang {st.session_state.combo_page}</div>", unsafe_allow_html=True)
            cols = st.columns(5)
            for i, item in enumerate(items):
                with cols[i % 5]:
                    render_movie_card(item, path_img, f"combo_{i}")

            # Pagination
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            pn1, pn2, pn3 = st.columns([1.2, 3, 1.2])
            with pn1:
                if st.session_state.combo_page > 1:
                    if st.button("⬅ Trang trước", use_container_width=True, key="combo_prev"):
                        st.session_state.combo_page -= 1; st.rerun()
            with pn2:
                st.markdown(f"""
                <div class="glass" style="text-align:center;">
                  <div style="font-family:var(--ff-display);font-weight:800;font-size:1rem;">Trang {st.session_state.combo_page}</div>
                </div>
                """, unsafe_allow_html=True)
            with pn3:
                if len(items) >= 20:
                    if st.button("Trang sau ➡", use_container_width=True, key="combo_next"):
                        st.session_state.combo_page += 1; st.rerun()
    elif not has_any:
        st.markdown(f"""
        <div class="empty" style="margin-top:24px;">
          <div class="empty-icon">🎛️</div>
          Chọn các tiêu chí bên trên rồi bấm <strong>Tìm phim</strong> để khám phá.<br>
          <span style="font-size:0.82rem;color:{muted};margin-top:8px;display:block;">
            Ví dụ: Hàn Quốc + Tình cảm + Phim bộ = series tình cảm Hàn đang chiếu
          </span>
        </div>
        """, unsafe_allow_html=True)


# ============================================================
# MAIN
# ============================================================
render_sidebar()
apply_theme()
render_top_bar()
render_nav_strip()
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

route = st.session_state.route
if route == "home":
    view_home()
elif route == "browse":
    view_browse()
elif route == "watch":
    view_watch()
elif route == "ai":
    view_ai()
elif route == "library":
    view_library()
elif route == "history":
    view_history()
elif route == "combo":
    view_combo()
else:
    view_home()