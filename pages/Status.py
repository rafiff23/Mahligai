import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import requests
import pydeck as pdk

st.set_page_config(page_title="Cek Status Driver", layout="wide")
st.title("📄 Cek Status Driver")

scope = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
client = gspread.authorize(creds)

sheet_id = "1RIW01gtWUobcaug5KtkmNC3KEeGgcAJ-6dKmk-VamTY"
sheet = client.open_by_key(sheet_id)
worksheet = sheet.sheet1
data = worksheet.get_all_records()
df = pd.DataFrame(data)

# Convert Date column
if 'Date' in df.columns:
    df['Date'] = pd.to_datetime(df['Date'])

# Format Status to Title Case
df['Status'] = df['Status'].astype(str).str.title()

worksheet2 = sheet.worksheet("FOTO")  # Access by sheet name
data2 = worksheet2.get_all_records()
df2 = pd.DataFrame(data2)

# --- Ambil Nama File Gambar dari Status Terbaru
foto_fields = ['Foto', 'Depan Container', 'Belakang Container', 'Kiri Container', 'Kanan Container']
image_titles = ['Foto', 'Depan Container', 'Belakang Container', 'Kiri Container', 'Kanan Container']

# Define Status Colors
status_colors = {
    "Tiba Di Depo Kosongan": "#D94F4F",
    "Muat Kosongan": "#D94F4F",
    "Menuju Gudang / Pabrik": "#D94F4F",
    "Sampai Tujuan Pabrik / Gudang": "#D94F4F",
    "Muat Barang": "#D94F4F",
    "Keluar Pabrik / Menuju Pelabuhan": "#D94F4F",
    "Menunggu Kartu Ekspor": "#D94F4F",
    "Tiba Di Pelabuhan": "#FFD700",
    "Selesai": "#88B04B",
    "Tidak Lanjut": "#A020F0",
    "Masuk Pelabuhan": "#D94F4F",
    "Muat Container": "#D94F4F",
    "Sampai Gudang / Pabrik": "#D94F4F",
    "Bongkar Barang": "#D94F4F",
    "Keluar Gudang / Pabrik": "#D94F4F",
    "Tiba Di Depo": "#FFD700",
    "Selesai": "#88B04B"
}

# --- Sidebar Filter ---
st.sidebar.header("🔍 Filter Driver")

name_options = sorted(df['Name'].dropna().unique().tolist())
selected_name = st.sidebar.selectbox("Pilih Driver", name_options)

# --- Filtered Data ---
df_filtered = df[df['Name'] == selected_name].copy()

# --- Display Latest Info at Top in Styled Card ---
st.subheader(f"🧑‍✈️ Informasi Terbaru untuk Driver: {selected_name}")

if not df_filtered.empty:
    latest_data = df_filtered.sort_values(by='Date', ascending=False).iloc[0]
    status_text = latest_data.get('Status', 'N/A')
    status_color = status_colors.get(status_text, '#FFFFFF')

# --- Pisahkan jadi dua kolom
    # col1, col2 = st.columns([0.5, 0.5])

    # KIRI = Status Driver
    # with col1:
        # Ambil dan parsing lokasi
    location_str = latest_data.get('Location', None)
    location_text = "Tidak tersedia"
    lat, lon = None, None

    if location_str and isinstance(location_str, str) and "," in location_str:
        try:
            lat_str, lon_str = location_str.split(",")
            lat, lon = float(lat_str.strip()), float(lon_str.strip())
            location_text = f"{lat}, {lon}"
        except:
            location_text = "Format koordinat tidak valid"

    # Tampilkan box status lengkap dengan koordinat
    st.markdown("""
        <div style="display: flex; flex-direction: column; background-color: #1f1f2e; padding: 25px; border-radius: 15px; box-shadow: 0 6px 15px rgba(0,0,0,0.3);">
            <div style="font-size: 36px; font-weight: bold; color: {status_color}; margin-bottom: 20px;">Status: {status_text}</div>
            <div style="font-size: 18px; color: #CCCCCC; line-height: 1.8">
                <b>Plat:</b> {plat}<br>
                <b>Tanggal:</b> {date}<br>
                <b>Jam:</b> {time}<br>
                <b>Ukuran Kontainer:</b> {container}<br>
                <b>Ekspor / Impor:</b> {ekspor}<br>
                <b>Koordinat Lokasi:</b> {location_text}
            </div>
        </div>
    """.format(
        status_text=status_text,
        status_color=status_color,
        plat=latest_data.get('Plat', 'N/A'),
        date=latest_data.get('Date', 'N/A').strftime('%Y-%m-%d') if pd.notnull(latest_data.get('Date')) else 'N/A',
        time=latest_data.get('Time', 'N/A'),
        container=latest_data.get('20 Feet / 40 Feet', 'N/A'),
        ekspor=latest_data.get('Ekspor / Impor', 'N/A'),
        location_text=location_text
    ), unsafe_allow_html=True)

    # Peta langsung di bawah box status (tetap dalam col1)
    if lat and lon:
        location_df = pd.DataFrame({'lat': [lat], 'lon': [lon]})
        st.map(location_df)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    with st.expander("📸 Dokumentasi Gambar Terkait Status Terakhir"):
        # Buat Dictionary mapping nama file → ID dari df2 (sheet FOTO)
        # Hapus baris dengan nama file kosong/null dari df2
        df2_clean = df2[df2['Foto'].notna() & (df2['Foto'].astype(str).str.strip() != "")]
        foto_mapping = dict(zip(df2_clean['Foto'], df2_clean['ID']))

        # Ambil nama file dari status terakhir
        image_files = [latest_data.get(col, None) for col in foto_fields]

        # Subheader
        st.subheader("📸 Dokumentasi Gambar Terkait Status Terakhir")

        # Layout kolom
        cols = st.columns(len(foto_fields))

        for i, col in enumerate(cols):
            image_file = image_files[i]
            image_title = image_titles[i]
            
            if pd.notnull(image_file) and image_file in foto_mapping:
                file_id = foto_mapping[image_file]
                image_url = f"https://drive.google.com/uc?export=view&id={file_id}"
                
                col.markdown(f"**{image_title}**")
                # col.image(image_url, use_column_width=True)
                response = requests.get(image_url)
                col.image(response.content, use_column_width=True)
            else:
                col.markdown(f"**{image_title}**")
                col.warning("Gambar tidak tersedia")

    # --- Expandable Detailed Data ---
    with st.expander("📂 Lihat Semua Riwayat Driver"):
        st.dataframe(df_filtered[['Name', 'Plat', 'Nama Perusahaan', 'Date', 'Time', '20 Feet / 40 Feet', 'Ekspor / Impor', 'Status']].reset_index(drop=True))

else:
    st.info("Data tidak ditemukan untuk driver tersebut.")
    

