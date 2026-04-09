import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import os

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="E-Commerce Analytics | Egi Farhan", layout="wide")

# Setup folder dan file
current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, "all_data.csv")

@st.cache_data
def load_data():
    if not os.path.exists(file_path):
        return None
    try:
        df = pd.read_csv(file_path)
        if 'order_purchase_timestamp' in df.columns:
            df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'], errors='coerce')
        return df.dropna(subset=['order_purchase_timestamp'])
    except:
        return None

all_df = load_data()

# --- 2. LOGIKA SIDEBAR & FILTERING ---
if all_df is not None:
    with st.sidebar:
        # Menampilkan Logo Resmi (Fix agar tidak pecah/ilang)
        st.image("https://raw.githubusercontent.com/dicodingacademy/dicoding_datasets/main/logo_dicoding_collection.png", width=150)
        st.title("🛒 E-Commerce Dashboard")
        st.subheader("Data Analysis Project")
        
        min_date, max_date = all_df["order_purchase_timestamp"].min(), all_df["order_purchase_timestamp"].max()
        
        st.write("**Filter Rentang Waktu**")
        # Mengambil input rentang waktu
        date_range = st.date_input(
            "Pilih Tanggal", 
            [min_date, max_date], 
            min_value=min_date, 
            max_value=max_date
        )
        
        # Validasi date_range agar main_df tidak error
        if isinstance(date_range, list) and len(date_range) == 2:
            start_date, end_date = date_range
        else:
            start_date, end_date = min_date, max_date
            
        # PROSES FILTERING DATA
        main_df = all_df[(all_df["order_purchase_timestamp"].dt.date >= start_date) & 
                         (all_df["order_purchase_timestamp"].dt.date <= end_date)]

    # --- 3. HEADER & METRICS ---
    st.title("📊 Dashboard Analisis E-Commerce")
    st.markdown(f"Menampilkan performa dari periode: **{start_date}** hingga **{end_date}**")

    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.metric("Total Order", f"{main_df.order_id.nunique():,}")
    with col_m2:
        st.metric("Total Revenue", f"BRL {main_df.price.sum():,.2f}")
    with col_m3:
        # Menghitung rata-rata pengiriman jika kolom tersedia
        avg_del = main_df['delivery_time'].mean() if 'delivery_time' in main_df.columns else 0
        st.metric("Avg Delivery", f"{avg_del:.1f} Days")

    st.markdown("---")

    # --- 4. PERTANYAAN 1: REVENUE PER STATE & CATEGORY ---
    st.header("1. Profitabilitas Produk Berdasarkan Wilayah")
    cat_col = 'product_category_name_english' if 'product_category_name_english' in main_df.columns else 'product_category_name'
    
    # Pengelompokan data
    top_5_states = main_df.groupby('customer_state')['price'].sum().sort_values(ascending=False).head(5).index
    top_states_df = main_df[main_df['customer_state'].isin(top_5_states)]
    
    top_product_state = top_states_df.groupby(['customer_state', cat_col])['price'].sum().reset_index()
    top_product_state = top_product_state.sort_values(['customer_state', 'price'], ascending=[True, False]).groupby('customer_state').head(1)
    top_product_state['label'] = top_product_state['customer_state'] + " (" + top_product_state[cat_col] + ")"
    top_product_state = top_product_state.sort_values(by='price', ascending=False)

    col_chart1, col_insight1 = st.columns([2, 1])
    with col_chart1:
        fig, ax = plt.subplots(figsize=(10, 6))
        # Highlight Biru untuk yang tertinggi, sisanya Abu-abu
        colors_1 = ["#0077b6" if i == 0 else "#D3D3D3" for i in range(len(top_product_state))]
        sns.barplot(x='price', y='label', data=top_product_state, palette=colors_1, ax=ax)
        ax.set_title("Kategori dengan Revenue Tertinggi di 5 State Terbesar", fontsize=15)
        ax.set_xlabel("Total Revenue (BRL)")
        ax.set_ylabel(None)
        st.pyplot(fig)
    
    with col_insight1:
        st.write("### 📌 Insight Wilayah")
        st.info(f"Negara bagian **{top_product_state.customer_state.iloc[0]}** menyumbang pendapatan tertinggi melalui kategori **{top_product_state[cat_col].iloc[0]}**.")
        st.markdown("""
        * **Strategi Warna:** Visualisasi ini mempermudah identifikasi wilayah prioritas secara instan.
        * **Saran:** Fokuskan kampanye pemasaran pada kategori populer di wilayah top 5.
        """)

    # --- 5. PERTANYAAN 2: AOV ANALYSIS ---
    st.header("2. Average Order Value (AOV) 'Bed Bath Table'")
    cama_df = main_df[main_df[cat_col] == 'bed_bath_table']
    
    if not cama_df.empty:
        aov_data = cama_df.groupby('customer_state').agg({'price': 'sum', 'order_id': 'nunique'})
        aov_data['AOV'] = aov_data['price'] / aov_data['order_id']
        aov_data = aov_data.sort_values('AOV', ascending=False).head(10).reset_index()

        col_chart2, col_insight2 = st.columns([2, 1])
        with col_chart2:
            fig2, ax2 = plt.subplots(figsize=(10, 6))
            colors_2 = ["#0077b6" if i == 0 else "#D3D3D3" for i in range(len(aov_data))]
            sns.barplot(x='AOV', y='customer_state', data=aov_data, palette=colors_2, ax=ax2)
            ax2.set_title("Top 10 State by AOV (Bed Bath Table)", fontsize=15)
            ax2.set_xlabel("Rata-rata Nilai Pesanan (BRL)")
            st.pyplot(fig2)
        
        with col_insight2:
            st.write("### 📈 AOV Discovery")
            st.success(f"**{aov_data.customer_state.iloc[0]}** memiliki nilai transaksi rata-rata tertinggi sebesar **BRL {aov_data.AOV.iloc[0]:.2f}**.")

    # --- 6. RFM ANALYSIS ---
    st.markdown("---")
    st.header("🎯 Analisis Lanjutan: RFM Analysis")
    
    rfm_df = main_df.groupby(by="customer_id", as_index=False).agg({
        "order_purchase_timestamp": "max",
        "order_id": "nunique",
        "price": "sum"
    })
    rfm_df.columns = ["customer_id", "max_order_timestamp", "frequency", "monetary"]
    recent_date = main_df["order_purchase_timestamp"].max()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days)

    col_r, col_f, col_m = st.columns(3)
    def short_id(df): return df['customer_id'].str[:5] + ".."

    with col_r:
        st.write("**Best Recency (Days)**")
        top_r = rfm_df.sort_values(by="recency", ascending=True).head(5)
        fig, ax = plt.subplots()
        sns.barplot(y="recency", x=short_id(top_r), data=top_r, color="#0077b6", ax=ax)
        plt.xticks(rotation=45)
        st.pyplot(fig)

    with col_f:
        st.write("**Best Frequency**")
        top_f = rfm_df.sort_values(by="frequency", ascending=False).head(5)
        fig, ax = plt.subplots()
        sns.barplot(y="frequency", x=short_id(top_f), data=top_f, color="#0077b6", ax=ax)
        plt.xticks(rotation=45)
        st.pyplot(fig)

    with col_m:
        st.write("**Best Monetary**")
        top_m = rfm_df.sort_values(by="monetary", ascending=False).head(5)
        fig, ax = plt.subplots()
        sns.barplot(y="monetary", x=short_id(top_m), data=top_m, color="#0077b6", ax=ax)
        plt.xticks(rotation=45)
        st.pyplot(fig)

    st.caption("Copyright © 2026 | Analisis Data Egi Farhan")
else:
    st.error("File all_data.csv tidak ditemukan. Pastikan file berada di folder yang sama dengan dashboard.py.")
