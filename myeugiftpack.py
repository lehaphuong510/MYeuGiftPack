import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# --- KẾT NỐI GOOGLE SHEETS TỪ SECRETS ---
@st.cache_resource
def get_credentials():
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
    )
    return creds

SHEET_ID = "1ce2iU7qzr9PUoGMorlIaNMYb3KDGizmhiIRquWN8dOE"

# --- CACHE & STATE QUẢN LÝ ĐĂNG NHẬP ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'staff_name' not in st.session_state:
    st.session_state['staff_name'] = ""

# --- CẤU HÌNH GIAO DIỆN & CSS ---
st.set_page_config(page_title="Đóng Thùng Sự Kiện", page_icon="📦", layout="centered")

css = """
<style>
    @media max-width: 768px {
        .main-title { font-size: 24px !important; line-height: 1.3 !important; white-space: nowrap !important; }
    }
    .main-title {
        background: linear-gradient(to right, #005C97, #363795);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: left; font-size: 32px; font-weight: bold; margin-bottom: 20px;
    }
    .question-text {
        background: linear-gradient(to right, #11998e, #38ef7d);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 18px; font-weight: 600; margin-bottom: 10px;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(to right, #005C97, #363795) !important;
        color: white !important; border: none !important;
    }
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# --- MÀN HÌNH ĐĂNG NHẬP ---
if not st.session_state['logged_in']:
    st.markdown('<div class="main-title">HỆ THỐNG ĐÓNG THÙNG<br>MYÊU SHOW</div>', unsafe_allow_html=True)
    password = st.text_input("Vui lòng nhập mã truy cập của bạn:", type="password")

    danh_sach_pass_hop_le = {
        "DongThung01": "Kho Bãi 1",
        "DongThung02": "Kho Bãi 2",
        "0519": "Admin Phương"
    }

    if st.button("Vào hệ thống", type="primary"):
        if password in danh_sach_pass_hop_le:
            st.session_state['staff_name'] = danh_sach_pass_hop_le[password]
            st.session_state['logged_in'] = True
            st.rerun()
        else:
            st.error("Sai password rồi nha!")

# --- MÀN HÌNH CHÍNH (SAU KHI ĐĂNG NHẬP) ---
else:
    col1, col2 = st.columns([8, 2])
    with col2:
        if st.button("Đăng xuất"):
            st.session_state['logged_in'] = False
            st.session_state['staff_name'] = ""
            st.rerun()

    st.markdown('<div class="main-title">KIỂM KÊ ĐÓNG THÙNG<br>📦 QUÀ TẶNG 📦</div>', unsafe_allow_html=True)
    st.write(f"Đang phụ trách: **{st.session_state['staff_name']}**")
    st.divider()

    st.markdown('<div class="question-text">Nhập số ghế ghi trên món quà:</div>', unsafe_allow_html=True)
    seat_num = st.text_input("Số ghế / SĐT:", key="seat_input")

    st.markdown('<div class="question-text">Cho quà vào Thùng số mấy?</div>', unsafe_allow_html=True)
    box_num = st.text_input("Nhập số thùng (VD: 1, 2, 3...)", key="box_input")

    if st.button("Hoàn thành", type="primary"):
        if not seat_num:
            st.warning("Bạn chưa nhập số ghế kìa!")
        elif not box_num:
            st.warning("Bạn chưa nhập số thùng kìa!")
        else:
            with st.spinner("Đang dò tìm và cập nhật dữ liệu..."):
                try:
                    creds = get_credentials()
                    client = gspread.authorize(creds)
                    sheet = client.open_by_key(SHEET_ID).worksheet("Sheet1")

                    # Lấy toàn bộ dữ liệu hiện tại của Sheet về dò
                    all_data = sheet.get_all_values()

                    # Cột Số ghế là cột thứ 3 (index 2)
                    seat_normalized = seat_num.upper().strip()
                    row_to_update = -1
                    is_already_packed = False
                    box_packed = ""

                    # Dò từ dưới lên trên (để lấy dữ liệu ghi nhận mới nhất)
                    for i in range(len(all_data) - 1, 0, -1):
                        row = all_data[i]
                        
                        # So sánh bỏ qua dấu nháy đơn ở đầu (nếu có)
                        sheet_seat = row[2].replace("'", "").upper().strip()

                        if sheet_seat == seat_normalized:
                            row_to_update = i + 1 # +1 vì gspread đếm từ 1
                            
                            # Kiểm tra xem đã đóng thùng chưa (Cột Packed giờ là cột 6, index 5)
                            if len(row) > 5 and row[5] == "☑️":
                                is_already_packed = True
                                # Số thùng giờ là cột 7, index 6
                                if len(row) > 6:
                                    box_packed = row[6]
                            break

                    if row_to_update == -1:
                        st.error(f"🚨 LỖI: Số ghế '{seat_normalized}' chưa được ghi nhận trên hệ thống Nhận Quà! Vui lòng kiểm tra lại món quà này.")
                    elif is_already_packed:
                        st.error(f"🚨 CẢNH BÁO TRÙNG LẶP: Số ghế '{seat_normalized}' đã được đóng vào Thùng số {box_packed} trước đó rồi!")
                    else:
                        # UPDATE VÀO SHEET ĐÚNG CỘT MỚI
                        # Cột 6: Packed, Cột 7: Số Thùng
                        sheet.update_cell(row_to_update, 6, "☑️")
                        sheet.update_cell(row_to_update, 7, str(box_num))
                        st.success(f"📦 Đã đóng món quà của ghế {seat_normalized} vào Thùng số {box_num} thành công!")

                except Exception as e:
                    st.error(f"Có lỗi xảy ra: {e}")
