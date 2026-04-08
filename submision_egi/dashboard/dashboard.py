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
    
    # Konversi tanggal secara otomatis
    for col in df.columns:
        if 'timestamp' in col or 'date' in col:
            df[col] = pd.to_datetime(df[col], errors='coerce')
            
    return df

df_raw = load_data()

if df_raw is not None:
    # --- DETEKSI KOLOM OTOMATIS (Biar Gak KeyError Lagi) ---
    # Mencari kolom kategori: coba cari yang 'english', kalau gak ada pakai yang biasa
    cat_col = None
    possible_cat_cols = ['product_category_name_english', 'product_category_name', 'category']
    for c in possible_cat_cols:
        if c in df_raw.columns:
            cat_col = c
            break
            
    # Mencari kolom tanggal utama
    date_col = 'order_purchase_timestamp' if 'order_purchase_timestamp' in df_raw.columns else None

    # --- 3. SIDEBAR ---
    with st.sidebar:
        st.title("🛍️ Menu Navigasi")
        if date_col:
            min_date, max_date = df_raw[date_col].min(), df_raw[date_col].max()
            start_date, end_date = st.date_input("Rentang Waktu", [min_date, max_date], min_value=min_date, max_value=max_date)
            main_df = df_raw[(df_raw[date_col] >= pd.to_datetime(start_date)) & (df_raw[date_col] <= pd.to_datetime(end_date))]
        else:
            main_df = df_raw

    # --- 4. DASHBOARD UTAMA ---
    st.title("Dashboard Insight Penjualan Egi")
    st.markdown("---")

    # Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Pesanan", f"{main_df['order_id'].nunique() if 'order_id' in main_df.columns else 0:,}")
    with col2:
        st.metric("Total Pendapatan", f"IDR {main_df['price'].sum() if 'price' in main_df.columns else 0:,.0f}")
    with col3:
        st.metric("Total Item", f"{main_df.shape[0]:,}")

    # --- 5. VISUALISASI ---
    tab1, tab2 = st.tabs(["🏆 Produk Terlaris", "📈 Tren Penjualan"])

    with tab1:
        if cat_col:
            st.subheader(f"Top 10 Kategori Produk ({cat_col})")
            top_cat = main_df.groupby(cat_col).order_id.nunique().sort_values(ascending=False).head(10).reset_index()
            
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.barplot(x="order_id", y=cat_col, data=top_cat, palette="viridis", ax=ax)
            st.pyplot(fig)
        else:
            st.warning("Kolom kategori tidak ditemukan di dataset.")

    with tab2:
        if date_col:
            st.subheader("Tren Pesanan Bulanan")
            monthly_orders = main_df.resample(rule='M', on=date_col).order_id.nunique().reset_index()
            
            fig, ax = plt.subplots(figsize=(12, 5))
            ax.plot(monthly_orders[date_col], monthly_orders['order_id'], marker='o', color="#E74C3C")
            st.pyplot(fig)
        else:
            st.warning("Kolom tanggal tidak ditemukan untuk membuat tren.")

    st.markdown("---")
    st.caption("Egi Farhan | Dicoding Submission 2026")
