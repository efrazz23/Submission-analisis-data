import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import os

# --- 1. SETTING DASAR ---
st.set_page_config(page_title="E-Commerce Analysis | Egi", layout="wide")

current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, "all_data.csv")

# --- 2. FUNGSI LOAD DATA ---
@st.cache_data
def load_data():
    if not os.path.exists(file_path):
        st.error(f"File {file_path} tidak ditemukan!")
        return None
    
    df = pd.read_csv(file_path)
    
    # Konversi tanggal dengan penanganan error 'coerce' (jadi NaT jika gagal)
    # Kita fokus ke kolom utama: order_purchase_timestamp
    if 'order_purchase_timestamp' in df.columns:
        df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'], errors='coerce')
        # Hapus data yang tanggalnya gagal diconvert
        df = df.dropna(subset=['order_purchase_timestamp'])
            
    return df

df_raw = load_data()

if df_raw is not None:
    # Identifikasi Kolom Kategori (Otomatis)
    cat_col = None
    for c in ['product_category_name_english', 'product_category_name']:
        if c in df_raw.columns:
            cat_col = c
            break

    # --- 3. SIDEBAR ---
    with st.sidebar:
        st.title("🛍️ Menu Navigasi")
        st.info("Analisis Data E-Commerce")
        
        # Filter Rentang Waktu
        min_date = df_raw["order_purchase_timestamp"].min()
        max_date = df_raw["order_purchase_timestamp"].max()
        
        # Penanganan filter tanggal agar tidak crash
        try:
            date_range = st.date_input(
                "Rentang Waktu",
                value=[min_date, max_date],
                min_value=min_date,
                max_value=max_date
            )
            if len(date_range) == 2:
                start_date, end_date = date_range
                main_df = df_raw[(df_raw["order_purchase_timestamp"] >= pd.to_datetime(start_date)) & 
                                 (df_raw["order_purchase_timestamp"] <= pd.to_datetime(end_date))]
            else:
                main_df = df_raw
        except:
            main_df = df_raw

    # --- 4. HEADER & METRICS ---
    st.title("📊 Dashboard Insight Penjualan - Egi")
    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Order", f"{main_df['order_id'].nunique():,}")
    with col2:
        st.metric("Total Revenue", f"IDR {main_df['price'].sum():,.0f}")
    with col3:
        st.metric("Total Produk", f"{main_df.shape[0]:,}")

    # --- 5. VISUALISASI ---
    tab1, tab2 = st.tabs(["🏆 Produk Terlaris", "📈 Tren Bulanan"])

    with tab1:
        if cat_col:
            st.subheader(f"Top 10 Kategori Produk")
            top_cat = main_df.groupby(cat_col).order_id.nunique().sort_values(ascending=False).head(10).reset_index()
            
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.barplot(x="order_id", y=cat_col, data=top_cat, palette="viridis", ax=ax)
            ax.set_xlabel("Jumlah Pesanan")
            ax.set_ylabel(None)
            st.pyplot(fig)
            st.success("Analisis: Kategori di atas merupakan penyumbang transaksi terbesar.")
        else:
            st.warning("Kolom kategori tidak ditemukan.")

    with tab2:
        st.subheader("Tren Pesanan Bulanan")
        
        # Menggunakan metode manual (bukan resample) agar lebih aman antar versi Pandas
        monthly_df = main_df.copy()
        monthly_df['month_year'] = monthly_df['order_purchase_timestamp'].dt.to_period('M').astype(str)
        monthly_trend = monthly_df.groupby('month_year').order_id.nunique().reset_index()
        
        fig, ax = plt.subplots(figsize=(12, 5))
        sns.lineplot(x='month_year', y='order_id', data=monthly_trend, marker='o', color="#E74C3C", linewidth=2.5)
        plt.xticks(rotation=45)
        ax.set_xlabel("Bulan")
        ax.set_ylabel("Jumlah Pesanan")
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        st.pyplot(fig)

    st.markdown("---")
    st.caption("Copyright © 2026 | Egi Farhan - Proyek Analisis Data")
