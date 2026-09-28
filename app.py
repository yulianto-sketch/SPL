import streamlit as st
import pandas as pd
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import datetime

st.set_page_config(page_title="SPL Online - Bukti Lembur", page_icon="📝", layout="wide")

# --- DATABASE SEMENTARA (SESSION STATE) ---
if "db_spl" not in st.session_state:
    st.session_state.db_spl = []

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = ""

# --- HALAMAN LOGIN ---
if not st.session_state.logged_in:
    st.title("🔐 Login Sistem SPL Lembur")
    st.caption("Masuk untuk membuat atau menandatangani Surat Perintah Lembur")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_login = st.form_submit_button("Masuk")
        
        if submit_login:
            # Login akun sederhana (Bisa disesuaikan)
            if username == "admin" and password == "admin123":
                st.session_state.logged_in = True
                st.session_state.role = "Admin"
                st.session_state.username = "Atasan / Admin"
                st.rerun()
            elif username == "user" and password == "user123":
                st.session_state.logged_in = True
                st.session_state.role = "User"
                st.session_state.username = "Karyawan / User"
                st.rerun()
            else:
                st.error("Username atau Password salah! (Hint: admin/admin123 atau user/user123)")

# --- HALAMAN SETELAH LOGIN ---
else:
    # Sidebar Logout & Info Account
    st.sidebar.title(f"👤 {st.session_state.username}")
    st.sidebar.write(f"**Role:** {st.session_state.role}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.role = None
        st.rerun()

    st.title("📝 Surat Perintah Lembur (SPL)")
    st.divider()

    # ==========================================
    # ROLE ADMIN (ATASAN) -> BUAT PERINDAH & TTD
    # ==========================================
    if st.session_state.role == "Admin":
        st.subheader("👨‍💼 Form Buat Perintah Lembur (Admin)")
        
        with st.form("form_buat_spl"):
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

            submit_spl = st.form_submit_button("Kirim Perintah Lembur")

            if submit_spl:
                if nama_karyawan and instruksi and canvas_admin.image_data is not None:
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
                        "status": "Menunggu TTD Karyawan"
                    }
                    st.session_state.db_spl.append(data_baru)
                    st.success(f"Berhasil menerbitkan {id_spl} untuk {nama_karyawan}!")
                else:
                    st.warning("Mohon lengkapi nama, instruksi, dan tanda tangan.")

    # ==========================================
    # ROLE USER (KARYAWAN) -> TERIMA & TTD
    # ==========================================
    elif st.session_state.role == "User":
        st.subheader("👷 Daftar Perintah Lembur Diterima (Karyawan)")
        
        # Cari SPL yang perlu ditandatangani
        spl_pending = [s for s in st.session_state.db_spl if not s["ttd_user"]]
        
        if spl_pending:
            st.info("Pilih SPL di bawah ini untuk mengonfirmasi dan menandatangani sebagai bukti diterima.")
            
            # Pilih Nomor SPL
            list_id = [s["id"] for s in spl_pending]
            selected_id = st.selectbox("Pilih Nomor SPL:", list_id)
            
            # Detail SPL terpilih
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
            
            if st.button("Konfirmasi & Tanda Tangan SPL"):
                spl_data["ttd_user"] = True
                spl_data["status"] = "Selesai (ACC 2 Belah Pihak)"
                st.success(f"SPL {selected_id} berhasil disetujui! Bukti lembur tersimpan.")
                st.rerun()
        else:
            st.success("Tidak ada perintah lembur baru yang menunggu tanda tangan Anda.")

    # ==========================================
    # TABEL BUKTI REKAPITULASI (BISA DILIHAT DUA-DUANYA)
    # ==========================================
    st.divider()
    st.subheader("📂 Bukti Arsip Perintah Lembur")
    
    if st.session_state.db_spl:
        df = pd.DataFrame(st.session_state.db_spl)
        # Tampilkan kolom ringkasan tanpa data gambar
        st.dataframe(df[["id", "tanggal", "karyawan", "departemen", "jam", "instruksi", "status"]], use_container_width=True)
    else:
        st.caption("Belum ada arsip SPL.")
