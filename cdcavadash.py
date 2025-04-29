import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import io

# --- Page Config ---
st.set_page_config(page_title="CDC Site Availability Tracker", layout="wide")
st.title('📊 CDC Site Availability Dashboard')

file_path = "data/CDC_Availability_2025_194 sites.xlsx"

try:
    df = pd.read_excel(file_path, sheet_name="Ava CDC", engine="openpyxl")
    st.success("Data loaded successfully from local file!")
except Exception as e:
    st.error(f"Failed to load data: {e}")
    st.stop()  # Stop the app if loading fails

# --- Data Preparation ---
melted_df = pd.melt(df, 
                    id_vars=['Area', 'Site ID', 'Regional', 'Site Name', 'NS', 'Cluster', 'On Service / Cut OFF', 'Site Class', 'Target AVA'],
                    var_name='Date', 
                    value_name='Availability')

melted_df['Date'] = pd.to_datetime(melted_df['Date'], format='%d-%b-%y', errors='coerce')
melted_df = melted_df.dropna(subset=['Date'])

# --- Tabs ---
tab1, tab2 = st.tabs(["📈 Daily Tracker", "📊 Summary View"])

with tab1:
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

with tab2:
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
        st.dataframe(styled_summary)

        # --- Download Button ---
        st.download_button(
            label="📥 Download Summary as Excel",
            data=monthly_summary_pivot.to_csv(index=False).encode('utf-8'),
            file_name="site_availability_summary.csv",
            mime="text/csv"
        )
