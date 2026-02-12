import streamlit as st
import requests
from groq import Groq  # Đổi từ google.generativeai sang groq
import time
import json

# --- 1. CẤU HÌNH GIAO DIỆN --- (Giữ nguyên)
st.set_page_config(
    page_title="T-HEXA Movies",
    page_icon="logo.jpg",
    layout="wide"
)

# --- 2. CSS CUSTOM --- (Giữ nguyên)
st.markdown("""
<style>
    .stApp { background-color: #f8f9fa; color: #212529; }
    header, footer {visibility: hidden;}
    .stButton>button {
        background-color: #fff; color: #495057; border: 1px solid #dee2e6; border-radius: 8px; font-size: 0.85rem;
        min-height: 2.8em; width: 100%; transition: all 0.2s;
    }
    .stButton>button:hover { background-color: #574b90; color: white; border-color: #574b90; }
    .stTextInput>div>div>input { border-radius: 20px; border: 1px solid #ced4da; padding-left: 15px; }
    .movie-chat-card {
        border: 1px solid #eee; border-radius: 12px; padding: 10px; background: #fff; 
        text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-top: 10px;
    }
    .movie-chat-card img { border-radius: 8px; object-fit: cover; margin-bottom: 8px; }
    .movie-chat-title { font-size: 0.85rem; font-weight: bold; height: 40px; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
</style>
""", unsafe_allow_html=True)

