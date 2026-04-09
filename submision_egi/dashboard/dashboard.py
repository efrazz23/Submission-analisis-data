import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import os

# --- 1. KONFIGURASI ---
st.set_page_config(page_title="E-Commerce Analytics | Egi Farhan", layout="wide")
sns.set(style='dark')

current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, "all_data.csv")

@st.cache_data
def load_data():
    if not os.path.exists(file_path):
        return None
    df = pd.read_csv(file_path)
    if 'order_purchase_timestamp' in df.columns:
        df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'])
    return df

all_df = load_data()

# --- 2. LOGIKA UTAMA ---
if all_df is not None:
    # Siapkan batas tanggal
    min_date = all_df["order_purchase_timestamp"].min().date()
    max_date = all_df["order_purchase_timestamp"].max().date()

    with st.sidebar:
        st.image("https://raw.githubusercontent.com/dicodingacademy/dicoding_datasets/main/logo_dicoding_collection.png", width=150)
        st.header("Filter Dashboard")
        
        # User memilih rentang waktu
        date_range = st.date_input(
            label='Rentang Waktu',
            min_value=min_date,
            max_value=max_date,
            value=[min_date, max_date]
        )

    # --- 3. PROSES FILTER (Kunci agar diagram berubah) ---
    # Kita hanya jalankan kode di bawah jika user sudah pilih 2 tanggal (start & end)
    if isinstance(date_range, list) and len(date_range) == 2:
        start_date, end_date = date_range
        
        # Filter data
        main_df = all_df[(all_df["order_purchase_timestamp"].dt.date >= start_date) & 
                         (all_df["order_purchase_timestamp"].dt.date <= end_date)]

        # --- 4. TAMPILAN DASHBOARD ---
        st.title('📊 Dashboard Analisis E-Commerce')
        st.subheader(f"Periode: {start_date} s/d {end_date}")

        # Metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Order", f"{main_df.order_id.nunique():,}")
        col2.metric("Total Revenue", f"BRL {main_df.price.sum():,.2f}")
        col3.metric("Total Customer", f"{main_df.customer_id.nunique():,}")

        st.divider()

        # Diagram 1
        st.subheader("Top Revenue per State")
        state_rev = main_df.groupby("customer_state").price.sum().sort_values(ascending=False).reset_index().head(5)
        
        if not state_rev.empty:
            fig, ax = plt.subplots(figsize=(10, 5))
            colors = ["#0077b6" if i == 0 else "#D3D3D3" for i in range(len(state_rev))]
            sns.barplot(x="price", y="customer_state", data=state_rev, palette=colors, ax=ax)
            st.pyplot(fig)
        else:
            st.warning("Data tidak tersedia untuk rentang waktu ini.")

        # Diagram RFM (Singkat)
        st.subheader("Best Customer (Monetary)")
        top_cust = main_df.groupby("customer_id").price.sum().sort_values(ascending=False).reset_index().head(5)
        top_cust['short_id'] = top_cust['customer_id'].str[:5] + ".."
        
        fig2, ax2 = plt.subplots(figsize=(10, 5))
        sns.barplot(x="price", y="short_id", data=top_cust, color="#0077b6", ax=ax2)
        st.pyplot(fig2)

    else:
        # Tampilan jika user baru pilih satu tanggal (saat mengklik kalender)
        st.info("Silakan pilih rentang tanggal (Tanggal Mulai dan Tanggal Selesai) pada sidebar.")

    st.caption('Copyright © 2026 | Egi Farhan')

else:
    st.error("File all_data.csv tidak ditemukan di folder yang sama.")
