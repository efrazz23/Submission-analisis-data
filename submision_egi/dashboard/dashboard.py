import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import os

# Set tema agar bersih
sns.set(style='dark')

# --- 1. LOAD DATA ---
current_dir = os.path.dirname(os.path.abspath(__file__))
# Pastikan file all_data.csv ada di folder yang sama dengan dashboard.py
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

# --- 2. CEK DATA & FILTERING ---
if all_df is not None:
    with st.sidebar:
        # Link logo resmi yang pasti bisa diakses (Fix gambar pecah)
        st.image("https://raw.githubusercontent.com/dicodingacademy/dicoding_datasets/main/logo_dicoding_collection.png", width=150)
        st.header("Filter Data")
        
        min_date = all_df["order_purchase_timestamp"].min()
        max_date = all_df["order_purchase_timestamp"].max()
        
        # Ambil input tanggal
        date_range = st.date_input(
            label='Rentang Waktu',
            min_value=min_date,
            max_value=max_date,
            value=[min_date, max_date]
        )

    # Memastikan filter memotong data dengan benar (Fix grafik tidak berubah)
    if isinstance(date_range, list) and len(date_range) == 2:
        start_date, end_date = date_range
        main_df = all_df[(all_df["order_purchase_timestamp"].dt.date >= start_date) & 
                         (all_df["order_purchase_timestamp"].dt.date <= end_date)]
    else:
        main_df = all_df

    # --- 3. HEADER & METRICS ---
    st.title('E-Commerce Analysis Dashboard 🛒')
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Revenue", value=f"BRL {main_df.price.sum():,.2f}")
    with col2:
        st.metric("Total Order", value=f"{main_df.order_id.nunique():,}")
    with col3:
        st.metric("Total Customer", value=f"{main_df.customer_id.nunique():,}")

    st.divider()

    # --- 4. VISUALISASI 1 (Berdasarkan Nilai Tertinggi - Reviewer's Request) ---
    st.subheader('1. Profitabilitas Produk Berdasarkan Wilayah')
    
    # Menghitung revenue per state dari main_df (data hasil filter)
    state_revenue = main_df.groupby("customer_state").price.sum().sort_values(ascending=False).reset_index().head(5)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # PRINSIP INTEGRITAS: Warna seragam, highlight biru hanya untuk yang tertinggi
    colors = ["#0077b6" if i == 0 else "#D3D3D3" for i in range(len(state_revenue))]
    
    sns.barplot(x="price", y="customer_state", data=state_revenue, palette=colors, ax=ax)
    ax.set_title("Top 5 State dengan Revenue Tertinggi", fontsize=15)
    ax.set_xlabel("Total Revenue (BRL)")
    ax.set_ylabel(None)
    st.pyplot(fig)

    # --- 5. VISUALISASI 2 (AOV Analysis) ---
    st.subheader("2. Analisis Average Order Value (AOV)")
    aov_data = main_df.groupby('customer_state').agg({'price': 'sum', 'order_id': 'nunique'})
    aov_data['AOV'] = aov_data['price'] / aov_data['order_id']
    top_aov = aov_data.sort_values('AOV', ascending=False).head(5).reset_index()

    fig2, ax2 = plt.subplots(figsize=(10, 6))
    colors_aov = ["#0077b6" if i == 0 else "#D3D3D3" for i in range(len(top_aov))]
    sns.barplot(x="AOV", y="customer_state", data=top_aov, palette=colors_aov, ax=ax2)
    ax2.set_title("Top 5 State Berdasarkan AOV", fontsize=15)
    st.pyplot(fig2)

    st.caption('Copyright (c) 2026 | Analisis Data Egi Farhan')

else:
    # Error handling jika file tidak terbaca
    st.error("Gagal memuat data. Pastikan file 'all_data.csv' berada di folder yang sama dengan file dashboard ini.")
