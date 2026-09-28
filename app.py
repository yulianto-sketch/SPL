import streamlit as st
import pandas as pd
from streamlit_drawable_canvas import st_canvas
import datetime
import json
import os
from fpdf import FPDF

st.set_page_config(page_title="Sistem SPL Online", page_icon="📝", layout="wide")

DB_FILE = "data_spl.json"

# --- FUNGSI GENERATE PDF SPL ---
def generate_pdf(spl_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    
    # Header Document
    pdf.cell(0, 10, "SURAT PERINTAH LEMBUR (SPL)", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 5, f"Nomor Dokumen: {spl_data['id']}", ln=True, align="C")
    pdf.ln(10)
    
    # Detail SPL
    pdf.set_font("Arial", "", 11)
    pdf.cell(50, 8, "Nama Karyawan", border=0)
    pdf.cell(5, 8, ":", border=0)
    pdf.cell(0, 8, f"{spl_data['karyawan']}", border=0, ln=True)
    
    pdf.cell(50, 8, "Departemen", border=0)
    pdf.cell(5, 8, ":", border=0)
    pdf.cell(0, 8, f"{spl_data['departemen']}", border=0, ln=True)
    
    pdf.cell(50, 8, "Tanggal Lembur", border=0)
    pdf.cell(5, 8, ":", border=0)
    pdf.cell(0, 8, f"{spl_data['tanggal']}", border=0, ln=True)
    
    pdf.cell(50, 8, "Jam Lembur", border=0)
    pdf.cell(5, 8, ":", border=0)
    pdf.cell(0, 8, f"{spl_data['jam']}", border=0, ln=True)
    
    pdf.ln(5)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 8, "Instruksi Pekerjaan Lembur:", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 6, f"{spl_data['instruksi']}", border=1)
    
    pdf.ln(15)
    
    # Status Tanda Tangan
    pdf.set_font("Arial", "B", 10)
    pdf.cell(90, 8, "Pemberi Perintah (Atasan)", align="C")
    pdf.cell(90, 8, "Penerima Perintah (Karyawan)", align="C", ln=True)
    
    pdf.ln(15) # Ruang untuk TTD
    
    pdf.set_font("Arial", "", 10)
    ttd_admin_status = "[ VALID - TTD DIGITAL ]" if spl_data.get("ttd_admin") else "[ BELUM TTD ]"
    ttd_user_status = "[ VALID - TTD DIGITAL ]" if spl_data.get("ttd_user") else "[ BELUM TTD ]"
    
    pdf.cell(90, 6, ttd_admin_status, align="C")
    pdf.cell(90, 6, ttd_user_status, align="C", ln=True)
    
    pdf.cell(90, 6, "( Atasan / Supervisor )", align="C")
    pdf.cell(90, 6, f"( {spl_data['karyawan']} )", align="C", ln=True)
    
    return pdf.output(dest="S").encode("latin-1")

# --- FUNGSI BACA, FILTER 3 BULAN, & SIMPAN DATA ---
def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                data = json.load(f)
                
            # Filter otomatis: hapus data yang lebih tua dari 90 hari (3 bulan)
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

# Inisialisasi Session State
if "db_spl" not in st.session_state:
    st.session_state.db_spl = load_data()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = ""

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
                st.error("Username atau Password salah! (Hint: admin/123 atau user/1234)")

