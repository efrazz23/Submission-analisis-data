import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency
import os

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="E-Commerce Public Dashboard", layout="wide")
sns.set(style='dark')

# --- 2. HELPER FUNCTIONS ---

def create_daily_orders_df(df):
    daily_orders_df = df.resample(rule='D', on='order_purchase_timestamp').agg({
        "order_id": "nunique",
        "price": "sum"
    }).reset_index()
    daily_orders_df.rename(columns={"order_id": "order_count", "price": "revenue"}, inplace=True)
    return daily_orders_df

def create_bystate_df(df):
    # Proteksi jika kolom customer_state tidak ada
    col = 'customer_state' if 'customer_state' in df.columns else 'state'
    if col not in df.columns: return pd.DataFrame()
    bystate_df = df.groupby(by=col).customer_id.nunique().reset_index()
    bystate_df.rename(columns={"customer_id": "customer_count"}, inplace=True)
    return bystate_df.sort_values(by="customer_count", ascending=False)

def create_rfm_df(df):
    # PERBAIKAN KEYERROR: Mencari kolom ID yang tersedia
    if 'customer_unique_id' in df.columns:
        cust_id_col = 'customer_unique_id'
    elif 'customer_id' in df.columns:
        cust_id_col = 'customer_id'
    else:
        return pd.DataFrame() # Kembalikan DF kosong jika tidak ada kolom ID

    rfm_df = df.groupby(by=cust_id_col, as_index=False).agg({
        "order_purchase_timestamp": "max",
        "order_id": "nunique",
        "price": "sum"
    })
    rfm_df.columns = ["customer_id", "max_order_timestamp", "frequency", "monetary"]
    rfm_df["max_order_timestamp"] = rfm_df["max_order_timestamp"].dt.date
    recent_date = df["order_purchase_timestamp"].dt.date.max()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days)
    return rfm_df

# --- 3. LOAD DATA ---
current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, "all_data.csv")

@st.cache_data
def load_data():
    if not os.path.exists(file_path):
        st.error(f"File {file_path} tidak ditemukan!")
        return pd.DataFrame()
    
    df = pd.read_csv(file_path)
    # Pastikan kolom waktu diconvert ke datetime
    if 'order_purchase_timestamp' in df.columns:
        df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'])
    return df

all_df = load_data()

# Cek jika data kosong
if all_df.empty:
    st.stop()

# --- 4. SIDEBAR FILTER ---
min_date = all_df["order_purchase_timestamp"].min().date()
max_date = all_df["order_purchase_timestamp"].max().date()

with st.sidebar:
    st.image("https://github.com/dicodingacademy/assets/raw/main/logo.png")
    st.header("Filter Rentang Waktu")
    
    # Perbaikan logika filter tanggal agar tidak error saat pemilihan
    try:
        date_range = st.date_input(
            label='Pilih Periode',
            min_value=min_date,
            max_value=max_date,
            value=[min_date, max_date]
        )
        start_date, end_date = date_range
    except:
        start_date, end_date = min_date, max_date

# Filter data utama (Filtering Responsif)
main_df = all_df[(all_df["order_purchase_timestamp"].dt.date >= start_date) & 
                 (all_df["order_purchase_timestamp"].dt.date <= end_date)]

# --- 5. DATA PREPARATION ---
daily_orders_df = create_daily_orders_df(main_df)
bystate_df = create_bystate_df(main_df)
rfm_df = create_rfm_df(main_df)

# --- 6. DASHBOARD UI ---
st.header('E-Commerce Public Dashboard :sparkles:')

# Visualisasi Daily Orders
st.subheader('Daily Orders')
col1, col2 = st.columns(2)
with col1:
    st.metric("Total orders", value=daily_orders_df.order_count.sum())
with col2:
    total_rev = format_currency(daily_orders_df.revenue.sum(), "BRL", locale='pt_BR')
    st.metric("Total Revenue", value=total_rev)

fig, ax = plt.subplots(figsize=(16, 8))
sns.barplot(x=daily_orders_df["order_purchase_timestamp"].dt.date, y=daily_orders_df["order_count"], color="#90CAF9", ax=ax)
plt.xticks(rotation=45)
st.pyplot(fig)

# Analisis RFM dengan Batang Warna Seragam (Highlighter)
if not rfm_df.empty:
    st.subheader("Best Customer Based on RFM Parameters")
    colors = ["#90CAF9", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]
    
    fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(35, 15))
    
    # Recency
    sns.barplot(y="recency", x="customer_id", data=rfm_df.sort_values(by="recency", ascending=True).head(5), palette=colors, ax=ax[0])
    ax[0].set_title("By Recency (days)", fontsize=50)
    ax[0].set_xticklabels(rfm_df.sort_values(by="recency", ascending=True).head(5).customer_id.str[:5], rotation=45, fontsize=30)
    
    # Frequency
    sns.barplot(y="frequency", x="customer_id", data=rfm_df.sort_values(by="frequency", ascending=False).head(5), palette=colors, ax=ax[1])
    ax[1].set_title("By Frequency", fontsize=50)
    ax[1].set_xticklabels(rfm_df.sort_values(by="frequency", ascending=False).head(5).customer_id.str[:5], rotation=45, fontsize=30)
    
    # Monetary
    sns.barplot(y="monetary", x="customer_id", data=rfm_df.sort_values(by="monetary", ascending=False).head(5), palette=colors, ax=ax[2])
    ax[2].set_title("By Monetary", fontsize=50)
    ax[2].set_xticklabels(rfm_df.sort_values(by="monetary", ascending=False).head(5).customer_id.str[:5], rotation=45, fontsize=30)
    
    st.pyplot(fig)

st.caption('Copyright (c) 2026 | Analisis Data Egi Farhan')
