# --- pages/tracker_bbm.py ---
import streamlit as st
import pandas as pd
from io import BytesIO

def show():
    st.title("\u26FD Tracker Pengisian BBM")
    tab1, tab2, tab3 = st.tabs(["📝 Form Pengisian BBM", "📊 Tracker Pengisian BBM", "🗂️ Riwayat Pengisian BBM"])

    # =========================
    # TAB 1: FORM PENGISIAN BBM
    # =========================
    with tab1:
        st.header("📝 Input Data Pengisian BBM")

        # Load site master (jika ada)
        try:
            site_master = pd.read_csv("all_site_master.csv")
            site_options = sorted(site_master['site_id'].unique().tolist())
        except:
            site_options = []

        # Form Input
        with st.form("form_pengisian"):
            site_id = st.selectbox("Pilih Site ID", site_options) if site_options else st.text_input("Site ID")
            tanggal_pengisian = st.date_input("Tanggal Pengisian")
            jumlah_pengisian = st.number_input("Jumlah Pengisian (Liter)", min_value=0.0, step=10.0, format="%.2f")
            submitted = st.form_submit_button("Simpan")

            if submitted:
                if not site_id:
                    st.warning("❗ Site ID tidak boleh kosong.")
                elif jumlah_pengisian <= 0:
                    st.warning("❗ Jumlah pengisian harus lebih dari 0 liter.")
                else:
                    new_data = pd.DataFrame([{
                        "site_id": site_id,
                        "tanggal_pengisian": pd.to_datetime(tanggal_pengisian),  # pastikan format datetime
                        "jumlah_pengisian_liter": jumlah_pengisian
                    }])

                    try:
                        existing = pd.read_csv("pengisian_bbm_streamlit.csv", parse_dates=["tanggal_pengisian"])
                        updated = pd.concat([existing, new_data], ignore_index=True)
                    except FileNotFoundError:
                        updated = new_data

                    updated.to_csv("pengisian_bbm_streamlit.csv", index=False, date_format="%Y-%m-%d")
                    st.success(f"✅ Data pengisian BBM untuk site {site_id} berhasil disimpan.")

    # Cache the data loading function
    @st.cache_data
    def load_bbm_data():
        # Load the CSV files
        df_pengisian = pd.read_csv("pengisian_bbm_streamlit.csv", parse_dates=["tanggal_pengisian"], date_format="%d-%b-%y")
        site_master = pd.read_csv("all_site_master.csv")

        # Merge the two dataframes
        df = pd.merge(df_pengisian, site_master, on="site_id", how="left")
        
        return df
    
    # Tab 2: Dashboard Status BBM
    with tab2:
        st.header("📊 Dashboard Status BBM")

        try:
            # Call the cached function to load the merged data
            df = load_bbm_data()

            # Buat tiga kolom untuk filter sejajar dalam satu baris
            col1, col2, col3 = st.columns(3)

            with col1:
                area_options = df["area"].dropna().unique()
                selected_area = st.selectbox("Pilih Area", options=["All"] + sorted(area_options.tolist()))

            # Filter berdasarkan Area terlebih dahulu
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

            # Konversi kolom numerik
            df["jumlah_pengisian_liter"] = pd.to_numeric(df["jumlah_pengisian_liter"], errors="coerce")
            df["liter_per_hari"] = pd.to_numeric(df["liter_per_hari"], errors="coerce")

            # Ambil pengisian terakhir per site
            df = df.sort_values("tanggal_pengisian", ascending=False).groupby("site_id", as_index=False).first()

            # Hitung estimasi tanggal habis
            df["tanggal_habis"] = df["tanggal_pengisian"] + pd.to_timedelta(
                df["jumlah_pengisian_liter"] / df["liter_per_hari"], unit="D"
            )

            # Hitung liter terpakai
            hari_berjalan = (pd.to_datetime("today") - df["tanggal_pengisian"]).dt.days
            df["liter_terpakai"] = hari_berjalan * df["liter_per_hari"]

            # Hitung persentase terpakai (float dan string)
            df["persentase_float"] = df["liter_terpakai"] / df["jumlah_pengisian_liter"]
            df["persentase_terpakai"] = (df["persentase_float"] * 100).apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else "-")

            # Klasifikasi status BBM
            def warnacol(row):
                if row["persentase_float"] >= 0.9:
                    return "🔴 Segera Isi BBM (90%+)"
                elif row["persentase_float"] >= 0.8:
                    return "🟠 Peringatan BBM Low (80%+)"
                else:
                    return "🟢 Aman"

            df["status_bbm"] = df.apply(warnacol, axis=1)

            # Format tanggal hanya tampilkan tanggal saja
            df["tanggal_pengisian"] = df["tanggal_pengisian"].dt.date
            df["tanggal_habis"] = df["tanggal_habis"].dt.date
            
            # Start the index from 1 instead of 0
            df.index += 1

            # Your code for tab2 visualization goes here...
            # st.dataframe(df)
            
            # Tampilkan tabel
            st.dataframe(df[[
                "area", "regional", "site_id", "site_name", "tanggal_pengisian", "jumlah_pengisian_liter",
                "liter_per_hari", "liter_terpakai", "persentase_terpakai",
                "tanggal_habis", "status_bbm"
            ]])

            # Create an Excel file from the DataFrame
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
                df[[
                    "area", "regional", "site_id", "site_name", "tanggal_pengisian", "jumlah_pengisian_liter",
                    "liter_per_hari", "liter_terpakai", "persentase_terpakai",
                    "tanggal_habis", "status_bbm"
                ]].to_excel(writer, index=False, sheet_name="BBM Data")

            # Add download button for Excel file
            st.download_button(
                label="Export Data as Excel File",
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