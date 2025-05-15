# --- utils/data_loader.py ---
import pandas as pd
import streamlit as st
import os
import re

def load_availability_data():
    file_path = "data/CDC_Availability_2025_194.xlsx"
    try:
        df = pd.read_excel(file_path, sheet_name="Ava CDC")
    except Exception as e:
        st.error(f"Failed to load CDC Availability data: {e}")
        st.stop()

    melted_df = pd.melt(df, 
                        id_vars=['Area', 'Site ID', 'Regional', 'Site Name', 'NS', 'Cluster', 'On Service / Cut OFF', 'Site Class', 'Target AVA'],
                        var_name='Date', 
                        value_name='Availability')

    melted_df['Date'] = pd.to_datetime(melted_df['Date'], format='%d-%b-%y', errors='coerce')
    melted_df = melted_df.dropna(subset=['Date'])
    return melted_df

def load_cdc_po_data():
    file_path = "data/ESTIMASIPO2025.xlsx"
    filename = os.path.basename(file_path)
    match = re.search(r"\d{4}", filename)
    cdc_year = match.group(0) if match else "Unknown"

    expected_sheets = ["JANUARI", "FEBRUARI", "MARET", "APRIL", "MEI", "JUNI", 
                       "JULI", "AGUSTUS", "SEPTEMBER", "OKTOBER", "NOVEMBER", "DESEMBER"]

    try:
        xls = pd.ExcelFile(file_path)
        available_sheets = xls.sheet_names
        cdc_df_list = []
        for month in expected_sheets:
            if month in available_sheets:
                df_month = pd.read_excel(xls, sheet_name=month, header=1)
                df_month['Month'] = month
                df_month['Year'] = cdc_year
                cdc_df_list.append(df_month)

        cdc_df = pd.concat(cdc_df_list, ignore_index=True)

        if 'Avaibility' in cdc_df.columns and 'Target Availability (%)' in cdc_df.columns:
            cdc_df['Ava Achievement'] = cdc_df.apply(
                lambda row: 'Achieved' if row['Avaibility'] >= row['Target Availability (%)'] else 'Not Achieved',
                axis=1
            )
        else:
            st.warning("Columns 'Avaibility' or 'Target Availability (%)' not found in PO data.")

    except Exception as e:
        st.error(f"Failed to read CDC Monthly file: {e}")
        return pd.DataFrame()

    return cdc_df

def load_dapot_alpro_data():
    file_path = "data/Dapot_Alpro_CDC_2025.xlsx"
    sheet_names = ["Sumbagsel", "Sumbagteng", "Jawa Timur", "Bali Nusra", "Kalimantan", "Puma", "Sulawesi"]

    try:
        xls = pd.ExcelFile(file_path)
        dapot_df_list = []

        for sheet in sheet_names:
            if sheet in xls.sheet_names:
                df_sheet = pd.read_excel(xls, sheet_name=sheet, header=1)  # Header is on the second row
                df_sheet['Region'] = sheet  # Add sheet name as region identifier
                
                if "On Service / Cut OFF" in df_sheet.columns:
                    col = "On Service / Cut OFF"

                    # Standardize values: lower, strip, then map
                    df_sheet[col] = (
                        df_sheet[col]
                        .astype(str)
                        .str.strip()
                        .str.lower()
                        .replace({
                            "on service": "On Service",
                            "cut off": "Cut Off",
                            "idle": "Cut Off"
                        })
                    )
                
                # Clean "Site Class"
                if "Site Class" in df_sheet.columns:
                    df_sheet["Site Class"] = (
                        df_sheet["Site Class"]
                        .astype(str)
                        .str.strip()
                        .str.title()  # Proper case formatting (e.g., "Silver", "Gold")
                    )

                df_sheet.rename(columns={"On Service / Cut OFF": "STATUS"}, inplace=True)
                dapot_df_list.append(df_sheet)

        dapot_df = pd.concat(dapot_df_list, ignore_index=True)
        return dapot_df

    except Exception as e:
        st.error(f"Failed to load Dapot Alpro data: {e}")
        return pd.DataFrame()

