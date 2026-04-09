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

# --- 2. LOGIKA FILTERING (SOLUSI NAMEERROR & DIAGRAM PASIF) ---
if all_df is not None:
    # Set nilai default di awal agar tidak NameError
    min_date = all_df["order_purchase_timestamp"].min().date()
    max_date = all_df["order_purchase_timestamp"].max().date()
    start_date, end_date = min_date, max_date # Default value

    with st.sidebar:
        st.image("https://raw.githubusercontent.com/dicodingacademy/dicoding_datasets/main/logo_dicoding_collection.png", width=150)
        st.title("🛒 E-Commerce Dashboard")
        
        # Input dari user
        date_range = st.date_input(
            label="Pilih Rentang Waktu",
            min_value=min_date,
            max_value=max_date,
            value=[min_date, max_date]
        )
        
        # Pastikan start_date & end_date terisi dari input sidebar
        if isinstance(date_range, list) and len(date_range) == 2:
            start_date, end_date = date_range

    # FILTER UTAMA: Gunakan .dt.date agar sinkron dengan input streamlit
    main_df = all_df[(all_df["order_purchase_timestamp"].dt.date >= start_date) & 
                     (all_df["order_purchase_timestamp"].dt.date <= end_date)]

    # --- 3. HEADER & METRICS ---
    st.title("📊 Dashboard Analisis E-Commerce")
    # Sekarang baris ini tidak akan NameError lagi
    st.markdown(f"Menampilkan performa dari: **{start_date}** hingga **{end_date}**")

    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.metric("Total Order", f"{main_df.order_id.nunique():,}")
    with col_m2:
        st.metric("Total Revenue", f"BRL {main_df.price.sum():,.2f}")
    with col_m3:
        avg_del = main_df['delivery_time'].mean() if 'delivery_time' in main_df.columns else 0
        st.metric("Avg Delivery", f"{avg_del:.1f} Days")

    st.markdown("---")

    # --- 4. DIAGRAM 1: REVENUE PER STATE ---
    st.header("1. Profitabilitas Produk Berdasarkan Wilayah")
    cat_col = 'product_category_name_english' if 'product_category_name_english' in main_df.columns else 'product_category_name'
    
    if not main_df.empty:
        top_5_states = main_df.groupby('customer_state')['price'].sum().sort_values(ascending=False).head(5).index
        top_states_df = main_df[main_df['customer_state'].isin(top_5_states)]
        
        top_product_state = top_states_df.groupby(['customer_state', cat_col])['price'].sum().reset_index()
        top_product_state = top_product_state.sort_values(['customer_state', 'price'], ascending=[True, False]).groupby('customer_state').head(1)
        top_product_state['label'] = top_product_state['customer_state'] + " (" + top_product_state[cat_col] + ")"
        top_product_state = top_product_state.sort_values(by='price', ascending=False)

        fig, ax = plt.subplots(figsize=(10, 6))
        colors_1 = ["#0077b6" if i == 0 else "#D3D3D3" for i in range(len(top_product_state))]
        sns.barplot(x='price', y='label', data=top_product_state, palette=colors_1, ax=ax)
        st.pyplot(fig)
    else:
        st.warning("Tidak ada data untuk rentang waktu ini.")

    # --- 5. DIAGRAM 2: RFM ANALYSIS ---
    st.header("🎯 Analisis Lanjutan: RFM Analysis")
    if not main_df.empty:
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
