import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import time

# --- 1. CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Luyện nghe TOEIC", page_icon="🎧", layout="centered")
st.title("Hệ thống Luyện nghe TOEIC - Ms. Thục")

# --- 2. KẾT NỐI GOOGLE SHEETS ---
# Yêu cầu file keys.json đặt cùng thư mục với app.py 
# (Khi đẩy lên mạng sẽ dùng st.secrets, tôi có ghi chú ở cuối bài)
@st.cache_resource
@st.cache_resource
def init_connection():
    import json
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    
    # Lấy chìa khóa bảo mật từ Streamlit Secrets
    key_dict = json.loads(st.secrets["google_json"])
    creds = Credentials.from_service_account_info(key_dict, scopes=scope)
    client = gspread.authorize(creds)
    
    sheet_url = "https://docs.google.com/spreadsheets/d/1JHynbU_LDlCfPi6budsjOlTa9Hv4zDrajT3CijJilno/edit?gid=931055085#gid=931055085" 
    doc = client.open_by_url(sheet_url)
    return doc

try:
    doc = init_connection()
    sheet_khode = doc.worksheet("KhoDe")
    sheet_dulieutho = doc.worksheet("DuLieuTho")
except Exception as e:
    st.error(f"Lỗi chi tiết: {e}")
    st.stop()

# --- 3. THÔNG TIN HỌC VIÊN ---
st.subheader("1. Thông tin học viên")
lop = st.radio("Chọn lớp của bạn:", options=["Ca 246", "Ca 357"], horizontal=True)

ten_hoc_vien = st.text_input("Nhập Họ và Tên của bạn:")
st.caption("🔴 *Lưu ý: Vui lòng nhập đúng chuẩn Họ và Tên đầy đủ có dấu để hệ thống ghi nhận điểm chính xác.*")

# --- 4. TRA CỨU MÃ ĐỀ ---
st.subheader("2. Bài tập luyện nghe")
ma_de = st.text_input("Nhập Mã đề (Ví dụ: Tuan1):").strip()

# Khởi tạo Session State để lưu trữ dữ liệu
if "audio_links" not in st.session_state:
    st.session_state.audio_links = []
if "current_made" not in st.session_state:
    st.session_state.current_made = ""

if ma_de:
    # Chỉ truy xuất Sheets nếu mã đề thay đổi để tránh quá tải API
    if ma_de != st.session_state.current_made:
        with st.spinner("Đang tải đề bài..."):
            records = sheet_khode.get_all_values()
            found_links = []
            for row in records:
                # Kiểm tra xem dòng đó có dữ liệu không rồi mới đọc Cột A
                if len(row) > 0 and row[0].strip() == ma_de:
                    # Lấy các link từ cột B trở đi, bỏ qua các ô trống
                    found_links = [link.strip() for link in row[1:] if link.strip() != ""]
                    break
            
            st.session_state.audio_links = found_links
            st.session_state.current_made = ma_de
            
            # Reset lượt nghe khi đổi mã đề
            for key in list(st.session_state.keys()):
                if key.startswith("play_count_"):
                    del st.session_state[key]

    links = st.session_state.audio_links

    if not links:
        st.warning("Không tìm thấy Mã đề này hoặc đề chưa có âm thanh. Vui lòng kiểm tra lại.")
    else:
        st.success(f"Đã tải thành công đề: {ma_de} ({len(links)} câu hỏi)")
        
        # Tạo danh sách hứng đáp án
        dap_an_list = []

        # --- 5. HIỂN THỊ CÂU HỎI VÀ NÚT NGHE ---
        for i, link in enumerate(links):
            st.markdown(f"**Câu {i + 1}:**")
            
            # Quản lý số lần nghe
            count_key = f"play_count_{i}"
            if count_key not in st.session_state:
                st.session_state[count_key] = 0

            # Cột giao diện cho nút nghe
            col1, col2 = st.columns([1, 3])
            
            with col1:
                luot_con_lai = 2 - st.session_state[count_key]
                button_label = f"▶️ Nghe (Còn {luot_con_lai} lần)" if luot_con_lai > 0 else "🚫 Đã hết lượt nghe"
                
                # Nút phát âm thanh
                if st.button(button_label, key=f"btn_play_{i}", disabled=(st.session_state[count_key] >= 2)):
                    st.session_state[count_key] += 1
                    # Tiêm mã HTML để phát âm thanh ẩn
                    audio_html = f"""
                        <audio autoplay>
                            <source src="{link}" type="audio/mpeg">
                        </audio>
                    """
                    st.components.v1.html(audio_html, width=0, height=0)
                    st.rerun()

            with col2:
                # Ô điền đáp án
                dap_an = st.text_area(f"Nhập bản dịch/chép chính tả Câu {i + 1}:", key=f"dapan_{i}", height=68, label_visibility="collapsed")
                dap_an_list.append(dap_an)
            
            st.markdown("---")

        # --- 6. NỘP BÀI ---
        if st.button("📤 Nộp bài", type="primary"):
            if not ten_hoc_vien:
                st.error("Vui lòng nhập Họ và Tên trước khi nộp bài!")
            else:
                with st.spinner("Đang lưu kết quả..."):
                    thoi_gian = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                    
                    # Cấu trúc dòng dữ liệu đẩy lên Sheet
                    # Mặc định tạo đủ 30 ô đáp án (bạn có thể tăng/giảm số 30 tùy ý)
                    max_cau_hoi = 30
                    dap_an_padded = dap_an_list + [""] * (max_cau_hoi - len(dap_an_list))
                    
                    row_data = [thoi_gian, lop, ten_hoc_vien, ma_de] + dap_an_padded
                    
                    # Đẩy lên Sheet
                    sheet_dulieutho.append_row(row_data)
                    
                    st.success("🎉 Nộp bài thành công! Bạn có thể đóng trình duyệt.")
                    time.sleep(2)
                    # Reset Form (Tùy chọn)
                    st.rerun()