# --- HALAMAN UTAMA ---
else:
    st.sidebar.title(f"👤 {st.session_state.username}")
    st.sidebar.write(f"**Role:** {st.session_state.role}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.role = None
        st.rerun()

    st.title("📝 Surat Perintah Lembur (SPL)")
    st.caption("🗓️ *Histori tersimpan otomatis selama 3 bulan terakhir*")
    st.divider()

    # ==========================================
    # ROLE ADMIN (ATASAN)
    # ==========================================
    if st.session_state.role == "Admin":
        st.subheader("👨‍💼 1. Buat Perintah Lembur Baru")
        
        col1, col2 = st.columns(2)
        with col1:
            nama_karyawan = st.text_input("Nama Karyawan yang Ditugaskan")
            departemen = st.selectbox("Departemen", ["Produksi", "Quality Control", "Warehouse", "HRD & GA", "IT", "Maintenance"])
            tanggal = st.date_input("Tanggal Lembur", datetime.date.today())
        with col2:
            jam_mulai = st.time_input("Jam Mulai", datetime.time(17, 0))
            jam_selesai = st.time_input("Jam Selesai", datetime.time(20, 0))
            instruksi = st.text_area("Instruksi / Perintah Pekerjaan Lembur")

        st.write("**Tanda Tangan Atasan (Pemberi Perintah):**")
        st.caption("💡 *Goreskan tanda tangan pada kotak abu-abu di bawah ini:*")
        
        canvas_admin = st_canvas(
            stroke_width=3,
            stroke_color="#000000",
            background_color="#EEEEEE",
            height=130,
            width=350,
            drawing_mode="freedraw",
            update_streamlit=True,
            key="canvas_admin_safe",
        )

        if st.button("Kirim Perintah Lembur", type="primary"):
            err_msg = []
            if not nama_karyawan.strip():
                err_msg.append("Nama Karyawan belum diisi")
            if not instruksi.strip():
                err_msg.append("Instruksi Pekerjaan belum diisi")

            ttd_ada = False
            try:
                if canvas_admin is not None and canvas_admin.json_data is not None:
                    objects = canvas_admin.json_data.get("objects", [])
                    if len(objects) > 0:
                        ttd_ada = True
            except Exception:
                ttd_ada = False

            if not ttd_ada:
                err_msg.append("Tanda tangan belum digoreskan")

            if err_msg:
                st.error("⚠️ Gagal mengirim! " + " | ".join(err_msg))
            else:
                id_spl = f"SPL-{len(st.session_state.db_spl) + 1:03d}"
                data_baru = {
                    "id": id_spl,
                    "karyawan": nama_karyawan,
                    "departemen": departemen,
                    "tanggal": tanggal.strftime("%Y-%m-%d"),
                    "jam": f"{jam_mulai.strftime('%H:%M')} - {jam_selesai.strftime('%H:%M')}",
                    "instruksi": instruksi,
                    "ttd_admin": True,
                    "ttd_user": False,
                    "req_delete": False,
                    "status": "Menunggu TTD Karyawan"
                }
                st.session_state.db_spl.append(data_baru)
                save_data(st.session_state.db_spl)
                st.success(f"✅ Berhasil menerbitkan {id_spl} untuk {nama_karyawan}!")
                st.rerun()

        # --- MENU AJUKAN HAPUS DATA (ADMIN) ---
        st.divider()
        st.subheader("🗑️ 2. Permohonan Hapus SPL (Butuh ACC Karyawan)")
        
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
                st.warning(f"Permohonan hapus untuk {id_to_req_del} telah dikirim ke Karyawan.")
                st.rerun()
        else:
            st.caption("Tidak ada data SPL yang bisa diajukan hapus.")

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
            **Nomor SPL:** `{spl_data['id']}`  
            **Untuk Karyawan:** {spl_data['karyawan']} ({spl_data['departemen']})  
            **Tanggal & Jam:** {spl_data['tanggal']} | {spl_data['jam']}  
            **Instruksi Lembur:** {spl_data['instruksi']}  
            **Status TTD Atasan:** ✅ Sudah ditandatangani Atasan
            """)
            
            st.write("**Tanda Tangan Karyawan (Penerima Perintah):**")
            canvas_user = st_canvas(
                stroke_width=3,
                stroke_color="#000000",
                background_color="#EEEEEE",
                height=130,
                width=350,
                drawing_mode="freedraw",
                update_streamlit=True,
                key="canvas_user_safe",
            )
            
            if st.button("Konfirmasi & Tanda Tangan SPL", type="primary"):
                ttd_user_ada = False
                try:
                    if canvas_user is not None and canvas_user.json_data is not None:
                        objects = canvas_user.json_data.get("objects", [])
                        if len(objects) > 0:
                            ttd_user_ada = True
                except Exception:
                    ttd_user_ada = False

                if ttd_user_ada:
                    for item in st.session_state.db_spl:
                        if item["id"] == selected_id:
                            item["ttd_user"] = True
                            item["status"] = "Selesai (ACC 2 Belah Pihak)"
                            break
                    save_data(st.session_state.db_spl)
                    st.success(f"✅ SPL {selected_id} berhasil disetujui!")
                    st.rerun()
                else:
                    st.error("⚠️ Tanda tangan belum terdeteksi. Silakan goreskan tanda tangan pada kotak terlebih dahulu.")
        else:
            st.info("Tidak ada perintah lembur baru yang menunggu tanda tangan Anda.")

        # --- MENU PERSETUJUAN HAPUS (USER) ---
        st.divider()
        st.subheader("⚠️ 2. Permohonan Hapus dari Atasan")
        
        spl_req_delete = [s for s in st.session_state.db_spl if s.get("req_delete", False)]
        if spl_req_delete:
            st.warning("Atasan meminta untuk menghapus data SPL berikut. Klik setuju jika konfirmasi hapus.")
            for s in spl_req_delete:
                col_info, col_btn = st.columns([3, 1])
                with col_info:
                    st.write(f"📌 **{s['id']}** - {s['karyawan']} ({s['tanggal']}) | *{s['instruksi']}*")
                with col_btn:
                    if st.button(f"Setujui Hapus {s['id']}", key=f"btn_del_{s['id']}"):
                        st.session_state.db_spl = [item for item in st.session_state.db_spl if item["id"] != s["id"]]
                        save_data(st.session_state.db_spl)
                        st.success(f"Data {s['id']} telah resmi dihapus permanen!")
                        st.rerun()
        else:
            st.caption("Tidak ada permohonan hapus dari Atasan.")

    # ==========================================
    # TABEL ARSIP & DOWNLOAD PDF (BISA AKSES DUA ROLE)
    # ==========================================
    st.divider()
    st.subheader("📂 Arsip Bukti & Download PDF SPL (3 Bulan Terakhir)")
    
    if st.session_state.db_spl:
        for spl in reversed(st.session_state.db_spl):
            with st.expander(f"📄 {spl['id']} - {spl['karyawan']} ({spl['tanggal']}) - Status: {spl['status']}"):
                col_detail, col_dl = st.columns([3, 1])
                
                with col_detail:
                    st.write(f"**Departemen:** {spl['departemen']}")
                    st.write(f"**Jam Lembur:** {spl['jam']}")
                    st.write(f"**Instruksi Pekerjaan:** {spl['instruksi']}")
                    st.write(f"**TTD Atasan:** {'✅ Sudah' if spl.get('ttd_admin') else '❌ Belum'}")
                    st.write(f"**TTD Karyawan:** {'✅ Sudah' if spl.get('ttd_user') else '❌ Belum'}")
                
                with col_dl:
                    pdf_bytes = generate_pdf(spl)
                    st.download_button(
                        label="📄 Download PDF",
                        data=pdf_bytes,
                        file_name=f"Surat_Perintah_Lembur_{spl['id']}.pdf",
                        mime="application/pdf",
                        key=f"dl_pdf_{spl['id']}"
                    )
    else:
        st.info("Belum ada arsip Surat Perintah Lembur.")
