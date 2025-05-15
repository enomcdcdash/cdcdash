# --- pages/availability.py ---
import streamlit as st
import io
import plotly.graph_objects as go
import pandas as pd
import random
from utils.data_loader import load_availability_data, load_cdc_po_data

def show():
    st.title("\U0001F4C5 CDC Availability")

    melted_df = load_availability_data()
    cdc_df = load_cdc_po_data()

    tab1, tab2, tab3 = st.tabs(["📅 CDC Monthly Summary", "📈 Availability Daily Tracker", "📊 Availability Summary (INAP)"])

    with tab1:
        st.subheader("📅 CDC Monthly Summary")

        if cdc_df.empty:
            st.warning("No CDC Monthly data available.")
        else:
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

            cdc_df['Site Id'] = cdc_df['Site Id'].astype(str).str.strip()

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                selected_month = st.selectbox("Select Month", ["All"] + sorted(cdc_df["Month"].dropna().unique().tolist()))

            with col2:
                selected_year = st.selectbox("Select Year", ["All"] + sorted(cdc_df["Year"].dropna().unique()))

            with col3:
                selected_regional = st.selectbox("Select Regional", ["All"] + sorted(cdc_df["Regional TI"].dropna().unique()))

            site_filter_df = cdc_df.copy()
            if selected_month != "All":
                site_filter_df = site_filter_df[site_filter_df["Month"] == selected_month]
            if selected_year != "All":
                site_filter_df = site_filter_df[site_filter_df["Year"] == selected_year]
            if selected_regional != "All":
                site_filter_df = site_filter_df[site_filter_df["Regional TI"] == selected_regional]

            available_sites = sorted(site_filter_df["Site Id"].dropna().unique().tolist())
            site_choices = ["All"] + available_sites

            if "default_site_index" not in st.session_state:
                st.session_state.default_site_index = random.randint(1, len(site_choices) - 1) if len(site_choices) > 1 else 0

            with col4:
                safe_index = st.session_state.default_site_index if st.session_state.default_site_index < len(site_choices) else 0
                selected_site = st.selectbox("Select Site ID", options=site_choices, index=safe_index)

            #with col5:
            #    search_site = st.text_input("🔍 Search Site ID")

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
            #if search_site:
            #    filtered_df = filtered_df[filtered_df["Site Id"].str.contains(search_site)]

            selected_site_name = ""
            if selected_site != "All":
                site_name_match = filtered_df[filtered_df["Site Id"] == selected_site]["Site Name"]
                if not site_name_match.empty:
                    selected_site_name = site_name_match.iloc[0]

            if not filtered_df.empty:
                month_translation = {
                    'JANUARI': 'January', 'FEBRUARI': 'February', 'MARET': 'March',
                    'APRIL': 'April', 'MEI': 'May', 'JUNI': 'June', 'JULI': 'July',
                    'AGUSTUS': 'August', 'SEPTEMBER': 'September', 'OKTOBER': 'October',
                    'NOVEMBER': 'November', 'DESEMBER': 'December'
                }

                filtered_df['Month_Eng'] = filtered_df['Month'].str.upper().map(month_translation)
                filtered_df['Month_Num'] = pd.to_datetime(filtered_df['Month_Eng'], format='%B').dt.month
                filtered_df['Month_Year'] = filtered_df['Month_Eng'] + " - " + filtered_df['Year'].astype(str)
                filtered_df = filtered_df.sort_values(by=['Year', 'Month_Num'])

                chart_col1, chart_col2 = st.columns(2)

                with chart_col1:
                    st.markdown("#### 📈 Site Monthly Availability Trend")
                    fig1 = go.Figure()

                    for site_id, group in filtered_df.groupby('Site Id'):
                        target_value = group['Target Availability (%)'].iloc[0] if not group['Target Availability (%)'].isnull().all() else 0
                        target_label = f"Target: {int(target_value * 100)}%" if target_value % 0.01 == 0 else f"Target: {target_value * 100:.1f}%"

                        fig1.add_trace(go.Scatter(
                            x=group['Month_Year'], y=group['Avaibility'], mode='lines+markers+text',
                            name=site_id, text=group['Avaibility'].apply(lambda x: f"{x:.2%}"),
                            textposition='bottom center', showlegend=True
                        ))
                        fig1.add_trace(go.Scatter(
                            x=group['Month_Year'], y=group['Target Availability (%)'], mode='lines+markers+text',
                            name=target_label, text=group['Target Availability (%)'].apply(lambda x: f"{x:.2%}"),
                            textposition='bottom center', line=dict(dash='dash'), showlegend=True
                        ))

                    fig1.update_layout(
                        title=dict(text=f"Availability Site {selected_site} - {selected_site_name}", x=0.5, xanchor='center', font=dict(size=18)),
                        yaxis_title="Availability", hovermode='closest', yaxis_tickformat=".0%",
                        yaxis=dict(range=[0, 1], tickmode="linear", tick0=0, dtick=0.1),
                        legend=dict(orientation="h", yanchor="top", y=-0.3, xanchor="center", x=0.5)
                    )
                    st.plotly_chart(fig1, use_container_width=True)

            with chart_col2:
                st.markdown("#### 💰 Nominal PO vs Penalty")
                fig2 = go.Figure()

                for site_id, group in filtered_df.groupby('Site Id'):
                    fig2.add_trace(go.Scatter(
                        x=group['Month_Year'], y=group['Nominal PO'], mode='lines+markers+text',
                        name=f'{site_id} - PO', line=dict(color='green'),
                        text=group['Nominal PO'].apply(lambda x: f"{x:,.0f}"),
                        textposition='top center', textfont=dict(color='green', size=10)
                    ))
                    fig2.add_trace(go.Scatter(
                        x=group['Month_Year'], y=group['Nilai Penalty'], mode='lines+markers+text',
                        name=f'{site_id} - Penalty', line=dict(color='red'),
                        fill='tozeroy', fillcolor='rgba(255, 0, 0, 0.2)',
                        text=group['Nilai Penalty'].apply(lambda x: f"{x:,.0f}"),
                        textposition='top center', textfont=dict(color='red', size=10)
                    ))

                fig2.update_layout(
                    title=dict(text=f"{selected_site} - {selected_site_name}", x=0.5, xanchor='center', font=dict(size=18)),
                    yaxis_title="IDR", hovermode='closest',
                    legend=dict(orientation="h", yanchor="top", y=-0.3, xanchor="center", x=0.5)
                )
                st.plotly_chart(fig2, use_container_width=True)

        if not filtered_df.empty:
            desired_columns = [
                'No', 'Month_Year', 'Regional TI', 'Site Id', 'Site Name', 'Daya PO',
                'Periode Tagihan (Awal)', 'Periode Tagihan (Akhir)', 'Jumlah Periode (Bulan)',
                'Nominal PO', 'Index BBM', 'Class Site', 'Target Availability (%)', 'Avaibility',
                'Persentase Penalty', 'Nilai Penalty', 'Nilai BAST', 'Nilai BAST dikurangi Penalty',
                'Ava Achievement'
            ]

            filtered_df = filtered_df[desired_columns]
            st.dataframe(style_cdc(filtered_df))

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                filtered_df.to_excel(writer, index=False, sheet_name='Filtered Data')
            output.seek(0)

            st.download_button(
                label="📥 Download Filtered Data as Excel",
                data=output,
                file_name="filtered_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

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
        st.subheader('📈 CDC Site Availability')

        # Create a single row for all filters (removing Search Site ID input)
        col1, col2, col3, col4 = st.columns(4)

        # --- Area filter ---
        with col1:
            area_options = ["Show All"] + list(melted_df['Area'].dropna().unique())
            selected_area = st.selectbox("Area", options=area_options)

        # --- Regional options based on selected area ---
        filtered_by_area = melted_df[melted_df['Area'] == selected_area] if selected_area != "Show All" else melted_df.copy()

        with col2:
            regional_options = ["Show All"] + list(filtered_by_area['Regional'].dropna().unique())
            selected_regional = st.selectbox("Regional", options=regional_options)

        # --- Date Range Picker ---
        with col3:
            valid_dates = melted_df['Date'].dropna()
            if not valid_dates.empty:
                selected_date = st.date_input(
                    "Date Range",
                    [valid_dates.min(), valid_dates.max()]
                )
            else:
                st.warning("No valid dates available.")
                selected_date = [None, None]

        # --- Site ID selection ---
        filtered_by_regional = filtered_by_area[filtered_by_area['Regional'] == selected_regional] if selected_regional != "Show All" else filtered_by_area.copy()
        site_id_options = filtered_by_regional['Site ID'].dropna().unique()
        site_id_options = ["Show All"] + list(site_id_options)

        with col4:
            selected_site = st.selectbox("Site ID", options=site_id_options)

        # --- Get Site Name after Site ID selection ---
        selected_site_name = ""
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

        if selected_site != "Show All":
            filtered_df = filtered_df[filtered_df['Site ID'] == selected_site]

        if selected_date[0] and selected_date[1]:
            filtered_df = filtered_df[
                (filtered_df['Date'] >= pd.to_datetime(selected_date[0])) &
                (filtered_df['Date'] <= pd.to_datetime(selected_date[1]))
            ]

        # --- Chart ---
        if filtered_df.empty:
            st.warning("No data available for selected filters.")
        else:
            fig = go.Figure()

            for site_id in filtered_df['Site ID'].unique():
                site_data = filtered_df[filtered_df['Site ID'] == site_id]
                fig.add_trace(go.Scatter(
                    x=site_data['Date'],
                    y=site_data['Availability'],
                    mode='lines+markers',
                    name=site_id,
                    hovertemplate=
                        "<b>Site ID:</b> " + site_id + "<br>" +
                        "<b>Date:</b> %{x}<br>" +
                        "<b>Availability:</b> %{y:.2f}%<br>" +
                        "<extra></extra>"
                ))

            # Add Target Line
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

            # Chart Title
            chart_title = f"Availability for Site ID: {selected_site} - {selected_site_name}" if selected_site != "Show All" and selected_site_name else "Availability Overview"

            fig.update_layout(
                title=chart_title,
                xaxis_title="Date",
                yaxis_title="Availability (%)",
                showlegend=True,
                hovermode='closest',
                plot_bgcolor='white',
                xaxis=dict(range=[selected_date[0], selected_date[1]])
            )

            st.plotly_chart(fig)

            # Download filtered data
            csv_buffer = io.StringIO()
            filtered_df.to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue()

            st.download_button(
                label="⬇️ Download Filtered Data as CSV",
                data=csv_data,
                file_name='filtered_site_availability.csv',
                mime='text/csv'
            )

    with tab3:
        st.subheader('📊 Site Availability Summary')

        # --- Create cascading filters: Area → Regional → Site ID ---
        col1, col2, col3 = st.columns(3)

        # Area filter
        with col1:
            selected_area_summary = st.selectbox("Select Area", 
                                                options=['Show All'] + sorted(melted_df['Area'].dropna().unique().tolist()), 
                                                key="summary_area")

        # Filter Regional options based on selected Area
        if selected_area_summary == 'Show All':
            regional_options = ['Show All'] + sorted(melted_df['Regional'].dropna().unique().tolist())
            filtered_df = melted_df.copy()
        else:
            regional_options = ['Show All'] + sorted(melted_df[melted_df['Area'] == selected_area_summary]['Regional'].dropna().unique().tolist())
            filtered_df = melted_df[melted_df['Area'] == selected_area_summary]

        with col2:
            selected_regional_summary = st.selectbox("Select Regional", options=regional_options, key="summary_regional")

        if selected_regional_summary != 'Show All':
            filtered_df = filtered_df[filtered_df['Regional'] == selected_regional_summary]

        # Site ID options based on filters above
        site_id_options = ['Show All'] + sorted(filtered_df['Site ID'].dropna().unique().tolist())
        with col3:
            selected_site_summary = st.selectbox("Select Site ID", options=site_id_options, key="summary_site")

        if selected_site_summary != 'Show All':
            filtered_df = filtered_df[filtered_df['Site ID'] == selected_site_summary]

        # Warn if no data after filtering
        if filtered_df.empty:
            st.warning("No data available for selected filters.")
        else:
            # Ensure 'Date' is in datetime format
            filtered_df['Date'] = pd.to_datetime(filtered_df['Date'], errors='coerce')
            filtered_df['Month_Year'] = filtered_df['Date'].dt.to_period('M')

            # Monthly average availability
            monthly_summary = filtered_df.groupby(['Area', 'Regional', 'Site ID', 'Site Name', 'Target AVA', 'Month_Year']).agg(
                avg_availability=('Availability', 'mean')
            ).reset_index()

            # Pivot table
            monthly_summary_pivot = monthly_summary.pivot_table(
                index=['Area', 'Regional', 'Site ID', 'Site Name', 'Target AVA'],
                columns='Month_Year',
                values='avg_availability'
            ).reset_index()

            # Format columns as 'Apr-25' etc.
            def format_columns(columns):
                formatted_columns = []
                for col in columns:
                    try:
                        if isinstance(col, (str, pd.Timestamp)):
                            period_col = pd.to_datetime(col).to_period('M')
                            formatted_columns.append(period_col.strftime('%b-%y'))
                        elif isinstance(col, pd.Period):
                            formatted_columns.append(col.strftime('%b-%y'))
                        else:
                            formatted_columns.append(str(col))
                    except Exception:
                        formatted_columns.append(str(col))
                return formatted_columns

            monthly_summary_pivot = monthly_summary_pivot.round(2) 
            monthly_summary_pivot.columns = format_columns(monthly_summary_pivot.columns)
            monthly_summary_pivot.reset_index(drop=True, inplace=True)
            monthly_summary_pivot.insert(0, 'No', range(1, len(monthly_summary_pivot) + 1))

            def highlight_availability(row):
                styles = []
                target = row['Target AVA']
                for i, col in enumerate(monthly_summary_pivot.columns):
                    if col in ['Area', 'Regional', 'Site ID', 'Site Name', 'Target AVA']:
                        styles.append('')  # No style for non-month columns
                    else:
                        val = row[col]
                        if pd.isnull(val):
                            styles.append('')
                        elif val >= target:
                            styles.append('background-color: #C4D79B; color: black')
                        else:
                            styles.append('background-color: #FFB7B7; color: black')
                return styles

            styled_df = monthly_summary_pivot.style.apply(highlight_availability, axis=1).format(precision=2)
            
            st.dataframe(styled_df, height=500)

            # --- Download Button ---
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                monthly_summary_pivot.to_excel(writer, index=False, sheet_name='Summary')

                workbook  = writer.book
                worksheet = writer.sheets['Summary']

                # Define format for two decimal places
                two_dec_format = workbook.add_format({'num_format': '0.00'})

                # Apply format to data columns (starting from 6th column = index 5)
                for col_num, value in enumerate(monthly_summary_pivot.columns.values):
                    if col_num >= 5:  # skip Area, Regional, Site ID, Site Name, Target AVA
                        worksheet.set_column(col_num, col_num, 12, two_dec_format)

            st.download_button(
                label="📥 Download Summary as Excel",
                data=excel_buffer.getvalue(),
                file_name="site_availability_summary.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )