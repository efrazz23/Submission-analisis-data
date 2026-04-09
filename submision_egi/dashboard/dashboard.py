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

# --- 5. PREPARATION ---
daily_orders_df = create_daily_orders_df(main_df)
sum_order_items_df = create_sum_order_items_df(main_df)
bystate_df = create_bystate_df(main_df)
rfm_df = create_rfm_df(main_df)

# --- 6. VISUALISASI DASHBOARD ---
st.header('E-Commerce Public Dashboard :sparkles:')

# Section 1: Daily Orders (Sekarang dalam bentuk Batang/Bar)
st.subheader('Daily Orders')
col1, col2 = st.columns(2)
with col1:
    st.metric("Total orders", value=daily_orders_df.order_count.sum())
with col2:
    total_rev = format_currency(daily_orders_df.revenue.sum(), "BRL", locale='pt_BR')
    st.metric("Total Revenue", value=total_rev)

fig, ax = plt.subplots(figsize=(16, 8))
# Menggunakan barplot untuk Daily Orders
sns.barplot(x=daily_orders_df["order_purchase_timestamp"].dt.date, y=daily_orders_df["order_count"], color="#90CAF9", ax=ax)
ax.set_title("Grafik Pesanan Harian", fontsize=20)
plt.xticks(rotation=45)
st.pyplot(fig)
st.markdown("""
**Deskripsi (Insight):** Pembersihan data dengan batasan waktu menghasilkan analisis yang akurat dan relevan. Bisnis dapat melihat tren yang terjadi pada periode tertentu tanpa terganggu oleh data usang, sehingga pengambilan keputusan didasarkan pada realitas pasar yang tepat.
""")

# Section 2: Product Performance
st.subheader("Best & Worst Performing Product")
fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(35, 15))
colors = ["#90CAF9", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

sns.barplot(x="order_id", y="category", data=sum_order_items_df.sort_values(by="order_id", ascending=False).head(5), palette=colors, ax=ax[0])
ax[0].set_title("Best Performing Product", loc="center", fontsize=50)
ax[0].tick_params(axis='y', labelsize=35)
ax[0].tick_params(axis='x', labelsize=30)

sns.barplot(x="order_id", y="category", data=sum_order_items_df.sort_values(by="order_id", ascending=True).head(5), palette=colors, ax=ax[1])
ax[1].set_title("Worst Performing Product", loc="center", fontsize=50)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].tick_params(axis='y', labelsize=35)
ax[1].tick_params(axis='x', labelsize=30)
st.pyplot(fig)
st.markdown("""
**Deskripsi (Insight):** Visualisasi berbasis prioritas dengan teknik Highlighting (warna berbeda pada peringkat pertama) mempermudah stakeholder menangkap informasi krusial. Pemilik bisnis bisa langsung tahu kategori mana yang merupakan 'tambang emas' atau yang perlu dievaluasi.
""")

# Section 3: Customer Demographics
st.subheader("Customer Demographics")
fig, ax = plt.subplots(figsize=(16, 8))
sns.barplot(x="customer_count", y="customer_state", data=bystate_df.head(5), palette=colors, ax=ax)
ax.set_title("Number of Customer by States", fontsize=30)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=20)
st.pyplot(fig)
st.markdown("""
**Deskripsi (Insight):** Integrasi data multidimensi memungkinkan analisis lintas variabel. Kita bisa melihat hubungan antara lokasi geografis pembeli dan frekuensi transaksi mereka untuk mendukung strategi logistik wilayah.
""")

# Section 4: RFM Analysis (Grafik Batang)
st.subheader("Best Customer Based on RFM Parameters")
col_r1, col_r2, col_r3 = st.columns(3)
with col_r1:
    st.metric("Avg Recency (days)", value=round(rfm_df.recency.mean(), 1))
with col_r2:
    st.metric("Avg Frequency", value=round(rfm_df.frequency.mean(), 2))
with col_r3:
    st.metric("Avg Monetary", value=format_currency(rfm_df.monetary.mean(), "BRL", locale='pt_BR'))

fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(35, 15))
# Recency
sns.barplot(y="recency", x="customer_id", data=rfm_df.sort_values(by="recency", ascending=True).head(5), color="#90CAF9", ax=ax[0])
ax[0].set_title("By Recency (days)", loc="center", fontsize=50)
ax[0].set_xticklabels(rfm_df.sort_values(by="recency", ascending=True).head(5).customer_id.str[:5], rotation=45, fontsize=30)
# Frequency
sns.barplot(y="frequency", x="customer_id", data=rfm_df.sort_values(by="frequency", ascending=False).head(5), color="#90CAF9", ax=ax[1])
ax[1].set_title("By Frequency", loc="center", fontsize=50)
ax[1].set_xticklabels(rfm_df.sort_values(by="frequency", ascending=False).head(5).customer_id.str[:5], rotation=45, fontsize=30)
# Monetary
sns.barplot(y="monetary", x="customer_id", data=rfm_df.sort_values(by="monetary", ascending=False).head(5), color="#90CAF9", ax=ax[2])
ax[2].set_title("By Monetary", loc="center", fontsize=50)
ax[2].set_xticklabels(rfm_df.sort_values(by="monetary", ascending=False).head(5).customer_id.str[:5], rotation=45, fontsize=30)
st.pyplot(fig)
st.markdown("""
**Deskripsi (Insight):** Pengukuran metrik RFM memberikan pandangan mendalam mengenai daya beli. Wilayah atau pelanggan dengan transaksi banyak namun nilai kecil bisa diberikan promo upselling (bundling), sedangkan yang bernilai besar diberikan promo loyalitas.
""")

st.caption('Copyright (c) 2026 | Analisis Data Egi Farhan')
