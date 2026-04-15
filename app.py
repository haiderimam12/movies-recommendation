import requests
import streamlit as st
import json
from streamlit.components.v1 import html

# =============================
# CONFIG & INITIALIZATION
# =============================
API_BASE = "https://movie-rec-466x.onrender.com"
# Changed to w342 for significantly faster loading times
TMDB_IMG = "https://image.tmdb.org/t/p/w342" 

st.set_page_config(
    page_title="MovieHub Pro", 
    page_icon="🎬", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- PERFORMANCE & NAVIGATION UTILS ---
def sync_wishlist_to_localstorage():
    """Pushes wishlist to browser storage"""
    wishlist_data = json.dumps(st.session_state.wishlist)
    js_code = f"<script>localStorage.setItem('movie_wishlist', JSON.stringify({wishlist_data}));</script>"
    html(js_code, height=0)

def scroll_to_top():
    """Forces browser to snap to top instantly"""
    js_scroll = "<script>window.parent.document.querySelector('.main').scrollTo(0,0);</script>"
    html(js_scroll, height=0)

# Initialize Session State
if "view" not in st.session_state: st.session_state.view = "home"
if "prev_view" not in st.session_state: st.session_state.prev_view = "home"
if "selected_tmdb_id" not in st.session_state: st.session_state.selected_tmdb_id = None
if "active_cat" not in st.session_state: st.session_state.active_cat = "popular"
if "search_results" not in st.session_state: st.session_state.search_results = None
if "wishlist" not in st.session_state: st.session_state.wishlist = []

# =============================
# MOBILE-FIRST FAST-LOAD UI (CSS)
# =============================
st.markdown("""
<style>
    @import url('https://api.fontshare.com/v2/css?f[]=satoshi@400,700&f[]=clash-display@600&display=swap');

    .stApp { background-color: #0b0f19; color: #f8fafc; font-family: 'Satoshi', sans-serif; }
    header, [data-testid="stHeader"] { display: none; }
    
    /* FAST LOAD & RESPONSIVE GRID */
    [data-testid="column"] [data-testid="stImage"] img {
        border-radius: 10px;
        object-fit: cover;
        background: #1e293b; /* Placeholder color while loading */
        transition: opacity 0.2s ease-in;
    }

    @media (max-width: 768px) {
        [data-testid="column"] {
            width: 48% !important;
            flex: 1 1 48% !important;
            min-width: 48% !important;
        }
        [data-testid="column"] [data-testid="stImage"] img {
            height: 200px !important;
        }
        .movie-title { font-size: 0.75rem !important; }
        h1 { font-size: 1.7rem !important; }
    }

    @media (min-width: 769px) {
        [data-testid="column"] [data-testid="stImage"] img {
            height: 330px !important;
        }
    }

    .movie-title { font-weight: 700; color: #f1f5f9; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; margin-top: 5px; }
    .card-meta { font-size: 0.65rem; color: #94a3b8; display: flex; justify-content: space-between; }
    
    .stButton > button {
        font-size: 0.6rem !important;
        font-weight: 700 !important;
        background-color: #1e293b !important;
        color: #38bdf8 !important;
        border: 1px solid #334155 !important;
        border-radius: 6px !important;
    }
</style>
""", unsafe_allow_html=True)

# =============================
# BACKEND CORE
# =============================
def api_get_json(path: str, params: dict | None = None):
    try:
        response = requests.get(f"{API_BASE}{path}", params=params, timeout=10.0)
        return response.json(), None
    except Exception as e:
        return None, str(e)

def navigate_to(view_name, tmdb_id=None):
    st.session_state.prev_view = st.session_state.view
    st.session_state.view = view_name
    if tmdb_id: st.session_state.selected_tmdb_id = int(tmdb_id)
    scroll_to_top()
    st.rerun()

# =============================
# REUSABLE COMPONENTS
# =============================
def movie_card_grid(movies, key_prefix="grid"):
    if not movies: return
    cols = st.columns(5)
    for idx, m in enumerate(movies):
        with cols[idx % 5]:
            p_url = m.get("poster_url") or "https://via.placeholder.com/342x513/0b0f19/ffffff?text=No+Image"
            st.image(p_url, use_column_width=True)
            
            st.markdown(f"<div class='movie-title'>{m.get('title', 'Untitled')}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='card-meta'><span>⭐ {m.get('vote_average', 'N/A')}</span></div>", unsafe_allow_html=True)
            
            b1, b2 = st.columns(2)
            with b1:
                if st.button("OPEN", key=f"v_{key_prefix}_{idx}_{m.get('tmdb_id')}", use_container_width=True):
                    navigate_to("details", m.get("tmdb_id"))
            with b2:
                is_saved = any(item['tmdb_id'] == m.get('tmdb_id') for item in st.session_state.wishlist)
                label = "❌" if is_saved else "➕"
                if st.button(label, key=f"w_{key_prefix}_{idx}_{m.get('tmdb_id')}", use_container_width=True):
                    if is_saved:
                        st.session_state.wishlist = [x for x in st.session_state.wishlist if x['tmdb_id'] != m.get('tmdb_id')]
                    else:
                        st.session_state.wishlist.append(m)
                    sync_wishlist_to_localstorage()
                    st.rerun()

def show_recommendations(title, key_pfx):
    recs, _ = api_get_json("/movie/search", params={"query": title, "tfidf_top_n": 10})
    if recs:
        clean = []
        for r in recs.get("tfidf_recommendations", []):
            t = r.get("tmdb") or {}
            if t.get("tmdb_id"):
                clean.append({"tmdb_id": t["tmdb_id"], "title": t.get("title"), "poster_url": t.get("poster_url"), "vote_average": t.get("vote_average")})
        if clean:
            st.markdown("### 🎬 SIMILAR MOVIES")
            movie_card_grid(clean, key_pfx)

# =============================
# HEADER & NAVIGATION
# =============================
with st.container():
    h1, h2, h3, h4 = st.columns([1, 3, 0.8, 0.6], vertical_alignment="center")
    with h1: st.markdown("<h2>🎬 Hub</h2>", unsafe_allow_html=True)
    with h2:
        with st.form(key="search_nav", clear_on_submit=True):
            s1, s2 = st.columns([4, 1])
            with s1: q = st.text_input("Search", placeholder="Quick search...", label_visibility="collapsed")
            with s2:
                if st.form_submit_button("GO") and q:
                    res, _ = api_get_json("/tmdb/search", params={"query": q})
                    if res:
                        st.session_state.search_results = [{"tmdb_id": x.get("id"), "title": x.get("title"), "poster_url": f"{TMDB_IMG}{x.get('poster_path')}", "vote_average": x.get("vote_average")} for x in res.get("results", []) if x.get('poster_path')]
                        st.session_state.view = "home"
                        st.rerun()
    with h3:
        if st.button("📁 LIST", use_container_width=True): navigate_to("wishlist_page")
    with h4:
        if st.button("🏠", use_container_width=True):
            st.session_state.search_results = None
            navigate_to("home")

st.divider()

# =============================
# MAIN VIEW LOGIC
# =============================
if st.session_state.view == "home":
    if st.session_state.search_results:
        st.markdown("### SEARCH RESULTS")
        movie_card_grid(st.session_state.search_results, "search")
    else:
        st.markdown("### TRENDING NOW")
        data, _ = api_get_json("/home", params={"category": st.session_state.active_cat, "limit": 20})
        if data: movie_card_grid(data, "home")

elif st.session_state.view == "wishlist_page":
    st.markdown("<h1>📁 MY WISHLIST PANEL</h1>", unsafe_allow_html=True)
    if not st.session_state.wishlist:
        st.info("Your list is empty.")
    else:
        movie_card_grid(st.session_state.wishlist, "full_wish")

else:
    # DETAIL VIEW
    movie, _ = api_get_json(f"/movie/id/{st.session_state.selected_tmdb_id}")
    if movie:
        if st.button("← BACK"): navigate_to(st.session_state.prev_view)
        
        dl, dr = st.columns([1, 2.5])
        with dl: st.image(movie.get("poster_url", ""), use_column_width=True)
        with dr:
            st.markdown(f"<h1>{movie.get('title')}</h1>", unsafe_allow_html=True)
            st.write(movie.get("overview"))
            if st.button("➕ ADD TO LIST", use_container_width=True):
                if not any(item['tmdb_id'] == movie.get('tmdb_id') for item in st.session_state.wishlist):
                    st.session_state.wishlist.append(movie)
                    sync_wishlist_to_localstorage()
                    st.toast("Saved to List!")

        st.markdown("<br>", unsafe_allow_html=True)
        show_recommendations(movie.get("title", ""), "detail")

st.markdown("<br><br>", unsafe_allow_html=True)
