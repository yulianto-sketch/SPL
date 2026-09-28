import streamlit as st
import pandas as pd
from streamlit_drawable_canvas import st_canvas
import datetime
import json
import os
import base64
import numpy as np
from io import BytesIO
from PIL import Image
from fpdf import FPDF

st.set_page_config(page_title="Sistem SPL Online", page_icon="📝", layout="wide")

DB_FILE = "data_spl.json"

# --- FUNGSI DETEKSI & KONVERSI TANDA TANGAN ---
def get_canvas_base64(canvas_obj):
    if canvas_obj is None or canvas_obj.image_data is None:
        return None
    try:
        img_data = canvas_obj.image_data
        if isinstance(img_data, np.ndarray):
            # Cek transparansi (Alpha channel > 0) atau ketebalan warna
            alpha = img_data[:, :, 3]
            if np.sum(alpha > 0) > 10:  # Jika ada minimal 10 piksel terisi
                img = Image.fromarray(img_data.astype('uint8'), 'RGBA')
                buffered = BytesIO()
                img.save(buffered, format="PNG")
                return base64.b64encode(buffered.getvalue()).decode('utf-8')
    except Exception:
        pass
    return None

# --- HELPER BASE64 TO FILE ---
def base64_to_temp_file(base64_str, filename):
    try:
        img_data = base64.b64decode(base64_str)
        img = Image.open(BytesIO(img_data))
        img.save(filename, "PNG")
        return filename
    except Exception:
        return None

