import httpx
import asyncio
import streamlit as st
import json
from streamlit.components.v1 import html

# =============================
# CONFIG & INITIALIZATION
# =============================
API_BASE = "https://movie-rec-466x.onrender.com"
TMDB_IMG = "https://image.tmdb.org/t/p/w500"

st.set_page_config(
    page_title="MovieHub Pro", 
    page_icon="🎬", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- PERSISTENCE ENGINE (Browser Bridge) ---
def sync_wishlist_to_localstorage():
    """Pushes the current Python wishlist to the browser's LocalStorage"""
    wishlist_data = json.dumps(st.session_state.wishlist)
    js_code = f"""
    <script>
        localStorage.setItem('movie_wishlist', JSON.stringify({wishlist_data}));
    </script>
    """
    html(js_code, height=0)

# Initialize Session State
if "view" not in st.session_state: st.session_state.view = "home"
if "selected_tmdb_id" not in st.session_state: st.session_state.selected_tmdb_id = None
if "active_cat" not in st.session_state: st.session_state.active_cat = "popular"
if "search_results" not in st.session_state: st.session_state.search_results = None
if "wishlist" not in st.session_state: st.session_state.wishlist = []

# =============================
# PREMIUM UI & TYPOGRAPHY
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
    [data-testid="stSidebar"] { background-color: #0f172a; border-right: 1px solid #1e293b; }

    h1 { font-family: 'Clash Display', sans-serif; font-size: 2.8rem !important; font-weight: 600; color: #ffffff; margin-bottom: 0px; }
    h2 { font-family: 'Clash Display', sans-serif; font-size: 1.6rem !important; color: #38bdf8; margin: 0; }
    h3 { font-family: 'Clash Display', sans-serif; font-size: 1.3rem !important; margin-top: 2rem; color: #f1f5f9; border-left: 4px solid #38bdf8; padding-left: 12px; }

    .movie-title {
        font-weight: 700;
        font-size: 0.85rem;
        margin-top: 10px;
        color: #f1f5f9;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .card-meta-row {
        font-size: 0.65rem;
        color: #94a3b8;
        display: flex;
        justify-content: space-between;
        margin-bottom: 6px;
    }

    [data-testid="column"] [data-testid="stImage"] img {
        border-radius: 12px;
        height: 340px !important;
        object-fit: cover;
        transition: none !important;
    }

    .stButton > button {
        font-size: 0.65rem !important;
        font-weight: 700 !important;
        padding: 4px 8px !important;
        min-height: 28px !important;
        border-radius: 6px !important;
        background-color: #1e293b !important;
        color: #cbd5e1 !important;
        border: 1px solid #334155 !important;
        text-transform: uppercase;
    }
    
    .stButton > button:hover {
        border-color: #38bdf8 !important;
        color: #38bdf8 !important;
    }

    .genre-pill {
        display: inline-block;
        background: rgba(56, 189, 248, 0.1);
        color: #38bdf8;
        padding: 5px 12px;
        border-radius: 6px;
        font-size: 0.85rem;
        margin-right: 8px;
        margin-top: 8px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# =============================
# ASYNC API ENGINE
# =============================
async def fetch_data(path: str, params: dict = None):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{API_BASE}{path}", params=params, timeout=15.0)
            return response.json(), None
        except Exception as e:
            return None, str(e)

def api_get_json(path: str, params: dict | None = None):
    return asyncio.run(fetch_data(path, params))

# =============================
# SHARED LOGIC FUNCTIONS
# =============================
def navigate_to_details(tmdb_id: int):
    st.session_state.view = "details"
    st.session_state.selected_tmdb_id = int(tmdb_id)

def clean_genres(raw_genres):
    if not raw_genres: return ["General"]
    return [g for g in raw_genres if isinstance(g, str) and not g.isdigit()]

def movie_card_grid(movies, key_prefix="grid"):
    if not movies: return
    
    cols = st.columns(5)
    for idx, m in enumerate(movies):
        with cols[idx % 5]:
            p_url = m.get("poster_url") or "https://via.placeholder.com/500x750/0b0f19/ffffff?text=No+Poster"
            st.image(p_url, use_column_width=True)
            
            title = m.get('title', 'Untitled')
            rating = m.get('vote_average', 'N/A')
            runtime = m.get('runtime', '--')
            release = m.get('release_date', '----')[:4]
            
            st.markdown(f"<div class='movie-title'>{title}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='card-meta-row'><span>⭐ {rating}</span><span>⏱️ {runtime}m</span><span>📅 {release}</span></div>", unsafe_allow_html=True)
            
            b1, b2 = st.columns(2)
            with b1:
                if st.button("OPEN", key=f"v_{key_prefix}_{m.get('tmdb_id')}_{idx}", use_container_width=True):
                    navigate_to_details(m.get("tmdb_id"))
                    st.rerun()
            with b2:
                # INSTANT ADD/REMOVE & PERSIST
                is_saved = any(item['tmdb_id'] == m.get('tmdb_id') for item in st.session_state.wishlist)
                label = "REMOVE" if is_saved else "➕ SAVE"
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
                processed.append({
                    "tmdb_id": t["tmdb_id"], "title": t.get("title"), "poster_url": t.get("poster_url"),
                    "vote_average": t.get("vote_average", "N/A"), "runtime": t.get("runtime", "--"),
                    "release_date": t.get("release_date", "----"), "genres": t.get("genres", [])
                })
        if processed:
            st.markdown("### 🎬 SIMILAR MOVIES YOU MAY LIKE")
            movie_card_grid(processed, key_pfx)

# =============================
# TOP NAVIGATION
# =============================
with st.container():
    c1, c2, c3 = st.columns([1.2, 3, 0.8], vertical_alignment="center")
    with c1:
        st.markdown("<h2>🎬 MoviesHub</h2>", unsafe_allow_html=True)
    with c2:
        with st.form(key="nav_search", clear_on_submit=True):
            s1, s2 = st.columns([4, 1])
            with s1:
                q = st.text_input("Search", placeholder="Search films...", label_visibility="collapsed")
            with s2:
                if st.form_submit_button("SEARCH", use_container_width=True) and q:
                    res, _ = api_get_json("/tmdb/search", params={"query": q})
                    if res:
                        st.session_state.search_results = [{
                                "tmdb_id": x.get("id"), "title": x.get("title"), 
                                "poster_url": f"{TMDB_IMG}{x.get('poster_path')}",
                                "vote_average": x.get("vote_average"), "release_date": x.get("release_date", "")
                            } for x in res.get("results", []) if x.get('poster_path')]
                        st.session_state.view = "home"
                        st.rerun()
    with c3: # FIXED SYNTAX HERE
        if st.button("🏠 HOME", use_container_width=True):
            st.session_state.view = "home"
            st.session_state.search_results = None
            st.rerun()

st.divider()

# =============================
# SIDEBAR
# =============================
with st.sidebar:
    st.markdown("### 📌 PERSISTENT WATCHLIST")
    if not st.session_state.wishlist:
        st.caption("Wishlist survives refreshes.")
    else:
        wish_map = {}
        for item in st.session_state.wishlist:
            g_names = clean_genres(item.get('genres', []))
            primary = g_names[0] if g_names else "Misc"
            if primary not in wish_map: wish_map[primary] = []
            wish_map[primary].append(item)
            
        for genre, items in wish_map.items():
            with st.expander(f"📁 {genre.upper()}"):
                for i, w in enumerate(items):
                    if st.button(w.get('title'), key=f"sw_{w.get('tmdb_id')}_{i}", use_container_width=True):
                        navigate_to_details(w.get('tmdb_id'))
                        st.rerun()

# =============================
# VIEW CONTROLLER
# =============================
if st.session_state.view == "home":
    if st.session_state.search_results:
        st.markdown("### Search Results")
        movie_card_grid(st.session_state.search_results, "search_res")
        if st.session_state.search_results:
            st.markdown("<br>", unsafe_allow_html=True)
            fetch_and_show_recs(st.session_state.search_results[0]['title'], "home_search_rec")
    else:
        st.markdown("### TRENDING MOVIES")
        data, _ = api_get_json("/home", params={"category": st.session_state.active_cat, "limit": 20})
        if data: 
            movie_card_grid(data, "home_grid")
            st.markdown("<br>", unsafe_allow_html=True)
            fetch_and_show_recs(data[0]['title'], "home_trending_rec")

else:
    # DETAIL VIEW
    m_id = st.session_state.selected_tmdb_id
    movie, _ = api_get_json(f"/movie/id/{m_id}")
    
    if movie:
        col_l, col_r = st.columns([1, 2.5])
        with col_l: st.image(movie.get("poster_url", ""), use_column_width=True)
        with col_r:
            st.markdown(f"<h1>{movie.get('title')}</h1>", unsafe_allow_html=True)
            g_list = clean_genres(movie.get("genres", []))
            st.markdown("".join([f"<span class='genre-pill'>{g}</span>" for g in g_list]), unsafe_allow_html=True)
            st.markdown(f"<p style='margin-top:20px; color:#cbd5e1; font-size:1.1rem; line-height:1.7;'>{movie.get('overview')}</p>", unsafe_allow_html=True)
            
            st.markdown("---")
            if st.button("➕ ADD TO MY LIST", use_container_width=True):
                if not any(item['tmdb_id'] == movie.get('tmdb_id') for item in st.session_state.wishlist):
                    st.session_state.wishlist.append(movie)
                    sync_wishlist_to_localstorage()
                    st.success(f"Added {movie.get('title')} to My List!")
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        fetch_and_show_recs(movie.get("title", ""), "detail_view_rec")

st.markdown("<br><br>", unsafe_allow_html=True)
