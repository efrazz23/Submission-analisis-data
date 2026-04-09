import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import os

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="E-Commerce Analytics | Egi Farhan", layout="wide")

# Penanganan Path File all_data.csv
current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, "all_data.csv")

@st.cache_data
def load_data():
    if not os.path.exists(file_path):
        return None
    try:
        if os.path.getsize(file_path) == 0:
            return None
        df = pd.read_csv(file_path)
        if 'order_purchase_timestamp' in df.columns:
            df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'], errors='coerce')
        return df.dropna(subset=['order_purchase_timestamp'])
    except:
        return None

all_df = load_data()

# --- 2. LOGIKA UTAMA DASHBOARD ---
if all_df is not None:
    with st.sidebar:
        st.title("🛒 E-Commerce Dashboard")
        st.image("https://raw.githubusercontent.com/dicodingacademy/dicoding_datasets/main/logo_dicoding.png", width=100)
        
        # Filter Rentang Waktu
        min_date = all_df["order_purchase_timestamp"].min()
        max_date = all_df["order_purchase_timestamp"].max()
        
        st.subheader("Filter Periode")
        # Handle jika date_input mengembalikan satu tanggal saat proses klik
        date_range = st.date_input(
            label='Pilih Rentang Waktu',
            min_value=min_date,
            max_value=max_date,
            value=[min_date, max_date]
        )
        
        if isinstance(date_range, list) and len(date_range) == 2:
            start_date, end_date = date_range
        else:
            start_date, end_date = min_date, max_date
            
        main_df = all_df[(all_df["order_purchase_timestamp"] >= pd.to_datetime(start_date)) & 
                         (all_df["order_purchase_timestamp"] <= pd.to_datetime(end_date))]

    # --- 3. HEADER & METRICS ---
    st.title("📊 Brazilian E-Commerce Performance Analysis")
    st.markdown(f"**Periode Analisis:** {start_date} s/d {end_date}")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Uniq Orders", value=f"{main_df.order_id.nunique():,}")
    with col2:
        st.metric("Total Revenue", value=f"BRL {main_df.price.sum():,.2f}")
    with col3:
        avg_delivery = main_df.delivery_time.mean() if 'delivery_time' in main_df.columns else 0
        st.metric("Avg Delivery Time", value=f"{avg_delivery:.1f} Days")

    st.markdown("---")

    # --- 4. PERTANYAAN 1 ---
    st.header("1. Profitabilitas Produk Berdasarkan Wilayah")
    top_5_states = main_df.groupby('customer_state')['price'].sum().sort_values(ascending=False).head(5).index
    top_states_df = main_df[main_df['customer_state'].isin(top_5_states)]
    cat_col = 'product_category_name_english' if 'product_category_name_english' in main_df.columns else 'product_category_name'
    
    top_product_state = top_states_df.groupby(['customer_state', cat_col])['price'].sum().reset_index()
    top_product_state = top_product_state.sort_values(['customer_state', 'price'], ascending=[True, False]).groupby('customer_state').head(1)
    top_product_state = top_product_state.sort_values(by='price', ascending=False)

    col_a, col_b = st.columns([2, 1])
    with col_a:
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(x='price', y='customer_state', data=top_product_state, palette='viridis', ax=ax)
        ax.set_title("Revenue Kategori Unggulan di 5 State Terbesar", fontsize=15)
        st.pyplot(fig)
    with col_b:
        st.write("### 📌 Top State Insights")
        for i, row in top_product_state.iterrows():
            st.write(f"**{row['customer_state']}**: `{row[cat_col]}`")

    # --- 5. PERTANYAAN 2 ---
    st.header("2. Analisis AOV Kategori 'Bed Bath Table'")
    cama_df = main_df[main_df[cat_col] == 'bed_bath_table']
    
    if not cama_df.empty:
        aov_data = cama_df.groupby('customer_state').agg({'price': 'sum', 'order_id': 'nunique'})
        aov_data['AOV'] = aov_data['price'] / aov_data['order_id']
        aov_data = aov_data.sort_values('AOV', ascending=False).head(10).reset_index()

        col_c, col_d = st.columns([2, 1])
        with col_c:
            fig2, ax2 = plt.subplots(figsize=(10, 6))
            colors = ["#FF595E" if i == 0 else "#FFCA3A" for i in range(len(aov_data))]
            sns.barplot(x='AOV', y='customer_state', data=aov_data, palette=colors, ax=ax2)
            ax2.set_title("Top 10 State Berdasarkan AOV (Bed Bath Table)", fontsize=15)
            st.pyplot(fig2)
        with col_d:
            st.success(f"State **{aov_data.customer_state.iloc[0]}** memiliki AOV tertinggi!")

    # --- 6. RFM ANALYSIS (VERSI BERSIH) ---
    st.markdown("---")
    st.header("🎯 Analisis Lanjutan: RFM Analysis")
    
    # Menghitung RFM
    rfm_df = main_df.groupby(by="customer_id", as_index=False).agg({
        "order_purchase_timestamp": "max",
        "order_id": "nunique",
        "price": "sum"
    })
    rfm_df.columns = ["customer_id", "max_order_timestamp", "frequency", "monetary"]
    recent_date = main_df["order_purchase_timestamp"].max()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days)

    def short_id(df):
        return df['customer_id'].str[:5] + "..."

    col_r, col_f, col_m = st.columns(3)
    with col_r:
        st.write("**Recency (Days)**")
        top_r = rfm_df.sort_values(by="recency", ascending=True).head(5).copy()
        top_r['display_id'] = short_id(top_r)
        fig, ax = plt.subplots()
        sns.barplot(y="recency", x="display_id", data=top_r, palette="Blues_r", ax=ax)
        st.pyplot(fig)
    with col_f:
        st.write("**Frequency**")
        top_f = rfm_df.sort_values(by="frequency", ascending=False).head(5).copy()
        top_f['display_id'] = short_id(top_f)
        fig, ax = plt.subplots()
        sns.barplot(y="frequency", x="display_id", data=top_f, palette="Greens_r", ax=ax)
        st.pyplot(fig)
    with col_m:
        st.write("**Monetary**")
        top_m = rfm_df.sort_values(by="monetary", ascending=False).head(5).copy()
        top_m['display_id'] = short_id(top_m)
        fig, ax = plt.subplots()
        sns.barplot(y="monetary", x="display_id", data=top_m, palette="Oranges_r", ax=ax)
        st.pyplot(fig)

    st.caption("Copyright © 2026 | Analisis Data Egi Farhan")

else:
    st.error("File 'all_data.csv' tidak ditemukan atau kosong. Pastikan file berada di folder yang sama dengan dashboard.py")
