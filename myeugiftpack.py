import streamlit as st
import gspread
import re
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

# --- HÀM SẮP XẾP SỐ GHẾ (CHỮ TRƯỚC SỐ SAU, SĐT CUỐI CÙNG) ---
def sort_seats(seat_list):
    regular_seats = []
    phone_numbers = []
    
    for seat in seat_list:
        if len(seat) > 5 or seat.isdigit():
            phone_numbers.append(seat)
        else:
            match = re.match(r"([A-Z]+)(\d+)", seat)
            if match:
                regular_seats.append((match.group(1), int(match.group(2)), seat))
            else:
                regular_seats.append((seat, 0, seat))
                
    regular_seats.sort(key=lambda x: (x[0], x[1]))
    return [item[2] for item in regular_seats] + sorted(phone_numbers)

# --- CACHE & STATE QUẢN LÝ ĐĂNG NHẬP VÀ FORM UI ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'staff_name' not in st.session_state:
    st.session_state['staff_name'] = ""

# Dùng key động để reset toàn bộ form nhập liệu
if 'form_key' not in st.session_state:
    st.session_state['form_key'] = 0

if 'success_msg' not in st.session_state:
    st.session_state['success_msg'] = ""
if 'error_msg' not in st.session_state:
    st.session_state['error_msg'] = ""

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
    .seat-chip {
        display: inline-block;
        background-color: #e0f2f1;
        color: #00695c;
        padding: 5px 10px;
        border-radius: 15px;
        margin: 3px;
        font-weight: bold;
        font-size: 14px;
    }
    .box-card {
        background-color: #f5f5f5;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
        border-left: 5px solid #005C97;
    }
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# --- MÀN HÌNH ĐĂNG NHẬP ---
if not st.session_state['logged_in']:
    st.markdown('<div class="main-title">Đăng nhập Trạm Carton</div>', unsafe_allow_html=True)
    password = st.text_input("Vui lòng nhập mã truy cập của bạn:", type="password")

    danh_sach_pass_hop_le = {
        "DongThung01": "Kho Bãi 1",
        "DongThung02": "Kho Bãi 2",
        "0519": "Lê Phương"
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

    # --- KHU VỰC 1: XỬ LÝ ĐÓNG THÙNG ---
    
    # Hiển thị thông báo CỦA LẦN BẤM TRƯỚC ĐÓ (nếu có)
    if st.session_state['success_msg']:
        st.success(st.session_state['success_msg'])
        st.session_state['success_msg'] = "" 
        
    if st.session_state['error_msg']:
        st.error(st.session_state['error_msg'])
        st.session_state['error_msg'] = ""

    st.markdown('<div class="question-text">Nhập số ghế ghi trên món quà:</div>', unsafe_allow_html=True)
    
    # Ép key động để reset ô input
    seat_num = st.text_input("Số ghế / SĐT:", key=f"seat_{st.session_state['form_key']}")

    st.markdown('<div class="question-text">Cho quà vào Thùng số mấy?</div>', unsafe_allow_html=True)
    
    # Ép key động để reset ô input
    box_num = st.text_input("Nhập số thùng (VD: 1, 2, 3...)", key=f"box_{st.session_state['form_key']}")

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

                    all_data = sheet.get_all_values()
                    seat_normalized = seat_num.upper().strip()
                    row_to_update = -1
                    is_already_packed = False
                    box_packed = ""

                    for i in range(len(all_data) - 1, 0, -1):
                        row = all_data[i]
                        sheet_seat = row[2].replace("'", "").upper().strip()

                        if sheet_seat == seat_normalized:
                            row_to_update = i + 1 
                            if len(row) > 5 and row[5] == "☑️":
                                is_already_packed = True
                                if len(row) > 6:
                                    box_packed = row[6]
                            break

                    # LUỒNG XỬ LÝ & BÁO LỖI VÀO SESSION STATE ĐỂ RERUN
                    if row_to_update == -1:
                        st.session_state['error_msg'] = f"🚨 LỖI: Số ghế '{seat_normalized}' chưa được ghi nhận trên hệ thống Nhận Quà!"
                    elif is_already_packed:
                        st.session_state['error_msg'] = f"🚨 CẢNH BÁO TRÙNG LẶP: Số ghế '{seat_normalized}' đã được đóng vào Thùng số {box_packed} trước đó rồi!"
                    else:
                        # Cập nhật vào Cột 6 (Packed) và Cột 7 (Số Thùng)
                        sheet.update_cell(row_to_update, 6, "☑️")
                        sheet.update_cell(row_to_update, 7, str(box_num))
                        
                        st.session_state['success_msg'] = f"📦 Đã đóng món quà của ghế {seat_normalized} vào Thùng số {box_num} thành công!"
                        
                        # TĂNG KEY ĐỂ RESET FORM SẠCH SẼ
                        st.session_state['form_key'] += 1 
                    
                    st.rerun() 

                except Exception as e:
                    st.session_state['error_msg'] = f"Có lỗi xảy ra: {e}"
                    st.rerun()

    st.divider()

    # --- KHU VỰC 2: HIỂN THỊ DỮ LIỆU ĐỘNG ---
    st.subheader("📋 Tình trạng kiểm kê")
    
    try:
        creds = get_credentials()
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID).worksheet("Sheet1")
        all_data = sheet.get_all_values()
        
        unpacked_seats = []
        packed_boxes = {}

        for i in range(1, len(all_data)):
            row = all_data[i]
            if len(row) >= 3:
                seat = row[2].replace("'", "").strip()
                if seat:
                    is_packed = True if len(row) > 5 and row[5] == "☑️" else False
                    
                    if not is_packed:
                        unpacked_seats.append(seat)
                    else:
                        box_id = row[6] if len(row) > 6 and row[6] else "Không rõ thùng"
                        if box_id not in packed_boxes:
                            packed_boxes[box_id] = []
                        packed_boxes[box_id].append(seat)

        # 1. HIỂN THỊ DANH SÁCH CHƯA ĐÓNG
        st.markdown('<div class="question-text">⏳ Danh sách Quà chưa vào thùng:</div>', unsafe_allow_html=True)
        if unpacked_seats:
            sorted_unpacked = sort_seats(unpacked_seats)
            chips_html = "".join([f'<span class="seat-chip">{s}</span>' for s in sorted_unpacked])
            st.markdown(f"<div>{chips_html}</div>", unsafe_allow_html=True)
        else:
            st.success("Tất cả quà đã được đóng thùng!")

        st.write("") 

        # 2. HIỂN THỊ DANH SÁCH ĐÃ ĐÓNG VÀO TỪNG THÙNG
        st.markdown('<div class="question-text">✅ Thống kê Thùng:</div>', unsafe_allow_html=True)
        if packed_boxes:
            sorted_boxes = sorted(packed_boxes.keys(), key=lambda x: int(x) if x.isdigit() else 999)
            cols = st.columns(3) 
            
            for index, box_id in enumerate(sorted_boxes):
                seats_in_box = sort_seats(packed_boxes[box_id])
                seat_str = ", ".join(seats_in_box)
                
                with cols[index % 3]:
                    st.markdown(f"""
                        <div class="box-card">
                            <b style="color: #005C97; font-size: 16px;">📦 Thùng {box_id}</b> <br>
                            <span style="color: gray; font-size: 12px;">{len(seats_in_box)} món</span><br>
                            <div style="font-size: 14px; margin-top: 5px;">{seat_str}</div>
                        </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("Chưa có thùng nào được đóng.")

    except Exception as e:
        st.warning("Đang tải dữ liệu kiểm kê...")
