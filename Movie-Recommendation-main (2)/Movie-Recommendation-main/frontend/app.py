
import streamlit as st
import requests
import time
import json
import os
from pathlib import Path

# ==================== Configuration ====================
API_BASE_URL = "http://localhost:8000/api"
CREDENTIALS_FILE = Path("user_credentials.json")

# Page configuration
st.set_page_config(
    page_title="Movie Recommendation System",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== Persistent Storage Helper Functions ====================
def load_saved_credentials():
    """Load saved username and password"""
    if CREDENTIALS_FILE.exists():
        try:
            with open(CREDENTIALS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_credentials(username, password):
    """Save username and password"""
    credentials = load_saved_credentials()
    credentials[username] = password
    with open(CREDENTIALS_FILE, 'w', encoding='utf-8') as f:
        json.dump(credentials, f, ensure_ascii=False, indent=2)

def get_saved_password(username):
    """Get saved password"""
    credentials = load_saved_credentials()
    return credentials.get(username, "")

# ==================== Initialize Session State ====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None
if "algorithm" not in st.session_state:
    st.session_state.algorithm = "user"
if "recommendations" not in st.session_state:
    st.session_state.recommendations = []
if "current_page" not in st.session_state:
    st.session_state.current_page = 1
if "user_ratings" not in st.session_state:
    st.session_state.user_ratings = {}
if "rating_pending" not in st.session_state:
    st.session_state.rating_pending = {}
if "remember_me" not in st.session_state:
    st.session_state.remember_me = False

# ==================== Helper Functions ====================
def call_api(method: str, endpoint: str, data=None, params=None):
    """Unified API call function"""
    url = f"{API_BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, params=params, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, timeout=10)
        else:
            return None, f"Unsupported request method: {method}"

        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"Request failed: {response.status_code} - {response.text}"
    except requests.exceptions.ConnectionError:
        return None, "Cannot connect to backend service. Please ensure backend is running (http://localhost:8000)"
    except Exception as e:
        return None, f"Request exception: {str(e)}"


def load_movies(page=1, size=20, keyword="", user_id=None):
    """Load movie list"""
    params = {"page": page, "size": size}
    if keyword:
        params["keyword"] = keyword
    if user_id:
        params["user_id"] = user_id
    return call_api("GET", "/movies", params=params)


def submit_rating(user_id, movie_id, rating):
    """Submit rating"""
    data = {"user_id": user_id, "movie_id": movie_id, "rating": rating}
    return call_api("POST", "/ratings", data=data)


def delete_rating(user_id, movie_id):
    """Delete rating"""
    return call_api("DELETE", f"/ratings/{user_id}/{movie_id}")


def get_user_ratings(user_id):
    """Get user's rating history"""
    return call_api("GET", f"/ratings/{user_id}")


def get_recommendations(user_id, algorithm, top_n=10):
    """Get recommendations"""
    params = {"user_id": user_id, "algorithm": algorithm, "top_n": top_n}
    return call_api("GET", "/recommend", params=params)


def refresh_cache():
    """Refresh algorithm cache"""
    return call_api("POST", "/recommend/refresh")


def login_user(username, password):
    """Execute login logic"""
    result, err = call_api("POST", "/user/login",
                           data={"username": username, "password": password})
    if result and result.get("code") == 200:
        st.session_state.logged_in = True
        st.session_state.user_id = result["user_id"]
        st.session_state.username = result["username"]
        st.session_state.recommendations = []
        st.session_state.rating_pending = {}
        
        ratings_result, _ = get_user_ratings(result["user_id"])
        if ratings_result:
            st.session_state.user_ratings = {
                r["movie_id"]: r["rating"] for r in ratings_result
            }
        else:
            st.session_state.user_ratings = {}
        
        st.rerun()
        return None
    else:
        return err or "Invalid username or password"


# ==================== Sidebar: User Login/Register ====================
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/movie-projector.png", width=80)
    st.title("🎬 Movie Recommendation System")
    st.markdown("---")

    if not st.session_state.logged_in:
        st.subheader("🔐 User Center")
        tab1, tab2 = st.tabs(["Login", "Register"])

        with tab1:
            saved_users = list(load_saved_credentials().keys())
            default_user = saved_users[0] if saved_users else ""
            
            login_username = st.text_input(
                "Username", 
                key="login_user", 
                placeholder="Enter username",
                value=default_user
            )
            
            saved_password = get_saved_password(login_username) if login_username else ""
            login_password = st.text_input(
                "Password", 
                type="password", 
                key="login_pwd", 
                placeholder="Enter password",
                value=saved_password
            )
            
            remember_me = st.checkbox("Remember me", value=st.session_state.remember_me, key="remember_checkbox")
            
            if st.button("Login", type="primary", use_container_width=True, key="login_btn"):
                if login_username and login_password:
                    if remember_me:
                        save_credentials(login_username, login_password)
                    st.session_state.remember_me = remember_me
                    
                    err = login_user(login_username, login_password)
                    if err:
                        st.error(err)
                else:
                    st.warning("Please enter username and password")

        with tab2:
            reg_username = st.text_input("Username", key="reg_user", placeholder="Enter username")
            reg_password = st.text_input("Password", type="password", key="reg_pwd", placeholder="Enter password")
            reg_confirm = st.text_input("Confirm Password", type="password", key="reg_cfm", placeholder="Enter password again")

            if st.button("Register", type="primary", use_container_width=True, key="reg_btn"):
                if not reg_username or not reg_password:
                    st.warning("Please fill in all fields")
                elif reg_password != reg_confirm:
                    st.warning("Passwords do not match")
                else:
                    result, err = call_api("POST", "/user/register",
                                           data={"username": reg_username, "password": reg_password})
                    if result and result.get("code") == 200:
                        st.success("Registration successful! Please login")
                        if st.session_state.remember_me:
                            save_credentials(reg_username, reg_password)
                        st.rerun()
                    else:
                        st.error(err or "Registration failed. Username may already exist")

    else:
        st.success(f"👤 Current User: **{st.session_state.username}**")
        st.info(f"🆔 User ID: `{st.session_state.user_id}`")

        st.markdown("---")

        algorithm_options = {
            "user": "👥 User-based (Find similar users)",
            "item": "🎬 Item-based (Find similar movies)"
        }
        selected_algo = st.radio(
            "Recommendation Algorithm",
            options=["user", "item"],
            format_func=lambda x: algorithm_options[x],
            horizontal=True
        )
        st.session_state.algorithm = selected_algo

        st.markdown("---")

        if st.button("🚪 Logout", use_container_width=True, key="logout_btn"):
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.username = None
            st.session_state.recommendations = []
            st.session_state.user_ratings = {}
            st.session_state.rating_pending = {}
            st.rerun()


# ==================== Main Area ====================
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 50px 0;">
            <h1>🎬 Movie Recommendation System</h1>
            <p style="font-size: 18px; color: gray;">
                Personalized movie recommendations powered by collaborative filtering<br>
                Login to start your movie journey
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.info("💡 **Instructions**\n\n1. Login or register on the left\n2. Rate movies you've watched\n3. Select algorithm to get recommendations")

else:
    st.header(f"🎬 Welcome back, {st.session_state.username}!")

    left_col, right_col = st.columns([2, 1])

    with left_col:
        st.subheader("📋 Movie List")

        search_col, page_col = st.columns([3, 1])
        with search_col:
            search_keyword = st.text_input("🔍 Search Movies", placeholder="Enter movie title...", key="search_input", label_visibility="collapsed")
        with page_col:
            st.write("")
            page_control = st.columns([1, 2, 1])
            with page_control[0]:
                if st.button("◀", key="prev_page", use_container_width=True):
                    if st.session_state.current_page > 1:
                        st.session_state.current_page -= 1
                        st.rerun()
            with page_control[1]:
                st.markdown(f"<div style='text-align: center; padding-top: 8px;'>Page {st.session_state.current_page}</div>", unsafe_allow_html=True)
            with page_control[2]:
                if st.button("▶", key="next_page", use_container_width=True):
                    st.session_state.current_page += 1
                    st.rerun()

        with st.spinner("Loading movies..."):
            result, err = load_movies(
                page=st.session_state.current_page,
                size=20,
                keyword=search_keyword if search_keyword else "",
                user_id=st.session_state.user_id
            )

        if err:
            st.error(err)
        elif result and result.get("movies"):
            movies = result["movies"]
            total = result.get("total", 0)
            
            movies_with_rating_status = []
            for movie in movies:
                movie_id = movie['id']
                has_rated = movie_id in st.session_state.user_ratings
                movies_with_rating_status.append((movie, has_rated))
            
            movies_with_rating_status.sort(key=lambda x: not x[1])
            
            rated_count = sum(1 for _, rated in movies_with_rating_status if rated)
            st.caption(f"Total {total} movies, showing {len(movies)} ({rated_count} rated)")

            for movie, has_rated in movies_with_rating_status:
                with st.container(border=True):
                    col_a, col_b, col_c = st.columns([4, 1, 1])
                    with col_a:
                        st.write(f"**{movie['title']}**")
                        genres = movie.get('genres', 'Unknown')[:50]
                        st.caption(genres)
                        
                        movie_id = movie['id']
                        if movie_id in st.session_state.user_ratings:
                            current_rating = st.session_state.user_ratings[movie_id]
                            st.markdown(f"<span style='color: orange;'>⭐ Rated: {current_rating}/10</span>", unsafe_allow_html=True)
                    
                    with col_b:
                        existing_rating = st.session_state.user_ratings.get(movie['id'], 0)
                        pending_rating = st.session_state.rating_pending.get(movie['id'], 0)
                        
                        # Display rating UI
                        if existing_rating > 0:
                            # Already rated movie - show current rating
                            st.markdown(
                                f"<div style='padding: 8px 0; color: orange; font-weight: 500;'>"
                                f"⭐ {existing_rating}/10"
                                f"</div>",
                                unsafe_allow_html=True
                            )
                            selected_rating = st.selectbox(
                                "Change Rating",
                                options=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
                                key=f"rating_{movie['id']}",
                                label_visibility="collapsed",
                                index=int(existing_rating) - 1
                            )
                        else:
                            # Not yet rated movie
                            st.markdown(
                                "<div style='padding: 8px 0; color: #999; font-style: italic;'>"
                                "Not yet rated"
                                "</div>",
                                unsafe_allow_html=True
                            )
                            selected_rating = st.selectbox(
                                "Rate this movie",
                                options=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
                                key=f"rating_{movie['id']}",
                                label_visibility="collapsed",
                                index=None
                            )
                        
                        # Track rating changes
                        if selected_rating is not None and selected_rating != existing_rating:
                            st.session_state.rating_pending[movie['id']] = selected_rating
                        elif pending_rating == existing_rating:
                            # Clear pending if user reselected same rating
                            if movie['id'] in st.session_state.rating_pending:
                                del st.session_state.rating_pending[movie['id']]
                    
                    with col_c:
                        existing = st.session_state.user_ratings.get(movie['id'], 0)
                        pending = st.session_state.rating_pending.get(movie['id'], 0)
                        
                        # Show Submit button only if rating changed
                        if pending > 0 and pending != existing:
                            if st.button("✓ Submit", key=f"submit_{movie['id']}", use_container_width=True, type="primary"):
                                result, err = submit_rating(st.session_state.user_id, movie['id'], pending)
                                if result:
                                    st.session_state.user_ratings[movie['id']] = pending
                                    del st.session_state.rating_pending[movie['id']]
                                    refresh_cache()
                                    st.toast(f"✅ Rated {movie['title']} with {pending}/10")
                                    st.rerun()
                                else:
                                    st.error(err or "Failed to save rating")
                                    if movie['id'] in st.session_state.rating_pending:
                                        del st.session_state.rating_pending[movie['id']]
                        # Show Remove button if movie has been rated
                        elif existing > 0 and pending == 0:
                            if st.button("🗑️ Remove", key=f"remove_{movie['id']}", use_container_width=True, type="secondary"):
                                result, err = delete_rating(st.session_state.user_id, movie['id'])
                                if result:
                                    # Completely remove rating, back to "Not yet rated" state
                                    if movie['id'] in st.session_state.user_ratings:
                                        del st.session_state.user_ratings[movie['id']]
                                    if movie['id'] in st.session_state.rating_pending:
                                        del st.session_state.rating_pending[movie['id']]
                                    refresh_cache()
                                    st.toast(f"✅ Rating removed for {movie['title']}")
                                    st.rerun()
                                else:
                                    st.error(err or "Failed to remove rating")

        else:
            st.info("No movie data available. Please import dataset first.")

    with right_col:
        st.subheader("🎯 Recommended for You")

        top_n = st.selectbox("Number of Recommendations", options=[5, 10, 15, 20], index=1, label_visibility="collapsed")

        if st.button("🔍 Get Recommendations", type="primary", use_container_width=True, key="get_recommend_btn"):
            with st.spinner("Generating recommendations..."):
                result, err = get_recommendations(
                    st.session_state.user_id,
                    st.session_state.algorithm,
                    top_n
                )
                if result and result.get("code") == 200:
                    st.session_state.recommendations = result.get("recommendations", [])
                    if not st.session_state.recommendations:
                        st.info("No recommendations yet. Please rate some movies first.")
                else:
                    st.error(err or "Failed to get recommendations")
                    st.session_state.recommendations = []

        if st.session_state.recommendations:
            st.markdown("---")
            for idx, rec in enumerate(st.session_state.recommendations[:top_n], 1):
                with st.container(border=True):
                    st.write(f"**{idx}. {rec.get('title', 'Unknown Movie')}**")
                    
                    movie_id = rec.get('id') or rec.get('movie_id')
                    if movie_id and movie_id in st.session_state.user_ratings:
                        user_rating = st.session_state.user_ratings[movie_id]
                        st.write(f"⭐ Your Rating: **{user_rating}/10**")
                    
                    if rec.get('predicted_rating'):
                        st.write(f"🎯 Predicted: {rec['predicted_rating']} / 10")
                    
                    reason = rec.get('reason', '')
                    if not reason or 'N/A' in reason or 'default' in reason.lower():
                        if movie_id and movie_id in st.session_state.user_ratings:
                            reason = f"Based on your watch history"
                        else:
                            reason = f"Based on your preferences"
                    st.caption(f" {reason}")
        else:
            st.info("Click 'Get Recommendations' to see personalized recommendations")


# ==================== Footer ====================
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray; font-size: 12px;'>"
    "Movie Recommendation System | Powered by Collaborative Filtering | Data Source: MovieLens"
    "</div>",
    unsafe_allow_html=True
)