import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
import io
from io import BytesIO
import os
import re
import random
import streamlit.components.v1 as components

# --- Page Config ---
st.set_page_config(page_title="Dashboard CDC", layout="wide")
st.title('📊 Dashboard CDC')

# --- Sidebar Navigation (Custom Buttons) ---
with st.sidebar:
    st.markdown("<div style='text-align: center; font-size: 30px;'>📊 CDC Project Dashboard</div>", unsafe_allow_html=True)
    st.markdown("---")  # horizontal line

    # Initialize session state
    if "page" not in st.session_state:
        st.session_state.page = "⛽ Tracker Pengisian BBM"

    # Use one column to stack buttons vertically
    col = st.container()
    with col:
        bbm_clicked = st.button("⛽ Tracker Pengisian BBM", use_container_width=True)
        availability_clicked = st.button("📅 CDC Availability", use_container_width=True)


    # Update session state based on button clicked
    if bbm_clicked:
        st.session_state.page = "⛽ Tracker Pengisian BBM"
    elif availability_clicked:
        st.session_state.page = "📅 CDC Availability"

# --- Main Content: ENOM KPI Placeholder ---
if st.session_state.page == "📅 CDC Availability":
    st.title("📅 CDC Availability")
    # === File Paths ===
    file_path1 = "data/CDC_Availability_2025_194.xlsx"
    file_path2 = "data/ESTIMASIPO2025.xlsx"

    # === Load First File ===
    try:
        df = pd.read_excel(file_path1, sheet_name="Ava CDC")
        #st.success("CDC Availability data loaded successfully from local file!")
    except Exception as e:
        st.error(f"Failed to load CDC Availability data: {e}")
        st.stop()

    # --- Data Preparation for Availability File ---
    melted_df = pd.melt(df, 
                        id_vars=['Area', 'Site ID', 'Regional', 'Site Name', 'NS', 'Cluster', 'On Service / Cut OFF', 'Site Class', 'Target AVA'],
                        var_name='Date', 
                        value_name='Availability')

    melted_df['Date'] = pd.to_datetime(melted_df['Date'], format='%d-%b-%y', errors='coerce')
    melted_df = melted_df.dropna(subset=['Date'])

    # === Load and Combine Second File (ESTIMASI PO) ===
    # --- Extract year from filename ---
    filename = os.path.basename(file_path2)
    match = re.search(r"\d{4}", filename)
    cdc_year = match.group(0) if match else "Unknown"

    expected_sheets = ["JANUARI", "FEBRUARI", "MARET", "APRIL", "MEI", "JUNI", 
                    "JULI", "AGUSTUS", "SEPTEMBER", "OKTOBER", "NOVEMBER", "DESEMBER"]

    cdc_df_list = []

    try:
        xls = pd.ExcelFile(file_path2)
        available_sheets = xls.sheet_names

        cdc_df_list = []
        for month in ["JANUARI", "FEBRUARI", "MARET", "APRIL", "MEI", "JUNI",
                    "JULI", "AGUSTUS", "SEPTEMBER", "OKTOBER", "NOVEMBER", "DESEMBER"]:
            if month in available_sheets:
                df_month = pd.read_excel(xls, sheet_name=month, header=1)  # Header in second row
                df_month['Month'] = month
                df_month['Year'] = cdc_year  # <- ✅ Add Year column here
                cdc_df_list.append(df_month)

        cdc_df = pd.concat(cdc_df_list, ignore_index=True)

        # Add "Ava Achievement" column
        cdc_df['Ava Achievement'] = cdc_df.apply(
            lambda row: 'Achieved' if row['Avaibility'] >= row['Target Availability (%)'] else 'Not Achieved', axis=1
        )

    except Exception as e:
        st.error(f"Failed to read CDC Monthly file: {e}")
        cdc_df = pd.DataFrame()

    # --- Add Ava Achievement Column ---
    if not cdc_df.empty:
        if 'Avaibility' in cdc_df.columns and 'Target Availability (%)' in cdc_df.columns:
            cdc_df['Ava Achievement'] = cdc_df.apply(
                lambda row: 'Achieved' if row['Avaibility'] >= row['Target Availability (%)'] else 'Not Achieved',
                axis=1
            )
        else:
            st.warning("Columns 'Avaibility' or 'Target Availability (%)' not found in PO data.")
    else:
        st.info("cdc_df is empty. Skipping Ava Achievement calculation.")

    tab1, tab2, tab3 = st.tabs(["📅 CDC Monthly Summary", "📈 Availability Daily Tracker", "📊 Availability Summary (INAP)"])

    with tab1:
        st.subheader("📅 CDC Monthly Summary")

        if cdc_df.empty:
            st.warning("No CDC Monthly data available.")
        else:
            import plotly.graph_objects as go
            import pandas as pd

            # --- Format currency and percentages for display ---
            def style_cdc(df):
                return df.style.format({
                    'Target Availability (%)': '{:.2%}',
                    'Avaibility': '{:.2%}',
                    'Persentase Penalty': '{:.2%}',
                    'Nominal PO': 'Rp {:,.0f}',
                    'Nilai Penalty': 'Rp {:,.0f}',
                    'Nilai BAST': 'Rp {:,.0f}',
                    'Nilai BAST dikurangi Penalty': 'Rp {:,.0f}'
                })

            if cdc_df.empty:
                st.warning("No CDC Monthly data available.")
            else:
                # --- Normalize Site Id as string ---
                cdc_df['Site Id'] = cdc_df['Site Id'].astype(str).str.strip()

                # --- Filter Layout: 5 columns ---
                col1, col2, col3, col4, col5 = st.columns(5)

                with col1:
                    selected_month = st.selectbox("Select Month", 
                                            options=["All"] + sorted(cdc_df["Month"].dropna().unique().tolist()))

                with col2:
                    selected_year = st.selectbox("Select Year", 
                                            options=["All"] + sorted(cdc_df["Year"].dropna().unique()))

                with col3:
                    selected_regional = st.selectbox("Select Regional", 
                                                options=["All"] + sorted(cdc_df["Regional TI"].dropna().unique()))

                # --- Dynamically update Site ID based on selected filters ---
                site_filter_df = cdc_df.copy()
                if selected_month != "All":
                    site_filter_df = site_filter_df[site_filter_df["Month"] == selected_month]
                if selected_year != "All":
                    site_filter_df = site_filter_df[site_filter_df["Year"] == selected_year]
                if selected_regional != "All":
                    site_filter_df = site_filter_df[site_filter_df["Regional TI"] == selected_regional]

                available_sites = sorted(site_filter_df["Site Id"].dropna().unique().tolist())

                #site_choices = ["All"] + available_sites
                #default_index = random.randint(1, len(site_choices) - 1)  # Skip index 0 ("All")
                site_choices = ["All"] + available_sites
                # Create a random Site ID only once per session
                if "default_site_index" not in st.session_state:
                    st.session_state.default_site_index = random.randint(1, len(site_choices) - 1) if len(site_choices) > 1 else 0           
                
                with col4:
                    if site_choices:
                        safe_index = (
                            st.session_state.default_site_index
                            if st.session_state.default_site_index < len(site_choices)
                            else 0
                        )
                        selected_site = st.selectbox(
                            "Select Site ID",
                            options=site_choices,
                            index=safe_index
                        )
                    else:
                        st.warning("No available Site IDs to select.")
                        selected_site = "All"

                    #selected_site = st.selectbox("Select Site ID", options=["All"] + available_sites)
                    #selected_site = st.selectbox("Select Site ID", options=site_choices, index=default_index)

                with col5:
                    search_site = st.text_input("🔍 Search Site ID")

                # --- Apply Filters ---
                filtered_df = cdc_df.copy()
                if selected_month != "All":
                    filtered_df = filtered_df[filtered_df["Month"] == selected_month]
                if selected_year != "All":
                    filtered_df = filtered_df[filtered_df["Year"] == selected_year]
                if selected_regional != "All":
                    filtered_df = filtered_df[filtered_df["Regional TI"] == selected_regional]
                if selected_site != "All":
                    filtered_df = filtered_df[filtered_df["Site Id"] == selected_site]
                if search_site:
                    filtered_df = filtered_df[filtered_df["Site Id"].str.contains(search_site)]
                # --- Get selected site name ---
                if selected_site != "All":
                    site_name_match = filtered_df[filtered_df["Site Id"] == selected_site]["Site Name"]
                    selected_site_name = site_name_match.iloc[0] if not site_name_match.empty else ""
                else:
                    selected_site_name = ""
                    
            # --- Charts Section ---
            if not filtered_df.empty:
                # Translate Indonesian month names to English
                month_translation = {
                    'JANUARI': 'January',
                    'FEBRUARI': 'February',
                    'MARET': 'March',
                    'APRIL': 'April',
                    'MEI': 'May',
                    'JUNI': 'June',
                    'JULI': 'July',
                    'AGUSTUS': 'August',
                    'SEPTEMBER': 'September',
                    'OKTOBER': 'October',
                    'NOVEMBER': 'November',
                    'DESEMBER': 'December'
                }

                filtered_df['Month_Eng'] = filtered_df['Month'].str.upper().map(month_translation)
                filtered_df['Month_Num'] = pd.to_datetime(filtered_df['Month_Eng'], format='%B').dt.month
                filtered_df['Month_Year'] = filtered_df['Month_Eng'] + " - " + filtered_df['Year'].astype(str)
                filtered_df = filtered_df.sort_values(by=['Year', 'Month_Num'])

                # Create chart columns
                chart_col1, chart_col2 = st.columns(2)

                with chart_col1:
                    st.markdown("#### 📈 Site Monthly Availability Trend")
                    fig1 = go.Figure()

                    for site_id, group in filtered_df.groupby('Site Id'):
                        # Format Target Availability for display in legend
                        target_value = group['Target Availability (%)'].iloc[0] if not group['Target Availability (%)'].isnull().all() else 0
                        target_label = f"Target: {int(target_value * 100)}%" if target_value % 0.01 == 0 else f"Target: {target_value * 100:.1f}%"

                        fig1.add_trace(go.Scatter(
                            x=group['Month_Year'],
                            y=group['Avaibility'],
                            mode='lines+markers+text',
                            name=site_id,  # Show only Site ID for Availability
                            text=group['Avaibility'].apply(lambda x: f"{x:.2%}"),  # Format values as percentages
                            textposition='bottom center',  # Position text above the dots
                            showlegend=True
                        ))
                        fig1.add_trace(go.Scatter(
                            x=group['Month_Year'],
                            y=group['Target Availability (%)'],
                            mode='lines+markers+text',  # Add 'text' to show labels
                            name=target_label,  # Custom label with "Target: XX%"
                            text=group['Target Availability (%)'].apply(lambda x: f"{x:.2%}"),  # Format values as percentages
                            textposition='bottom center',  # Position text above the dots
                            line=dict(dash='dash'),
                            showlegend=True
                        ))

                    fig1.update_layout(
                        title=dict(
                            text=f"Availability Site {selected_site} - {selected_site_name}",
                            x=0.5,  # center the title
                            xanchor='center',
                            font=dict(size=18)
                        ),
                        #xaxis_title="Month - Year",
                        yaxis_title="Availability",
                        hovermode='closest',
                        #legend_title="Site ID",
                        yaxis_tickformat=".0%",
                        yaxis=dict(
                            range=[0, 1],  # Set y-axis range from 0% to 100%
                            tickmode="linear",  # Use linear ticks
                            tick0=0,           # Start ticks at 0
                            dtick=0.1          # Set ticks every 10% (0.1)
                        ),
                        legend=dict(
                            orientation="h",     # horizontal legend
                            yanchor="top",
                            y=-0.3,              # adjust as needed to move it below the chart
                            xanchor="center",
                            x=0.5
                        )
                    )
                    st.plotly_chart(fig1, use_container_width=True)

                with chart_col2:
                    st.markdown("#### 💰 Nominal PO vs Penalty")
                    fig2 = go.Figure()

                    for site_id, group in filtered_df.groupby('Site Id'):
                        fig2.add_trace(go.Scatter(
                            x=group['Month_Year'],
                            y=group['Nominal PO'],
                            mode='lines+markers+text',
                            name=f'{site_id} - PO',
                            line=dict(color='green'),
                            text=group['Nominal PO'].apply(lambda x: f"{x:,.0f}"),
                            textposition='top center',
                            textfont=dict(color='green', size=10)
                        ))
                        fig2.add_trace(go.Scatter(
                            x=group['Month_Year'],
                            y=group['Nilai Penalty'],
                            mode='lines+markers+text',
                            name=f'{site_id} - Penalty',
                            fill='tozeroy',
                            line=dict(color='red'),
                            fillcolor='rgba(255, 0, 0, 0.2)',  # Semi-transparent red
                            text=group['Nilai Penalty'].apply(lambda x: f"{x:,.0f}"),
                            textposition='top center',
                            textfont=dict(color='red', size=10)
                        ))

                    fig2.update_layout(
                        title=dict(
                            text=f"{selected_site} - {selected_site_name}",
                            x=0.5,  # center the title
                            xanchor='center',
                            font=dict(size=18)
                        ),
                        #xaxis_title="Month - Year",
                        yaxis_title="IDR",
                        hovermode='closest',
                        #legend_title="Site ID",
                        legend=dict(
                            orientation="h",     # horizontal legend
                            yanchor="top",
                            y=-0.3,              # adjust as needed to move it below the chart
                            xanchor="center",
                            x=0.5
                        )
                    )
                    st.plotly_chart(fig2, use_container_width=True)

            # --- Display Filtered Table ---
            if filtered_df.empty:
                st.info("No data matches the selected filters.")
            else:
                desired_columns = [
                    'No',
                    'Month_Year',
                    'Regional TI',
                    'Site Id',
                    'Site Name',
                    'Daya PO',
                    'Periode Tagihan (Awal)',
                    'Periode Tagihan (Akhir)',
                    'Jumlah Periode (Bulan)',
                    'Nominal PO',
                    'Index BBM',
                    'Class Site',
                    'Target Availability (%)',
                    'Avaibility',
                    'Persentase Penalty',
                    'Nilai Penalty',
                    'Nilai BAST',
                    'Nilai BAST dikurangi Penalty',
                    'Ava Achievement'
                ]
                # Filter and reorder DataFrame
                filtered_df = filtered_df[desired_columns]
                st.dataframe(style_cdc(filtered_df))

                # Create a BytesIO buffer and write the DataFrame to Excel
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    filtered_df.to_excel(writer, index=False, sheet_name='Filtered Data')
                output.seek(0)

                # Add download button
                st.download_button(
                    label="📥 Download Filtered Data as Excel",
                    data=output,
                    file_name="filtered_data.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

                # --- Achievement Summary ---
                if 'Ava Achievement' in filtered_df.columns:
                    st.markdown("### 🎯 Achievement Summary")
                    st.dataframe(
                        filtered_df['Ava Achievement']
                        .value_counts()
                        .reset_index()
                        .rename(columns={'index': 'Achievement', 'Ava Achievement': 'Count'})
                    )
                else:
                    st.info("'Ava Achievement' column not available in the data.")

    with tab2:
        # st.header("Filters (Daily Tracker)")

        # Create two rows for the filters layout
        col1, col2, col3 = st.columns(3)

        # --- First Row: Area, Regional, Date Range Picker ---
        with col1:
            area_options = ["Show All"] + list(melted_df['Area'].dropna().unique())
            selected_area = st.selectbox("Select Area", options=area_options)

        # Filter Regional options based on the selected Area
        if selected_area != "Show All":
            filtered_by_area = melted_df[melted_df['Area'] == selected_area]
        else:
            filtered_by_area = melted_df.copy()

        with col2:
            regional_options = ["Show All"] + list(filtered_by_area['Regional'].dropna().unique())
            selected_regional = st.selectbox("Select Regional", options=regional_options)

        with col3:
            valid_dates = melted_df['Date'].dropna()
            if not valid_dates.empty:
                selected_date = st.date_input(
                    "Select Date Range",
                    [valid_dates.min(), valid_dates.max()]
                )
            else:
                st.warning("No valid dates available.")
                selected_date = [None, None]

        # --- Second Row: Search Site ID and Site ID ---
        col4, col5 = st.columns(2)

        with col4:
            selected_site_search = st.text_input("Search Site ID", "")

        # Filter Site IDs based on selected Area and Regional
        if selected_regional != "Show All":
            filtered_by_regional = filtered_by_area[filtered_by_area['Regional'] == selected_regional]
        else:
            filtered_by_regional = filtered_by_area.copy()

        site_id_options = filtered_by_regional['Site ID'].dropna().unique()

        # Apply Site ID search filter
        if selected_site_search:
            site_id_options = [site_id for site_id in site_id_options if selected_site_search.lower() in site_id.lower()]

        # Add "Show All" option for Site ID
        site_id_options = ["Show All"] + list(site_id_options)

        with col5:
            selected_site = st.selectbox("Select Site ID", options=site_id_options)

        # --- Get Site Name after Site ID selection ---
        selected_site_name = ""  # <-- Default value

        if selected_site and selected_site != "Show All":
            site_name_series = filtered_by_regional[filtered_by_regional['Site ID'] == selected_site]['Site Name']
            if not site_name_series.empty:
                selected_site_name = site_name_series.iloc[0]
                st.write(f"Selected Site Name: {selected_site_name}")

        # --- Apply Filters ---
        filtered_df = melted_df.copy()

        if selected_area != "Show All":
            filtered_df = filtered_df[filtered_df['Area'] == selected_area]

        if selected_regional != "Show All":
            filtered_df = filtered_df[filtered_df['Regional'] == selected_regional]

        if selected_site and selected_site != "Show All":
            filtered_df = filtered_df[filtered_df['Site ID'] == selected_site]

        if selected_date[0] and selected_date[1]:
            filtered_df = filtered_df[
                (filtered_df['Date'] >= pd.to_datetime(selected_date[0])) &
                (filtered_df['Date'] <= pd.to_datetime(selected_date[1]))
            ]

        # Display filtered DataFrame
        # st.dataframe(filtered_df)


        st.subheader('📈 CDC Site Availability')

        if filtered_df.empty:
            st.warning("No data available for selected filters.")
        else:
            # --- Plotly Chart ---
            fig = go.Figure()

            for site_id in filtered_df['Site ID'].unique():
                site_data = filtered_df[filtered_df['Site ID'] == site_id]
                fig.add_trace(go.Scatter(x=site_data['Date'], y=site_data['Availability'],
                                        mode='lines+markers', name=site_id))

            # --- Target Line ---
            if filtered_df['Site ID'].nunique() == 1:
                target_value = filtered_df['Target AVA'].iloc[0]
                fig.add_trace(go.Scatter(x=filtered_df['Date'], y=[target_value] * len(filtered_df),
                                        mode='lines', name=f"Target: {target_value:.1f}%",
                                        line=dict(dash='dash', color='red')))
            else:
                target_value = filtered_df['Target AVA'].mean()
                fig.add_trace(go.Scatter(x=filtered_df['Date'], y=[target_value] * len(filtered_df),
                                        mode='lines', name=f"Avg Target: {target_value:.2f}%",
                                        line=dict(dash='dash', color='red')))

            # --- Update Layout ---
            if selected_site != "Show All" and selected_site_name:
                chart_title = f"Availability for Site ID: {selected_site} - {selected_site_name}"
            else:
                chart_title = "Availability Overview"
            fig.update_layout(
                #title=f"Availability for Site ID: {selected_site} - {selected_site_name}",
                title=chart_title,
                xaxis_title="Date",
                yaxis_title="Availability (%)",
                showlegend=True,
                hovermode='x unified',
                plot_bgcolor='white',
                xaxis=dict(range=[selected_date[0], selected_date[1]])
            )

            st.plotly_chart(fig)
        
        # Convert filtered_df to CSV in memory
        csv_buffer = io.StringIO()
        filtered_df.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()

        # Add Download Button
        st.download_button(
            label="⬇️ Download Filtered Data as CSV",
            data=csv_data,
            file_name='filtered_site_availability.csv',
            mime='text/csv'
        )

    with tab3:
        # --- Area and Regional Filters Above the Table --- 
        # st.header("Filters (Summary View)")

        # Create two columns for side-by-side layout
        col1, col2 = st.columns(2)

        # Place the "Select Area" filter in the first column, with "Show All" option
        with col1:
            selected_area_summary = st.selectbox("Select Area", 
                                                options=['Show All'] + list(melted_df['Area'].unique()), 
                                                key="summary_area")

        # Filter Regional options based on the selected Area, with "Show All" option
        if selected_area_summary == 'Show All':
            regional_options = ['Show All'] + list(melted_df['Regional'].unique())
        else:
            regional_options = ['Show All'] + list(melted_df[melted_df['Area'] == selected_area_summary]['Regional'].unique())

        # Place the "Select Regional" filter in the second column, with "Show All" option
        with col2:
            selected_regional_summary = st.selectbox("Select Regional", options=regional_options, key="summary_regional")

        # Apply the filters
        summary_df = melted_df.copy()

        if selected_area_summary != 'Show All':
            summary_df = summary_df[summary_df['Area'] == selected_area_summary]

        if selected_regional_summary != 'Show All':
            summary_df = summary_df[summary_df['Regional'] == selected_regional_summary]
        
        st.subheader('📊 Site Availability Summary')

        if summary_df.empty:
            st.warning("No data available for selected filters.")
        else:
            # --- Add Month_Year column for monthly grouping --- 
            summary_df['Month_Year'] = summary_df['Date'].dt.to_period('M')

            # Calculate monthly average availability 
            monthly_summary = summary_df.groupby(['Area', 'Regional', 'Site ID', 'Site Name', 'Target AVA', 'Month_Year']).agg(
                avg_availability=('Availability', 'mean')
            ).reset_index()

            # Pivot table to get months as columns 
            monthly_summary_pivot = monthly_summary.pivot_table(
                index=['Area', 'Regional', 'Site ID', 'Site Name', 'Target AVA'],
                columns='Month_Year',
                values='avg_availability'
            ).reset_index()

            # Function to format Month_Year columns as 'Month-LastTwoDigitsYear' (e.g., 'Apr-25')
            def format_columns(columns):
                formatted_columns = []
                for col in columns:
                    try:
                        # Only attempt conversion if the column is a string or Timestamp
                        if isinstance(col, str) or isinstance(col, pd.Timestamp):
                            # Try to convert the column to Period (monthly frequency)
                            period_col = pd.to_datetime(col, errors='raise').to_period('M')
                            # Format as 'Month-LastTwoDigitsYear' (e.g., 'Apr-25')
                            formatted_columns.append(period_col.strftime('%b-%y'))
                        elif isinstance(col, pd.Period):
                            # If it's already a Period, format it
                            formatted_columns.append(col.strftime('%b-%y'))  # Using strftime to format Period
                        else:
                            formatted_columns.append(str(col))  # For other types, just convert to string
                    except Exception as e:
                        # Log the error if a column cannot be converted
                        print(f"Error converting column '{col}': {e}")
                        formatted_columns.append(str(col))  # If conversion fails, keep the original value
                return formatted_columns

            monthly_summary_pivot.columns = format_columns(monthly_summary_pivot.columns)

            # Function to apply coloring based on comparison with target
            def color_target_comparison(val, target):
                if val >= target:
                    return 'background-color: #c4d79b; color: black'
                else:
                    return 'background-color: #DA9694; color: black'

            # Function to highlight the availability columns (only month columns) using map
            def highlight_availability(df):
                styled_df = df.style.applymap(lambda val: color_target_comparison(val, df['Target AVA'].iloc[0]), subset=df.columns[5:])
                return styled_df

            # Apply rounding to two decimal places for 'Target AVA' and availability columns
            monthly_summary_pivot['Target AVA'] = monthly_summary_pivot['Target AVA'].round(2)
            monthly_summary_pivot.iloc[:, 5:] = monthly_summary_pivot.iloc[:, 5:].round(2)

            # Apply the color formatting
            styled_summary = highlight_availability(monthly_summary_pivot)

            # Display the styled dataframe
            st.dataframe(styled_summary, height=700)

            # --- Download Button ---
            st.download_button(
                label="📥 Download Summary as Excel",
                data=monthly_summary_pivot.to_csv(index=False).encode('utf-8'),
                file_name="site_availability_summary.csv",
                mime="text/csv"
            )

elif st.session_state.page == "⛽ Tracker Pengisian BBM":
    st.title("⛽ Tracker Pengisian BBM")
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
        df_pengisian = pd.read_csv("pengisian_bbm_streamlit.csv", parse_dates=["tanggal_pengisian"])
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
