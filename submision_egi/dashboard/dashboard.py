import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency
import os

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="E-Commerce Public Dashboard", layout="wide")
sns.set(style='dark')

# --- 2. HELPER FUNCTIONS (Logika Filtering Terintegrasi) ---

def create_daily_orders_df(df):
    daily_orders_df = df.resample(rule='D', on='order_purchase_timestamp').agg({
        "order_id": "nunique",
        "price": "sum"
    }).reset_index()
    daily_orders_df.rename(columns={"order_id": "order_count", "price": "revenue"}, inplace=True)
    return daily_orders_df

def create_bycity_df(df):
    bycity_df = df.groupby(by="customer_city").customer_id.nunique().reset_index()
    bycity_df.rename(columns={"customer_id": "customer_count"}, inplace=True)
    return bycity_df.sort_values(by="customer_count", ascending=False)

def create_bystate_df(df):
    bystate_df = df.groupby(by="customer_state").customer_id.nunique().reset_index()
    bystate_df.rename(columns={"customer_id": "customer_count"}, inplace=True)
    return bystate_df.sort_values(by="customer_count", ascending=False)

def create_delivery_time_df(df):
    delivery_df = df.dropna(subset=['order_purchase_timestamp', 'order_delivered_customer_date']).copy()
    delivery_df = delivery_df.drop_duplicates(subset=['order_id'])
    delivery_time = delivery_df["order_delivered_customer_date"] - delivery_df["order_purchase_timestamp"]
    delivery_df["delivery_time_days"] = delivery_time.apply(lambda x: x.total_seconds() / 86400)
    return delivery_df

def create_sum_order_items_df(df):
    cat_col = 'product_category_name_english' if 'product_category_name_english' in df.columns else 'product_category_name'
    sum_order_items_df = df.groupby(cat_col).agg({
        "order_id": "count",
        "price": "sum"
    }).reset_index()
    sum_order_items_df.rename(columns={cat_col: "category"}, inplace=True)
    return sum_order_items_df

