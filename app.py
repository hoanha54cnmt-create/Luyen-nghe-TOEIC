import streamlit as st
import gspread
import json
# (Nếu code cũ của bạn có import thêm thư viện nào, hãy dán lên đây)

# ==========================================
# 1. CÀI ĐẶT GIAO DIỆN TRANG WEB
# ==========================================
st.set_page_config(page_title="Hệ thống Luyện nghe - Ms.Thục TOEIC", page_icon="🎧", layout="centered")
st.title("🎧 Hệ thống Luyện nghe TOEIC")
st.markdown("**Bản quyền thuộc về lớp học Ms. Thục TOEIC**")
st.markdown("---")

# ==========================================
# 2. KẾT NỐI GOOGLE SHEETS (BẢN GỐC CỦA BẠN)
# ==========================================
# 👇👇👇 BẠN HÃY DÁN NGUYÊN SI ĐOẠN CODE KẾT NỐI CŨ ĐÃ TỪNG CHẠY ĐƯỢC VÀO ĐÂY 👇👇👇



# 👆👆👆 ======================================================================= 👆👆👆

# Đảm bảo file Excel được mở đúng link này (Biến doc phải khớp với code cũ của bạn)
doc = gc.open_by_url("https://docs.google.com/spreadsheets/d/1JHynbU_LDlCfPi6budsjOlTa9Hv4zDrajT3CijJilno/edit?usp=sharing")

# ==========================================
# 3. CỔNG 1: KHAI BÁO DANH TÍNH & BẢO MẬT
# ==========================================
lop_hoc = st.selectbox("Chọn Lớp học của bạn:", ["246", "357"])

@st.cache_data(ttl=600)
def lay_danh_sach_hoc_vien(lop_chon):
    try:
        sheet_hv = doc.worksheet("Hocvien")
        records = sheet_hv.get_all_values()
        danh_sach = []
        for row in records[1:]:
            if len(row) >= 3:
                lop_trong_sheet = row[0].strip()
                ten_trong_sheet = row[1].strip()
                trang_thai = row[2].strip()
                if lop_trong_sheet == lop_chon and trang_thai == "Đang học":
                    danh_sach.append(ten_trong_sheet.lower())
        return danh_sach
    except Exception as e:
        return []

danh_sach_hop_le = lay_danh_sach_hoc_vien(lop_hoc)
ten_nhap_vao = st.text_input("Nhập chính xác Họ và Tên của bạn:")

if ten_nhap_vao:
    ten_kiem_tra = ten_nhap_vao.strip().lower()
    
    if ten_kiem_tra in danh_sach_hop_le:
        st.success(f"✅ Xác thực thành công! Chào mừng **{ten_nhap_vao.title()}**.")
        st.markdown("---")

        # ==========================================
        # 4. CHỌN ĐỀ TỰ ĐỘNG
        # ==========================================
        if lop_hoc == "246":
            danh_sach_de = ["6U", "De1", "De2"]
        else:
            danh_sach_de = ["6U", "Test1", "Test2"]

        ma_de_chon = st.selectbox("Chọn Mã đề:", danh_sach_de)
        ma_bi_mat = f"{lop_hoc}-{ma_de_chon}"

        def lay_link_audio(ma_tim_kiem):
            sheet_khode = doc.worksheet("KhoDe")
            danh_sach_dong = sheet_khode.get_all_values()
            links = []
            for row in danh_sach_dong:
                if row[0].strip() == ma_tim_kiem:
                    for cell in row[2:]:
                        if cell.strip() != "":
                            links.append(cell.strip())
                    break
            return links

        found_links = lay_link_audio(ma_bi_mat)

        if len(found_links) > 0:
            st.success(f"🎉 Đã tải đề thành công! (Gồm {len(found_links)} câu hỏi)")
            
            # ==========================================
            # 5. TRẠM KIỂM TRA ÂM THANH
            # ==========================================
            st.markdown("### 🎧 Bước 1: Kiểm tra âm thanh")
            st.info("Vui lòng nghe thử đoạn âm thanh dưới đây và điều chỉnh âm lượng thiết bị cho phù hợp.")
            
            # Link file test
            link_test = "https://drive.google.com/uc?export=download&id=ID_FILE_TEST_CUA_BAN"
            st.audio(link_test)
            
            da_nghe_ro = st.checkbox("✅ Tôi đã nghe rõ âm thanh và sẵn sàng làm bài!")

            # ==========================================
            # 6. LÀM BÀI VÀ NỘP BÀI
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
