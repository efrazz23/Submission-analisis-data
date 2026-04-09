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

main_df = all_df[(all_df["order_purchase_timestamp"].dt.date >= start_date) & 
                 (all_df["order_purchase_timestamp"].dt.date <= end_date)]

# --- 5. DATA PREPARATION ---
daily_orders_df = create_daily_orders_df(main_df)
sum_order_items_df = create_sum_order_items_df(main_df)
bystate_df = create_bystate_df(main_df)
rfm_df = create_rfm_df(main_df)

# --- 6. LAYOUT DASHBOARD ---
st.header('E-Commerce Public Dashboard :sparkles:')

# Section 1: Daily Orders (Bar Chart)
st.subheader('Daily Orders')
col1, col2 = st.columns(2)
with col1:
    st.metric("Total orders", value=daily_orders_df.order_count.sum())
with col2:
    total_rev = format_currency(daily_orders_df.revenue.sum(), "BRL", locale='pt_BR')
    st.metric("Total Revenue", value=total_rev)

fig, ax = plt.subplots(figsize=(16, 8))
sns.barplot(x=daily_orders_df["order_purchase_timestamp"].dt.date, y=daily_orders_df["order_count"], color="#90CAF9", ax=ax)
ax.set_title("Grafik Pesanan Harian", fontsize=20)
plt.xticks(rotation=45)
st.pyplot(fig)

# Section 2: Product Performance (Highlighter Color)
st.subheader("Best & Worst Performing Product")
col_p1, col_p2 = st.columns(2)
# Warna: Biru untuk ranking 1, Abu-abu untuk sisanya
colors_highlight = ["#90CAF9", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

with col_p1:
    st.write("**5 Kategori Produk Terlaris (Volume)**")
    fig, ax = plt.subplots(figsize=(12, 6))
    top_v = sum_order_items_df.sort_values(by="order_id", ascending=False).head(5)
    sns.barplot(x="order_id", y="category", data=top_v, palette=colors_highlight, ax=ax)
    st.pyplot(fig)

with col_p2:
    st.write("**5 Kategori Produk Terendah (Volume)**")
    fig, ax = plt.subplots(figsize=(12, 6))
    bot_v = sum_order_items_df.sort_values(by="order_id", ascending=True).head(5)
    sns.barplot(x="order_id", y="category", data=bot_v, palette=colors_highlight, ax=ax)
    st.pyplot(fig)

st.info("**Kesimpulan Pertanyaan 1: Analisis Profitabilitas Produk berdasarkan Wilayah**")
st.write("""Berdasarkan analisis data periode 2016-2018, pendapatan (revenue) perusahaan sangat terpusat pada wilayah dengan aktivitas ekonomi tinggi, khususnya di negara bagian SP (São Paulo) yang mendominasi total pendapatan secara signifikan sebesar 472.238,07 BRL. Kategori produk yang memberikan kontribusi profitabilitas tertinggi di wilayah utama tersebut adalah bed_bath_table. Namun, wilayah lain seperti RJ dan MG menunjukkan keunikan dengan kategori unggulan pada watches_gifts dan health_beauty. Hal ini mengindikasikan bahwa strategi pemenuhan stok di wilayah padat transaksi harus dipersonalisasi sesuai dengan preferensi kategori dominan di masing-masing state.""")

# Section 3: Customer Demographics
st.subheader("Customer Demographics")
fig, ax = plt.subplots(figsize=(16, 8))
# Highlight State SP sebagai yang tertinggi
colors_state = ["#90CAF9" if i == 0 else "#D3D3D3" for i in range(10)]
sns.barplot(x="customer_count", y="customer_state", data=bystate_df.head(10), palette=colors_state, ax=ax)
ax.set_title("10 Negara Bagian dengan Pelanggan Terbanyak", fontsize=20)
st.pyplot(fig)

st.info("**Kesimpulan Pertanyaan 2: Analisis Loyalitas & Nilai Transaksi Pelanggan**")
st.write("""Hasil analisis pada kategori 'bed_bath_table' periode 2017-2018 menunjukkan korelasi unik: wilayah di luar pusat ekonomi cenderung memiliki daya beli per transaksi yang lebih tinggi. Meskipun São Paulo memimpin secara volume, negara bagian RR (Roraima) memiliki Average Order Value (AOV) tertinggi mencapai 304.85 BRL, jauh di atas rata-rata wilayah perkotaan.""")

# Section 4: RFM Analysis (Bar Chart & Highlighter)
st.subheader("Best Customer Based on RFM Parameters")
col_r1, col_r2, col_r3 = st.columns(3)
with col_r1:
    st.metric("Avg Recency (Days)", value=round(rfm_df.recency.mean(), 1))
with col_r2:
    st.metric("Avg Frequency", value=round(rfm_df.frequency.mean(), 2))
with col_r3:
    st.metric("Avg Monetary", value=format_currency(rfm_df.monetary.mean(), "BRL", locale='pt_BR'))

fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(35, 15))

# Recency (Low is Better)
top_rec = rfm_df.sort_values(by="recency", ascending=True).head(5)
sns.barplot(y="recency", x="customer_id", data=top_rec, palette=colors_highlight, ax=ax[0])
ax[0].set_title("By Recency (days)", fontsize=50)
ax[0].set_xticklabels(top_rec.customer_id.str[:5], rotation=45, fontsize=30)

# Frequency (High is Better)
top_freq = rfm_df.sort_values(by="frequency", ascending=False).head(5)
sns.barplot(y="frequency", x="customer_id", data=top_freq, palette=colors_highlight, ax=ax[1])
ax[1].set_title("By Frequency", fontsize=50)
ax[1].set_xticklabels(top_freq.customer_id.str[:5], rotation=45, fontsize=30)

# Monetary (High is Better)
top_mon = rfm_df.sort_values(by="monetary", ascending=False).head(5)
sns.barplot(y="monetary", x="customer_id", data=top_mon, palette=colors_highlight, ax=ax[2])
ax[2].set_title("By Monetary", fontsize=50)
ax[2].set_xticklabels(top_mon.customer_id.str[:5], rotation=45, fontsize=30)

st.pyplot(fig)
st.markdown("""
> **Insight Strategis:** Analisis RFM mengungkap tantangan besar di mana mayoritas pelanggan masih bersifat One-Time Buyers. Oleh karena itu, rekomendasi strategis utamanya adalah mengalihkan fokus dari sekadar akuisisi pelanggan baru menjadi program retensi pelanggan. Perusahaan perlu menargetkan pelanggan di wilayah dengan AOV tinggi (seperti RR, AP, dan AC) melalui penawaran produk premium atau loyalty reward untuk meningkatkan frekuensi belanja mereka.
""")

st.caption('Copyright (c) 2026 | Analisis Data Egi Farhan')