# --- 3, 4, 5, 6, 7 --- (Giữ nguyên toàn bộ logic Header và API phim của bạn)
MENU_DATA = {
    "DANH_SACH": {
        "Phim Mới": "phim-moi-cap-nhat", "Phim Bộ": "phim-bo", "Phim Lẻ": "phim-le",
        "TV Shows": "tv-shows", "Hoạt Hình": "hoat-hinh", "Phim Vietsub": "phim-vietsub",
        "Thuyết Minh": "phim-thuyet-minh", "Lồng Tiếng": "phim-long-tieng",
        "Bộ Đang Chiếu": "phim-bo-dang-chieu", "Trọn Bộ": "phim-bo-hoan-thanh",
        "Sắp Chiếu": "phim-sap-chieu", "Chiếu Rạp": "phim-chieu-rap"
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

if 'view' not in st.session_state: st.session_state.view = 'home'
if 'current_movie' not in st.session_state: st.session_state.current_movie = None
if 'favorites' not in st.session_state: st.session_state.favorites = []
if 'page' not in st.session_state: st.session_state.page = 1
if 'filter_type' not in st.session_state: st.session_state.filter_type = 'moi-cap-nhat'
if 'filter_slug' not in st.session_state: st.session_state.filter_slug = ''
if 'search_query' not in st.session_state: st.session_state.search_query = ''
if 'current_title' not in st.session_state: st.session_state.current_title = "Phim Mới Cập Nhật"
if "chat_history" not in st.session_state: st.session_state.chat_history = [] 

API_BASE = "https://ophim1.com"
CDN_FALLBACK = "https://img.ophim1.com/uploads/movies/"

@st.cache_data(ttl=600)
def fetch_data(url):
    try:
        r = requests.get(url, timeout=10)
        return r.json() if r.status_code == 200 else None
    except: return None

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

with st.container():
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        try: st.image("logo.jpg", width=120)
        except: st.title("T-HEXA")
    with c2:
        st.text_input("🔍", placeholder="Bạn muốn tìm phim gì?", key="search_input", on_change=handle_search, label_visibility="collapsed")
    with c3:
        if st.button("🤖 Trợ Lý AI", use_container_width=True): navigate('chat')

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        if st.button("🏠 Trang Chủ", use_container_width=True): set_filter('moi-cap-nhat', '', "Phim Mới Cập Nhật")
    with m2:
        with st.popover("📂 Danh Sách", use_container_width=True):
            cols = st.columns(2)
            for i, (name, slug) in enumerate(MENU_DATA["DANH_SACH"].items()):
                if cols[i % 2].button(name, key=f"ds_{slug}", use_container_width=True): set_filter('danh-sach', slug, name)
    with m3:
        with st.popover("🎬 Thể Loại", use_container_width=True):
            cols = st.columns(2)
            for i, (name, slug) in enumerate(MENU_DATA["THE_LOAI"].items()):
                if cols[i % 2].button(name, key=f"tl_{slug}", use_container_width=True): set_filter('the-loai', slug, f"Thể Loại: {name}")
    with m4:
        with st.popover("🌍 Quốc Gia", use_container_width=True):
            cols = st.columns(2)
            for i, (name, slug) in enumerate(MENU_DATA["QUOC_GIA"].items()):
                if cols[i % 2].button(name, key=f"qg_{slug}", use_container_width=True): set_filter('quoc-gia', slug, f"Quốc Gia: {name}")

st.divider()

# --- 8. XỬ LÝ NỘI DUNG CHÍNH ---
# === VIEW: CHAT AI NÂNG CẤP TOÀN DIỆN (THE ULTIMATE STORYTELLER) ===
if st.session_state.view == 'chat':
    st.title("🤖 T-HEXA AI - Chuyên Gia Điện Ảnh")
    st.caption("Review chuyên sâu, kể truyện hấp dẫn và tìm phim tức thì")
    
    api_key = st.secrets.get("GROQ_API_KEY", "")
    if api_key:
        try:
            client = Groq(api_key=api_key)
            model_name = "llama-3.3-70b-versatile" # Model thông minh nhất để đảm bảo khả năng tư vấn
        except Exception as e:
            st.error(f"Lỗi hệ thống AI: {e}")
            client = None
    else:
        st.warning("⚠️ Vui lòng cấu hình GROQ_API_KEY trong hệ thống.")
        client = None

    if client:
        # Lời chào thông minh hơn
        if not st.session_state.chat_history:
            st.session_state.chat_history.append({
                "role": "assistant", 
                "content": "Chào bạn! Mình là trợ lý T-HEXA. Đừng chỉ bảo mình tìm phim, hãy thử hỏi: 'Kể mình nghe nội dung phim kinh dị nào thật ám ảnh' hoặc 'Gợi ý phim Tết vui vẻ' xem nhé! 😉", 
                "type": "text"
            })
            
        # HIỂN THỊ LỊCH SỬ CHAT
        for idx, message in enumerate(st.session_state.chat_history):
            with st.chat_message(message["role"]):
                if message.get("type") == "text":
                    st.markdown(message["content"])
                elif message.get("type") == "movie_list":
                    st.markdown(message["content"]) # Phần AI kể chuyện/tư vấn
                    # Hiển thị Card phim ngay dưới lời kể
                    cols = st.columns(4) 
                    for i, m in enumerate(message["data"][:4]):
                        with cols[i]:
                            img_url = m['thumb_url'] if m['thumb_url'].startswith('http') else f"{message['path_img']}{m['thumb_url']}"
                            st.markdown(f'''
                                <div class="movie-chat-card">
                                    <img src="{img_url}" width="100%">
                                    <div class="movie-chat-title">{m["name"]}</div>
                                </div>
                            ''', unsafe_allow_html=True)
                            if st.button("Xem phim này", key=f"chat_btn_{idx}_{m['_id']}"):
                                navigate('watch', m['slug'])
                                st.rerun()

        # XỬ LÝ NHẬP LIỆU
        if prompt := st.chat_input("Hỏi bất cứ điều gì về phim..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt, "type": "text"})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.chat_message("assistant"):
                with st.spinner("Đang phân tích và viết review..."):
                    try:
                        # --- HỆ THỐNG NÃO BỘ NÂNG CẤP ---
                        SYSTEM_PROMPT = """Bạn là T-HEXA AI - Một nhà phê bình phim có kiến thức sâu rộng và giọng văn lôi cuốn.
                        NHIỆM VỤ:
                        1. Nếu user hỏi về nội dung, gợi ý phim, hoặc tìm phim:
                           - BƯỚC 1: Phân tích gu của user.
                           - BƯỚC 2: Viết một đoạn review hoặc tóm tắt nội dung thật 'bánh cuốn' (khoảng 3-6 câu). 
                             Dùng các tính từ mạnh (hấp dẫn, kịch tính, ám ảnh, lãng mạn...).
                           - BƯỚC 3: Chọn ra 1 tên phim CHÍNH XÁC NHẤT để đưa vào từ khóa tìm kiếm.
                        
                        ĐỊNH DẠNG TRẢ VỀ (LUÔN LUÔN LÀ JSON NẾU LIÊN QUAN ĐẾN PHIM):
                        {"action": "search", "keyword": "Tên phim đích danh", "reply": "Đoạn văn review lôi cuốn của bạn ở đây."}
                        
                        2. Nếu user chỉ chào hỏi/tán gẫu: Trả lời Text thân thiện, hài hước.
                        
                        LƯU Ý: Tuyệt đối không tìm từ khóa chung chung như 'phim Tết'. Hãy tự chọn một phim như 'Mai' hoặc 'Nhà Bà Nữ' để tìm."""
                        
                        # Lọc hội thoại gửi lên AI
                        msg_history = [{"role": "system", "content": SYSTEM_PROMPT}]
                        for msg in st.session_state.chat_history[-6:]: # Chỉ gửi 6 câu gần nhất để AI không bị loạn
                            if msg.get("type") == "text":
                                msg_history.append({"role": msg["role"], "content": msg["content"]})
                        
                        completion = client.chat.completions.create(model=model_name, messages=msg_history, temperature=0.6)
                        reply_text = completion.choices[0].message.content.strip()
                        
                        # XỬ LÝ KẾT QUẢ TỪ AI
                        if '{"action": "search"' in reply_text:
                            try:
                                start = reply_text.find('{'); end = reply_text.rfind('}') + 1
                                command = json.loads(reply_text[start:end])
                                
                                # Tìm dữ liệu phim từ API
                                items, path_img = get_movies('tim-kiem', command["keyword"])
                                
                                if items:
                                    st.markdown(command["reply"]) # Hiện đoạn kể chuyện
                                    cols = st.columns(4)
                                    for i, m in enumerate(items[:4]):
                                        with cols[i]:
                                            img_url = m['thumb_url'] if m['thumb_url'].startswith('http') else f"{path_img}{m['thumb_url']}"
                                            st.markdown(f'<div class="movie-chat-card"><img src="{img_url}" width="100%"><div class="movie-chat-title">{m["name"]}</div></div>', unsafe_allow_html=True)
                                            if st.button("Xem ngay", key=f"now_{m['_id']}"):
                                                navigate('watch', m['slug'])
                                                st.rerun()
                                    # Lưu vào lịch sử
                                    st.session_state.chat_history.append({
                                        "role": "assistant", "content": command["reply"], 
                                        "type": "movie_list", "data": items, "path_img": path_img
                                    })
                                else:
                                    # Fallback nếu tìm không ra
                                    st.markdown(command["reply"] + "\n\n*(Phim này mình chưa thấy trong kho, nhưng nội dung thì tuyệt vời như mình kể đấy!)*")
                                    st.session_state.chat_history.append({"role": "assistant", "content": command["reply"], "type": "text"})
                            except:
                                st.markdown(reply_text)
                        else:
                            st.markdown(reply_text)
                            st.session_state.chat_history.append({"role": "assistant", "content": reply_text, "type": "text"})
                    except Exception as e: st.error(f"Lỗi kết nối: {e}")
# === VIEW: WATCH & HOME === (Giữ nguyên toàn bộ phần dưới của bạn)
elif st.session_state.view == 'watch':
    if st.button("⬅️ Quay lại"):
        st.session_state.view = 'chat' if len(st.session_state.chat_history) > 1 else 'home'
        st.rerun()
    data = get_movie_detail(st.session_state.current_movie)
    if data and data.get('status'):
        mv = data['movie']; eps = data['episodes']
        c1, c2 = st.columns([1, 2.5])
        with c1:
            st.image(mv['thumb_url'], use_container_width=True)
            is_fav = any(m['slug'] == mv['slug'] for m in st.session_state.favorites)
            if st.button("💔 Bỏ Thích" if is_fav else "❤️ Thêm Yêu Thích", use_container_width=True):
                if is_fav: st.session_state.favorites = [m for m in st.session_state.favorites if m['slug'] != mv['slug']]
                else: st.session_state.favorites.insert(0, {'slug': mv['slug'], 'name': mv['name']})
                st.rerun()
        with c2:
            st.markdown(f"<h2 style='color: #574b90;'>{mv['name']}</h2>", unsafe_allow_html=True)
            st.write(mv['content'].replace('<p>','').replace('</p>',''))
        st.divider()
        if eps and eps[0]['server_data']:
            ep_dict = {f"Tập {e['name']}": e['link_embed'] for e in eps[0]['server_data']}
            selected_ep = st.selectbox("Chọn tập:", list(ep_dict.keys()), label_visibility="collapsed")
            st.markdown(f'<div style="position: relative; padding-bottom: 56.25%; height: 0; background: #000; border-radius: 12px; overflow: hidden;"><iframe src="{ep_dict[selected_ep]}" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;" frameborder="0" allowfullscreen></iframe></div>', unsafe_allow_html=True)
        else: st.warning("⚠️ Phim chưa có link xem.")

else:
    st.markdown(f"### {st.session_state.current_title}")
    with st.spinner("Đang tải phim..."):
        items, path_img = get_movies(st.session_state.filter_type, st.session_state.filter_slug, st.session_state.page)
    if items:
        cols = st.columns(5)
        for i, item in enumerate(items):
            with cols[i % 5]:
                img_url = item['thumb_url'] if item['thumb_url'].startswith('http') else f"{path_img}{item['thumb_url']}"
                st.image(img_url, use_container_width=True)
                st.markdown(f"<div class='movie-title' title='{item['name']}'>{item['name']}</div>", unsafe_allow_html=True)
                if st.button("Xem ngay", key=f"b_{item['_id']}", use_container_width=True):
                    navigate('watch', item['slug'])
                    st.rerun()
        st.divider()
        c1, c2, c3 = st.columns([1, 4, 1])
        with c1:
            if st.session_state.page > 1 and st.button("⬅ Trang trước"): st.session_state.page -= 1; st.rerun()
        with c3:
            if st.button("Trang sau ➡"): st.session_state.page += 1; st.rerun()
    else: st.warning("Không tìm thấy phim!")