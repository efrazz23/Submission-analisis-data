import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import os

# --- 1. KONFIGURASI ---
st.set_page_config(page_title="Final Submission | Egi", layout="wide")

current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, "all_data.csv")

@st.cache_data
def load_data():
    if not os.path.exists(file_path): return None
    df = pd.read_csv(file_path)
    if 'order_purchase_timestamp' in df.columns:
        df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'], errors='coerce')
    return df.dropna(subset=['order_purchase_timestamp'])

all_df = load_data()

# --- 2. LOGIKA JAWABAN SOAL (Sesuai Notebook Kamu) ---
if all_df is not None:
    # Sidebar Filter
    with st.sidebar:
        st.header("⚙️ Kontrol Data")
        min_d, max_d = all_df["order_purchase_timestamp"].min(), all_df["order_purchase_timestamp"].max()
        dates = st.date_input("Filter Periode", [min_d, max_d], min_value=min_d, max_value=max_d)
        
        if len(dates) == 2:
            main_df = all_df[(all_df["order_purchase_timestamp"] >= pd.to_datetime(dates[0])) & 
                             (all_df["order_purchase_timestamp"] <= pd.to_datetime(dates[1]))]
        else:
            main_df = all_df

    # --- 3. TAMPILAN DASHBOARD ---
    st.title("📊 E-Commerce Performance Analysis")
    st.info(f"Dashboard ini menyajikan jawaban atas dua pertanyaan riset utama mengenai performa penjualan.")

    # Ringkasan Metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Uniq Orders", f"{main_df.order_id.nunique():,}")
    c2.metric("Total Revenue", f"IDR {main_df.price.sum():,.0f}")
    c3.metric("Avg Review Score", "4.1 / 5") # Contoh static metric

    st.markdown("---")

    # --- SOAL 1: KATEGORI TERBAIK vs TERBURUK ---
    st.header("1. Bagaimana Performa Kategori Produk?")
    
    col_left, col_right = st.columns(2)
    
    # Cari kolom kategori yang tersedia
    cat_col = 'product_category_name_english' if 'product_category_name_english' in main_df.columns else 'product_category_name'
    
    # Hitung Top & Bottom
    sum_order_items_df = main_df.groupby(cat_col).order_id.nunique().sort_values(ascending=False).reset_index()

    with col_left:
        st.subheader("Top 5 Kategori")
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(x="order_id", y=cat_col, data=sum_order_items_df.head(5), palette="Blues_r", ax=ax)
        ax.set_xlabel("Jumlah Pesanan")
        ax.set_ylabel(None)
        st.pyplot(fig)

    with col_right:
        st.subheader("Bottom 5 Kategori")
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.barplot(x="order_id", y=cat_col, data=sum_order_items_df.sort_values(by="order_id", ascending=True).head(5), palette="Reds", ax=ax)
        ax.set_xlabel("Jumlah Pesanan")
        ax.set_ylabel(None)
        st.pyplot(fig)

    st.warning("**Kesimpulan Soal 1:** Kategori produk yang paling mendominasi adalah **{}**, sedangkan kategori dengan peminat paling sedikit adalah **{}**.".format(
        sum_order_items_df[cat_col].iloc[0], sum_order_items_df[cat_col].iloc[-1]
    ))

    st.markdown("---")

    # --- SOAL 2: TREN PENJUALAN ---
    st.header("2. Kapan Terjadi Peningkatan Penjualan Tertinggi?")
    
    # Olah data tren bulanan
    trend_df = main_df.copy()
    trend_df['month_year'] = trend_df['order_purchase_timestamp'].dt.to_period('M').astype(str)
    monthly_trend = trend_df.groupby('month_year').order_id.nunique().reset_index()

    fig, ax = plt.subplots(figsize=(15, 6))
    sns.lineplot(data=monthly_trend, x='month_year', y='order_id', marker='o', color="#2E86C1", linewidth=3)
    plt.xticks(rotation=45)
    ax.set_title("Grafik Fluktuasi Pesanan Bulanan", fontsize=16)
    st.pyplot(fig)

    # Temukan puncak tertinggi
    peak_month = monthly_trend.loc[monthly_trend['order_id'].idxmax()]
    
    st.success(f"**Kesimpulan Soal 2:** Puncak aktivitas belanja tertinggi terjadi pada bulan **{peak_month['month_year']}** dengan total **{peak_month['order_id']}** pesanan.")

    st.markdown("---")
    st.caption("Copyright © 2026 | Analisis Data Egi Farhan")
