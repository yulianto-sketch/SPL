import streamlit as st
import pandas as pd
from streamlit_drawable_canvas import st_canvas
import datetime
import json
import os

st.set_page_config(page_title="Sistem SPL Online", page_icon="📝", layout="wide")

DB_FILE = "data_spl.json"

# --- FUNGSI SIMPAN & BACA DATA (PERMANEN KE JSON) ---
def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Inisialisasi Session State Data
if "db_spl" not in st.session_state:
    st.session_state.db_spl = load_data()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = ""

# --- HALAMAN LOGIN ---
if not st.session_state.logged_in:
    st.title("🔐 Login Sistem SPL Lembur")
    st.caption("Masuk untuk membuat, menandatangani, atau menyetujui hapus SPL")
    
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
    # Sidebar Logout
    st.sidebar.title(f"👤 {st.session_state.username}")
    st.sidebar.write(f"**Role:** {st.session_state.role}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.role = None
        st.rerun()

    st.title("📝 Surat Perintah Lembur (SPL)")
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
        canvas_admin = st_canvas(
            stroke_width=2,
            stroke_color="#000000",
            background_color="#EEEEEE",
            height=120,
            width=350,
            drawing_mode="freedraw",
            key="canvas_admin",
        )

        if st.button("Kirim Perintah Lembur", type="primary"):
            # Pengecekan aman untuk image_data kanvas
            has_drawing = False
            try:
                if canvas_admin is not None and canvas_admin.image_data is not None:
                    has_drawing = canvas_admin.image_data.any()
            except Exception:
                has_drawing = False

            if nama_karyawan and instruksi and has_drawing:
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
                st.success(f"Berhasil menerbitkan {id_spl} untuk {nama_karyawan}! Data tersimpan.")
                st.rerun()
            else:
                st.warning("Mohon lengkapi nama, instruksi, dan goreskan tanda tangan pada kotak di atas.")

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
                st.warning(f"Permohonan hapus untuk {id_to_req_del} telah dikirim ke Karyawan untuk disetujui.")
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
                stroke_width=2,
                stroke_color="#000000",
                background_color="#EEEEEE",
                height=120,
                width=350,
                drawing_mode="freedraw",
                key="canvas_user",
            )
            
            if st.button("Konfirmasi & Tanda Tangan SPL", type="primary"):
                has_drawing_user = False
                try:
                    if canvas_user is not None and canvas_user.image_data is not None:
                        has_drawing_user = canvas_user.image_data.any()
                except Exception:
                    has_drawing_user = False

                if has_drawing_user:
                    for item in st.session_state.db_spl:
                        if item["id"] == selected_id:
                            item["ttd_user"] = True
                            item["status"] = "Selesai (ACC 2 Belah Pihak)"
                            break
                    save_data(st.session_state.db_spl)
                    st.success(f"SPL {selected_id} berhasil disetujui! Bukti tersimpan permanen.")
                    st.rerun()
                else:
                    st.warning("Mohon bubuhkan tanda tangan sebelum mengonfirmasi.")
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
    # TABEL ARSIP BUKTI
    # ==========================================
    st.divider()
    st.subheader("📂 Arsip Bukti Pengajuan SPL")
    
    if st.session_state.db_spl:
        df = pd.DataFrame(st.session_state.db_spl)
        st.dataframe(df[["id", "tanggal", "karyawan", "departemen", "jam", "instruksi", "status"]], use_container_width=True)
    else:
        st.caption("Belum ada arsip SPL.")
