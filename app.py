import streamlit as st
import pandas as pd

# Konfigurasi Halaman
st.set_page_config(page_title="Sistem Pengajuan SPL", page_icon="📝", layout="wide")

st.title("📝 Form Pengajuan Surat Perintah Lembur (SPL)")
st.write("Silakan isi formulir di bawah ini untuk mengajukan lembur.")

# Inisialisasi session state untuk menyimpan data sementara
if "data_spl" not in st.session_state:
    st.session_state.data_spl = []

# Form Input SPL
with st.form("form_spl", clear_on_submit=True):
    col1, col2 = st.columns(2)
    
    with col1:
        nama = st.text_input("Nama Karyawan")
        departemen = st.selectbox("Departemen", ["Produksi", "Quality Control", "Warehouse", "HRD & GA", "IT", "Maintenance"])
        tanggal = st.date_input("Tanggal Lembur")
        
    with col2:
        jam_mulai = st.time_input("Jam Mulai")
        jam_selesai = st.time_input("Jam Selesai")
        alasan = st.text_area("Alasan/Pekerjaan Lembur")
        
    submitted = st.form_submit_button("Kirim Pengajuan SPL")
    
    if submitted:
        if nama and alasan:
            # Simpan data ke session state
            data_baru = {
                "Nama": nama,
                "Departemen": departemen,
                "Tanggal": tanggal.strftime("%Y-%m-%d"),
                "Jam Mulai": jam_mulai.strftime("%H:%M"),
                "Jam Selesai": jam_selesai.strftime("%H:%M"),
                "Alasan Lembur": alasan
            }
            st.session_state.data_spl.append(data_baru)
            st.success(f"SPL untuk {nama} berhasil diajukan!")
        else:
            st.error("Mohon isi Nama dan Alasan Lembur.")

# Menampilkan Rekap Data SPL
st.divider()
st.subheader("📊 Rekapitulasi Pengajuan SPL Hari Ini")

if st.session_state.data_spl:
    df = pd.DataFrame(st.session_state.data_spl)
    st.dataframe(df, use_container_width=True)
    
    # Export ke Excel
    df.to_excel("rekap_spl.xlsx", index=False)
    with open("rekap_spl.xlsx", "rb") as file:
        st.download_button(
            label="📥 Download Rekap Data (Excel)",
            data=file,
            file_name="Rekap_SPL_Lembur.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("Belum ada pengajuan SPL yang terdaftar.")