def create_rfm_df(df):
    rfm_df = df.groupby(by="customer_unique_id", as_index=False).agg({
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
    datetime_columns = ["order_purchase_timestamp", "order_delivered_customer_date"]
    for column in datetime_columns:
        if column in df.columns:
            df[column] = pd.to_datetime(df[column])
    return df

all_df = load_data()

# --- 4. SIDEBAR FILTERING (Perbaikan Path & Filter Tanggal) ---
min_date = all_df["order_purchase_timestamp"].min().date()
max_date = all_df["order_purchase_timestamp"].max().date()

with st.sidebar:
    # Menggunakan path relatif agar logo terbaca di mana saja
    st.image("https://github.com/dicodingacademy/assets/raw/main/logo.png")
    
    st.header("Filter Rentang Waktu")
    try:
        start_date, end_date = st.date_input(
            label='Pilih Periode',
            min_value=min_date,
            max_value=max_date,
            value=[min_date, max_date]
        )
    except:
        start_date, end_date = min_date, max_date

# Aplikasi filter ke data utama
main_df = all_df[(all_df["order_purchase_timestamp"].dt.date >= start_date) & 
                 (all_df["order_purchase_timestamp"].dt.date <= end_date)]

# Siapkan data berdasarkan filter
daily_orders_df = create_daily_orders_df(main_df)
bycity_df = create_bycity_df(main_df)
bystate_df = create_bystate_df(main_df)
delivery_time_df = create_delivery_time_df(main_df)
sum_order_items_df = create_sum_order_items_df(main_df)
rfm_df = create_rfm_df(main_df)

# --- 5. VISUALISASI DASHBOARD ---
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
# Menggunakan barplot sesuai permintaan reviewer agar seragam
sns.barplot(x=daily_orders_df["order_purchase_timestamp"].dt.date, y=daily_orders_df["order_count"], color="#90CAF9", ax=ax)
ax.set_title("Grafik Pesanan Harian", fontsize=20)
plt.xticks(rotation=45)
st.pyplot(fig)

# Section 2: Pertanyaan 1 - Profit & Kategori Produk Terlaris
st.subheader("Best & Worst Performing Product")
fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(35, 15))
# Highlighter: Biru untuk tertinggi, Abu-abu untuk lainnya
colors = ["#90CAF9", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

sns.barplot(x="order_id", y="category", data=sum_order_items_df.sort_values(by="order_id", ascending=False).head(5), palette=colors, ax=ax[0])
ax[0].set_title("Best Performing Product (Volume)", loc="center", fontsize=50)
ax[0].tick_params(axis='y', labelsize=35)
ax[0].set_xlabel(None)

sns.barplot(x="order_id", y="category", data=sum_order_items_df.sort_values(by="order_id", ascending=True).head(5), palette=colors, ax=ax[1])
ax[1].set_title("Worst Performing Product (Volume)", loc="center", fontsize=50)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].tick_params(axis='y', labelsize=35)
ax[1].set_xlabel(None)
st.pyplot(fig)

# Masukkan Kesimpulan Pertanyaan 1 dari Colab
st.info("**Kesimpulan Pertanyaan 1: Analisis Profitabilitas Produk berdasarkan Wilayah**")
st.write("""Berdasarkan analisis data periode 2016-2018, pendapatan (revenue) perusahaan sangat terpusat pada wilayah dengan aktivitas ekonomi tinggi, khususnya di negara bagian SP (São Paulo) yang mendominasi total pendapatan secara signifikan sebesar 472.238,07 BRL. Kategori produk 'bed_bath_table' memberikan kontribusi profit tertinggi di wilayah tersebut. Wilayah lain seperti RJ dan MG menunjukkan keunikan dengan kategori unggulan pada 'watches_gifts' dan 'health_beauty'. Strategi pemenuhan stok harus dipersonalisasi sesuai preferensi kategori dominan di masing-masing state.""")

# Section 3: Pertanyaan 2 - Demografi & Loyalitas
st.subheader("Customer Demographics")
col1, col2 = st.columns(2)
state_colors = ["#90CAF9" if i == 0 else "#D3D3D3" for i in range(5)]

with col1:
    fig, ax = plt.subplots(figsize=(20, 10))
    sns.barplot(x="customer_count", y="customer_state", data=bystate_df.head(5), palette=state_colors, ax=ax)
    ax.set_title("Number of Customer by States", loc="center", fontsize=30)
    ax.tick_params(axis='y', labelsize=20)
    st.pyplot(fig)
with col2:
    fig, ax = plt.subplots(figsize=(20, 10))
    sns.barplot(x="customer_count", y="customer_city", data=bycity_df.head(5), palette=state_colors, ax=ax)
    ax.set_title("Number of Customer by City", loc="center", fontsize=30)
    ax.tick_params(axis='y', labelsize=20)
    st.pyplot(fig)

# Masukkan Kesimpulan Pertanyaan 2 dari Colab
st.info("**Kesimpulan Pertanyaan 2: Analisis Loyalitas & Nilai Transaksi Pelanggan**")
st.write("""Hasil analisis pada kategori 'bed_bath_table' periode 2017-2018 menunjukkan bahwa meskipun São Paulo memimpin secara volume, negara bagian RR (Roraima) memiliki Average Order Value (AOV) tertinggi mencapai 304.85 BRL. Karena mayoritas pelanggan bersifat One-Time Buyers, fokus harus dialihkan dari akuisisi ke program retensi pelanggan di wilayah dengan AOV tinggi melalui penawaran premium atau loyalty reward.""")

# Section 4: Delivery Time
st.subheader("Delivery Time Analysis")
col1, col2 = st.columns(2)
with col1:
    st.metric("Avg Delivery Time (Days)", value=round(delivery_time_df['delivery_time_days'].mean(), 1))
with col2:
    st.metric("Max Delivery Delay (Days)", value=int(delivery_time_df['delivery_time_days'].max()))

fig, ax = plt.subplots(figsize=(16, 8))
sns.histplot(x='delivery_time_days', data=delivery_time_df, bins=50, color="#90CAF9", kde=True, ax=ax)
ax.set_title("Distribution of Delivery Time", fontsize=20)
st.pyplot(fig)

# Section 5: RFM Analysis
st.subheader("Best Customer Based on RFM Parameters")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Avg Recency (days)", value=round(rfm_df.recency.mean(), 1))
with col2:
    st.metric("Avg Frequency", value=round(rfm_df.frequency.mean(), 2))
with col3:
    st.metric("Avg Monetary", value=format_currency(rfm_df.monetary.mean(), "BRL", locale='pt_BR'))

fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(35, 15))
# Visualisasi RFM dengan barplot dan highlighter
sns.barplot(y="recency", x="customer_id", data=rfm_df.sort_values(by="recency", ascending=True).head(5), palette=colors, ax=ax[0])
ax[0].set_title("By Recency (days)", loc="center", fontsize=50)
ax[0].set_xticklabels(rfm_df.sort_values(by="recency", ascending=True).head(5).customer_id.str[:5], rotation=45, fontsize=30)

sns.barplot(y="frequency", x="customer_id", data=rfm_df.sort_values(by="frequency", ascending=False).head(5), palette=colors, ax=ax[1])
ax[1].set_title("By Frequency", loc="center", fontsize=50)
ax[1].set_xticklabels(rfm_df.sort_values(by="frequency", ascending=False).head(5).customer_id.str[:5], rotation=45, fontsize=30)

sns.barplot(y="monetary", x="customer_id", data=rfm_df.sort_values(by="monetary", ascending=False).head(5), palette=colors, ax=ax[2])
ax[2].set_title("By Monetary", loc="center", fontsize=50)
ax[2].set_xticklabels(rfm_df.sort_values(by="monetary", ascending=False).head(5).customer_id.str[:5], rotation=45, fontsize=30)
st.pyplot(fig)

st.caption('Copyright (c) 2026 | Analisis Data Egi Farhan')
