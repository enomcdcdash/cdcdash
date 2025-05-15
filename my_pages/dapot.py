# --- my_pages/dapot.py ---
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data_loader import load_dapot_alpro_data

def show():
    dapot_df = load_dapot_alpro_data()

    # Ensure column names are consistent
    dapot_df.columns = dapot_df.columns.str.strip().str.upper()
    # ✅ Add this cleaning line here
    dapot_df['LATTITUDE'] = pd.to_numeric(dapot_df['LATTITUDE'].astype(str).str.replace("'", ""), errors='coerce')
    dapot_df['LONGITUDE'] = pd.to_numeric(dapot_df['LONGITUDE'].astype(str).str.replace("'", ""), errors='coerce')
    
    st.title("🏗️ Dapot Asset CDC")

    tab1, tab2 = st.tabs(["🔍 Site Details", "📋 Tabel Dapot"])
    with tab1:
        st.subheader("🔍 Site Detail Viewer")

        if not dapot_df.empty:
            site_ids = sorted(dapot_df['SITE ID'].dropna().unique().tolist())
            selected_site = st.selectbox("Select Site ID", site_ids)

            site_details = dapot_df[dapot_df['SITE ID'] == selected_site]

            if not site_details.empty:
                st.markdown(f"### Details for Site ID: `{selected_site}`")

                # Extract first row info (assuming one row per site or using first record)
                site_row = site_details.iloc[0]

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Area", site_row.get("AREA", "N/A"))
                with col2:
                    st.metric("Regional", site_row.get("REGIONAL", "N/A"))
                with col3:
                    st.metric("Status", site_row.get("STATUS", "N/A"))
                # Second row of metrics
                col4, col5, col6 = st.columns(3)
                with col4:
                    st.metric("Kapasitas (KVA)", site_row.get("KAPASITAS (KVA)", "N/A"))
                with col5:
                    st.metric("Kapasitas Batere (Bank)", site_row.get("KAPASITAS BATERE (BANK)", "N/A"))
                with col6:
                    st.metric("Jumlah Modul Rectifier", site_row.get("JUMLAH MODUL RECTIFIER", "N/A"))

                # Optionally show more info in expandable section
                with st.expander("📄 Full Site Record"):
                     st.dataframe(site_details, use_container_width=True)
                    #site_row = site_details.iloc[0]

                    #st.markdown(f"""
                    #```text
                    #Site ID     : {site_row.get("SITE ID", "N/A")}
                    #Site Name   : {site_row.get("SITE NAME", "N/A")}
                    #Site Class  : {site_row.get("SITE CLASS", "N/A")}
                    #Area        : {site_row.get("AREA", "N/A")}
                    #Regional    : {site_row.get("REGIONAL", "N/A")}
                    #""")
            else:
                st.warning("No data found for the selected Site ID.")
        else:
            st.info("Dapot Alpro data is empty or failed to load.")

    with tab2:
        st.subheader("📋 Tabel Dapot Asset CDC")

        # Filter UI (1 row, 3 columns)
        col1, col2, col3 = st.columns(3)

        with col1:
            selected_area = st.selectbox("Area", options=["All"] + sorted(dapot_df["AREA"].dropna().unique().tolist()))
        
        with col2:
            if selected_area != "All":
                regional_options = dapot_df[dapot_df["AREA"] == selected_area]["REGIONAL"].dropna().unique().tolist()
            else:
                regional_options = dapot_df["REGIONAL"].dropna().unique().tolist()
            selected_regional = st.selectbox("Regional", options=["All"] + sorted(regional_options))

        with col3:
            # Build filter step-by-step to avoid KeyError
            filtered_for_sites = dapot_df
            if selected_area != "All":
                filtered_for_sites = filtered_for_sites[filtered_for_sites["AREA"] == selected_area]
            if selected_regional != "All":
                filtered_for_sites = filtered_for_sites[filtered_for_sites["REGIONAL"] == selected_regional]

            site_options = filtered_for_sites["SITE ID"].dropna().unique().tolist()
            selected_site_id = st.selectbox("Site ID", options=["All"] + sorted(site_options))

        # Apply filters to the main DataFrame
        filtered_df = dapot_df.copy()
        if selected_area != "All":
            filtered_df = filtered_df[filtered_df["AREA"] == selected_area]
        if selected_regional != "All":
            filtered_df = filtered_df[filtered_df["REGIONAL"] == selected_regional]
        if selected_site_id != "All":
            filtered_df = filtered_df[filtered_df["SITE ID"] == selected_site_id]

        chart_col1, chart_col2, chart_col3 = st.columns(3)

        with chart_col1:
            st.markdown("#### 🟢 Status Distribution")
            status_count = filtered_df["STATUS"].value_counts().reset_index()
            status_count.columns = ["STATUS", "count"]  # Rename columns properly

            status_chart = px.pie(
                status_count,
                names="STATUS",  # ✅ Use correct column name
                values="count",  # ✅ Count of each status
                hole=0.5,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            status_chart.update_traces(textinfo='value')  # or 'label+value' for both
            st.plotly_chart(status_chart, use_container_width=True)

        with chart_col2:
            st.markdown("#### 🟣 Site Class Distribution")
            class_count = filtered_df["SITE CLASS"].value_counts().reset_index()
            class_count.columns = ["SITE CLASS", "count"]
            class_chart = px.pie(
                class_count,
                names="SITE CLASS",
                values="count",
                hole=0.5,
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            status_chart.update_traces(textinfo='value')  # or 'label+value' for both
            st.plotly_chart(class_chart, use_container_width=True)

        with chart_col3:
            st.markdown("#### 🔧 Add your chart here")
            # Optional third chart (leave empty or add e.g. battery capacity bar, etc.)
            pass

        # Start the index from 1 instead of 0
        filtered_df.index += 1

        # Show filtered table
        st.dataframe(filtered_df, use_container_width=True)