# --- GENERATE PDF ---
def generate_pdf(spl_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    
    pdf.cell(0, 10, "SURAT PERINTAH LEMBUR (SPL)", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 5, f"Nomor Dokumen: {spl_data['id']}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(10)
    
    pdf.set_font("Arial", "", 11)
    pdf.cell(50, 8, "Nama Atasan (Pemberi)", border=0)
    pdf.cell(5, 8, ":", border=0)
    pdf.cell(0, 8, f"{spl_data.get('nama_atasan', 'Atasan / Admin')}", border=0, new_x="LMARGIN", new_y="NEXT")

    pdf.cell(50, 8, "Nama Karyawan", border=0)
    pdf.cell(5, 8, ":", border=0)
    pdf.cell(0, 8, f"{spl_data['karyawan']}", border=0, new_x="LMARGIN", new_y="NEXT")
    
    pdf.cell(50, 8, "Departemen", border=0)
    pdf.cell(5, 8, ":", border=0)
    pdf.cell(0, 8, f"{spl_data['departemen']}", border=0, new_x="LMARGIN", new_y="NEXT")
    
    pdf.cell(50, 8, "Tanggal Lembur", border=0)
    pdf.cell(5, 8, ":", border=0)
    pdf.cell(0, 8, f"{spl_data['tanggal']}", border=0, new_x="LMARGIN", new_y="NEXT")
    
    pdf.cell(50, 8, "Jam Lembur", border=0)
    pdf.cell(5, 8, ":", border=0)
    pdf.cell(0, 8, f"{spl_data['jam']}", border=0, new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(5)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, "Instruksi Pekerjaan Lembur:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 6, f"{spl_data['instruksi']}", border=1)
    
    pdf.ln(10)
    
    pdf.set_font("Arial", "B", 10)
    pdf.cell(90, 8, "Pemberi Perintah (Atasan)", align="C")
    pdf.cell(90, 8, "Penerima Perintah (Karyawan)", align="C", new_x="LMARGIN", new_y="NEXT")
    
    y_before_ttd = pdf.get_y()
    
    if spl_data.get("ttd_admin_img"):
        file_admin = f"temp_admin_{spl_data['id']}.png"
        if base64_to_temp_file(spl_data["ttd_admin_img"], file_admin):
            pdf.image(file_admin, x=35, y=y_before_ttd, w=40, h=20)
            if os.path.exists(file_admin):
                os.remove(file_admin)

    if spl_data.get("ttd_user_img"):
        file_user = f"temp_user_{spl_data['id']}.png"
        if base64_to_temp_file(spl_data["ttd_user_img"], file_user):
            pdf.image(file_user, x=125, y=y_before_ttd, w=40, h=20)
            if os.path.exists(file_user):
                os.remove(file_user)

    pdf.ln(22)
    pdf.set_font("Arial", "", 10)
    nama_atasan_ttd = spl_data.get('nama_atasan', 'Atasan / Supervisor')
    pdf.cell(90, 6, f"( {nama_atasan_ttd} )", align="C")
    pdf.cell(90, 6, f"( {spl_data['karyawan']} )", align="C", new_x="LMARGIN", new_y="NEXT")
    
    return bytes(pdf.output())

# --- DATABASE LOAD/SAVE ---
def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                data = json.load(f)
            today = datetime.date.today()
            filtered_data = []
            for item in data:
                try:
                    tgl_item = datetime.datetime.strptime(item["tanggal"], "%Y-%m-%d").date()
                    if (today - tgl_item).days <= 90:
                        filtered_data.append(item)
                except Exception:
                    filtered_data.append(item)
            return filtered_data
        except Exception:
            return []
    return []

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

def hitung_durasi_jam(string_jam):
    try:
        jam_mulai_str, jam_selesai_str = string_jam.split(" - ")
        t_mulai = datetime.datetime.strptime(jam_mulai_str.strip(), "%H:%M")
        t_selesai = datetime.datetime.strptime(jam_selesai_str.strip(), "%H:%M")
        if t_selesai < t_mulai:
            t_selesai += datetime.timedelta(days=1)
        selisih = t_selesai - t_mulai
        return selisih.total_seconds() / 3600.0
    except Exception:
        return 0.0

st.session_state.db_spl = load_data()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = ""

if "last_sent_spl" not in st.session_state:
    st.session_state.last_sent_spl = None

if "reset_canvas_admin" not in st.session_state:
    st.session_state.reset_canvas_admin = 0

if "reset_canvas_user" not in st.session_state:
    st.session_state.reset_canvas_user = 0

# --- HALAMAN LOGIN ---
if not st.session_state.logged_in:
    st.title("🔐 Login Sistem SPL Lembur")
    st.caption("Masuk untuk membuat, menandatangani, atau mengunduh dokumen SPL")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_login = st.form_submit_button("Masuk")
        
        if submit_login:
            if username == "admin" and password == "123":
                st.session_state.logged_in = True
                st.session_state.role = "Admin"
                st.session_state.username = "Atasan / Admin"
                st.rerun()
            elif username == "user" and password == "1234":
                st.session_state.logged_in = True
                st.session_state.role = "User"
                st.session_state.username = "Karyawan / User"
                st.rerun()
            else:
                st.error("Username atau Password salah!")

# --- HALAMAN UTAMA ---
else:
    st.sidebar.title(f"👤 {st.session_state.username}")
    st.sidebar.write(f"**Role:** {st.session_state.role}")
    
    if st.sidebar.button("🔄 Perbarui Data"):
        st.session_state.db_spl = load_data()
        st.toast("Data diperbarui!", icon="🔄")
        st.rerun()
        
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.role = None
        st.session_state.last_sent_spl = None
        st.rerun()

    st.title("📝 Surat Perintah Lembur (SPL)")
    st.divider()

    # ==========================================
    # ROLE ADMIN (ATASAN)
    # ==========================================
    if st.session_state.role == "Admin":
        st.subheader("👨‍💼 1. Buat Perintah Lembur Baru")
        
        if st.session_state.last_sent_spl:
            spl_sent = st.session_state.last_sent_spl
            st.success("🎉 **SURAT PERINTAH LEMBUR BERHASIL DITERBITKAN & TERKIRIM!**")
            st.info(f"Nomor Dokumen: `{spl_sent['id']}` | Karyawan: {spl_sent['karyawan']} | Status: Menunggu TTD Karyawan")
            
            if st.button("➕ Buat SPL Baru Lagi"):
                st.session_state.last_sent_spl = None
                st.rerun()
            st.divider()

        col1, col2 = st.columns(2)
        with col1:
            nama_atasan = st.text_input("Nama Atasan / Pemberi Perintah")
            nama_karyawan = st.text_input("Nama Karyawan yang Ditugaskan")
            departemen = st.selectbox("Departemen", ["Driver"])
        with col2:
            tanggal = st.date_input("Tanggal Lembur", datetime.date.today())
            jam_mulai = st.time_input("Jam Mulai", datetime.time(17, 0))
            jam_selesai = st.time_input("Jam Selesai", datetime.time(20, 0))
            
        instruksi = st.text_area("Instruksi / Perintah Pekerjaan Lembur")

        st.write("**Tanda Tangan Atasan:**")
        st.caption("✏️ Goreskan tanda tangan Anda pada kotak di bawah ini.")
        
        canvas_admin_key = f"canvas_admin_{st.session_state.reset_canvas_admin}"
        canvas_admin = st_canvas(
            stroke_width=3,
            stroke_color="#000000",
            background_color="#FFFFFF",
            height=130,
            width=350,
            drawing_mode="freedraw",
            update_streamlit=True,
            key=canvas_admin_key,
        )

        # OTOMATIS AMBIL DATA GAMBAR DARI CANVAS
        ttd_admin_base64 = get_canvas_base64(canvas_admin)

        col_a1, col_a2 = st.columns([2, 2])
        with col_a1:
            if ttd_admin_base64:
                st.success("✅ Tanda tangan terdeteksi!")
            else:
                st.warning("⚠️ Belum ada tanda tangan di canvas.")

        with col_a2:
            if st.button("🗑️ Reset Tanda Tangan", key="reset_admin"):
                st.session_state.reset_canvas_admin += 1
                st.rerun()

        st.divider()

        if st.button("🚀 Kirim Perintah Lembur", type="primary"):
            err_msg = []
            if not nama_atasan.strip():
                err_msg.append("Nama Atasan belum diisi")
            if not nama_karyawan.strip():
                err_msg.append("Nama Karyawan belum diisi")
            if not instruksi.strip():
                err_msg.append("Instruksi Pekerjaan belum diisi")
            if not ttd_admin_base64:
                err_msg.append("Tanda tangan Atasan belum diisi di canvas")

            if err_msg:
                st.error("⚠️ " + " | ".join(err_msg))
            else:
                id_spl = f"SPL-{len(st.session_state.db_spl) + 1:03d}"
                data_baru = {
                    "id": id_spl,
                    "nama_atasan": nama_atasan,
                    "karyawan": nama_karyawan,
                    "departemen": departemen,
                    "tanggal": tanggal.strftime("%Y-%m-%d"),
                    "jam": f"{jam_mulai.strftime('%H:%M')} - {jam_selesai.strftime('%H:%M')}",
                    "instruksi": instruksi,
                    "ttd_admin": True,
                    "ttd_admin_img": ttd_admin_base64,
                    "ttd_user": False,
                    "ttd_user_img": None,
                    "req_delete": False,
                    "status": "Menunggu TTD Karyawan"
                }
                st.session_state.db_spl.append(data_baru)
                save_data(st.session_state.db_spl)
                
                st.session_state.reset_canvas_admin += 1
                st.session_state.last_sent_spl = data_baru
                st.toast(f"✅ {id_spl} Berhasil Dikirim!", icon="🚀")
                st.balloons()
                st.rerun()

        # --- MENU HAPUS ---
        st.divider()
        st.subheader("🗑️ 2. Permohonan Hapus SPL")
        spl_aktif = [s for s in st.session_state.db_spl if not s.get("req_delete", False)]
        if spl_aktif:
            list_id_del = [s["id"] for s in spl_aktif]
            id_to_req_del = st.selectbox("Pilih Nomor SPL yang ingin dihapus:", list_id_del, key="select_del_admin")
            if st.button("Ajukan Penghapusan ke Karyawan"):
                for item in st.session_state.db_spl:
                    if item["id"] == id_to_req_del:
                        item["req_delete"] = True
                        item["status"] = "Menunggu Persetujuan Hapus Karyawan"
                        break
                save_data(st.session_state.db_spl)
                st.warning(f"Permohonan hapus untuk {id_to_req_del} dikirim ke Karyawan.")
                st.rerun()

    # ==========================================
    # ROLE USER (KARYAWAN)
    # ==========================================
    elif st.session_state.role == "User":
        st.subheader("👷 1. Tanda Tangan Penerimaan SPL")
        
        spl_pending = [s for s in st.session_state.db_spl if not s["ttd_user"] and not s.get("req_delete", False)]
        
        if spl_pending:
            list_id = [s["id"] for s in spl_pending]
            selected_id = st.selectbox("Pilih Nomor SPL:", list_id)
            spl_data = next(s for s in spl_pending if s["id"] == selected_id)
            
            st.markdown(f"""
            **Nomor SPL:** `{spl_data['id']}` | **Atasan:** {spl_data.get('nama_atasan', '-')}  
            **Karyawan:** {spl_data['karyawan']} ({spl_data['departemen']})  
            **Tanggal & Jam:** {spl_data['tanggal']} | {spl_data['jam']}  
            **Instruksi:** {spl_data['instruksi']}
            """)
            
            st.write("**Tanda Tangan Karyawan:**")
            st.caption("✏️ Goreskan tanda tangan Anda pada kotak di bawah ini.")

            canvas_user_key = f"canvas_user_{st.session_state.reset_canvas_user}"
            canvas_user = st_canvas(
                stroke_width=3,
                stroke_color="#000000",
                background_color="#FFFFFF",
                height=130,
                width=350,
                drawing_mode="freedraw",
                update_streamlit=True,
                key=canvas_user_key,
            )

            ttd_user_base64 = get_canvas_base64(canvas_user)

            col_u1, col_u2 = st.columns([2, 2])
            with col_u1:
                if ttd_user_base64:
                    st.success("✅ Tanda tangan terdeteksi!")
                else:
                    st.warning("⚠️ Belum ada tanda tangan di canvas.")

            with col_u2:
                if st.button("🗑️ Reset Tanda Tangan", key="reset_user"):
                    st.session_state.reset_canvas_user += 1
                    st.rerun()

            st.divider()

            if st.button("Konfirmasi & Tanda Tangan SPL", type="primary"):
                if ttd_user_base64:
                    for item in st.session_state.db_spl:
                        if item["id"] == selected_id:
                            item["ttd_user"] = True
                            item["ttd_user_img"] = ttd_user_base64
                            item["status"] = "Selesai (ACC 2 Belah Pihak)"
                            break
                    save_data(st.session_state.db_spl)
                    st.session_state.reset_canvas_user += 1
                    st.toast(f"✅ SPL {selected_id} disetujui!", icon="🎉")
                    st.rerun()
                else:
                    st.error("⚠️ Silakan goreskan tanda tangan Anda terlebih dahulu!")
        else:
            st.info("Tidak ada perintah lembur baru yang menunggu tanda tangan Anda.")

        # --- MENU PERSETUJUAN HAPUS ---
        st.divider()
        st.subheader("⚠️ 2. Permohonan Hapus dari Atasan")
        spl_req_delete = [s for s in st.session_state.db_spl if s.get("req_delete", False)]
        if spl_req_delete:
            for s in spl_req_delete:
                col_info, col_btn = st.columns([3, 1])
                with col_info:
                    st.write(f"📌 **{s['id']}** - {s['karyawan']} ({s['tanggal']})")
                with col_btn:
                    if st.button(f"Setujui Hapus {s['id']}", key=f"btn_del_{s['id']}"):
                        st.session_state.db_spl = [item for item in st.session_state.db_spl if item["id"] != s["id"]]
                        save_data(st.session_state.db_spl)
                        st.success(f"Data {s['id']} dihapus permanen!")
                        st.rerun()

    # ==========================================
    # FILTER PERIODE & ARSIP PDF
    # ==========================================
    st.divider()
    st.subheader("📊 Pencarian & Total Jam Lembur")
    
    col_f1, col_f2, col_f3 = st.columns([2, 2, 2])
    with col_f1:
        start_date = st.date_input("Tanggal Mulai", datetime.date.today() - datetime.timedelta(days=30))
    with col_f2:
        end_date = st.date_input("Tanggal Selesai", datetime.date.today())
    with col_f3:
        filter_nama = st.text_input("Filter Nama Karyawan", "")

    data_filtered = []
    total_jam_periode = 0.0

    for item in st.session_state.db_spl:
        try:
            tgl_item = datetime.datetime.strptime(item["tanggal"], "%Y-%m-%d").date()
            if start_date <= tgl_item <= end_date:
                if filter_nama.strip() == "" or filter_nama.lower() in item["karyawan"].lower():
                    durasi = hitung_durasi_jam(item["jam"])
                    item_copy = item.copy()
                    item_copy["durasi_jam"] = durasi
                    data_filtered.append(item_copy)
                    total_jam_periode += durasi
        except Exception:
            pass

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.metric("Total Dokumen SPL", f"{len(data_filtered)} SPL")
    with col_m2:
        st.metric("Total Jam Lembur Periode Ini", f"{total_jam_periode:.1f} Jam")

    st.subheader("📂 Detail Arsip & Download PDF SPL")
    if data_filtered:
        for spl in reversed(data_filtered):
            durasi_text = f"{spl.get('durasi_jam', 0):.1f} Jam"
            with st.expander(f"📄 {spl['id']} - {spl['karyawan']} ({spl['tanggal']}) | {durasi_text} - Status: {spl['status']}"):
                col_detail, col_dl = st.columns([3, 1])
                with col_detail:
                    st.write(f"**Pemberi Perintah:** {spl.get('nama_atasan', '-')}")
                    st.write(f"**Karyawan:** {spl['karyawan']} ({spl['departemen']})")
                    st.write(f"**Jam Lembur:** {spl['jam']} ({durasi_text})")
                    st.write(f"**Instruksi:** {spl['instruksi']}")
                with col_dl:
                    pdf_bytes = generate_pdf(spl)
                    st.download_button(
                        label="📄 Download PDF",
                        data=pdf_bytes,
                        file_name=f"Surat_Perintah_Lembur_{spl['id']}.pdf",
                        mime="application/pdf",
                        key=f"dl_pdf_{spl['id']}"
                    )
