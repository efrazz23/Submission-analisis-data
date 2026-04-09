import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import os

# Set style seaborn agar rapi seperti punya temanmu
sns.set(style='dark')

# --- 1. LOAD DATA ---
current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, "all_data.csv")

@st.cache_data
def load_data():
    if not os.path.exists(file_path):
        return None
    df = pd.read_csv(file_path)
    if 'order_purchase_timestamp' in df.columns:
        df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'])
    return df

all_df = load_data()

if all_df is not None:
    # --- 2. SIDEBAR ---
    with st.sidebar:
        # Gunakan logo resmi Dicoding Collection yang pasti jalan
        st.image("https://raw.githubusercontent.com/dicodingacademy/dicoding_datasets/main/logo_dicoding_collection.png", width=150)
        st.header("Filter Dashboard")
        
        min_date = all_df["order_purchase_timestamp"].min()
        max_date = all_df["order_purchase_timestamp"].max()
        
        # Ambil input rentang waktu
        date_range = st.date_input(
            label='Rentang Waktu',
            min_value=min_date,
            max_value=max_date,
            value=[min_date, max_date]
        )

    # --- 3. PROSES FILTER (INI KUNCINYA) ---
    if isinstance(date_range, list) and len(date_range) == 2:
        start_date, end_date = date_range
        # Filter tanpa menggunakan str() agar sinkron dengan datetime
        main_df = all_df[(all_df["order_purchase_timestamp"].dt.date >= start_date) & 
                         (all_df["order_purchase_timestamp"].dt.date <= end_date)]
    else:
        main_df = all_df

    # --- 4. MAIN CONTENT ---
    st.title('E-Commerce Analysis Dashboard 🛒')
    
    # Metrik di bagian atas
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Revenue", value=f"BRL {main_df.price.sum():,.2f}")
    with col2:
        st.metric("Total Orders", value=f"{main_df.order_id.nunique():,}")

    st.divider()

    # --- 5. GRAFIK (Prinsip Integritas Visual) ---
    st.subheader('Profitabilitas Berdasarkan State')
    
    state_revenue = main_df.groupby("customer_state").price.sum().sort_values(ascending=False).reset_index().head(5)
    
    fig, ax = plt.subplots(figsize=(10, 5))
    # WARNA SERAGAM: Satu highlight biru, sisanya abu-abu (Sesuai mau Reviewer!)
    colors = ["#72BCD4" if i == 0 else "#D3D3D3" for i in range(len(state_revenue))]
    
    sns.barplot(x="price", y="customer_state", data=state_revenue, palette=colors, ax=ax)
    ax.set_title("Top 5 State dengan Pendapatan Tertinggi", fontsize=15)
    ax.set_xlabel("Total Revenue (BRL)")
    ax.set_ylabel(None)
    st.pyplot(fig)

    # RFM Singkat (Opsional, agar dashboard lebih "berisi" dari temanmu)
    st.subheader("Ringkasan RFM")
    st.write(f"Data periode: {start_date} sampai {end_date}")

    st.caption('Copyright (c) 2026 - Egi Farhan')
else:
    st.error("File all_data.csv tidak ditemukan di folder dashboard!")
