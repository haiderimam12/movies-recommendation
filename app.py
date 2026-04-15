import requests
import streamlit as st
import json
from streamlit.components.v1 import html

# =============================
# CONFIG & INITIALIZATION
# =============================
API_BASE = "https://movie-rec-466x.onrender.com"
TMDB_IMG = "https://image.tmdb.org/p/w500"

st.set_page_config(
    page_title="MovieHub Pro", 
    page_icon="🎬", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- UTILITY: SYNC & SCROLL ---
def sync_wishlist_to_localstorage():
    """Pushes current Python wishlist to Browser LocalStorage"""
    wishlist_data = json.dumps(st.session_state.wishlist)
    js_code = f"""
    <script>
        localStorage.setItem('movie_wishlist', JSON.stringify({wishlist_data}));
    </script>
    """
    html(js_code, height=0)

def scroll_to_top():
    """Forces browser to scroll to top on navigation"""
    js_scroll = """
    <script>
        window.parent.document.querySelector('.main').scrollTo(0,0);
    </script>
    """
    html(js_scroll, height=0)

# Initialize Session State
if "view" not in st.session_state: st.session_state.view = "home"
if "prev_view" not in st.session_state: st.session_state.prev_view = "home"
if "selected_tmdb_id" not in st.session_state: st.session_state.selected_tmdb_id = None
if "active_cat" not in st.session_state: st.session_state.active_cat = "popular"
if "search_results" not in st.session_state: st.session_state.search_results = None
if "wishlist" not in st.session_state: st.session_state.wishlist = []
if "show_sidebar" not in st.session_state: st.session_state.show_sidebar = True

# =============================
# MOBILE-OPTIMIZED UI (CSS)
# =============================
st.markdown("""
<style>
    @import url('https://api.fontshare.com/v2/css?f[]=satoshi@400,700&f[]=clash-display@600&display=swap');

    .stApp {
        background-color: #0b0f19;
        color: #f8fafc;
        font-family: 'Satoshi', sans-serif;
    }

    header, [data-testid="stHeader"] { display: none; }
    
    /* MOBILE VS DESKTOP RESPONSIVENESS */
    @media (max-width: 768px) {
        [data-testid="column"] {
            width: 48% !important; /* Two cards side-by-side on mobile */
            flex: 1 1 48% !important;
            min-width: 48% !important;
        }
        [data-testid="column"] [data-testid="stImage"] img {
            height: 180px !important; /* Smaller cards for mobile */
            border-radius: 8px;
        }
        .movie-title { font-size: 0.7rem !important; margin-top: 5px; }
        .card-meta-row { font-size: 0.5rem !important; }
        h1 { font-size: 1.6rem !important; }
        
        [data-testid="stSidebar"] {
            width: 85% !important;
            z-index: 1000001;
        }
    }

    @media (min-width: 769px) {
        [data-testid="column"] [data-testid="stImage"] img {
            height: 320px !important;
            border-radius: 12px;
        }
    }

    [data-testid="stSidebar"] { 
        background-color: #0f172a; 
        border-right: 1px solid #1e293b;
    }

    h1 { font-family: 'Clash Display', sans-serif; font-size: 2.5rem !important; font-weight: 600; color: #ffffff; }
    h2 { font-family: 'Clash Display', sans-serif; font-size: 1.4rem !important; color: #38bdf8; margin: 0; }
    
    .movie-title {
        font-weight: 700;
        font-size: 0.85rem;
        color: #f1f5f9;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .card-meta-row {
        font-size: 0.6rem;
        color: #94a3b8;
        display: flex;
        justify-content: space-between;
    }

    .stButton > button {
        font-size: 0.6rem !important;
        font-weight: 700 !important;
        padding: 2px 6px !important;
        min-height: 24px !important;
        border-radius: 4px !important;
        background-color: #1e293b !important;
        color: #cbd5e1 !important;
        border: 1px solid #334155 !important;
    }
    
    .genre-pill {
        display: inline-block;
        background: rgba(56, 189, 248, 0.1);
        color: #38bdf8;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        margin-right: 5px;
    }
</style>
""", unsafe_allow_html=True)

# =============================
# BACKEND API ENGINE
# =============================
def api_get_json(path: str, params: dict | None = None):
    try:
        response = requests.get(f"{API_BASE}{path}", params=params, timeout=15.0)
        return response.json(), None
    except Exception as e:
        return None, str(e)

# =============================
# LOGIC FUNCTIONS
# =============================
def navigate_to(view_name, tmdb_id=None):
    st.session_state.prev_view = st.session_state.view
    st.session_state.view = view_name
    if tmdb_id:
        st.session_state.selected_tmdb_id = int(tmdb_id)
    scroll_to_top()
    st.rerun()

def movie_card_grid(movies, key_prefix="grid"):
    if not movies: return
    cols = st.columns(5)
    for idx, m in enumerate(movies):
        with cols[idx % 5]:
            p_url = m.get("poster_url") or "https://via.placeholder.com/500x750/0b0f19/ffffff?text=No+Poster"
            st.image(p_url, use_column_width=True)
            
            title = m.get('title', 'Untitled')
            rating = m.get('vote_average', 'N.A')
            
            st.markdown(f"<div class='movie-title'>{title}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='card-meta-row'><span>⭐ {rating}</span></div>", unsafe_allow_html=True)
            
            b1, b2 = st.columns(2)
            with b1:
                if st.button("OPEN", key=f"v_{key_prefix}_{m.get('tmdb_id')}_{idx}", use_container_width=True):
                    navigate_to("details", m.get("tmdb_id"))
            with b2:
                is_saved = any(item['tmdb_id'] == m.get('tmdb_id') for item in st.session_state.wishlist)
                label = "❌" if is_saved else "➕"
                if st.button(label, key=f"w_{key_prefix}_{m.get('tmdb_id')}_{idx}", use_container_width=True):
                    if is_saved:
                        st.session_state.wishlist = [x for x in st.session_state.wishlist if x['tmdb_id'] != m.get('tmdb_id')]
                    else:
                        st.session_state.wishlist.append(m)
                    sync_wishlist_to_localstorage()
                    st.rerun()

def fetch_and_show_recs(movie_title, key_pfx):
    recs, _ = api_get_json("/movie/search", params={"query": movie_title, "tfidf_top_n": 10})
    if recs:
        processed = []
        for r in recs.get("tfidf_recommendations", []):
            t = r.get("tmdb") or {}
            if t.get("tmdb_id"):
                processed.append({"tmdb_id": t["tmdb_id"], "title": t.get("title"), "poster_url": t.get("poster_url"), "vote_average": t.get("vote_average", "N/A")})
        if processed:
            st.markdown("### 🎬 SIMILAR MOVIES")
            movie_card_grid(processed, key_pfx)

# =============================
# TOP NAVIGATION
# =============================
with st.container():
    c1, c2, c3, c4 = st.columns([1, 3, 0.8, 0.8], vertical_alignment="center")
    with c1:
        st.markdown("<h2>🎬 Hub</h2>", unsafe_allow_html=True)
    with c2:
        with st.form(key="search_fm", clear_on_submit=True):
            s1, s2 = st.columns([4, 1])
            with s1: q = st.text_input("Search", placeholder="Movies...", label_visibility="collapsed")
            with s2: 
                if st.form_submit_button("GO") and q:
                    res, _ = api_get_json("/tmdb/search", params={"query": q})
                    if res:
                        st.session_state.search_results = [{"tmdb_id": x.get("id"), "title": x.get("title"), "poster_url": f"{TMDB_IMG}{x.get('poster_path')}", "vote_average": x.get("vote_average")} for x in res.get("results", []) if x.get('poster_path')]
                        st.session_state.view = "home"
                        st.rerun()
    with c3:
        if st.button("📁 LIST", use_container_width=True):
            navigate_to("wishlist_page")
    with c4:
        if st.button("🏠", use_container_width=True):
            st.session_state.view = "home"
            st.session_state.search_results = None
            navigate_to("home")

st.divider()

# =============================
# SIDEBAR (QUICK WATCHLIST)
# =============================
with st.sidebar:
    st.markdown("### 📌 QUICK LIST")
    if not st.session_state.wishlist:
        st.caption("Empty")
    else:
        for i, w in enumerate(st.session_state.wishlist[-5:]): # Show last 5
            if st.button(f"🎥 {w.get('title')[:15]}...", key=f"side_{i}", use_container_width=True):
                navigate_to("details", w.get('tmdb_id'))
    
    st.divider()
    if st.button("OPEN FULL PANEL", use_container_width=True):
        navigate_to("wishlist_page")

# =============================
# VIEW CONTROLLER
# =============================
if st.session_state.view == "home":
    if st.session_state.search_results:
        st.markdown("### SEARCH RESULTS")
        movie_card_grid(st.session_state.search_results, "search")
    else:
        st.markdown("### TRENDING")
        data, _ = api_get_json("/home", params={"category": st.session_state.active_cat, "limit": 20})
        if data: movie_card_grid(data, "home")

elif st.session_state.view == "wishlist_page":
    st.markdown("<h1>📁 YOUR WISHLIST PANEL</h1>", unsafe_allow_html=True)
    if not st.session_state.wishlist:
        st.info("Your wishlist is currently empty. Add movies to see them here!")
    else:
        movie_card_grid(st.session_state.wishlist, "full_wishlist")

else:
    # DETAIL VIEW
    m_id = st.session_state.selected_tmdb_id
    movie, _ = api_get_json(f"/movie/id/{m_id}")
    if movie:
        if st.button("← BACK"):
            st.session_state.view = st.session_state.prev_view
            navigate_to(st.session_state.prev_view)
            
        cl, cr = st.columns([1, 2.5])
        with cl: st.image(movie.get("poster_url", ""), use_column_width=True)
        with cr:
            st.markdown(f"<h1>{movie.get('title')}</h1>", unsafe_allow_html=True)
            st.markdown(f"<p style='color:#cbd5e1;'>{movie.get('overview')}</p>", unsafe_allow_html=True)
            if st.button("➕ SAVE TO LIST", use_container_width=True):
                if not any(item['tmdb_id'] == movie.get('tmdb_id') for item in st.session_state.wishlist):
                    st.session_state.wishlist.append(movie)
                    sync_wishlist_to_localstorage()
                    st.success("Saved!")

        st.markdown("<br>", unsafe_allow_html=True)
        fetch_and_show_recs(movie.get("title", ""), "detail")

st.markdown("<br><br>", unsafe_allow_html=True)
