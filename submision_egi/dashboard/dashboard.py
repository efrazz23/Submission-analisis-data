import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import os

# 1. Konfigurasi Path & Load Data
current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, "all_data.csv")

# Set Page Config (Biar tampilan lebih luas dan profesional)
st.set_page_config(page_title="Analisis Bisnis E-Commerce", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv(file_path)
    df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'])
    return df

all_df = load_data()

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://raw.githubusercontent.com/efrazz23/Submission-analisis-data/main/logo.png", width=100) # Ganti link logo jika ada
    st.header("Filter Analisis")
    # Filter rentang waktu
    min_date = all_df["order_purchase_timestamp"].min()
    max_date = all_df["order_purchase_timestamp"].max()
    
    start_date, end_date = st.date_input(
        "Pilih Rentang Waktu",
        [min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )

# Filter Data Berdasarkan Tanggal
main_df = all_df[(all_df["order_purchase_timestamp"] >= pd.to_datetime(start_date)) & 
                 (all_df["order_purchase_timestamp"] <= pd.to_datetime(end_date))]

# --- DASHBOARD UTAMA ---
st.title("🚀 Business Insights Dashboard")
st.markdown("---")

# Row 1: Key Metrics (Ini pembeda besar dengan dashboard biasa)
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Transaksi", value=f"{main_df.order_id.nunique():,}")
with col2:
    st.metric("Total Pendapatan", value=f"IDR {main_df.price.sum():,.0f}")
with col3:
    st.metric("Produk Terjual", value=f"{main_df.order_item_id.count():,}")

# Row 2: Dua Soal Inti (Menggunakan Tabs agar rapi)
tab1, tab2 = st.tabs(["🏆 Produk Terpopuler", "📈 Tren Penjualan"])

with tab1:
    st.subheader("Kategori Produk dengan Volume Penjualan Tertinggi")
    
    # Menyiapkan data
    top_products = main_df.groupby("product_category_name_english").order_id.nunique().sort_values(ascending=False).head(10).reset_index()
    
    fig, ax = plt.subplots(figsize=(12, 6))
    # Pakai warna "deep" atau "magma" agar beda dari temanmu
    sns.barplot(
        x="order_id", 
        y="product_category_name_english", 
        data=top_products, 
        palette="magma", 
        ax=ax
    )
    ax.set_xlabel("Jumlah Pesanan")
    ax.set_ylabel(None)
    ax.set_title("10 Kategori Produk Paling Laris", loc="center", fontsize=15)
    st.pyplot(fig)
    
    with st.expander("Lihat Analisis"):
        st.write("Kategori produk yang mendominasi menunjukkan tren kebutuhan pasar saat ini. Strategi stok harus difokuskan pada kategori teratas ini.")

with tab2:
    st.subheader("Analisis Fluktuasi Penjualan Bulanan")
    
    # Menyiapkan data tren
    monthly_df = main_df.resample(rule='M', on='order_purchase_timestamp').agg({
        "order_id": "nunique",
        "price": "sum"
    })
    monthly_df.index = monthly_df.index.strftime('%B %Y')
    monthly_df = monthly_df.reset_index()

    fig, ax = plt.subplots(figsize=(16, 8))
    ax.plot(
        monthly_df["order_purchase_timestamp"],
        monthly_df["order_id"],
        marker='o', 
        linewidth=3,
        color="#D4AC0D" # Warna Emas agar elegan
    )
    ax.set_title("Jumlah Pesanan per Bulan", loc="center", fontsize=20)
    plt.xticks(rotation=45)
    st.pyplot(fig)

# Footer
st.markdown("---")
st.caption("Copyright © 2026 | Analisis Data Egi Farhan")
