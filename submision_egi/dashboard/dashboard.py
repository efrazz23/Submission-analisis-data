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
        # PERBAIKAN LOGO: Menggunakan URL langsung agar pasti terbaca oleh Streamlit Cloud
        st.image("https://raw.githubusercontent.com/dicodingacademy/dicoding_datasets/main/logo_dicoding.png", width=150)
        
        min_date, max_date = all_df["order_purchase_timestamp"].min(), all_df["order_purchase_timestamp"].max()
        st.subheader("Filter Rentang Waktu")
        # Pastikan filter ini langsung mengubah data
        date_range = st.date_input("Pilih Tanggal", [min_date, max_date], min_value=min_date, max_value=max_date)
        
        if len(date_range) == 2:
            start_date, end_date = date_range
        else:
            start_date, end_date = min_date, max_date
            
        main_df = all_df[(all_df["order_purchase_timestamp"] >= pd.to_datetime(start_date)) & 
                         (all_df["order_purchase_timestamp"] <= pd.to_datetime(end_date))]

    # --- 3. HEADER ---
    st.title("📊 Dashboard Analisis E-Commerce")
    st.markdown(f"Periode: **{start_date}** sampai **{end_date}**")

    # --- 4. VISUALISASI 1: REVENUE PER STATE ---
    st.header("1. Profitabilitas Produk Berdasarkan Wilayah")
    
    cat_col = 'product_category_name_english' if 'product_category_name_english' in main_df.columns else 'product_category_name'
    top_5_states = main_df.groupby('customer_state')['price'].sum().sort_values(ascending=False).head(5).index
    top_states_df = main_df[main_df['customer_state'].isin(top_5_states)]
    
    top_product_state = top_states_df.groupby(['customer_state', cat_col])['price'].sum().reset_index()
    top_product_state = top_product_state.sort_values(['customer_state', 'price'], ascending=[True, False]).groupby('customer_state').head(1)
    top_product_state['label'] = top_product_state['customer_state'] + " (" + top_product_state[cat_col] + ")"
    top_product_state = top_product_state.sort_values(by='price', ascending=False)

    fig, ax = plt.subplots(figsize=(10, 6))
    
    # PERBAIKAN VISUALISASI: Warna seragam, hanya highlight yang tertinggi (Prinsip Integritas)
    # Biru Tua untuk tertinggi, Abu-abu untuk sisanya
    colors = ["#0077b6" if i == 0 else "#D3D3D3" for i in range(len(top_product_state))]
    
    sns.barplot(x='price', y='label', data=top_product_state, palette=colors, ax=ax)
    ax.set_title("Top Revenue per State & Category", fontsize=15)
    ax.set_xlabel("Total Revenue (BRL)")
    ax.set_ylabel(None)
    st.pyplot(fig)

    # --- 5. VISUALISASI 2: AOV ANALYSIS ---
    st.header("2. Average Order Value (AOV) 'Bed Bath Table'")
    cama_df = main_df[main_df[cat_col] == 'bed_bath_table']
    
    if not cama_df.empty:
        aov_data = cama_df.groupby('customer_state').agg({'price': 'sum', 'order_id': 'nunique'})
        aov_data['AOV'] = aov_data['price'] / aov_data['order_id']
        aov_data = aov_data.sort_values('AOV', ascending=False).head(10).reset_index()

        fig2, ax2 = plt.subplots(figsize=(10, 6))
        # Highlight AOV tertinggi
        colors_aov = ["#0077b6" if i == 0 else "#D3D3D3" for i in range(len(aov_data))]
        
        sns.barplot(x='AOV', y='customer_state', data=aov_data, palette=colors_aov, ax=ax2)
        ax2.set_title("Top 10 State by AOV (Kategori Terlaris)", fontsize=15)
        st.pyplot(fig2)

    st.caption("Copyright © 2026 | Analisis Data Egi Farhan")
else:
    st.error
