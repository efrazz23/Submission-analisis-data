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

   # --- SOAL 1: ANALISIS PROFITABILITAS WILAYAH & PRODUK ---
    st.header("1. Profitabilitas Produk Berdasarkan Wilayah")
    st.markdown("Analisis kategori produk dengan pendapatan tertinggi di 5 negara bagian teraktif.")

    # 1. Cari Top 5 State berdasarkan jumlah transaksi (sesuai soal)
    top_5_states = main_df.groupby('customer_state').order_id.nunique().sort_values(ascending=False).head(5).index
    
    # 2. Filter data hanya untuk 5 state tersebut
    top_states_df = main_df[main_df['customer_state'].isin(top_5_states)]
    
    # 3. Cari Produk terbaik di masing-masing state tersebut
    # Gunakan 'product_category_name_english' atau 'product_category_name'
    cat_col = 'product_category_name_english' if 'product_category_name_english' in main_df.columns else 'product_category_name'
    
    product_revenue_state = top_states_df.groupby(['customer_state', cat_col])['price'].sum().reset_index()
    
    # Ambil yang tertinggi saja per state
    top_product_per_state = product_revenue_state.sort_values(['customer_state', 'price'], ascending=[True, False]).groupby('customer_state').head(1).reset_index(drop=True)

    # --- VISUALISASI SOAL 1 ---
    col_chart, col_desc = st.columns([2, 1]) # Membagi layout: 2 bagian grafik, 1 bagian penjelasan

    with col_chart:
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(
            x='price', 
            y='customer_state', 
            data=top_product_per_state, 
            palette='viridis',
            ax=ax
        )
        ax.set_title("Revenue Tertinggi per Negara Bagian (Top 5 States)", fontsize=14)
        ax.set_xlabel("Total Revenue (BRL)")
        ax.set_ylabel("State")
        
        # Tambahkan label nama produk langsung di grafik agar keren
        for i, p in enumerate(ax.patches):
            ax.annotate(f" {top_product_per_state[cat_col].iloc[i]}", 
                        (p.get_width(), p.get_y() + p.get_height()/2), 
                        va='center', fontsize=10, fontweight='bold')
        
        st.pyplot(fig)

    with col_desc:
        st.write("### 📌 Insight Wilayah")
        for index, row in top_product_per_state.iterrows():
            st.write(f"- Di **{row['customer_state']}**, kategori **{row[cat_col]}** adalah penyumbang revenue terbesar dengan total **BRL {row['price']:,.0f}**.")
        
        st.info("💡 Data ini membantu tim logistik menentukan gudang mana yang harus memperbanyak stok kategori produk tertentu.")

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
