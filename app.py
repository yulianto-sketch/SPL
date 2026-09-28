import streamlit as st
import pandas as pd
import datetime
import json
import os
import time
from fpdf import FPDF

st.set_page_config(page_title="Sistem SPL Online", page_icon="📝", layout="wide")

DB_FILE = "data_spl.json"

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
    
    pdf.ln(12)
    
    # --- KETERANGAN PENGESAHAN OTOMATIS (DIGITAL APPROVAL STATEMENT) ---
    pdf.set_font("Arial", "I", 9)
    status_text = spl_data.get('status', 'Disetujui secara elektronik')
    
    pdf.multi_cell(
        0, 5, 
        f"Catatan Pengesahan:\n"
        f"Dokumen Surat Perintah Lembur ini telah diterbitkan oleh Atasan ({spl_data.get('nama_atasan', 'Atasan')}) "
        f"dan dikonfirmasi oleh Karyawan ({spl_data['karyawan']}) secara elektronik melalui Sistem SPL Online. "
        f"Dokumen ini sah dan berlaku resmi tanpa memerlukan tanda tangan basah.\n"
        f"Status Dokumen: {status_text}",
        border=1,
        align="L"
    )
    
    pdf.ln(10)
    
    # Informasi Pihak Terkait
    pdf.set_font("Arial", "B", 10)
    pdf.cell(90, 6, "Diterbitkan Oleh (Atasan):", align="C")
    pdf.cell(90, 6, "Disetujui Oleh (Karyawan):", align="C", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("Arial", "", 10)
    nama_atasan_ttd = spl_data.get('nama_atasan', 'Atasan / Supervisor')
    pdf.cell(90, 6, f"[ {nama_atasan_ttd} ]", align="C")
    pdf.cell(90, 6, f"[ {spl_data['karyawan']} ]", align="C", new_x="LMARGIN", new_y="NEXT")
    
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

if "show_success_notif" not in st.session_state:
    st.session_state.show_success_notif = False

# --- HALAMAN LOGIN ---
if not st.session_state.logged_in:
    st.title("🔐 Login Sistem SPL Lembur")
    st.caption("Masuk untuk membuat, mengonfirmasi, atau mengunduh dokumen SPL")
    
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
        st.session_state.show_success_notif = False
        st.rerun()

    st.title("📝 Surat Perintah Lembur (SPL)")
    st.divider()

    # ==========================================
    # ROLE ADMIN (ATASAN)
    # ==========================================
    if st.session_state.role == "Admin":
        st.subheader("👨‍💼 1. Buat Perintah Lembur Baru")
        
        # --- NOTIFIKASI SEMENTARA (HILANG DALAM 2 DETIK) ---
        if st.session_state.show_success_notif:
            notif_container = st.empty()
            with notif_container.container():
                st.success("🎉 **SURAT PERINTAH LEMBUR BERHASIL DITERBITKAN & TERKIRIM!**")
            time.sleep(2)
            notif_container.empty()
            st.session_state.show_success_notif = False

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

        st.divider()

        if st.button("🚀 Kirim Perintah Lembur", type="primary"):
            err_msg = []
            if not nama_atasan.strip():
                err_msg.append("Nama Atasan belum diisi")
            if not nama_karyawan.strip():
                err_msg.append("Nama Karyawan belum diisi")
            if not instruksi.strip():
                err_msg.append("Instruksi Pekerjaan belum diisi")

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
                    "confirmed_user": False,
                    "req_delete": False,
                    "status": "Menunggu Konfirmasi Karyawan"
                }
                st.session_state.db_spl.append(data_baru)
                save_data(st.session_state.db_spl)
                
                st.session_state.show_success_notif = True
                st.toast(f"🚀 {id_spl} Terkirim!", icon="✅")
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
        st.subheader("👷 1. Konfirmasi Penerimaan SPL")
        
        # Hanya tampilkan SPL yang BELUM dikonfirmasi user
        spl_pending = [s for s in st.session_state.db_spl if not s.get("confirmed_user", False) and not s.get("req_delete", False)]
        
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

            st.divider()

            if st.button("✅ Konfirmasi Terima SPL", type="primary"):
                for item in st.session_state.db_spl:
                    if item["id"] == selected_id:
                        item["confirmed_user"] = True
                        item["status"] = "Selesai (Disetujui secara Elektronik)"
                        break
                save_data(st.session_state.db_spl)
                
                # Tampilkan notifikasi singkat 2 detik lalu hilangkan tampilan
                notif_user = st.empty()
                notif_user.success(f"🎉 SPL {selected_id} Berhasil Dikonfirmasi & Disetujui!")
                time.sleep(2)
                notif_user.empty()
                st.rerun()
        else:
            st.info("Tidak ada perintah lembur baru yang menunggu konfirmasi Anda.")

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
