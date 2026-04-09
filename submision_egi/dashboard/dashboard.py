import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import os

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="E-Commerce Analytics | Egi Farhan", layout="wide")

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

# --- 2. LOGIKA FILTERING ---
if all_df is not None:
    with st.sidebar:
        st.title("🛒 E-Commerce Dashboard")
        # Menggunakan Header Teks jika logo gambar bermasalah agar tetap rapi
        st.subheader("Data Analysis Project")
        
        min_date, max_date = all_df["order_purchase_timestamp"].min(), all_df["order_purchase_timestamp"].max()
        st.write("**Filter Rentang Waktu**")
        date_range = st.date_input("Pilih Tanggal", [min_date, max_date], min_value=min_date, max_value=max_date)
        
        if isinstance(date_range, list) and len(date_range) == 2:
            start_date, end_date = date_range
        else:
            start_date, end_date = min_date, max_date
            
        main_df = all_df[(all_df["order_purchase_timestamp"] >= pd.to_datetime(start_date)) & 
                         (all_df["order_purchase_timestamp"] <= pd.to_datetime(end_date))]

    # --- 3. HEADER & METRICS ---
    st.title("📊 Dashboard Analisis E-Commerce")
    st.markdown(f"Menampilkan performa dari **{start_date}** hingga **{end_date}**")

    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Total Order", f"{main_df.order_id.nunique():,}")
    col_m2.metric("Total Revenue", f"BRL {main_df.price.sum():,.2f}")
    col_m3.metric("Avg Delivery", f"{main_df.delivery_time.mean() if 'delivery_time' in main_df.columns else 0:.1f} Days")

    st.markdown("---")

    # --- 4. PERTANYAAN 1: REVENUE PER STATE & CATEGORY ---
    st.header("1. Profitabilitas Produk Berdasarkan Wilayah")
    cat_col = 'product_category_name_english' if 'product_category_name_english' in main_df.columns else 'product_category_name'
    
    top_5_states = main_df.groupby('customer_state')['price'].sum().sort_values(ascending=False).head(5).index
    top_states_df = main_df[main_df['customer_state'].isin(top_5_states)]
    
    top_product_state = top_states_df.groupby(['customer_state', cat_col])['price'].sum().reset_index()
    top_product_state = top_product_state.sort_values(['customer_state', 'price'], ascending=[True, False]).groupby('customer_state').head(1)
    top_product_state['label'] = top_product_state['customer_state'] + " (" + top_product_state[cat_col] + ")"
    top_product_state = top_product_state.sort_values(by='price', ascending=False)

    col_chart1, col_insight1 = st.columns([2, 1])
    with col_chart1:
        fig, ax = plt.subplots(figsize=(10, 6))
        # PRINSIP INTEGRITAS: Warna seragam (Abu-abu), Highlight Biru untuk yang tertinggi
        colors_1 = ["#0077b6" if i == 0 else "#D3D3D3" for i in range(len(top_product_state))]
        sns.barplot(x='price', y='label', data=top_product_state, palette=colors_1, ax=ax)
        ax.set_title("Kategori dengan Revenue Tertinggi di 5 State Terbesar", fontsize=15)
        st.pyplot(fig)
    
    with col_insight1:
        st.write("### 📌 Insight Wilayah")
        st.markdown("""
        * **Dominasi SP:** Negara bagian **SP** memimpin pendapatan dengan kategori **Bed Bath Table**.
        * **Strategi Warna:** Batang biru menunjukkan kategori paling menguntungkan secara nasional.
        * **Saran:** Optimalkan logistik di wilayah SP untuk kategori rumah tangga.
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
            st.pyplot(fig2)
        
        with col_insight2:
            st.write("### 📈 AOV Discovery")
            st.success(f"**{aov_data.customer_state.iloc[0]}** memiliki daya beli tertinggi per transaksi.")

    # --- 6. RFM ANALYSIS (MUNCUL KEMBALI) ---
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
        st.pyplot(fig)

    with col_f:
        st.write("**Best Frequency**")
        top_f = rfm_df.sort_values(by="frequency", ascending=False).head(5)
        fig, ax = plt.subplots()
        sns.barplot(y="frequency", x=short_id(top_f), data=top_f, color="#0077b6", ax=ax)
        st.pyplot(fig)

    with col_m:
        st.write("**Best Monetary**")
        top_m = rfm_df.sort_values(by="monetary", ascending=False).head(5)
        fig, ax = plt.subplots()
        sns.barplot(y="monetary", x=short_id(top_m), data=top_m, color="#0077b6", ax=ax)
        st.pyplot(fig)

    st.caption("Copyright © 2026 | Analisis Data Egi Farhan")
else:
    st.error("Gagal memuat file all_data.csv.")
