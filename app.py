import requests
import streamlit as st
import json
import math
from datetime import datetime

# =============================
# CONFIG
# =============================
API_BASE = "https://movie-rec-466x.onrender.com" or "http://127.0.0.1:8000"
TMDB_IMG = "https://image.tmdb.org/t/p/w500"
TMDB_IMG_ORIG = "https://image.tmdb.org/t/p/original"
TMDB_IMG_W300 = "https://image.tmdb.org/t/p/w300"

st.set_page_config(
    page_title="CineVerse — Movie Recommender",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================
# GENRE → THEME COLOR PALETTE
# =============================
GENRE_PALETTES = {
    "Action":           {"primary": "#ef4444", "secondary": "#f97316", "accent": "#fbbf24", "dark": "#1c0a00"},
    "Comedy":           {"primary": "#f59e0b", "secondary": "#fbbf24", "accent": "#84cc16", "dark": "#0d1300"},
    "Drama":            {"primary": "#8b5cf6", "secondary": "#a78bfa", "accent": "#c4b5fd", "dark": "#0d0010"},
    "Horror":           {"primary": "#dc2626", "secondary": "#991b1b", "accent": "#f87171", "dark": "#0a0000"},
    "Romance":          {"primary": "#ec4899", "secondary": "#f472b6", "accent": "#fbcfe8", "dark": "#1a0010"},
    "Science Fiction":  {"primary": "#06b6d4", "secondary": "#0891b2", "accent": "#67e8f9", "dark": "#00101a"},
    "Sci-Fi":           {"primary": "#06b6d4", "secondary": "#0891b2", "accent": "#67e8f9", "dark": "#00101a"},
    "Thriller":         {"primary": "#f97316", "secondary": "#ea580c", "accent": "#fed7aa", "dark": "#100500"},
    "Animation":        {"primary": "#10b981", "secondary": "#34d399", "accent": "#a7f3d0", "dark": "#001510"},
    "Documentary":      {"primary": "#64748b", "secondary": "#94a3b8", "accent": "#cbd5e1", "dark": "#0a0e12"},
    "Fantasy":          {"primary": "#7c3aed", "secondary": "#a78bfa", "accent": "#ddd6fe", "dark": "#0d0020"},
    "Adventure":        {"primary": "#14b8a6", "secondary": "#0d9488", "accent": "#5eead4", "dark": "#001210"},
    "Crime":            {"primary": "#b91c1c", "secondary": "#dc2626", "accent": "#fca5a5", "dark": "#0f0000"},
    "Mystery":          {"primary": "#4c1d95", "secondary": "#6d28d9", "accent": "#c4b5fd", "dark": "#0a0015"},
    "Music":            {"primary": "#0ea5e9", "secondary": "#38bdf8", "accent": "#bae6fd", "dark": "#00101a"},
    "History":          {"primary": "#b45309", "secondary": "#d97706", "accent": "#fde68a", "dark": "#100800"},
    "War":              {"primary": "#374151", "secondary": "#4b5563", "accent": "#9ca3af", "dark": "#050708"},
    "Family":           {"primary": "#16a34a", "secondary": "#22c55e", "accent": "#86efac", "dark": "#001508"},
    "Western":          {"primary": "#b45309", "secondary": "#92400e", "accent": "#fde68a", "dark": "#0f0800"},
    "Biography":        {"primary": "#0891b2", "secondary": "#06b6d4", "accent": "#a5f3fc", "dark": "#00101a"},
    "default":          {"primary": "#6366f1", "secondary": "#818cf8", "accent": "#c7d2fe", "dark": "#05050f"},
}

# =============================
# GENRE CARDS CONFIG (with TMDB genre IDs)
# =============================
GENRE_CARDS = [
    {"name": "Action",          "icon": "💥", "tmdb_id": 28},
    {"name": "Comedy",          "icon": "😂", "tmdb_id": 35},
    {"name": "Drama",           "icon": "🎭", "tmdb_id": 18},
    {"name": "Horror",          "icon": "👻", "tmdb_id": 27},
    {"name": "Romance",         "icon": "💕", "tmdb_id": 10749},
    {"name": "Science Fiction", "icon": "🚀", "tmdb_id": 878},
    {"name": "Thriller",        "icon": "⚡", "tmdb_id": 53},
    {"name": "Animation",       "icon": "✨", "tmdb_id": 16},
    {"name": "Adventure",       "icon": "🗺️", "tmdb_id": 12},
    {"name": "Crime",           "icon": "🕵️", "tmdb_id": 80},
    {"name": "Mystery",         "icon": "🔮", "tmdb_id": 9648},
    {"name": "Fantasy",         "icon": "🧙", "tmdb_id": 14},
    {"name": "Documentary",     "icon": "🎥", "tmdb_id": 99},
    {"name": "Family",          "icon": "👨‍👩‍👧", "tmdb_id": 10751},
]

# =============================
# LANGUAGE MAP
# =============================
LANGUAGE_MAP = {
    "All Languages":  "",
    "🇬🇧 English":   "en",
    "🇮🇳 Hindi":     "hi",
    "🇪🇸 Spanish":   "es",
    "🇫🇷 French":    "fr",
    "🇰🇷 Korean":    "ko",
    "🇯🇵 Japanese":  "ja",
    "🇩🇪 German":    "de",
    "🇮🇹 Italian":   "it",
    "🇵🇹 Portuguese":"pt",
    "🇨🇳 Chinese":   "zh",
    "🇮🇳 Tamil":     "ta",
    "🇮🇳 Telugu":    "te",
    "🇷🇺 Russian":   "ru",
    "🇸🇦 Arabic":    "ar",
}

def get_palette(genres_list):
    for g in (genres_list or []):
        name = g if isinstance(g, str) else g.get("name", "")
        if name in GENRE_PALETTES:
            return GENRE_PALETTES[name]
    return GENRE_PALETTES["default"]

# =============================
# SESSION STATE
# =============================
if "view"                  not in st.session_state:
    st.session_state.view = "home"
if "selected_tmdb_id"      not in st.session_state:
    st.session_state.selected_tmdb_id = None
if "watchlist"             not in st.session_state:
    st.session_state.watchlist = {}
if "watched"               not in st.session_state:
    st.session_state.watched = set()
if "last_viewed"           not in st.session_state:
    st.session_state.last_viewed = []
if "theme_palette"         not in st.session_state:
    st.session_state.theme_palette = GENRE_PALETTES["default"]
if "selected_genre_filter" not in st.session_state:
    st.session_state.selected_genre_filter = "All"
if "timeline_year"         not in st.session_state:
    st.session_state.timeline_year = 2020
if "selected_language"     not in st.session_state:
    st.session_state.selected_language = "All Languages"
if "show_side_panel"       not in st.session_state:
    st.session_state.show_side_panel = False

# =============================
# QUERY PARAM ROUTING
# =============================
qp_view = st.query_params.get("view")
qp_id   = st.query_params.get("id")
if qp_view in ("home", "details", "watchlist", "timeline"):
    st.session_state.view = qp_view
if qp_id:
    try:
        st.session_state.selected_tmdb_id = int(qp_id)
        st.session_state.view = "details"
    except:
        pass

# =============================
# NAVIGATION HELPERS
# =============================
def goto_home():
    st.session_state.view = "home"
    st.query_params["view"] = "home"
    if "id" in st.query_params:
        del st.query_params["id"]
    st.rerun()

def goto_details(tmdb_id: int):
    st.session_state.view               = "details"
    st.session_state.selected_tmdb_id  = int(tmdb_id)
    st.query_params["view"]             = "details"
    st.query_params["id"]               = str(int(tmdb_id))
    st.rerun()

def goto_watchlist():
    st.session_state.view = "watchlist"
    st.query_params["view"] = "watchlist"
    st.rerun()

def goto_timeline():
    st.session_state.view = "timeline"
    st.query_params["view"] = "timeline"
    st.rerun()

# =============================
# API HELPERS
# =============================
@st.cache_data(ttl=30)
def api_get_json(path: str, params: dict | None = None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=25)
        if r.status_code >= 400:
            return None, f"HTTP {r.status_code}: {r.text[:300]}"
        return r.json(), None
    except Exception as e:
        return None, f"Request failed: {e}"

def poster_grid(cards, cols=6, key_prefix="grid"):
    if not cards:
        st.info("No movies to show.")
        return
    rows = (len(cards) + cols - 1) // cols
    idx  = 0
    for r in range(rows):
        colset = st.columns(cols)
        for c in range(cols):
            if idx >= len(cards):
                break
            m       = cards[idx]; idx += 1
            tmdb_id = m.get("tmdb_id")
            title   = m.get("title", "Untitled")
            poster  = m.get("poster_url")
            with colset[c]:
                if poster:
                    st.image(poster, use_container_width=True)
                else:
                    st.write("🖼️ No poster")
                if st.button("Open", key=f"{key_prefix}_{r}_{c}_{idx}_{tmdb_id}"):
                    if tmdb_id:
                        goto_details(tmdb_id)
                st.markdown(
                    f"<div class='movie-title'>{title}</div>",
                    unsafe_allow_html=True,
                )

def to_cards_from_tfidf_items(tfidf_items):
    cards = []
    for x in tfidf_items or []:
        tmdb = x.get("tmdb") or {}
        if tmdb.get("tmdb_id"):
            cards.append({
                "tmdb_id":    tmdb["tmdb_id"],
                "title":      tmdb.get("title") or x.get("title") or "Untitled",
                "poster_url": tmdb.get("poster_url"),
            })
    return cards

def parse_tmdb_search_to_cards(data, keyword: str, limit: int = 24):
    keyword_l = keyword.strip().lower()
    if isinstance(data, dict) and "results" in data:
        raw_items = []
        for m in data.get("results") or []:
            title       = (m.get("title") or "").strip()
            tmdb_id     = m.get("id")
            poster_path = m.get("poster_path")
            if not title or not tmdb_id:
                continue
            raw_items.append({
                "tmdb_id":      int(tmdb_id),
                "title":        title,
                "poster_url":   f"{TMDB_IMG}{poster_path}" if poster_path else None,
                "release_date": m.get("release_date", ""),
                "original_language": m.get("original_language", ""),
            })
    elif isinstance(data, list):
        raw_items = []
        for m in data:
            tmdb_id = m.get("tmdb_id") or m.get("id")
            title   = (m.get("title") or "").strip()
            if not title or not tmdb_id:
                continue
            raw_items.append({
                "tmdb_id":      int(tmdb_id),
                "title":        title,
                "poster_url":   m.get("poster_url"),
                "release_date": m.get("release_date", ""),
                "original_language": m.get("original_language", ""),
            })
    else:
        return [], []

    matched    = [x for x in raw_items if keyword_l in x["title"].lower()]
    final_list = matched if matched else raw_items

    suggestions = []
    for x in final_list[:10]:
        year  = (x.get("release_date") or "")[:4]
        label = f"{x['title']} ({year})" if year else x["title"]
        suggestions.append((label, x["tmdb_id"]))

    cards = [
        {"tmdb_id": x["tmdb_id"], "title": x["title"], "poster_url": x["poster_url"]}
        for x in final_list[:limit]
    ]
    return suggestions, cards

# =============================
# UI COMPONENT HELPERS
# =============================

def circular_rating_svg(score: float, label: str, color: str, size: int = 120) -> str:
    r      = 40
    cx     = cy = size // 2
    circ   = 2 * math.pi * r
    dash   = (score / 10) * circ
    gap    = circ - dash
    offset = circ / 4
    font_score = int(size * 0.22)
    font_label = int(size * 0.11)
    safe_id = label.replace(" ", "").replace("/", "")
    return f"""
    <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <filter id="glow-{safe_id}">
          <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
          <feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge>
        </filter>
      </defs>
      <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="8"/>
      <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="8"
              stroke-dasharray="{dash:.2f} {gap:.2f}"
              stroke-dashoffset="{offset:.2f}" stroke-linecap="round"
              filter="url(#glow-{safe_id})">
        <animate attributeName="stroke-dasharray"
                 from="0 {circ:.2f}" to="{dash:.2f} {gap:.2f}"
                 dur="1.4s" ease="ease-out" fill="freeze"/>
      </circle>
      <text x="{cx}" y="{cy - 4}" text-anchor="middle" fill="white"
            font-size="{font_score}" font-weight="700" font-family="Georgia,serif">{score:.1f}</text>
      <text x="{cx}" y="{cy + font_label + 4}" text-anchor="middle" fill="rgba(255,255,255,0.6)"
            font-size="{font_label}" font-family="sans-serif">{label}</text>
    </svg>"""

def genre_chip_html(genre: str, active: bool, color: str) -> str:
    bg     = color if active else "rgba(255,255,255,0.07)"
    border = color if active else "rgba(255,255,255,0.15)"
    text   = "#fff" if active else "rgba(255,255,255,0.7)"
    weight = "600" if active else "400"
    return (f'<span style="display:inline-block;padding:6px 16px;margin:4px;border-radius:99px;'
            f'background:{bg};border:1.5px solid {border};color:{text};font-weight:{weight};'
            f'font-size:0.82rem;letter-spacing:0.03em;">{genre}</span>')

def hero_section_html(title: str, tagline: str, backdrop_url: str,
                      release: str, genres_str: str, palette: dict) -> str:
    p1, p2 = palette["primary"], palette["secondary"]
    img_tag = (f'<img src="{backdrop_url}" style="position:absolute;inset:0;width:100%;'
               f'height:100%;object-fit:cover;filter:brightness(0.55);">'
               if backdrop_url else
               f'<div style="position:absolute;inset:0;background:linear-gradient(135deg,{p1},{p2});"></div>')
    return f"""
    <div style="position:relative;width:100%;height:480px;border-radius:24px;overflow:hidden;
                margin-bottom:28px;box-shadow:0 32px 64px rgba(0,0,0,0.6);">
      {img_tag}
      <div style="position:absolute;inset:0;background:linear-gradient(90deg,
           rgba(0,0,0,0.92) 0%,rgba(0,0,0,0.55) 55%,rgba(0,0,0,0.1) 100%);"></div>
      <div style="position:absolute;inset:0;background:linear-gradient(0deg,
           rgba(0,0,0,0.7) 0%,transparent 45%);"></div>
      <div style="position:absolute;bottom:40px;left:44px;max-width:60%;">
        <div style="display:flex;gap:8px;margin-bottom:14px;flex-wrap:wrap;">
          <span style="background:{p1};color:#fff;padding:3px 12px;border-radius:99px;
                       font-size:0.72rem;font-weight:700;letter-spacing:0.08em;">
            {release[:4] if release else "–"}</span>
          <span style="background:rgba(255,255,255,0.12);color:rgba(255,255,255,0.8);
                       padding:3px 12px;border-radius:99px;font-size:0.72rem;">{genres_str or "–"}</span>
        </div>
        <h1 style="margin:0 0 8px;color:#fff;font-size:2.6rem;font-weight:800;
                   letter-spacing:-0.02em;text-shadow:0 2px 20px rgba(0,0,0,0.5);
                   font-family:Georgia,serif;line-height:1.1;">{title}</h1>
        <p style="margin:0;color:rgba(255,255,255,0.7);font-size:1rem;
                  font-style:italic;font-family:Georgia,serif;">{tagline or ""}</p>
      </div>
    </div>"""

def glass_card_html(content_html: str, extra_style: str = "") -> str:
    return (f'<div style="background:rgba(255,255,255,0.06);backdrop-filter:blur(18px);'
            f'-webkit-backdrop-filter:blur(18px);border:1px solid rgba(255,255,255,0.12);'
            f'border-radius:20px;padding:24px;{extra_style}">{content_html}</div>')

def cast_card_html(name: str, character: str, profile_url: str, color: str) -> str:
    img = (f'<img src="{profile_url}" style="width:80px;height:80px;border-radius:50%;'
           f'object-fit:cover;border:3px solid {color};">'
           if profile_url else
           f'<div style="width:80px;height:80px;border-radius:50%;background:rgba(255,255,255,0.1);'
           f'display:flex;align-items:center;justify-content:center;font-size:2rem;'
           f'border:3px solid {color};">👤</div>')
    return f"""
    <div style="text-align:center;padding:14px 10px;min-width:110px;max-width:120px;">
      {img}
      <div style="color:#fff;font-size:0.84rem;font-weight:700;margin-top:10px;
                  line-height:1.25;overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;
                  -webkit-box-orient:vertical;letter-spacing:0.01em;">{name}</div>
      <div style="color:rgba(255,255,255,0.5);font-size:0.72rem;margin-top:4px;
                  overflow:hidden;white-space:nowrap;text-overflow:ellipsis;
                  font-style:italic;">{character or ""}</div>
    </div>"""

def watchlist_badge_html(count: int, color: str) -> str:
    return (f'<span style="background:{color};color:#fff;border-radius:99px;'
            f'padding:2px 9px;font-size:0.75rem;font-weight:700;margin-left:6px;">{count}</span>'
            if count else "")

def timeline_movie_card(title: str, poster_url: str, year: str, color: str) -> str:
    img = (f'<img src="{poster_url}" style="width:100%;height:150px;object-fit:cover;'
           f'border-radius:10px 10px 0 0;">'
           if poster_url else
           f'<div style="width:100%;height:150px;background:rgba(255,255,255,0.06);'
           f'border-radius:10px 10px 0 0;display:flex;align-items:center;'
           f'justify-content:center;font-size:2rem;">🎬</div>')
    return f"""
    <div style="width:130px;flex-shrink:0;background:rgba(255,255,255,0.06);
                border:1px solid rgba(255,255,255,0.1);border-radius:12px;overflow:hidden;
                text-align:center;">
      {img}
      <div style="padding:8px 6px;">
        <div style="color:#fff;font-size:0.75rem;font-weight:600;line-height:1.2;
                    overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;
                    -webkit-box-orient:vertical;">{title}</div>
        <div style="color:{color};font-size:0.7rem;margin-top:4px;font-weight:500;">{year}</div>
      </div>
    </div>"""

def genre_card_html(name: str, icon: str, color: str, active: bool) -> str:
    border  = f"2px solid {color}"       if active else "1px solid rgba(255,255,255,0.1)"
    glow    = f"0 0 22px {color}55"      if active else "none"
    bg      = f"linear-gradient(135deg, {color}44, {color}18)" if active else "rgba(255,255,255,0.04)"
    tw      = "700"                       if active else "500"
    scale   = "transform:scale(1.04);"   if active else ""
    return (
        f'<div style="background:{bg};border:{border};border-radius:18px;'
        f'padding:20px 8px;text-align:center;cursor:pointer;box-shadow:{glow};'
        f'transition:all 0.25s;min-height:96px;{scale}'
        f'display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;">'
        f'<div style="font-size:2rem;line-height:1;">{icon}</div>'
        f'<div style="color:#fff;font-size:0.78rem;font-weight:{tw};'
        f'letter-spacing:0.02em;line-height:1.2;">{name}</div>'
        f'</div>'
    )

def filter_cards_by_language(cards: list, lang_code: str) -> list:
    """Client-side filter: keep only cards whose original_language matches."""
    if not lang_code:
        return cards
    return [c for c in cards if c.get("original_language", "") == lang_code] or cards

# =============================
# GLOBAL CSS — Glassmorphism + Cinematic Dark
# =============================
def inject_css(palette: dict):
    p1, p2, acc = palette["primary"], palette["secondary"], palette["accent"]
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Crimson+Pro:ital,wght@0,400;0,600;0,700;1,400&family=DM+Sans:wght@300;400;500;600&display=swap');

/* ── Root ── */
:root {{ --c-primary:{p1}; --c-secondary:{p2}; --c-accent:{acc}; }}

/* ── App background ── */
.stApp {{
  background:
    radial-gradient(ellipse at 20% 20%, {p1}18 0%, transparent 55%),
    radial-gradient(ellipse at 80% 80%, {p2}12 0%, transparent 55%),
    linear-gradient(160deg, #09090f 0%, #0d0d1a 100%) !important;
  font-family:'DM Sans',sans-serif;
}}

/* ── Sidebar — blends with home background ── */
[data-testid="stSidebar"] {{
  background:
    radial-gradient(ellipse at 10% 15%, {p1}20 0%, transparent 55%),
    radial-gradient(ellipse at 90% 85%, {p2}14 0%, transparent 55%),
    linear-gradient(180deg, #08080e 0%, #0c0c1a 100%) !important;
  backdrop-filter:blur(20px) !important;
  -webkit-backdrop-filter:blur(20px) !important;
  border-right:1px solid rgba(255,255,255,0.07) !important;
}}
[data-testid="stSidebar"] * {{ color:rgba(255,255,255,0.88) !important; }}

/* ── Hide default header ── */
header[data-testid="stHeader"] {{ display:none !important; }}
#MainMenu, footer {{ visibility:hidden !important; }}

/* ── Block container ── */
.block-container {{
  padding-top:1.5rem !important;
  padding-bottom:3rem !important;
  max-width:1500px !important;
}}

/* ── Typography ── */
h1,h2,h3 {{
  font-family:'Crimson Pro',Georgia,serif !important;
  color:#fff !important;
  letter-spacing:-0.02em;
}}
.stMarkdown p, .stMarkdown li {{ color:rgba(255,255,255,0.75) !important; }}

/* ── Movie title ── */
.movie-title {{
  color:rgba(255,255,255,0.85);
  font-size:0.78rem;
  font-family:'DM Sans',sans-serif;
  line-height:1.2rem;
  height:2.4rem;
  overflow:hidden;
  margin-top:4px;
  font-weight:500;
}}

/* ── Glass card ── */
.card {{
  background:rgba(255,255,255,0.05) !important;
  backdrop-filter:blur(18px) !important;
  -webkit-backdrop-filter:blur(18px) !important;
  border:1px solid rgba(255,255,255,0.1) !important;
  border-radius:20px !important;
  padding:20px !important;
}}

/* ── Buttons ── */
.stButton > button {{
  background:rgba(255,255,255,0.07) !important;
  color:rgba(255,255,255,0.9) !important;
  border:1px solid rgba(255,255,255,0.15) !important;
  border-radius:10px !important;
  font-family:'DM Sans',sans-serif !important;
  font-weight:500 !important;
  font-size:0.8rem !important;
  padding:6px 14px !important;
  transition:all 0.2s ease !important;
  backdrop-filter:blur(8px) !important;
  width:100% !important;
}}
.stButton > button:hover {{
  background:{p1} !important;
  border-color:{p1} !important;
  transform:translateY(-1px) !important;
  box-shadow:0 6px 20px {p1}55 !important;
}}

/* ── Primary action button ── */
.primary-btn {{
  display:inline-flex;align-items:center;gap:8px;
  background:{p1};color:#fff;border:none;
  padding:12px 28px;border-radius:12px;cursor:pointer;
  font-family:'DM Sans',sans-serif;font-weight:600;
  font-size:0.95rem;letter-spacing:0.02em;
  box-shadow:0 8px 24px {p1}55;transition:all 0.2s;
}}
.primary-btn:hover {{ transform:translateY(-2px);box-shadow:0 12px 32px {p1}77; }}

/* ── Watchlist button ── */
.wl-btn {{
  display:inline-flex;align-items:center;gap:8px;
  background:rgba(255,255,255,0.08);backdrop-filter:blur(10px);
  color:rgba(255,255,255,0.9);border:1.5px solid rgba(255,255,255,0.2);
  padding:11px 24px;border-radius:12px;cursor:pointer;
  font-family:'DM Sans',sans-serif;font-weight:500;font-size:0.95rem;transition:all 0.2s;
}}
.wl-btn:hover {{ background:rgba(255,255,255,0.15);border-color:rgba(255,255,255,0.4); }}

/* ── Inputs ── */
.stTextInput input,.stSelectbox select {{
  background:rgba(255,255,255,0.06) !important;
  color:#fff !important;
  border:1px solid rgba(255,255,255,0.15) !important;
  border-radius:12px !important;
  font-family:'DM Sans',sans-serif !important;
}}
.stTextInput input:focus {{
  border-color:{p1} !important;
  box-shadow:0 0 0 3px {p1}33 !important;
}}

/* ── Selectbox ── */
[data-testid="stSelectbox"] > div > div {{
  background:rgba(255,255,255,0.06) !important;
  border:1px solid rgba(255,255,255,0.14) !important;
  border-radius:12px !important;color:#fff !important;
}}

/* ── Horizontal scroll ── */
.hscroll {{
  display:flex;gap:14px;overflow-x:auto;
  padding:12px 0 16px;
  scrollbar-width:thin;scrollbar-color:{p1}44 transparent;
}}
.hscroll::-webkit-scrollbar {{ height:4px; }}
.hscroll::-webkit-scrollbar-thumb {{ background:{p1}66;border-radius:99px; }}

/* ── Section label ── */
.section-label {{
  font-family:'DM Sans',sans-serif;
  font-size:0.72rem;font-weight:600;letter-spacing:0.12em;
  text-transform:uppercase;color:{p1};margin-bottom:4px;
}}
</style>
""", unsafe_allow_html=True)

# ── Apply CSS ──────────────────────────────────────────────
inject_css(st.session_state.theme_palette)

# =============================
# SIDEBAR
# =============================
with st.sidebar:
    st.markdown(
        "<h2 style='font-family:Crimson Pro,Georgia,serif;font-size:1.5rem;"
        "color:#fff;margin:0 0 4px;'>🎬 CineVerse</h2>",
        unsafe_allow_html=True,
    )
    st.markdown("<div class='small-muted'>Your cinematic universe</div>", unsafe_allow_html=True)
    st.divider()

    # ── Navigation ────────────────────────────────────────
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🏠 Home", use_container_width=True):
            goto_home()
    with col_b:
        wl_count = len(st.session_state.watchlist)
        if st.button(f"📌 List ({wl_count})", use_container_width=True):
            goto_watchlist()

    col_c, col_d = st.columns(2)
    with col_c:
        if st.button("📅 Timeline", use_container_width=True):
            goto_timeline()
    with col_d:
        watched_count = len(st.session_state.watched)
        if st.button(f"✅ Watched ({watched_count})", use_container_width=True):
            goto_watchlist()

    st.divider()

    # ── Feed Settings ─────────────────────────────────────
    st.markdown("### ⚙️ Feed Settings")
    home_category = st.selectbox(
        "Category",
        ["trending", "popular", "top_rated", "now_playing", "upcoming"],
        index=0,
    )
    grid_cols = st.slider("Grid columns", 4, 8, 6)

    st.divider()

    # ── Language Filter ───────────────────────────────────
    st.markdown("### 🌐 Language")
    lang_choice = st.selectbox(
        "Movie Language",
        list(LANGUAGE_MAP.keys()),
        index=list(LANGUAGE_MAP.keys()).index(st.session_state.selected_language),
        label_visibility="collapsed",
    )
    if lang_choice != st.session_state.selected_language:
        st.session_state.selected_language = lang_choice
        st.rerun()

    lang_code = LANGUAGE_MAP[st.session_state.selected_language]
    if lang_code:
        st.markdown(
            f"<div class='small-muted' style='margin-top:-8px;margin-bottom:4px;'>"
            f"Showing: <strong style='color:{st.session_state.theme_palette['primary']};'>"
            f"{st.session_state.selected_language}</strong></div>",
            unsafe_allow_html=True,
        )

    st.divider()

    # ── Quick Watchlist Preview ───────────────────────────
    if st.session_state.watchlist:
        st.markdown("### 📌 Watchlist")
        for tid, info in list(st.session_state.watchlist.items())[:4]:
            is_w  = tid in st.session_state.watched
            icon  = "✅" if is_w else "🎬"
            label = info["title"]
            short = f"{icon} {label[:22]}…" if len(label) > 22 else f"{icon} {label}"
            if st.button(short, key=f"wl_sidebar_{tid}"):
                goto_details(tid)
        if len(st.session_state.watchlist) > 4:
            st.caption(f"+ {len(st.session_state.watchlist) - 4} more…")

# =============================
# MAIN HEADER
# =============================
col_h1, col_h2 = st.columns([5, 1])
with col_h1:
    st.markdown(
        "<h1 style='font-family:Crimson Pro,Georgia,serif;font-size:2.8rem;"
        "font-weight:700;color:#fff;margin:0 0 4px;letter-spacing:-0.03em;'>"
        "🎬 CineVerse</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='small-muted' style='margin-bottom:8px;'>Discover • Curate • Experience</div>",
        unsafe_allow_html=True,
    )
with col_h2:
    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
    if st.button("📂 Toggle Panel", use_container_width=True):
        st.session_state.show_side_panel = not st.session_state.show_side_panel
        st.rerun()

st.divider()

# ── Custom Toggleable Side Panel ──
if st.session_state.show_side_panel:
    with st.expander("📌 Quick View Panel", expanded=True):
        st.markdown(
            "<div style='color:rgba(255,255,255,0.8);'>"
            "This is your custom side panel. You can easily place additional filters, stats, or tools here without disrupting the core app UI."
            "</div>", unsafe_allow_html=True
        )
        if st.session_state.watchlist:
            st.write(f"**Watchlist Items:** {len(st.session_state.watchlist)}")
        else:
            st.write("Your Watchlist is empty.")
    st.divider()

# ══════════════════════════════════════════════════════════
# VIEW: HOME
# ══════════════════════════════════════════════════════════
if st.session_state.view == "home":

    # ── Search ────────────────────────────────────────────
    search_col, lang_col = st.columns([3, 1])
    with search_col:
        typed = st.text_input(
            "🔍  Search",
            placeholder="Type: inception, batman, interstellar…",
            label_visibility="collapsed",
        )
    with lang_col:
        if lang_code:
            st.markdown(
                f"<div style='padding:10px 0;'>"
                f"<span class='rating-badge' style='background:rgba(99,102,241,0.15);"
                f"border-color:rgba(99,102,241,0.4);color:#a5b4fc;'>"
                f"🌐 {st.session_state.selected_language}</span></div>",
                unsafe_allow_html=True,
            )

    # ── GENRE SELECTION (Dropdown) ────────────────────
    st.markdown("<div class='section-label'>Browse by Genre</div>", unsafe_allow_html=True)

    genre_names = ["All"] + [g["name"] for g in GENRE_CARDS]
    def get_genre_label(gname):
        if gname == "All": return "🌍 All Genres"
        gicon = next((g["icon"] for g in GENRE_CARDS if g["name"] == gname), "🎬")
        return f"{gicon} {gname}"

    current_sel = st.session_state.selected_genre_filter
    current_idx = genre_names.index(current_sel) if current_sel in genre_names else 0

    selected_genre = st.selectbox(
        "Select a Genre",
        options=genre_names,
        index=current_idx,
        format_func=get_genre_label,
        label_visibility="collapsed"
    )

    if selected_genre != current_sel:
        st.session_state.selected_genre_filter = selected_genre
        if selected_genre != "All":
            gpal = GENRE_PALETTES.get(selected_genre, GENRE_PALETTES["default"])
            st.session_state.theme_palette = gpal
            inject_css(gpal)
        else:
            st.session_state.theme_palette = GENRE_PALETTES["default"]
            inject_css(GENRE_PALETTES["default"])
        st.rerun()

    st.divider()

    # ── SEARCH MODE ───────────────────────────────────────
    if typed.strip():
        if len(typed.strip()) < 2:
            st.caption("Type at least 2 characters for suggestions.")
        else:
            search_params = {"query": typed.strip()}
            if lang_code:
                search_params["language"] = lang_code
            data, err = api_get_json("/tmdb/search", params=search_params)
            if err or data is None:
                st.error(f"Search failed: {err}")
            else:
                suggestions, cards = parse_tmdb_search_to_cards(data, typed.strip(), limit=24)

                # Apply language filter client-side as fallback
                if lang_code:
                    cards = filter_cards_by_language(cards, lang_code)

                if suggestions:
                    labels   = ["— Select a movie —"] + [s[0] for s in suggestions]
                    selected = st.selectbox("Suggestions", labels, index=0)
                    if selected != "— Select a movie —":
                        label_to_id = {s[0]: s[1] for s in suggestions}
                        goto_details(label_to_id[selected])
                else:
                    st.info("No suggestions found. Try another keyword.")

                st.markdown("### Search Results")
                poster_grid(cards, cols=grid_cols, key_prefix="search_results")
        st.stop()

    # ── GENRE FILTER MODE ─────────────────────────────────
    active_genre = st.session_state.selected_genre_filter
    if active_genre != "All":
        gpal  = GENRE_PALETTES.get(active_genre, GENRE_PALETTES["default"])
        gicon = next((g["icon"] for g in GENRE_CARDS if g["name"] == active_genre), "🎬")

        st.markdown(
            f"<div class='section-label'>Genre Collection</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<h2 style='margin-top:2px;'>{gicon} {active_genre} Movies</h2>",
            unsafe_allow_html=True,
        )
        if lang_code:
            st.markdown(
                f"<div class='small-muted' style='margin-bottom:10px;'>"
                f"Filtered by language: {st.session_state.selected_language}</div>",
                unsafe_allow_html=True,
            )

        genre_params = {"query": active_genre, "limit": 24}
        if lang_code:
            genre_params["language"] = lang_code
            genre_params["with_original_language"] = lang_code

        genre_data, g_err = api_get_json("/tmdb/search", params=genre_params)
        if not g_err and genre_data:
            _, genre_cards = parse_tmdb_search_to_cards(genre_data, active_genre, limit=24)
            if lang_code:
                genre_cards = filter_cards_by_language(genre_cards, lang_code)
            if genre_cards:
                poster_grid(genre_cards, cols=grid_cols, key_prefix=f"genre_{active_genre}")
            else:
                st.info(f"No {active_genre} movies found for the selected language. Showing all languages.")
                genre_data2, _ = api_get_json("/tmdb/search", params={"query": active_genre, "limit": 24})
                if genre_data2:
                    _, genre_cards2 = parse_tmdb_search_to_cards(genre_data2, active_genre, limit=24)
                    poster_grid(genre_cards2, cols=grid_cols, key_prefix=f"genre_fallback_{active_genre}")
        else:
            st.warning(f"Could not load {active_genre} movies right now.")

        st.divider()

        # Also show similar from API
        st.markdown("<div class='section-label'>More in this Genre</div>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='margin-top:2px;'>🎭 Popular {active_genre}</h3>", unsafe_allow_html=True)
        home_genre, hg_err = api_get_json("/home", params={"category": "popular", "limit": 18})
        if home_genre and not hg_err:
            poster_grid(home_genre[:12], cols=grid_cols, key_prefix="genre_popular")
        st.stop()

    # ── HOME FEED MODE ─────────────────────────────────────
    st.markdown(
        f"<div class='section-label'>Now Showing — {home_category.replace('_',' ').upper()}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<h2 style='margin-top:2px;'>{home_category.replace('_',' ').title()} Movies</h2>",
        unsafe_allow_html=True,
    )

    home_params = {"category": home_category, "limit": 24}
    if lang_code:
        home_params["language"] = lang_code
        home_params["with_original_language"] = lang_code

    home_cards, err = api_get_json("/home", params=home_params)
    if err or not home_cards:
        st.error(f"Home feed failed: {err or 'Unknown error'}")
        st.stop()

    # Client-side language filter fallback
    filtered_cards = filter_cards_by_language(home_cards, lang_code) if lang_code else home_cards

    poster_grid(filtered_cards, cols=grid_cols, key_prefix="home_feed")

    st.divider()

    # ── Underrated Picks ──────────────────────────────────
    st.markdown("<div class='section-label'>Hidden Gems</div>", unsafe_allow_html=True)
    st.markdown("<h2 style='margin-top:2px;'>🪩 Underrated Movies for You</h2>", unsafe_allow_html=True)
    st.markdown(
        "<div class='small-muted'>Films flying under the radar</div>",
        unsafe_allow_html=True,
    )
    underrated, err2 = api_get_json("/home", params={"category": "top_rated", "limit": 12})
    if underrated and not err2:
        ur_filtered = filter_cards_by_language(underrated[6:], lang_code) if lang_code else underrated[6:]
        poster_grid(ur_filtered, cols=grid_cols, key_prefix="underrated")

    st.divider()

    # ── Because You Watched ───────────────────────────────
    if st.session_state.last_viewed:
        last = st.session_state.last_viewed[-1]
        st.markdown("<div class='section-label'>Personalised for You</div>", unsafe_allow_html=True)
        st.markdown(
            f"<h2 style='margin-top:2px;'>🎵 Because You Liked <em>{last['title']}</em>…</h2>",
            unsafe_allow_html=True,
        )
        similar, err3 = api_get_json(
            "/movie/search",
            params={"query": last["title"], "tfidf_top_n": 12, "genre_limit": 0},
        )
        if similar and not err3:
            recs_cards = to_cards_from_tfidf_items(similar.get("tfidf_recommendations", []))
            if lang_code:
                recs_cards = filter_cards_by_language(recs_cards, lang_code) or recs_cards
            poster_grid(recs_cards, cols=grid_cols, key_prefix="because_you_liked")
        st.divider()

    # ── Coming Soon ───────────────────────────────────────
    st.markdown("<div class='section-label'>On the Horizon</div>", unsafe_allow_html=True)
    st.markdown("<h2 style='margin-top:2px;'>🚀 Coming Soon</h2>", unsafe_allow_html=True)
    upcoming_params = {"category": "upcoming", "limit": 6}
    if lang_code:
        upcoming_params["language"] = lang_code
    upcoming, err4 = api_get_json("/home", params=upcoming_params)
    if upcoming and not err4:
        up_filtered = filter_cards_by_language(upcoming, lang_code) if lang_code else upcoming
        poster_grid(up_filtered, cols=6, key_prefix="coming_soon")


# ══════════════════════════════════════════════════════════
# VIEW: TIMELINE
# ══════════════════════════════════════════════════════════
elif st.session_state.view == "timeline":

    nav_l, _ = st.columns([1, 6])
    with nav_l:
        if st.button("← Home"):
            goto_home()

    st.markdown("<div class='section-label'>Cinematic Time Machine</div>", unsafe_allow_html=True)
    st.markdown("<h2 style='margin-top:2px;'>📅 Browse Movies by Era</h2>", unsafe_allow_html=True)
    st.markdown(
        "<div class='small-muted'>Slide through the decades and discover cinema's greatest eras.</div>",
        unsafe_allow_html=True,
    )

    # ── Decade visual bar ─────────────────────────────────
    decades    = list(range(1990, 2026, 5))
    dot_color  = st.session_state.theme_palette["primary"]
    tl_html    = '<div style="display:flex;align-items:flex-start;gap:0;margin:24px 0 32px;">'
    for i, d in enumerate(decades):
        active = abs(st.session_state.timeline_year - d) <= 2
        tl_html += f"""
        <div style="display:flex;flex-direction:column;align-items:center;flex:1;">
          <div style="width:16px;height:16px;border-radius:50%;
               background:{'#fff' if active else dot_color};
               box-shadow:{'0 0 16px ' + dot_color if active else 'none'};
               border:2.5px solid {dot_color};transition:all 0.3s;"></div>
          <div style="font-size:0.72rem;color:{'#fff' if active else 'rgba(255,255,255,0.4)'};
               font-weight:{'700' if active else '400'};margin-top:8px;">{d}s</div>
        </div>
        {"" if i == len(decades)-1 else '<div style="flex:1;height:2px;background:linear-gradient(90deg,rgba(255,255,255,0.15),rgba(255,255,255,0.05));margin-top:7px;"></div>'}"""
    tl_html += "</div>"
    st.markdown(tl_html, unsafe_allow_html=True)

    year = st.slider("Year", min_value=1990, max_value=2025,
                     value=st.session_state.timeline_year, step=1,
                     label_visibility="collapsed")
    st.session_state.timeline_year = year

    st.markdown(
        f"<h3 style='text-align:center;color:{st.session_state.theme_palette['primary']};'>"
        f"📽️ {year}</h3>",
        unsafe_allow_html=True,
    )

    year_params = {"query": str(year)}
    if lang_code:
        year_params["language"] = lang_code
    year_data, err = api_get_json("/tmdb/search", params=year_params)
    if err or not year_data:
        st.warning("Could not load movies for this year. Try adjusting the slider.")
    else:
        _, year_cards = parse_tmdb_search_to_cards(year_data, str(year), limit=18)
        if lang_code:
            year_cards = filter_cards_by_language(year_cards, lang_code) or year_cards
        if year_cards:
            poster_grid(year_cards, cols=grid_cols, key_prefix=f"timeline_{year}")
        else:
            st.info(f"No results found for {year}.")


# ══════════════════════════════════════════════════════════
# VIEW: WATCHLIST
# ══════════════════════════════════════════════════════════
elif st.session_state.view == "watchlist":

    nav_l, _ = st.columns([1, 6])
    with nav_l:
        if st.button("← Home"):
            goto_home()

    palette = st.session_state.theme_palette
    p1      = palette["primary"]

    st.markdown("<div class='section-label'>Your Collection</div>", unsafe_allow_html=True)
    st.markdown("<h2 style='margin-top:2px;'>📌 Watchlist & Progress</h2>", unsafe_allow_html=True)

    if not st.session_state.watchlist:
        st.markdown(
            glass_card_html(
                "<div style='text-align:center;padding:40px;'>"
                "<div style='font-size:3rem;margin-bottom:12px;'>🍿</div>"
                "<div style='color:rgba(255,255,255,0.7);font-size:1.1rem;'>"
                "Your watchlist is empty.<br>Open any movie and add it here!</div>"
                "</div>"
            ),
            unsafe_allow_html=True,
        )
        st.stop()

    total   = len(st.session_state.watchlist)
    watched = len(st.session_state.watched)
    pct     = int(watched / total * 100) if total else 0

    overview_html = f"""
    <div style="display:flex;gap:32px;align-items:center;flex-wrap:wrap;">
      <div style="text-align:center;">
        <div style="font-size:2.2rem;font-weight:700;color:#fff;font-family:Crimson Pro,serif;">{total}</div>
        <div style="color:rgba(255,255,255,0.5);font-size:0.8rem;">Saved</div>
      </div>
      <div style="text-align:center;">
        <div style="font-size:2.2rem;font-weight:700;color:{p1};font-family:Crimson Pro,serif;">{watched}</div>
        <div style="color:rgba(255,255,255,0.5);font-size:0.8rem;">Watched</div>
      </div>
      <div style="flex:1;min-width:200px;">
        <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
          <span style="color:rgba(255,255,255,0.7);font-size:0.82rem;">Overall Progress</span>
          <span style="color:{p1};font-size:0.82rem;font-weight:600;">{pct}%</span>
        </div>
        <div style="background:rgba(255,255,255,0.08);border-radius:99px;height:10px;">
          <div style="height:10px;width:{pct}%;border-radius:99px;
               background:linear-gradient(90deg,{p1},{palette['secondary']});
               transition:width 0.8s ease;"></div>
        </div>
      </div>
    </div>"""
    st.markdown(glass_card_html(overview_html, "margin-bottom:24px;"), unsafe_allow_html=True)

    cols = st.columns(2)
    for i, (tid, info) in enumerate(st.session_state.watchlist.items()):
        is_watched = tid in st.session_state.watched
        with cols[i % 2]:
            item_html = f"""
            <div style="display:flex;gap:14px;align-items:center;">
              {'<img src="' + info["poster_url"] + '" style="width:54px;height:78px;object-fit:cover;border-radius:8px;flex-shrink:0;">' if info.get("poster_url") else '<div style="width:54px;height:78px;background:rgba(255,255,255,0.06);border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:1.4rem;flex-shrink:0;">🎬</div>'}
              <div style="flex:1;min-width:0;">
                <div style="color:#fff;font-weight:600;font-size:0.9rem;
                            overflow:hidden;white-space:nowrap;text-overflow:ellipsis;">{info["title"]}</div>
                <div style="color:rgba(255,255,255,0.4);font-size:0.75rem;margin-top:2px;">{info.get("added_at","")}</div>
              </div>
              <span style="font-size:1.2rem;">{"✅" if is_watched else "🎬"}</span>
            </div>"""
            st.markdown(
                f'<div style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.09);'
                f'border-radius:14px;padding:14px;margin-bottom:10px;">{item_html}</div>',
                unsafe_allow_html=True,
            )
            btn_cols = st.columns(3)
            with btn_cols[0]:
                if st.button("Open", key=f"wl_open_{tid}"):
                    goto_details(tid)
            with btn_cols[1]:
                w_lbl = "Unwatch" if is_watched else "✅ Watched"
                if st.button(w_lbl, key=f"wl_watch_{tid}"):
                    if is_watched:
                        st.session_state.watched.discard(tid)
                    else:
                        st.session_state.watched.add(tid)
                    st.rerun()
            with btn_cols[2]:
                if st.button("Remove", key=f"wl_del_{tid}"):
                    del st.session_state.watchlist[tid]
                    st.session_state.watched.discard(tid)
                    st.rerun()


# ══════════════════════════════════════════════════════════
# VIEW: DETAILS
# ══════════════════════════════════════════════════════════
elif st.session_state.view == "details":
    tmdb_id = st.session_state.selected_tmdb_id
    if not tmdb_id:
        st.warning("No movie selected.")
        if st.button("← Back to Home"):
            goto_home()
        st.stop()

    nav_l, _ = st.columns([1, 6])
    with nav_l:
        if st.button("← Home"):
            goto_home()

    data, err = api_get_json(f"/movie/id/{tmdb_id}")
    if err or not data:
        st.error(f"Could not load details: {err or 'Unknown error'}")
        st.stop()

    title        = data.get("title", "Untitled")
    overview     = data.get("overview", "")
    release_date = data.get("release_date", "") or ""
    genres_raw   = data.get("genres", [])
    genres_str   = ", ".join(
        [g["name"] if isinstance(g, dict) else str(g) for g in genres_raw]
    )
    tagline      = data.get("tagline", "")
    vote_avg     = float(data.get("vote_average") or 0)
    vote_count   = int(data.get("vote_count") or 0)
    popularity   = float(data.get("popularity") or 0)
    runtime      = data.get("runtime") or 0
    orig_lang    = data.get("original_language", "")
    poster_url   = data.get("poster_url") or data.get("poster_path", "")
    backdrop_url = data.get("backdrop_url") or data.get("backdrop_path", "")

    # ── Update theme based on genre ──────────────────────
    genre_names = [g["name"] if isinstance(g, dict) else str(g) for g in genres_raw]
    palette     = get_palette(genre_names)
    st.session_state.theme_palette = palette
    inject_css(palette)
    p1, p2 = palette["primary"], palette["secondary"]

    # ── Track last viewed ─────────────────────────────────
    entry = {"tmdb_id": tmdb_id, "title": title, "genres": genre_names}
    lv    = st.session_state.last_viewed
    if not any(x["tmdb_id"] == tmdb_id for x in lv):
        lv.append(entry)
        st.session_state.last_viewed = lv[-5:]

    # ── CINEMATIC HERO ─────────────────────────────────────
    st.markdown(
        hero_section_html(title, tagline, backdrop_url, release_date, genres_str, palette),
        unsafe_allow_html=True,
    )

    # ── ACTION BUTTONS ─────────────────────────────────────
    btn_l, btn_m, btn_r, _ = st.columns([1.2, 1.4, 1.4, 4])
    is_in_watchlist = tmdb_id in st.session_state.watchlist
    is_watched      = tmdb_id in st.session_state.watched

    with btn_l:
        st.markdown(
            f'<div class="primary-btn">▶ Play Trailer</div>',
            unsafe_allow_html=True,
        )
    with btn_m:
        wl_label = "✅ In Watchlist" if is_in_watchlist else "📌 Add to Watchlist"
        if st.button(wl_label, key="wl_toggle", use_container_width=True):
            if is_in_watchlist:
                del st.session_state.watchlist[tmdb_id]
            else:
                st.session_state.watchlist[tmdb_id] = {
                    "title":     title,
                    "poster_url": poster_url,
                    "added_at":  datetime.now().strftime("%b %d, %Y"),
                }
            st.rerun()
    with btn_r:
        w_label = "✅ Watched" if is_watched else "Mark as Watched"
        if st.button(w_label, key="watched_toggle", use_container_width=True):
            if is_watched:
                st.session_state.watched.discard(tmdb_id)
            else:
                st.session_state.watched.add(tmdb_id)
                if tmdb_id not in st.session_state.watchlist:
                    st.session_state.watchlist[tmdb_id] = {
                        "title":     title,
                        "poster_url": poster_url,
                        "added_at":  datetime.now().strftime("%b %d, %Y"),
                    }
            st.rerun()

    st.divider()

    # ── MAIN LAYOUT: Poster | Info | Ratings ─────────────
    col_poster, col_info, col_ratings = st.columns([1, 2.2, 1.6], gap="large")

    with col_poster:
        if poster_url:
            st.image(poster_url, use_container_width=True)
        meta_parts = []
        if runtime:
            meta_parts.append(f"⏱️ {runtime} min")
        if orig_lang:
            lang_display = next(
                (k for k, v in LANGUAGE_MAP.items() if v == orig_lang and k != "All Languages"),
                orig_lang.upper()
            )
            meta_parts.append(f"🌐 {lang_display}")
        if meta_parts:
            st.markdown(
                f"<div style='text-align:center;color:rgba(255,255,255,0.5);"
                f"font-size:0.8rem;margin-top:8px;'>{' · '.join(meta_parts)}</div>",
                unsafe_allow_html=True,
            )

    with col_info:
        st.markdown("<div class='section-label'>Overview</div>", unsafe_allow_html=True)

        chips_html = ""
        for g in genre_names:
            gp = GENRE_PALETTES.get(g, palette)
            chips_html += genre_chip_html(g, False, gp["primary"])
        if chips_html:
            st.markdown(f"<div style='margin:8px 0 14px;'>{chips_html}</div>",
                        unsafe_allow_html=True)

        st.markdown(
            f"<div style='color:rgba(255,255,255,0.8);line-height:1.7;"
            f"font-family:Crimson Pro,Georgia,serif;font-size:1.06rem;'>"
            f"{overview or 'No overview available.'}</div>",
            unsafe_allow_html=True,
        )

        if release_date:
            st.markdown(
                f"<div style='color:rgba(255,255,255,0.4);font-size:0.82rem;margin-top:14px;'>"
                f"📅 Released: {release_date}</div>",
                unsafe_allow_html=True,
            )

    with col_ratings:
        st.markdown("<div class='section-label'>Ratings</div>", unsafe_allow_html=True)

        # ── TMDB real ratings (from tmdb.org — free, crowd-sourced) ──
        tmdb_score  = round(vote_avg, 1)
        # Normalise popularity to a 0–10 buzz score
        buzz_score  = round(min(popularity / 100, 10), 1)
        # Weighted critics estimate (TMDB vote_average skews well with critic scores)
        critic_est  = round(min(vote_avg * 1.04, 10), 1)

        # TMDB badge
        st.markdown(
            f"<div style='display:flex;gap:10px;align-items:center;margin-bottom:14px;flex-wrap:wrap;'>"
            f"<span class='rating-badge'>⭐ {tmdb_score}/10</span>"
            f"<span style='color:rgba(255,255,255,0.4);font-size:0.78rem;'>"
            f"TMDB · {vote_count:,} votes</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

        # Three animated ring meters
        rings_html = (
            '<div class="rating-rings">'
            + circular_rating_svg(tmdb_score, "TMDB",    p1,       110)
            + circular_rating_svg(critic_est, "Critics", p2,       110)
            + circular_rating_svg(buzz_score, "Buzz",    "#10b981", 110)
            + "</div>"
        )
        st.markdown(glass_card_html(rings_html, "text-align:center;"), unsafe_allow_html=True)

        if vote_count:
            st.markdown(
                f"<div class='small-muted' style='text-align:center;margin-top:8px;'>"
                f"Source: TMDB Community · {vote_count:,} ratings</div>",
                unsafe_allow_html=True,
            )

    st.divider()

    # ── CAST & CREW ────────────────────────────────────────
    st.markdown("<div class='section-label'>Cast & Crew</div>", unsafe_allow_html=True)
    st.markdown("<h3 style='margin-top:2px;'>👥 Featured Cast</h3>", unsafe_allow_html=True)

    cast_data, cast_err = api_get_json(f"/movie/id/{tmdb_id}/credits")
    if not cast_err and cast_data and isinstance(cast_data, dict):
        cast_list = cast_data.get("cast", [])[:16]
    else:
        cast_list = []

    if cast_list:
        cast_html = '<div class="hscroll">'
        for member in cast_list:
            name          = member.get("name", "")
            character     = member.get("character", "")
            profile_path  = member.get("profile_path")
            profile_url_m = f"{TMDB_IMG_W300}{profile_path}" if profile_path else None
            cast_html += (
                f'<div style="flex-shrink:0;" title="{name} as {character}">'
                + cast_card_html(name, character, profile_url_m, p1)
                + "</div>"
            )
        cast_html += "</div>"

        # Cast names list below for quick reference
        def _cast_pill(member: dict) -> str:
            _name = member.get("name", "")
            _char = member.get("character", "")
            _char_span = (
                '<span style="color:rgba(255,255,255,0.4);font-style:italic;"> as ' + _char + '</span>'
                if _char else ""
            )
            return (
                '<span style="background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.12);'
                'border-radius:99px;padding:4px 14px;color:#fff;font-size:0.78rem;font-weight:500;">'
                '<strong>' + _name + '</strong>' + _char_span + '</span>'
            )

        name_list_html = (
            '<div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:14px;">'
            + "".join(_cast_pill(m) for m in cast_list[:12])
            + "</div>"
        )

        st.markdown(
            glass_card_html(cast_html + name_list_html),
            unsafe_allow_html=True,
        )

        # ── Actor drill-down dropdown ──────────────────────
        actor_names   = [m.get("name", "") for m in cast_list[:12] if m.get("name")]
        selected_actor = st.selectbox(
            "🎬 Explore actor's filmography",
            ["— Select an actor —"] + actor_names,
            index=0,
        )
        if selected_actor != "— Select an actor —":
            st.markdown(
                f"<div class='section-label' style='margin-top:12px;'>"
                f"🎞️ More films featuring {selected_actor}</div>",
                unsafe_allow_html=True,
            )
            actor_data, actor_err = api_get_json("/tmdb/search",
                                                  params={"query": selected_actor})
            if not actor_err and actor_data:
                _, actor_cards = parse_tmdb_search_to_cards(actor_data, selected_actor, limit=12)
                if actor_cards:
                    poster_grid(actor_cards, cols=6,
                                key_prefix=f"actor_{selected_actor[:10].replace(' ','_')}")
                else:
                    st.info(f"No results for '{selected_actor}'.")
    else:
        st.markdown(
            glass_card_html(
                "<div style='color:rgba(255,255,255,0.4);text-align:center;padding:20px;'>"
                "Cast data is not available for this title.</div>"
            ),
            unsafe_allow_html=True,
        )

    st.divider()

    # ── SIMILAR MOVIES (TF-IDF + Genre) ───────────────────
    st.markdown("<div class='section-label'>Similar Titles</div>", unsafe_allow_html=True)
    st.markdown(
        f"<h3 style='margin-top:2px;'>🔎 Movies Like <em>{title}</em></h3>",
        unsafe_allow_html=True,
    )

    if title:
        bundle, err2 = api_get_json(
            "/movie/search",
            params={"query": title, "tfidf_top_n": 12, "genre_limit": 12},
        )
        if not err2 and bundle:
            st.markdown(
                "<div class='small-muted' style='margin-bottom:14px;'>Content similarity · TF-IDF engine</div>",
                unsafe_allow_html=True,
            )
            poster_grid(
                to_cards_from_tfidf_items(bundle.get("tfidf_recommendations")),
                cols=grid_cols,
                key_prefix="details_tfidf",
            )
            st.markdown("")
            st.markdown(
                "<div class='small-muted' style='margin-bottom:14px;'>Same genre universe</div>",
                unsafe_allow_html=True,
            )
            poster_grid(
                bundle.get("genre_recommendations", []),
                cols=grid_cols,
                key_prefix="details_genre",
            )
        else:
            genre_only, err3 = api_get_json(
                "/recommend/genre", params={"tmdb_id": tmdb_id, "limit": 18}
            )
            if not err3 and genre_only:
                poster_grid(genre_only, cols=grid_cols, key_prefix="details_genre_fallback")
            else:
                st.warning("No recommendations available right now.")
    else:
        st.warning("No title available to compute recommendations.")
