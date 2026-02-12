import streamlit as st
import requests
import google.generativeai as genai
import time

# --- 1. CẤU HÌNH GIAO DIỆN ---
st.set_page_config(
    page_title="T-HEXA Movies",
    page_icon="logo.jpg",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CSS CUSTOM ---
st.markdown("""
<style>
    .stApp { background-color: #f8f9fa; color: #212529; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e9ecef; }
    header, footer {visibility: hidden;}
    
    .brand-container { text-align: center; padding-bottom: 20px; margin-bottom: 20px; border-bottom: 1px dashed #dee2e6; }
    .brand-text { font-family: 'Helvetica Neue', sans-serif; font-size: 1.5rem; font-weight: 800; color: #574b90; margin-top: -10px; margin-bottom: 0px; letter-spacing: 1px; }
    .brand-slogan { font-size: 0.8rem; color: #888; font-style: italic; margin-top: 0px; }

    .stButton>button {
        background-color: #fff; color: #495057; border: 1px solid #dee2e6; border-radius: 8px; font-size: 0.85rem;
        height: auto !important; min-height: 3.2em; white-space: normal !important; padding: 5px 10px; line-height: 1.2;
        width: 100%; transition: all 0.2s; box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .stButton>button:hover {
        background-color: #574b90; color: white; border-color: #574b90; transform: translateY(-2px); box-shadow: 0 4px 8px rgba(87, 75, 144, 0.2);
    }
    
    .stTextInput>div>div>input { border-radius: 8px; padding-left: 10px; border: 1px solid #ced4da; background-color: #f1f3f5; }
    .stTextInput>div>div>input:focus { background-color: #fff; border-color: #574b90; box-shadow: 0 0 0 2px rgba(87, 75, 144, 0.2); }
    
    div[data-testid="stImage"] img { object-fit: contain; margin: 0 auto; }
    .movie-title { font-size: 0.95rem; font-weight: 700; margin-top: 8px; color: #333; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .movie-year { font-size: 0.75rem; color: #adb5bd; }
    
    /* CHAT STYLING */
    .stChatMessage { background-color: white; border-radius: 10px; border: 1px solid #eee; margin-bottom: 10px; }
    .movie-chat-card {
        border: 1px solid #eee; border-radius: 8px; padding: 10px; background: #fff; margin-top: 10px; text-align: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .movie-chat-card img { border-radius: 5px; height: 150px; object-fit: cover; }
    .movie-chat-title { font-size: 0.8rem; font-weight: bold; margin: 5px 0; height: 35px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# --- 3. DỮ LIỆU MENU ---
MENU_DATA = {
    "DANH_SACH": {
        "Phim Mới": "phim-moi-cap-nhat", "Phim Bộ": "phim-bo", "Phim Lẻ": "phim-le",
        "TV Shows": "tv-shows", "Hoạt Hình": "hoat-hinh", "Phim Vietsub": "phim-vietsub",
        "Thuyết Minh": "phim-thuyet-minh", "Lồng Tiếng": "phim-long-tieng",
        "Bộ Đang Chiếu": "phim-bo-dang-chieu", "Trọn Bộ": "phim-bo-hoan-thanh",
        "Sắp Chiếu": "phim-sap-chieu", "Subteam": "subteam", "Chiếu Rạp": "phim-chieu-rap"
    },
    "THE_LOAI": {
        "Hành Động": "hanh-dong", "Tình Cảm": "tinh-cam", "Hài Hước": "hai-huoc", "Cổ Trang": "co-trang",
        "Tâm Lý": "tam-ly", "Hình Sự": "hinh-su", "Chiến Tranh": "chien-tranh", "Thể Thao": "the-thao",
        "Võ Thuật": "vo-thuat", "Viễn Tưởng": "vien-tuong", "Phiêu Lưu": "phieu-luu", "Khoa Học": "khoa-hoc",
        "Kinh Dị": "kinh-di", "Âm Nhạc": "am-nhac", "Thần Thoại": "than-thoai", "Tài Liệu": "tai-lieu",
        "Gia Đình": "gia-dinh", "Chính Kịch": "chinh-kich", "Bí Ẩn": "bi-an", "Học Đường": "hoc-duong",
        "Kinh Điển": "kinh-dien"
    },
    "QUOC_GIA": {
        "Trung Quốc": "trung-quoc", "Hàn Quốc": "han-quoc", "Nhật Bản": "nhat-ban", "Thái Lan": "thai-lan",
        "Âu Mỹ": "au-my", "Đài Loan": "dai-loan", "Hồng Kông": "hong-kong", "Ấn Độ": "an-do",
        "Anh": "anh", "Pháp": "phap", "Việt Nam": "viet-nam"
    }
}

# --- 4. STATE ---
if 'view' not in st.session_state: st.session_state.view = 'home'
if 'current_movie' not in st.session_state: st.session_state.current_movie = None
if 'favorites' not in st.session_state: st.session_state.favorites = []
if 'page' not in st.session_state: st.session_state.page = 1
if 'filter_type' not in st.session_state: st.session_state.filter_type = 'moi-cap-nhat'
if 'filter_slug' not in st.session_state: st.session_state.filter_slug = ''
if 'search_query' not in st.session_state: st.session_state.search_query = ''
if 'current_title' not in st.session_state: st.session_state.current_title = "Phim Mới Cập Nhật"
if "chat_history" not in st.session_state: st.session_state.chat_history = [] 
if "api_key" not in st.session_state: st.session_state.api_key = ""
if "ai_model_name" not in st.session_state: st.session_state.ai_model_name = "gemini-pro"

# --- 5. LOGIC API ---
API_BASE = "https://ophim1.com"
CDN_FALLBACK = "https://img.ophim1.com/uploads/movies/"

@st.cache_data(ttl=600)
def fetch_data(url):
    try:
        r = requests.get(url, timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def get_movies(filter_type, slug='', page=1):
    if filter_type == 'tim-kiem': url = f"{API_BASE}/v1/api/tim-kiem?keyword={slug}"
    elif filter_type == 'danh-sach':
        if slug == 'phim-moi-cap-nhat': url = f"{API_BASE}/danh-sach/phim-moi-cap-nhat?page={page}"
        else: url = f"{API_BASE}/v1/api/danh-sach/{slug}?page={page}"
    elif filter_type == 'moi-cap-nhat': url = f"{API_BASE}/danh-sach/phim-moi-cap-nhat?page={page}"
    else: url = f"{API_BASE}/v1/api/{filter_type}/{slug}?page={page}"
    data = fetch_data(url)
    items, path_img = [], CDN_FALLBACK
    if data:
        if 'items' in data: items, path_img = data['items'], data.get('pathImage', CDN_FALLBACK)
        elif 'data' in data and 'items' in data['data']:
            items, domain = data['data']['items'], data['data'].get('APP_DOMAIN_CDN_IMAGE', 'https://img.ophim1.com')
            path_img = f"{domain}/uploads/movies/"
    return items, path_img

def get_movie_detail(slug): return fetch_data(f"{API_BASE}/phim/{slug}")

# --- 6. ACTIONS ---
def navigate(view, slug=None):
    st.session_state.view = view
    if slug: st.session_state.current_movie = slug

def set_filter(f_type, f_slug, title):
    st.session_state.filter_type = f_type
    st.session_state.filter_slug = f_slug
    st.session_state.current_title = title
    st.session_state.page = 1
    navigate('home')

def handle_search():
    if st.session_state.search_input:
        st.session_state.search_query = st.session_state.search_input
        st.session_state.current_title = f"Kết quả: {st.session_state.search_input}"
        st.session_state.filter_type = 'tim-kiem'
        st.session_state.filter_slug = st.session_state.search_input
        st.session_state.page = 1
        navigate('home')

# --- 7. SIDEBAR ---
with st.sidebar:
    st.markdown('<div class="brand-container">', unsafe_allow_html=True)
    try:
        c1, c2, c3 = st.columns([0.2, 0.6, 0.2])
        with c2: st.image("logo.jpg", use_container_width=True)
    except: pass
    st.markdown('<p class="brand-text">T-HEXA</p>', unsafe_allow_html=True)
    st.markdown('<p class="brand-slogan">Thế giới phim trong tầm tay</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.text_input("🔍", placeholder="Tìm tên phim...", key="search_input", on_change=handle_search, label_visibility="collapsed")
    st.write("") 

    if st.button("🏠 Trang Chủ", use_container_width=True): set_filter('moi-cap-nhat', '', "Phim Mới Cập Nhật")
    
    st.divider()
    if st.button("🤖 T-HEXA AI (Trợ Lý)", use_container_width=True):
        st.session_state.view = 'chat'
        st.rerun()
    st.divider()

    with st.expander("📂 Danh Sách", expanded=True):
        cols = st.columns(2)
        for i, (name, slug) in enumerate(MENU_DATA["DANH_SACH"].items()):
            if cols[i % 2].button(name, use_container_width=True): set_filter('danh-sach', slug, name)

    with st.expander("🎬 Thể Loại", expanded=False):
        cols = st.columns(2)
        for i, (name, slug) in enumerate(MENU_DATA["THE_LOAI"].items()):
            if cols[i % 2].button(name, use_container_width=True): set_filter('the-loai', slug, f"Thể Loại: {name}")

    with st.expander("🌍 Quốc Gia", expanded=False):
        cols = st.columns(2)
        for i, (name, slug) in enumerate(MENU_DATA["QUOC_GIA"].items()):
            if cols[i % 2].button(name, use_container_width=True): set_filter('quoc-gia', slug, f"Quốc Gia: {name}")
    
    if st.session_state.favorites:
        st.divider()
        st.caption("Đã thích ❤️")
        for m in st.session_state.favorites[:5]:
            if st.button(f"🎬 {m['name']}", key=f"fav_{m['slug']}"): navigate('watch', m['slug'])

    st.divider()
    with st.expander("⚙️ Cài đặt AI", expanded=True):
        api_key_input = st.text_input("🔑 Nhập Google API Key:", value=st.session_state.api_key, type="password")
        if api_key_input:
            st.session_state.api_key = api_key_input

# --- 8. MAIN CONTENT ---

# === VIEW: CHAT AI PRO (EMBEDDED MOVIES) ===
if st.session_state.view == 'chat':
    st.title("🤖 T-HEXA AI - Trợ Lý Điện Ảnh")
    st.caption("Trò chuyện, tư vấn và mở phim ngay tại đây!")

    model = None
    if st.session_state.api_key:
        try:
            genai.configure(api_key=st.session_state.api_key)
            found_model = False
            try:
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        if 'flash' in m.name: st.session_state.ai_model_name = m.name; found_model = True; break
                        elif 'pro' in m.name and not found_model: st.session_state.ai_model_name = m.name; found_model = True
                if not found_model: st.session_state.ai_model_name = 'gemini-pro'
            except: st.session_state.ai_model_name = 'gemini-pro'
            model = genai.GenerativeModel(st.session_state.ai_model_name)
        except Exception as e:
            st.error(f"Lỗi API Key: {e}")
    else:
        st.warning("⚠️ Vui lòng nhập API Key ở cột trái.")

    if not st.session_state.chat_history:
        st.session_state.chat_history.append({"role": "assistant", "content": "Chào bạn! Mình có thể giúp gì? (Tìm phim, review, mở phim...)", "type": "text"})
        
    # HIỂN THỊ LỊCH SỬ CHAT (XỬ LÝ CẢ TEXT VÀ THẺ PHIM)
    for idx, message in enumerate(st.session_state.chat_history):
        with st.chat_message(message["role"]):
            if message.get("type") == "text":
                st.markdown(message["content"])
            elif message.get("type") == "movie_list":
                # Render danh sách phim ngang
                st.markdown(message["content"]) # Text dẫn dắt
                movies = message["data"]
                path_img = message["path_img"]
                
                cols = st.columns(4) # 4 phim 1 hàng
                for i, m in enumerate(movies[:4]): # Chỉ hiện tối đa 4 phim để đỡ rối
                    with cols[i]:
                        img_url = m['thumb_url'] if m['thumb_url'].startswith('http') else f"{path_img}{m['thumb_url']}"
                        st.markdown(f"""
                        <div class="movie-chat-card">
                            <img src="{img_url}" width="100%">
                            <div class="movie-chat-title">{m['name']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        if st.button("Xem ngay", key=f"chat_btn_{idx}_{m['_id']}"):
                            navigate('watch', m['slug'])
                            st.rerun()

    if prompt := st.chat_input("Hỏi AI..."):
        if not model:
            st.error("Chưa có API Key!")
        else:
            st.session_state.chat_history.append({"role": "user", "content": prompt, "type": "text"})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("AI đang trả lời..."):
                    try:
                        # SYSTEM PROMPT: CHẶT CHẼ HƠN ĐỂ TRÁNH LOOP
                        SYSTEM_PROMPT = """Bạn là T-HEXA AI.
                        Nhiệm vụ:
                        1. Nếu user yêu cầu "mở phim", "tìm phim" [Tên Phim], hãy trả lời theo định dạng JSON:
                           {"action": "search", "keyword": "Tên Phim", "reply": "Ok, đây là kết quả cho [Tên Phim]:"}
                        
                        2. Nếu user CHỈ chào hỏi, hoặc hỏi review, nội dung: HÃY TRẢ LỜI BÌNH THƯỜNG (Text), KHÔNG dùng định dạng JSON.
                        
                        3. Đừng bao giờ tự bịa ra link phim.
                        """
                        
                        # Lọc lịch sử để tránh gửi JSON cũ làm AI bị lú
                        history_for_ai = [{"role": "user", "parts": [SYSTEM_PROMPT]}, {"role": "model", "parts": ["Ok"]}]
                        for msg in st.session_state.chat_history:
                            if msg.get("type") == "text": # Chỉ gửi text qua lại cho AI
                                role_map = "user" if msg["role"] == "user" else "model"
                                history_for_ai.append({"role": role_map, "parts": [msg["content"]]})
                        
                        chat = model.start_chat(history=history_for_ai)
                        response = chat.send_message(prompt)
                        reply_text = response.text.strip()
                        
                        import json
                        # Kiểm tra xem AI có trả về JSON lệnh không
                        if '{"action": "search"' in reply_text:
                            # Cố gắng parse JSON
                            try:
                                # Lấy phần JSON trong string (đề phòng AI nói nhảm thêm)
                                start = reply_text.find('{')
                                end = reply_text.rfind('}') + 1
                                json_str = reply_text[start:end]
                                command = json.loads(json_str)
                                
                                keyword = command["keyword"]
                                bot_reply = command["reply"]
                                
                                # GỌI HÀM SEARCH
                                items, path_img = get_movies('tim-kiem', keyword)
                                
                                if items:
                                    st.markdown(bot_reply)
                                    # Render ngay lập tức
                                    cols = st.columns(4)
                                    for i, m in enumerate(items[:4]):
                                        with cols[i]:
                                            img_url = m['thumb_url'] if m['thumb_url'].startswith('http') else f"{path_img}{m['thumb_url']}"
                                            st.markdown(f"""<div class="movie-chat-card"><img src="{img_url}" width="100%"><div class="movie-chat-title">{m['name']}</div></div>""", unsafe_allow_html=True)
                                            if st.button("Xem ngay", key=f"now_btn_{m['_id']}"):
                                                navigate('watch', m['slug'])
                                                st.rerun()
                                    
                                    # Lưu vào lịch sử dạng Movie List
                                    st.session_state.chat_history.append({
                                        "role": "assistant", 
                                        "content": bot_reply, 
                                        "type": "movie_list",
                                        "data": items,
                                        "path_img": path_img
                                    })
                                else:
                                    fallback = f"Mình đã tìm '{keyword}' nhưng không thấy phim nào. Bạn thử tên khác nhé?"
                                    st.markdown(fallback)
                                    st.session_state.chat_history.append({"role": "assistant", "content": fallback, "type": "text"})
                                    
                            except:
                                # Fallback nếu parse lỗi
                                st.markdown(reply_text)
                                st.session_state.chat_history.append({"role": "assistant", "content": reply_text, "type": "text"})
                        else:
                            # Trả lời bình thường
                            st.markdown(reply_text)
                            st.session_state.chat_history.append({"role": "assistant", "content": reply_text, "type": "text"})
                            
                    except Exception as e:
                        st.error(f"Lỗi: {e}")

# === VIEW: WATCH ===
elif st.session_state.view == 'watch':
    if st.button("⬅️ Quay lại", key="back_btn"):
        # Quay lại view trước đó (nếu từ chat thì về chat)
        st.session_state.view = 'chat' # Ưu tiên quay về chat nếu đang dùng chat
        st.rerun()

    data = get_movie_detail(st.session_state.current_movie)
    if data and data.get('status'):
        mv = data['movie']
        eps = data['episodes']
        has_episodes = False
        server_data = []
        if eps and len(eps) > 0 and 'server_data' in eps[0] and len(eps[0]['server_data']) > 0:
            has_episodes = True
            server_data = eps[0]['server_data']

        c1, c2 = st.columns([1, 2.5])
        with c1:
            st.image(mv['thumb_url'], use_container_width=True)
            is_fav = any(m['slug'] == mv['slug'] for m in st.session_state.favorites)
            if st.button("💔 Bỏ Thích" if is_fav else "❤️ Thêm Yêu Thích", use_container_width=True):
                if is_fav: st.session_state.favorites = [m for m in st.session_state.favorites if m['slug'] != mv['slug']]
                else: st.session_state.favorites.insert(0, {'slug': mv['slug'], 'name': mv['name']})
                st.rerun()

        with c2:
            st.markdown(f"<h2 style='color: #574b90; margin-bottom: 5px;'>{mv['name']}</h2>", unsafe_allow_html=True)
            st.markdown(f"**Gốc:** {mv['origin_name']} ({mv['year']})")
            st.markdown(f"**Trạng thái:** {mv['episode_current']} | **Thời lượng:** {mv['time']}")
            with st.expander("Nội dung chi tiết", expanded=True):
                st.write(mv['content'].replace('<p>','').replace('</p>',''))

        st.divider()
        if has_episodes:
            st.markdown("### 🍿 Màn Hình Chiếu")
            ep_dict = {f"Tập {e['name']}": e['link_embed'] for e in server_data}
            c_sel, _ = st.columns([1, 2])
            with c_sel:
                selected_ep = st.selectbox("Chọn tập:", list(ep_dict.keys()), label_visibility="collapsed")
            link = ep_dict[selected_ep]
            st.markdown(f"""<div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; background: #000; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);"><iframe src="{link}" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;" frameborder="0" allowfullscreen></iframe></div>""", unsafe_allow_html=True)
        else:
            st.warning("⚠️ Phim này đang cập nhật Trailer hoặc chưa có Link xem.")
else:
    # HOME VIEW
    st.markdown(f"### {st.session_state.current_title}")
    with st.spinner("Đang tải dữ liệu..."):
        items, path_img = get_movies(st.session_state.filter_type, st.session_state.filter_slug, st.session_state.page)
    if items:
        cols = st.columns(5)
        for i, item in enumerate(items):
            with cols[i % 5]:
                img_url = item['thumb_url'] if item['thumb_url'].startswith('http') else f"{path_img}{item['thumb_url']}"
                st.image(img_url, use_container_width=True)
                st.markdown(f"<div class='movie-title' title='{item['name']}'>{item['name']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='movie-year'>{item.get('year', '')}</div>", unsafe_allow_html=True)
                if st.button("Xem", key=f"b_{item['_id']}"):
                    navigate('watch', item['slug'])
                    st.rerun()
        st.divider()
        if st.session_state.filter_type != 'tim-kiem':
            c1, c2, c3 = st.columns([1, 4, 1])
            with c1:
                if st.session_state.page > 1 and st.button("⬅ Trang trước"): st.session_state.page -= 1; st.rerun()
            with c3:
                if st.button("Trang sau ➡"): st.session_state.page += 1; st.rerun()
    else:
        st.warning("⚠️ Không tìm thấy phim nào trong mục này!")