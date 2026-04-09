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

def create_sum_order_items_df(df):
    # Mencari kolom kategori yang tersedia (english atau original)
    cat_col = 'product_category_name_english' if 'product_category_name_english' in df.columns else 'product_category_name'
    if cat_col not in df.columns:
        return pd.DataFrame(columns=['category', 'order_id', 'price'])
    
    sum_order_items_df = df.groupby(cat_col).agg({
        "order_id": "count",
        "price": "sum"
    }).reset_index()
    sum_order_items_df.rename(columns={cat_col: "category"}, inplace=True)
    return sum_order_items_df

def create_bystate_df(df):
    col = 'customer_state' if 'customer_state' in df.columns else 'state'
    bystate_df = df.groupby(by=col).customer_id.nunique().reset_index()
    bystate_df.rename(columns={"customer_id": "customer_count"}, inplace=True)
    return bystate_df.sort_values(by="customer_count", ascending=False)

def create_rfm_df(df):
    cust_col = 'customer_unique_id' if 'customer_unique_id' in df.columns else 'customer_id'
    rfm_df = df.groupby(by=cust_col, as_index=False).agg({
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
    df = pd.read_csv(file_path)
    if 'order_purchase_timestamp' in df.columns:
        df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'])
    return df

all_df = load_data()

# --- 4. SIDEBAR FILTER ---
min_date = all_df["order_purchase_timestamp"].min().date()
max_date = all_df["order_purchase_timestamp"].max().date()

with st.sidebar:
    st.image("https://github.com/dicodingacademy/assets/raw/main/logo.png")
    st.header("Filter Rentang Waktu")
    
    # Try-except untuk menangani transisi pemilihan tanggal
    try:
        date_range = st.date_input(
            label="Pilih Periode",
            min_value=min_date,
            max_value=max_date,
            value=(min_date, max_date)
        )
        start_date, end_date = date_range
    except:
        start_date, end_date = min_date, max_date

# Filter data utama
main_df = all_df[(all_df["order_purchase_timestamp"].dt.date >= start_date) & 
                 (all_df["order_purchase_timestamp"].dt.date <= end_date)]

# --- 5. MENYIAPKAN DATAFRAME ---
daily_orders_df = create_daily_orders_df(main_df)
sum_order_items_df = create_sum_order_items_df(main_df)
bystate_df = create_bystate_df(main_df)
rfm_df = create_rfm_df(main_df)

# --- 6. LAYOUT DASHBOARD ---
st.header('E-Commerce Public Dashboard :sparkles:')

# Section 1: Daily Orders
st.subheader('Daily Orders')
col1, col2 = st.columns(2)
with col1:
    st.metric("Total orders", value=daily_orders_df.order_count.sum())
with col2:
    total_rev = format_currency(daily_orders_df.revenue.sum(), "BRL", locale='pt_BR')
    st.metric("Total Revenue", value=total_rev)

fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(daily_orders_df["order_purchase_timestamp"], daily_orders_df["order_count"], marker='o', linewidth=2, color="#90CAF9")
ax.set_title("Grafik Pesanan Harian", fontsize=20)
st.pyplot(fig)
st.markdown("> **Deskripsi:** Grafik ini menunjukkan fluktuasi jumlah pesanan setiap harinya pada periode yang dipilih. Membantu melihat tren lonjakan transaksi pada tanggal tertentu.")

# Section 2: Product Performance
st.subheader("Best & Worst Performing Product")
col_p1, col_p2 = st.columns(2)

with col_p1:
    st.write("**5 Kategori Produk Terlaris (Volume)**")
    fig, ax = plt.subplots(figsize=(12, 6))
    top_v = sum_order_items_df.sort_values(by="order_id", ascending=False).head(5)
    sns.barplot(x="order_id", y="category", data=top_v, palette="Blues_d", ax=ax)
    st.pyplot(fig)

with col_p2:
    st.write("**5 Kategori Produk Terendah (Volume)**")
    fig, ax = plt.subplots(figsize=(12, 6))
    bot_v = sum_order_items_df.sort_values(by="order_id", ascending=True).head(5)
    sns.barplot(x="order_id", y="category", data=bot_v, palette="Reds_d", ax=ax)
    st.pyplot(fig)
st.markdown("> **Deskripsi:** Perbandingan antara kategori produk yang paling diminati (biru) dan yang kurang diminati (merah) berdasarkan jumlah barang yang terjual.")

# Section 3: Customer Demographics
st.subheader("Customer Demographics")
fig, ax = plt.subplots(figsize=(16, 8))
sns.barplot(x="customer_count", y="customer_state", data=bystate_df.head(10), palette="viridis", ax=ax)
ax.set_title("10 Negara Bagian dengan Pelanggan Terbanyak", fontsize=20)
st.pyplot(fig)
st.markdown("> **Deskripsi:** Visualisasi ini memetakan konsentrasi pelanggan berdasarkan wilayah (state). Membantu strategi logistik dan pemasaran di wilayah padat pembeli.")

# Section 4: RFM Analysis
st.subheader("Best Customer Based on RFM Parameters")
col_r1, col_r2, col_r3 = st.columns(3)

with col_r1:
    avg_recency = round(rfm_df.recency.mean(), 1)
    st.metric("Avg Recency (Days)", value=avg_recency)
with col_r2:
    avg_freq = round(rfm_df.frequency.mean(), 2)
    st.metric("Avg Frequency", value=avg_freq)
with col_r3:
    avg_monetary = format_currency(rfm_df.monetary.mean(), "BRL", locale='pt_BR')
    st.metric("Avg Monetary", value=avg_monetary)

# Visualisasi RFM
fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(35, 15))
colors = ["#90CAF9"] * 5

# Recency
top_rec = rfm_df.sort_values(by="recency", ascending=True).head(5)
sns.barplot(y="recency", x="customer_id", data=top_rec, palette=colors, ax=ax[0])
ax[0].set_title("By Recency (days)", fontsize=50)
ax[0].set_xticklabels(top_rec.customer_id.str[:5], rotation=45, fontsize=30)

# Frequency
top_freq = rfm_df.sort_values(by="frequency", ascending=False).head(5)
sns.barplot(y="frequency", x="customer_id", data=top_freq, palette=colors, ax=ax[1])
ax[1].set_title("By Frequency", fontsize=50)
ax[1].set_xticklabels(top_freq.customer_id.str[:5], rotation=45, fontsize=30)

# Monetary
top_mon = rfm_df.sort_values(by="monetary", ascending=False).head(5)
sns.barplot(y="monetary", x="customer_id", data=top_mon, palette=colors, ax=ax[2])
ax[2].set_title("By Monetary", fontsize=50)
ax[2].set_xticklabels(top_mon.customer_id.str[:5], rotation=45, fontsize=30)

st.pyplot(fig)
st.markdown("> **Deskripsi:** Analisis RFM mengelompokkan pelanggan berdasarkan **Recency** (kapan terakhir belanja), **Frequency** (seberapa sering belanja), dan **Monetary** (total uang yang dihabiskan).")

st.caption('Copyright (c) 2026 | Analisis Data Egi Farhan')
