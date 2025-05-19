# --- pages/tracker_bbm.py ---
import streamlit as st
import pandas as pd
from io import BytesIO
import os
import base64
import datetime
import json
import pytz
from utils.drive_utils import upload_photo_to_drive, get_photo_download_link
from utils.sheets_utils import append_row_to_sheet, read_sheet_as_dataframe

def show():
    st.title("\u26FD Tracker Pengisian BBM")
    tab1, tab2, tab3 = st.tabs(["📝 Form Pengisian BBM", "📊 Tracker Pengisian BBM", "🗂️ Riwayat Pengisian BBM"])
    
    # Cache the data loading function
    @st.cache_data
    def load_bbm_data():
        sheet_id = "13A8ckogwxlMYDXKXrW84h0XkWOIbIMUWiePK6uTRzfc"
        worksheet_name = "pengisian_bbm"
        df_pengisian = read_sheet_as_dataframe(sheet_id, worksheet_name)
        df_pengisian["tanggal_pengisian"] = pd.to_datetime(df_pengisian["tanggal_pengisian"], errors='coerce')
    
        site_master = pd.read_csv("all_site_master.csv")
    
        # Merge the two dataframes
        df = pd.merge(df_pengisian, site_master, on="site_id", how="left")
        
        return df
    
    MAX_PHOTOS = 3
    STATIC_PHOTO_DIR = "static/bbm_photos"
    os.makedirs(STATIC_PHOTO_DIR, exist_ok=True)

    # =========================
    # TAB 1: FORM PENGISIAN BBM
    # =========================
    with tab1:
        st.header("📝 Input Data Pengisian BBM")

        try:
            site_master = pd.read_csv("all_site_master.csv")
            site_options = sorted(site_master['site_id'].unique().tolist())
        except FileNotFoundError:
            site_options = []

        with st.form("form_pengisian"):
            site_id = st.selectbox("Pilih Site ID", site_options) if site_options else st.text_input("Site ID")
            tanggal_pengisian = st.date_input("Tanggal Pengisian", value=datetime.date.today())
            jumlah_pengisian = st.number_input("Jumlah Pengisian (Liter)", min_value=0.0, step=10.0, format="%.2f")

            uploaded_photos = st.file_uploader(
                "Upload Foto Evidence (max 3, max size 2MB each)",
                type=["jpg", "jpeg", "png"],
                accept_multiple_files=True,
                key="foto_pengisian"
            )

            submitted = st.form_submit_button("Simpan")

            if submitted:
                if not site_id:
                    st.warning("❗ Site ID tidak boleh kosong.")
                elif jumlah_pengisian <= 0:
                    st.warning("❗ Jumlah pengisian harus lebih dari 0 liter.")
                elif not uploaded_photos:
                    st.warning("❗ Harap upload minimal 1 foto sebagai bukti.")
                elif len(uploaded_photos) > MAX_PHOTOS:
                    st.warning(f"❗ Maksimum upload adalah {MAX_PHOTOS} foto.")
                elif any(photo.size > 2 * 1024 * 1024 for photo in uploaded_photos):
                    st.warning("❗ Ukuran setiap file harus maksimal 2MB.")
                else:
                    # 1. Upload photos to Google Drive and collect metadata
                    folder_id = "1ih1JXOS6-BGfVPBT-vSMSg07XnBPuoME"  # set your Google Drive folder ID here

                    uploaded_file_ids = []
                    for i, photo in enumerate(uploaded_photos):
                        photo_ext = photo.name.split(".")[-1]
                        # Define timezone GMT+7
                        tz = pytz.timezone('Asia/Bangkok')  # GMT+7 timezone
                        # Get current time in GMT+7
                        now_gmt7 = datetime.datetime.now(tz)
                        timestamp = now_gmt7.strftime("%Y-%m-%d_%H-%M-%S")
                        unique_suffix = f"{i+1}"
                        photo_filename = f"{site_id}_{timestamp}_{unique_suffix}.{photo_ext}"
                    
                        file_id, web_link = upload_photo_to_drive(photo, photo_filename, folder_id)
                        uploaded_file_ids.append({"filename": photo_filename, "file_id": file_id, "web_link": web_link})
                    
                        st.success(f"✅ Uploaded {photo_filename} to Google Drive")
            
                    new_row = {
                        "site_id": site_id,
                        "tanggal_pengisian": tanggal_pengisian.strftime("%Y-%m-%d"),
                        "jumlah_pengisian_liter": jumlah_pengisian,
                        "foto_evidence_drive": json.dumps(uploaded_file_ids),
                        # Add any other required fields (area, regional, etc.)
                    }
                               
                    # 3. Append the new row to Google Sheets
                    sheet_id = "13A8ckogwxlMYDXKXrW84h0XkWOIbIMUWiePK6uTRzfc"
                    worksheet_name = "pengisian_bbm"
                    append_row_to_sheet(sheet_id, worksheet_name, new_row)
            
                    st.success(f"✅ Data dan foto untuk site {site_id} berhasil disimpan.")
                    st.cache_data.clear()
                    st.rerun()

    # Tab 2: Dashboard Status BBM
    with tab2:
        st.header("📊 Tracker Pengisian BBM")
    
        try:
            # Load data from Google Sheets and merge with site master
            df = load_bbm_data()
    
            # Apply cascading filters
            col1, col2, col3 = st.columns(3)
            with col1:
                area_options = df["area"].dropna().unique()
                selected_area = st.selectbox("Pilih Area", options=["All"] + sorted(area_options.tolist()))
            if selected_area != "All":
                df = df[df["area"] == selected_area]
    
            with col2:
                regional_options = df["regional"].dropna().unique()
                if selected_area != "All":
                    regional_options = df[df["area"] == selected_area]["regional"].dropna().unique()
                selected_regional = st.selectbox("Pilih Regional", options=["All"] + sorted(regional_options.tolist()))
            if selected_regional != "All":
                df = df[df["regional"] == selected_regional]
    
            with col3:
                site_options = df["site_id"].dropna().unique()
                if selected_regional != "All":
                    site_options = df[df["regional"] == selected_regional]["site_id"].dropna().unique()
                selected_site = st.selectbox("Pilih Site ID", options=["All"] + sorted(site_options.tolist()))
            if selected_site != "All":
                df = df[df["site_id"] == selected_site]
    
            # Convert numeric columns and datetime
            df["jumlah_pengisian_liter"] = pd.to_numeric(df["jumlah_pengisian_liter"], errors="coerce")
            df["liter_per_hari"] = pd.to_numeric(df["liter_per_hari"], errors="coerce")
            df["tanggal_pengisian"] = pd.to_datetime(df["tanggal_pengisian"], errors='coerce')
    
            # Process latest record per site_id
            df_latest = (
                df.sort_values("tanggal_pengisian", ascending=False)
                  .groupby("site_id", as_index=False)
                  .first()
            )
    
            # Calculate tanggal_habis based on usage rate
            df_latest["tanggal_habis"] = df_latest["tanggal_pengisian"] + pd.to_timedelta(
                df_latest["jumlah_pengisian_liter"] / df_latest["liter_per_hari"], unit="D"
            )
    
            # Calculate liters used and percentage used
            hari_berjalan = (pd.to_datetime("today") - df_latest["tanggal_pengisian"]).dt.days
            df_latest["liter_terpakai"] = hari_berjalan * df_latest["liter_per_hari"]
            df_latest["persentase_float"] = df_latest["liter_terpakai"] / df_latest["jumlah_pengisian_liter"]
            df_latest["persentase_terpakai"] = df_latest["persentase_float"].apply(
                lambda x: f"{x:.2%}" if pd.notnull(x) else "-"
            )
    
            # Define status column with emojis
            def warnacol(row):
                if row["persentase_float"] >= 0.9:
                    return "🔴 Segera Isi BBM (90%+)"
                elif row["persentase_float"] >= 0.8:
                    return "🟠 Peringatan BBM Low (80%+)"
                else:
                    return "🟢 Aman"
    
            df_latest["status_bbm"] = df_latest.apply(warnacol, axis=1)
            df_latest["tanggal_pengisian"] = df_latest["tanggal_pengisian"].dt.date
            df_latest["tanggal_habis"] = df_latest["tanggal_habis"].dt.date

            # Define helper to create Google Drive viewable URL
            def get_photo_download_link(file_id):
                return f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"
            
            # Function to convert photo metadata JSON to clickable links
            def get_photo_links_drive(foto_evidence_drive_json):
                try:
                    foto_list = json.loads(foto_evidence_drive_json)
                except Exception:
                    return ""
                
                links = []
                for item in foto_list:
                    filename = item.get("filename")
                    file_id = item.get("file_id")
                    if file_id:
                        url = get_photo_download_link(file_id)
                        href = f'<a href="{url}" target="_blank">📷 {filename}</a>'
                        links.append(href)
                return "<br>".join(links) if links else ""
            
            # Ensure 'foto_evidence_drive' column exists
            if "foto_evidence_drive" not in df_latest.columns:
                df_latest["foto_evidence_drive"] = None
                       
            # Convert photo metadata JSON into clickable links
            df_latest["foto_evidence"] = df_latest["foto_evidence_drive"].apply(get_photo_links_drive)
            
            # Columns to display
            display_cols = [
                "area", "regional", "site_id", "site_name", "tanggal_pengisian",
                "jumlah_pengisian_liter", "liter_per_hari", "liter_terpakai",
                "persentase_terpakai", "tanggal_habis", "status_bbm", "foto_evidence"
            ]
            display_cols = [col for col in display_cols if col in df_latest.columns]
            df_display = df_latest[display_cols].copy()
            df_display["foto_evidence"] = df_display["foto_evidence"].fillna("")
            
            # Add row number
            df_display.reset_index(drop=True, inplace=True)
            df_display.insert(0, "No.", df_display.index + 1)
            
            # Show styled table with photo links clickable
            st.markdown(
                df_display.to_html(escape=False, index=False),
                unsafe_allow_html=True
            )

            # Export Excel without photo links
            export_cols = [col for col in display_cols if col != "foto_evidence"]
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
                df_latest[export_cols].to_excel(writer, index=False, sheet_name="BBM Data")
    
            st.download_button(
                label="📥 Export Data as Excel File",
                data=excel_buffer.getvalue(),
                file_name="bbm_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
        except Exception as e:
            st.warning("Gagal menampilkan dashboard: " + str(e))
    
    # Tab 3: Riwayat Pengisian BBM
    with tab3:
        st.header("🗂️ Riwayat Pengisian BBM")

        try:
            # Call the cached function to load the merged data
            df_hist = load_bbm_data()

            # Buat tiga kolom untuk filter sejajar dalam satu baris
            col1, col2, col3 = st.columns(3)

            # Filter Area
            with col1:
                area_options = df_hist["area"].dropna().unique()
                selected_area = st.selectbox(
                    "Pilih Area", 
                    options=["All"] + sorted(area_options.tolist()), 
                    key="select_area"
                )

            # Apply Area filter
            if selected_area != "All":
                df_hist = df_hist[df_hist["area"] == selected_area]

            # Filter Regional (based on Area filter if applied)
            with col2:
                regional_options = df_hist["regional"].dropna().unique()
                selected_regional = st.selectbox(
                    "Pilih Regional", 
                    options=["All"] + sorted(regional_options.tolist()), 
                    key="select_regional"
                )

            # Apply Regional filter
            if selected_regional != "All":
                df_hist = df_hist[df_hist["regional"] == selected_regional]

            # Filter Site ID (based on Area and Regional filters if applied)
            with col3:
                site_options = df_hist["site_id"].dropna().unique()
                selected_site = st.selectbox(
                    "Pilih Site ID", 
                    options=["All"] + sorted(site_options.tolist()), 
                    key="select_site"
                )

            # Apply Site ID filter
            if selected_site != "All":
                df_hist = df_hist[df_hist["site_id"] == selected_site]

            # Konversi kolom numerik
            df_hist["jumlah_pengisian_liter"] = pd.to_numeric(df_hist["jumlah_pengisian_liter"], errors="coerce")

            # Urutkan berdasarkan tanggal_pengisian (terbaru di atas) dan site_id
            df_hist = df_hist.sort_values(by=["tanggal_pengisian", "site_id"], ascending=[False, True])

            # Format jadi hanya tanggal (untuk ditampilkan)
            df_hist["tanggal_pengisian"] = df_hist["tanggal_pengisian"].dt.date
            
            # Your code for tab3 visualization goes here...
            st.dataframe(df_hist[["area", "regional", "site_id", "site_name", "tanggal_pengisian", "jumlah_pengisian_liter"]])
            
            # Create an Excel file from the DataFrame
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
                df_hist[[
                    "area", "regional", "site_id", "site_name", "tanggal_pengisian", "jumlah_pengisian_liter"
                ]].to_excel(writer, index=False, sheet_name="Riwayat BBM")

            # Add download button for Excel file
            st.download_button(
                label="Export Data as Excel File",
                data=excel_buffer.getvalue(),
                file_name="riwayat_bbm.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        except Exception as e:
            st.warning("Gagal menampilkan riwayat pengisian: " + str(e))
