import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# ==========================================
# 1. CÀI ĐẶT GIAO DIỆN TRANG WEB
# ==========================================
st.set_page_config(page_title="Hệ thống Luyện nghe - Ms.Thục TOEIC", page_icon="🎧", layout="centered")
st.title("🎧 Hệ thống Luyện nghe TOEIC")
st.markdown("**Bản quyền thuộc về lớp học Ms. Thục TOEIC**")
st.markdown("---")

# ==========================================
# --- 2. KẾT NỐI GOOGLE SHEETS ---
# Yêu cầu file keys.json đặt cùng thư mục với app.py 
# (Khi đẩy lên mạng sẽ dùng st.secrets, tôi có ghi chú ở cuối bài)
@st.cache_resource
@st.cache_resource
def init_connection():
    import json
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

# ĐIỀN ĐƯỜNG LINK HOẶC ID FILE GOOGLE SHEETS CỦA BẠN VÀO ĐÂY:
doc = gc.open_by_url("https://docs.google.com/spreadsheets/d/1JHynbU_LDlCfPi6budsjOlTa9Hv4zDrajT3CijJilno/edit?usp=sharing") 

# ==========================================
# 3. CỔNG 1: KHAI BÁO DANH TÍNH & BẢO MẬT
# ==========================================
lop_hoc = st.selectbox("Chọn Lớp học của bạn:", ["246", "357"])

# Hàm tự động chui vào tab "Hocvien" để kiểm tra danh sách
@st.cache_data(ttl=600) # Lưu bộ nhớ đệm 10 phút để web chạy nhanh
def lay_danh_sach_hoc_vien(lop_chon):
    try:
        sheet_hv = doc.worksheet("Hocvien")
        records = sheet_hv.get_all_values()
        danh_sach = []
        for row in records[1:]: # Bỏ qua dòng tiêu đề
            if len(row) >= 3:
                lop_trong_sheet = row[0].strip()
                ten_trong_sheet = row[1].strip()
                trang_thai = row[2].strip()
                
                # Chỉ lấy những bạn đúng lớp và đang học
                if lop_trong_sheet == lop_chon and trang_thai == "Đang học":
                    danh_sach.append(ten_trong_sheet.lower())
        return danh_sach
    except Exception as e:
        return []

danh_sach_hop_le = lay_danh_sach_hoc_vien(lop_hoc)
ten_nhap_vao = st.text_input("Nhập chính xác Họ và Tên của bạn:")

if ten_nhap_vao:
    ten_kiem_tra = ten_nhap_vao.strip().lower()
    
    # KỂ TỪ ĐÂY: CHỈ NHỮNG AI NHẬP ĐÚNG TÊN MỚI THẤY ĐƯỢC ĐỀ THI
    if ten_kiem_tra in danh_sach_hop_le:
        st.success(f"✅ Xác thực thành công! Chào mừng **{ten_nhap_vao.title()}**.")
        st.markdown("---")

        # ==========================================
        # 4. CỔNG 2: CHỌN ĐỀ TỰ ĐỘNG THEO LỚP
        # ==========================================
        if lop_hoc == "246":
            danh_sach_de = ["6U", "De1", "De2"] # Bạn sửa lại tên đề lớp 246 ở đây
        else:
            danh_sach_de = ["6U", "Test1", "Test2"] # Bạn sửa lại tên đề lớp 357 ở đây

        ma_de_chon = st.selectbox("Chọn Mã đề:", danh_sach_de)
        
        # Ghép mã bí mật để đi tìm (Ví dụ: 246-6U)
        ma_bi_mat = f"{lop_hoc}-{ma_de_chon}"

        # Hàm chui vào tab "KhoDe" rút link âm thanh ra
        def lay_link_audio(ma_tim_kiem):
            sheet_khode = doc.worksheet("KhoDe")
            danh_sach_dong = sheet_khode.get_all_values()
            links = []
            for row in danh_sach_dong:
                if row[0].strip() == ma_tim_kiem:
                    # Lấy link từ Cột C (vị trí số 2) trở đi
                    for cell in row[2:]:
                        if cell.strip() != "":
                            links.append(cell.strip())
                    break
            return links

        found_links = lay_link_audio(ma_bi_mat)

        if len(found_links) > 0:
            st.success(f"🎉 Đã tải đề thành công! (Gồm {len(found_links)} câu hỏi)")
            
            # ==========================================
            # 5. CỔNG 3: TRẠM KIỂM TRA ÂM THANH (SOUND CHECK)
            # ==========================================
            st.markdown("### 🎧 Bước 1: Kiểm tra âm thanh")
            st.info("Vui lòng nghe thử đoạn âm thanh dưới đây và điều chỉnh âm lượng thiết bị cho phù hợp.")
            
            # BẠN DÁN LINK PHÁT TRỰC TIẾP ÂM THANH TEST CỦA BẠN VÀO ĐÂY:
            link_test = "https://drive.google.com/uc?export=download&id=ID_FILE_TEST_CUA_BAN"
            st.audio(link_test)
            
            da_nghe_ro = st.checkbox("✅ Tôi đã nghe rõ âm thanh và sẵn sàng làm bài!")

            # ==========================================
            # 6. CỔNG 4: LÀM BÀI VÀ NỘP BÀI
            # ==========================================
            if da_nghe_ro:
                st.markdown("---")
                st.markdown("### 📝 Bước 2: Bắt đầu làm bài")
                
                with st.form("form_lam_bai"):
                    dap_an_hoc_vien = {}
                    
                    for i, link in enumerate(found_links):
                        so_cau = i + 1
                        st.markdown(f"**Câu {so_cau}**")
                        st.audio(link)
                        
                        chon = st.radio(
                            "Chọn đáp án:", 
                            ["A", "B", "C", "D"], 
                            key=f"cau_{so_cau}", 
                            horizontal=True,
                            index=None
                        )
                        dap_an_hoc_vien[f"Câu {so_cau}"] = chon
                        st.divider()
                    
                    nut_nop_bai = st.form_submit_button("Nộp bài ngay", type="primary")
                    
                if nut_nop_bai:
                    so_cau_chua_lam = sum(1 for ans in dap_an_hoc_vien.values() if ans is None)
                    if so_cau_chua_lam > 0:
                        st.warning(f"⚠️ Bạn còn {so_cau_chua_lam} câu chưa chọn đáp án. Hãy kiểm tra lại nhé!")
                    else:
                        st.balloons()
                        st.success("Tuyệt vời! Bạn đã nộp bài thành công.")
                        st.write("Đáp án của bạn:", dap_an_hoc_vien)
        else:
            st.info("⏳ Chưa có file nghe cho đề này. Vui lòng báo lại với trung tâm nhé!")
    else:
        st.error("⛔ Tên của bạn không khớp với danh sách lớp hiện tại, hoặc bạn đã gõ sai chính tả.")
