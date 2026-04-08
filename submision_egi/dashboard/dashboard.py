import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import os

# --- 1. SETTING DASAR & PATH ---
st.set_page_config(page_title="E-Commerce Analysis | Egi", layout="wide")

# Penanganan Path File yang Aman
current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, "all_data.csv")

# --- 2. FUNGSI LOAD DATA ---
@st.cache_data
def load_data():
    if not os.path.exists(file_path):
        st.error(f"File {file_path} tidak ditemukan! Pastikan CSV ada di folder yang sama.")
        return None
    
    df = pd.read_csv(file_path)
    
    # Konversi kolom tanggal (sesuaikan nama kolom jika berbeda di datasetmu)
    datetime_columns = ["order_purchase_timestamp", "order_delivered_customer_date"]
    for col in datetime_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col])
            
    return df

df_raw = load_data()

if df_raw is not None:
    # --- 3. SIDEBAR FILTER ---
    with st.sidebar:
        st.title("🛍️ Menu Navigasi")
        st.info("Gunakan filter di bawah untuk mengubah tampilan data.")
        
        # Filter Rentang Waktu
        min_date = df_raw["order_purchase_timestamp"].min()
        max_date = df_raw["order_purchase_timestamp"].max()
        
        try:
            start_date, end_date = st.date_input(
                label='Rentang Waktu Analisis',
                min_value=min_date,
                max_value=max_date,
                value=[min_date, max_date]
            )
        except:
            start_date, end_date = min_date, max_date

    # Filter Data Utama
    main_df = df_raw[(df_raw["order_purchase_timestamp"] >= pd.to_datetime(start_date)) & 
                     (df_raw["order_purchase_timestamp"] <= pd.to_datetime(end_date))]

    # --- 4. HEADER & METRICS ---
    st.title("Dashboard Insight Penjualan Egi")
    st.markdown("---")

    # Barisan Angka Utama (Metrics)
    col1, col2, col3 = st.columns(3)
    with col1:
        total_orders = main_df["order_id"].nunique()
        st.metric("Total Pesanan", value=f"{total_orders:,}")
    with col2:
        total_rev = main_df["price"].sum()
        st.metric("Total Pendapatan", value=f"IDR {total_rev:,.0f}")
    with col3:
        # Menggunakan .shape[0] lebih aman daripada memanggil nama kolom item_id
        total_items = main_df.shape[0] 
        st.metric("Item Terjual", value=f"{total_items:,}")

    # --- 5. VISUALISASI UTAMA (2 SOAL INTI) ---
    st.write("### 🔍 Analisis Mendalam")
    
    tab1, tab2 = st.tabs(["🏆 Produk Terlaris", "📈 Tren Bulanan"])

    with tab1:
        st.subheader("Top 10 Kategori Produk Berdasarkan Order")
        
        # Agregasi data
        top_cat = main_df.groupby("product_category_name_english")["order_id"].nunique().sort_values(ascending=False).head(10).reset_index()
        
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(
            x="order_id", 
            y="product_category_name_english", 
            data=top_cat, 
            palette="rocket", # Warna Rocket biar gahar
            ax=ax
        )
        ax.set_title("Kategori Paling Diminati Pelanggan", fontsize=15)
        ax.set_xlabel("Jumlah Unik Order")
        ax.set_ylabel(None)
        st.pyplot(fig)
        
        st.success("💡 **Insight:** Fokus pada kategori teratas untuk kampanye promosi bulan depan.")

    with tab2:
        st.subheader("Performa Penjualan dari Waktu ke Waktu")
        
        # Resample data bulanan
        monthly_orders = main_df.resample(rule='M', on='order_purchase_timestamp').agg({
            "order_id": "nunique"
        }).reset_index()
        
        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(
            monthly_orders["order_purchase_timestamp"], 
            monthly_orders["order_id"], 
            marker='s', # Kotak
            linewidth=2, 
            color="#2E86C1"
        )
        ax.fill_between(monthly_orders["order_purchase_timestamp"], monthly_orders["order_id"], alpha=0.1, color="#2E86C1")
        ax.set_title("Tren Pesanan Bulanan", fontsize=15)
        plt.grid(True, linestyle='--', alpha=0.6)
        st.pyplot(fig)

    # --- 6. FOOTER ---
    st.markdown("---")
    st.caption("Egi Farhan - Submission Analisis Data Dicoding 2026")

else:
    st.warning("Menunggu data dimuat...")
