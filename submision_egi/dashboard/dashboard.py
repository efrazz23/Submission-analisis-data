import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import os

# --- SETUP ---
st.set_page_config(page_title="E-Commerce Performance Dashboard", layout="wide")

current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, "all_data.csv")

@st.cache_data
def load_data():
    if not os.path.exists(file_path): return None
    df = pd.read_csv(file_path)
    # Pastikan format tanggal benar
    if 'order_purchase_timestamp' in df.columns:
        df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'], errors='coerce')
    return df.dropna(subset=['order_purchase_timestamp'])

all_df = load_data()

if all_df is not None:
    # --- SIDEBAR ---
    with st.sidebar:
        st.title("📊 Filter Analisis")
        min_date, max_date = all_df["order_purchase_timestamp"].min(), all_df["order_purchase_timestamp"].max()
        start_date, end_date = st.date_input("Periode Waktu", [min_date, max_date], min_value=min_date, max_value=max_date)
        
        main_df = all_df[(all_df["order_purchase_timestamp"] >= pd.to_datetime(start_date)) & 
                         (all_df["order_purchase_timestamp"] <= pd.to_datetime(end_date))]

    st.title("E-Commerce Business Insights")
    st.markdown("---")

    # --- SOAL 1: PROFITABILITAS WILAYAH & PRODUK ---
    st.header("1. Kategori Produk Berpendapatan Tertinggi per Wilayah")
    
    # Logic: Top 5 States -> Top Category in each
    top_5_states = main_df.groupby('customer_state').order_id.nunique().sort_values(ascending=False).head(5).index
    top_states_df = main_df[main_df['customer_state'].isin(top_5_states)]
    cat_col = 'product_category_name_english' if 'product_category_name_english' in main_df.columns else 'product_category_name'
    
    rev_state_cat = top_states_df.groupby(['customer_state', cat_col])['price'].sum().reset_index()
    top_res_s1 = rev_state_cat.sort_values(['customer_state', 'price'], ascending=[True, False]).groupby('customer_state').head(1)

    fig1, ax1 = plt.subplots(figsize=(10, 5))
    sns.barplot(x='price', y='customer_state', data=top_res_s1, palette='viridis', ax=ax1)
    for i, p in enumerate(ax1.patches):
        ax1.annotate(f" {top_res_s1[cat_col].iloc[i]}", (p.get_width(), p.get_y() + p.get_height()/2), va='center', fontweight='bold')
    st.pyplot(fig1)

    st.markdown("---")

    # --- SOAL 2: AOV PADA PRODUK UNGGULAN ---
    st.header("2. Analisis AOV pada Produk Unggulan")
    
    # Cari kategori terlaris (Cama Mesa Banho biasanya)
    unggulan_name = main_df.groupby(cat_col).order_id.nunique().idxmax()
    unggulan_df = main_df[main_df[cat_col] == unggulan_name]
    
    # Hitung AOV
    aov_geo = unggulan_df.groupby('customer_state').agg({'price': 'sum', 'order_id': 'nunique'})
    aov_geo['AOV'] = aov_geo['price'] / aov_geo['order_id']
    aov_geo = aov_geo.sort_values('AOV', ascending=False).head(10).reset_index()

    fig2, ax2 = plt.subplots(figsize=(10, 5))
    sns.barplot(x='AOV', y='customer_state', data=aov_geo, palette='flare', ax=ax2)
    avg_line = aov_geo['AOV'].mean()
    ax2.axvline(avg_line, color='red', linestyle='--', label=f'Rata-rata {unggulan_name}')
    ax2.set_title(f"Average Order Value Wilayah - Kategori: {unggulan_name}")
    st.pyplot(fig2)

    st.markdown("---")
    st.caption("Submission Analisis Data - Egi Farhan 2026")
