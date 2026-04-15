import requests
import streamlit as st
import json
from streamlit.components.v1 import html

# =============================
# CONFIG & INITIALIZATION
# =============================
API_BASE = "https://movie-rec-466x.onrender.com"
TMDB_IMG = "https://image.tmdb.org/t/p/w342"
TMDB_BACKDROP = "https://image.tmdb.org/t/p/original"

st.set_page_config(
    page_title="CineVault",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- UTILS ---
def sync_wishlist_to_localstorage():
    wishlist_data = json.dumps(st.session_state.wishlist)
    js_code = f"<script>localStorage.setItem('movie_wishlist', JSON.stringify({wishlist_data}));</script>"
    html(js_code, height=0)

def scroll_to_top():
    js_scroll = "<script>window.parent.document.querySelector('.main').scrollTo(0,0);</script>"
    html(js_scroll, height=0)

# Initialize Session State
if "view" not in st.session_state: st.session_state.view = "home"
if "prev_view" not in st.session_state: st.session_state.prev_view = "home"
if "selected_tmdb_id" not in st.session_state: st.session_state.selected_tmdb_id = None
if "search_results" not in st.session_state: st.session_state.search_results = None
if "wishlist" not in st.session_state: st.session_state.wishlist = []

# =============================
# CINEMA NOIR UI — CSS
# =============================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Outfit:wght@300;400;500;600;700&display=swap');

:root {
    --bg:        #07090e;
    --surface:   #111622;
    --border:    rgba(255,255,255,0.07);
    --gold:      #f5c518;
    --text:      #dde1ea;
    --text-sub:  #6b7588;
    --radius:    10px;
}

.stApp {
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'Outfit', sans-serif !important;
}

header, [data-testid="stHeader"] { display: none !important; }

/* Grid and Card Alignment */
.movie-card {
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    height: 100%;
}

/* Force buttons to equal height and alignment */
.stButton > button {
    width: 100% !important;
    height: 40px !important;
    font-size: 0.7rem !important;
    margin-top: 5px !important;
    border-radius: 6px !important;
}

/* Background Wallpaper Detail View */
.wallpaper-overlay {
    position: fixed;
    top: 0; left: 0; width: 100vw; height: 100vh;
    background-size: cover;
    background-position: center;
    filter: brightness(0.15) blur(10px);
    z-index: -1;
}

/* Vertical Scrollbar for Categories */
.category-container {
    max-height: 600px;
    overflow-y: auto;
    padding-right: 15px;
    margin-bottom: 30px;
}

::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-thumb { background: var(--gold); border-radius: 10px; }

.cv-nav {
    position: sticky; top: 0; z-index: 999;
    display: flex; align-items: center; gap: 1.5rem;
    padding: 15px 0;
    background: var(--bg);
    border-bottom: 1px solid rgba(245,197,24,0.1);
}

.cv-logo { font-family: 'Bebas Neue'; font-size: 2rem; color: var(--gold); letter-spacing: 3px; }
.cv-sec { font-family: 'Bebas Neue'; font-size: 1.4rem; color: var(--text); margin: 25px 0 10px 0; border-left: 4px solid var(--gold); padding-left: 10px; }

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
# UI COMPONENTS
# =============================
def _render_card(m, key):
    tmdb_id = m.get("tmdb_id")
    poster = m.get("poster_url") or "https://via.placeholder.com/342x513/111622/f5c518?text=NO+IMAGE"
    
    st.image(poster, use_column_width=True)
    st.markdown(f"<div style='font-size:0.85rem; font-weight:600; height:40px; overflow:hidden;'>{m.get('title')}</div>", unsafe_allow_html=True)
    
    if st.button("▶ OPEN", key=f"o_{key}"):
        navigate_to("details", tmdb_id)
    
    is_saved = any(x.get("tmdb_id") == tmdb_id for x in st.session_state.wishlist)
    wl_label = "❌ REMOVE" if is_saved else "＋ LIST"
    if st.button(wl_label, key=f"w_{key}"):
        if is_saved:
            st.session_state.wishlist = [x for x in st.session_state.wishlist if x.get("tmdb_id") != tmdb_id]
        else:
            st.session_state.wishlist.append(m)
        sync_wishlist_to_localstorage()
        st.rerun()

def render_movie_grid(movies, key_pfx):
    cols_count = 5
    for i in range(0, len(movies), cols_count):
        cols = st.columns(cols_count)
        for idx, col in enumerate(cols):
            if i + idx < len(movies):
                with col:
                    _render_card(movies[i+idx], f"{key_pfx}_{i+idx}")

# =============================
# TOP NAVBAR
# =============================
st.markdown("<div class='cv-nav'>", unsafe_allow_html=True)
n1, n2, n3, n4 = st.columns([1.2, 3, 1, 1], vertical_alignment="center")

with n1:
    st.markdown("<div class='cv-logo'>CINEVAULT</div>", unsafe_allow_html=True)

with n2:
    with st.form(key="search_form", clear_on_submit=True):
        sk1, sk2 = st.columns([4,1])
        with sk1:
            q = st.text_input("Search", placeholder="Search movies...", label_visibility="collapsed")
        with sk2:
            if st.form_submit_button("GO"):
                res, _ = api_get_json("/tmdb/search", params={"query": q})
                if res:
                    st.session_state.search_results = [{"tmdb_id": x.get("id"), "title": x.get("title"), "poster_url": f"{TMDB_IMG}{x.get('poster_path')}"} for x in res.get("results", []) if x.get("poster_path")]
                    st.session_state.view = "home"
                    st.rerun()

with n3:
    if st.button("📁 MY LIST"):
        navigate_to("wishlist_page")

with n4:
    if st.button("🏠 HOME"):
        # Reset Logic: Clear search and return to main home
        st.session_state.search_results = None
        st.session_state.selected_tmdb_id = None
        navigate_to("home")

st.markdown("</div>", unsafe_allow_html=True)

# =============================
# MAIN VIEW LOGIC
# =============================

# --- HOME VIEW ---
if st.session_state.view == "home":
    if st.session_state.search_results:
        st.markdown("<div class='cv-sec'>SEARCH RESULTS</div>", unsafe_allow_html=True)
        render_movie_grid(st.session_state.search_results, "search")
    else:
        for cat_key, label in [("trending", "TRENDING NOW"), ("popular", "POPULAR")]:
            st.markdown(f"<div class='cv-sec'>{label}</div>", unsafe_allow_html=True)
            data, _ = api_get_json("/home", params={"category": cat_key, "limit": 15})
            if data:
                st.markdown("<div class='category-container'>", unsafe_allow_html=True)
                render_movie_grid(data, cat_key)
                st.markdown("</div>", unsafe_allow_html=True)

# --- MY LIST PAGE ---
elif st.session_state.view == "wishlist_page":
    st.markdown("<div class='cv-sec'>MY LIST</div>", unsafe_allow_html=True)
    if not st.session_state.wishlist:
        st.info("Your list is empty. Add movies to see them here!")
    else:
        render_movie_grid(st.session_state.wishlist, "wishlist_page")

# --- DETAIL VIEW ---
elif st.session_state.view == "details":
    movie, _ = api_get_json(f"/movie/id/{st.session_state.selected_tmdb_id}")
    if movie:
        # Wallpaper Logic
        backdrop = movie.get("backdrop_path")
        if backdrop:
            st.markdown(f'<div class="wallpaper-overlay" style="background-image: url(\'{TMDB_BACKDROP}{backdrop}\');"></div>', unsafe_allow_html=True)
        
        c1, c2 = st.columns([1, 2.5])
        with c1:
            st.image(movie.get("poster_url"), use_column_width=True)
        with c2:
            st.title(movie.get("title"))
            st.write(movie.get("overview"))
            if st.button("← BACK"): navigate_to(st.session_state.prev_view)

        # Similar Movies - Persistent at bottom
        st.markdown("<div class='cv-sec'>SIMILAR MOVIES</div>", unsafe_allow_html=True)
        recs, _ = api_get_json("/movie/search", params={"query": movie.get("title"), "tfidf_top_n": 10})
        if recs:
            clean = [{"tmdb_id": r['tmdb']['tmdb_id'], "title": r['tmdb']['title'], "poster_url": r['tmdb']['poster_url']} for r in recs.get("tfidf_recommendations", []) if r.get('tmdb')]
            render_movie_grid(clean, "details_recs")
