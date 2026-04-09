import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency
import os

sns.set(style='dark')

# =========================
# HELPER FUNCTIONS
# =========================

def create_daily_orders_df(df):
    daily_orders_df = df.resample(rule='D', on='order_purchase_timestamp').agg({
        "order_id": "nunique",
        "price": "sum"
    }).reset_index()

    daily_orders_df.rename(columns={
        "order_id": "order_count",
        "price": "revenue"
    }, inplace=True)

    return daily_orders_df


def create_bycity_df(df):
    bycity_df = df.groupby("customer_city")["customer_id"].nunique().reset_index()
    bycity_df.rename(columns={"customer_id": "customer_count"}, inplace=True)
    return bycity_df.sort_values(by="customer_count", ascending=False)


def create_bystate_df(df):
    bystate_df = df.groupby("customer_state")["customer_id"].nunique().reset_index()
    bystate_df.rename(columns={"customer_id": "customer_count"}, inplace=True)
    return bystate_df.sort_values(by="customer_count", ascending=False)


def create_delivery_time_df(df):
    delivery_df = df.dropna(subset=[
        "order_purchase_timestamp",
        "order_delivered_customer_date"
    ]).copy()

    delivery_df = delivery_df.drop_duplicates(subset=["order_id"])

    delivery_time = (
        delivery_df["order_delivered_customer_date"]
        - delivery_df["order_purchase_timestamp"]
    ).dt.total_seconds()

    delivery_df["delivery_time_days"] = (delivery_time / 86400).round()

    return delivery_df


def create_sum_order_items_df(df):
    sum_df = df.groupby("product_category_name_english").agg({
        "order_id": "count",
        "price": "sum"
    }).reset_index()

    return sum_df.sort_values(by="price", ascending=False)


def create_rfm_df(df):
    rfm_df = df.groupby("customer_id").agg({
        "order_purchase_timestamp": "max",
        "order_id": "nunique",
        "price": "sum"
    }).reset_index()

    rfm_df.columns = ["customer_id", "max_order_timestamp", "frequency", "monetary"]

    recent_date = df["order_purchase_timestamp"].max()

    rfm_df["recency"] = (
        recent_date - rfm_df["max_order_timestamp"]
    ).dt.days

    rfm_df.drop(columns=["max_order_timestamp"], inplace=True)

    # =========================
    # SEGMENTASI RFM (BONUS)
    # =========================
    rfm_df["segment"] = "Regular"

    rfm_df.loc[
        (rfm_df["recency"] <= 30) & (rfm_df["frequency"] >= 3),
        "segment"
    ] = "Loyal"

    rfm_df.loc[
        rfm_df["monetary"] >= rfm_df["monetary"].quantile(0.75),
        "segment"
    ] = "High Value"

    return rfm_df


# =========================
# LOAD DATA
# =========================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(BASE_DIR, "all_data.csv")

all_df = pd.read_csv(file_path)

all_df["order_purchase_timestamp"] = pd.to_datetime(all_df["order_purchase_timestamp"])
all_df["order_delivered_customer_date"] = pd.to_datetime(all_df["order_delivered_customer_date"])

all_df.sort_values(by="order_purchase_timestamp", inplace=True)

# =========================
# SIDEBAR
# =========================

min_date = all_df["order_purchase_timestamp"].min().date()
max_date = all_df["order_purchase_timestamp"].max().date()

with st.sidebar:
    st.image("https://github.com/dicodingacademy/assets/raw/main/logo.png")

    start_date, end_date = st.date_input(
        "Rentang Waktu",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date)
    )

# =========================
# FILTER
# =========================

main_df = all_df[
    (all_df["order_purchase_timestamp"].dt.date >= start_date) &
    (all_df["order_purchase_timestamp"].dt.date <= end_date)
]

# =========================
# PREPARE DATA
# =========================

daily_orders_df = create_daily_orders_df(main_df)
bycity_df = create_bycity_df(main_df)
bystate_df = create_bystate_df(main_df)
delivery_time_df = create_delivery_time_df(main_df)
sum_order_items_df = create_sum_order_items_df(main_df)
rfm_df = create_rfm_df(main_df)

# =========================
# DASHBOARD
# =========================

st.header('📊 E-Commerce Public Dashboard')

# =========================
# DAILY ORDERS
# =========================

st.subheader('Daily Orders')
st.markdown("Menampilkan tren jumlah pesanan dan revenue harian.")

col1, col2 = st.columns(2)
with col1:
    st.metric("Total Orders", daily_orders_df.order_count.sum())
with col2:
    st.metric("Total Revenue", format_currency(daily_orders_df.revenue.sum(), "USD", locale='en_US'))

fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(
    daily_orders_df["order_purchase_timestamp"],
    daily_orders_df["order_count"],
    marker='o',
    linewidth=2,
    color="#90CAF9"
)
ax.set_title("Daily Orders Trend")
st.pyplot(fig)

st.info("Insight: Terlihat fluktuasi jumlah order yang menunjukkan pola pembelian pelanggan.")

# =========================
# DEMOGRAFI
# =========================

st.subheader("Customer Demographics")

col1, col2 = st.columns(2)

with col1:
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(x="customer_count", y="customer_state", data=bystate_df.head(5), color="#90CAF9")
    ax.set_title("Top States")
    st.pyplot(fig)

with col2:
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(x="customer_count", y="customer_city", data=bycity_df.head(5), color="#90CAF9")
    ax.set_title("Top Cities")
    st.pyplot(fig)

st.info("Insight: Wilayah tertentu memiliki konsentrasi pelanggan yang tinggi.")

# =========================
# DELIVERY
# =========================

st.subheader("Delivery Time Analysis")

col1, col2 = st.columns(2)
with col1:
    st.metric("Avg Delivery Time", round(delivery_time_df['delivery_time_days'].mean(), 1))
with col2:
    st.metric("Max Delay", delivery_time_df['delivery_time_days'].max())

fig, ax = plt.subplots(figsize=(16, 8))
sns.histplot(delivery_time_df['delivery_time_days'], bins=40, color="#90CAF9", kde=True)
ax.set_title("Delivery Time Distribution")
st.pyplot(fig)

st.info("Insight: Mayoritas pengiriman berada dalam rentang waktu tertentu.")

# =========================
# PRODUCT
# =========================

st.subheader("Best Product Categories")

fig, ax = plt.subplots(ncols=2, figsize=(16, 6))

sns.barplot(
    x="order_id",
    y="product_category_name_english",
    data=sum_order_items_df.sort_values(by="order_id", ascending=False).head(5),
    color="#90CAF9",
    ax=ax[0]
)
ax[0].set_title("Top by Volume")

sns.barplot(
    x="price",
    y="product_category_name_english",
    data=sum_order_items_df.head(5),
    color="#90CAF9",
    ax=ax[1]
)
ax[1].set_title("Top by Revenue")

st.pyplot(fig)

st.info("Insight: Beberapa kategori produk mendominasi penjualan.")

# =========================
# RFM ANALYSIS (FINAL)
# =========================

st.subheader("RFM Analysis")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Avg Recency", round(rfm_df.recency.mean(), 1))
with col2:
    st.metric("Avg Frequency", round(rfm_df.frequency.mean(), 2))
with col3:
    st.metric("Avg Monetary", format_currency(rfm_df.monetary.mean(), "USD", locale='en_US'))

# BAR CHART
fig, ax = plt.subplots(ncols=3, figsize=(18, 6))

sns.barplot(data=rfm_df.sort_values(by="recency").head(5), x="customer_id", y="recency", ax=ax[0], color="#90CAF9")
ax[0].set_title("Best Recency")

sns.barplot(data=rfm_df.sort_values(by="frequency", ascending=False).head(5), x="customer_id", y="frequency", ax=ax[1], color="#90CAF9")
ax[1].set_title("Top Frequency")

sns.barplot(data=rfm_df.sort_values(by="monetary", ascending=False).head(5), x="customer_id", y="monetary", ax=ax[2], color="#90CAF9")
ax[2].set_title("Top Monetary")

st.pyplot(fig)

# TABEL
st.subheader("Top Customers (RFM Table)")
st.dataframe(rfm_df.sort_values(by=["monetary", "frequency"], ascending=False).head(10))

# SEGMENTASI
st.subheader("Customer Segmentation")

fig, ax = plt.subplots()
sns.countplot(data=rfm_df, x="segment", palette=["#90CAF9"])
st.pyplot(fig)

st.info("""
Insight:
- Loyal = sering beli & baru transaksi
- High Value = kontribusi revenue tinggi
- Regular = pelanggan biasa
""")


st.header("📌 Business Questions & Insights")

# =========================
# PERTANYAAN 1
# =========================

st.subheader("1️⃣ Pertanyaan 1")

st.markdown("""
**Kategori produk apa yang menghasilkan total pendapatan (revenue) tertinggi di 5 negara bagian (state) 
dengan volume transaksi terbesar selama periode 2016-2018?**
""")

st.markdown("""
📊 **Visualisasi yang digunakan:**
- Grafik **Top States (Customer Demographics)** → untuk melihat 5 state dengan volume transaksi terbesar  
- Grafik **Top Product Categories (By Revenue)** → untuk melihat kategori dengan revenue tertinggi  

📌 **Interpretasi:**
- State dengan jumlah pelanggan tertinggi merepresentasikan volume transaksi terbesar  
- Dari grafik produk, terlihat bahwa kategori dengan revenue tertinggi adalah kategori yang paling berkontribusi terhadap total pendapatan  

💡 **Kesimpulan:**
Kategori produk dengan revenue tertinggi (misalnya: *bed_bath_table* atau kategori lain pada grafik) merupakan kontributor utama pada state dengan aktivitas transaksi terbesar.
""")

# =========================
# PERTANYAAN 2
# =========================

st.subheader("2️⃣ Pertanyaan 2")

st.markdown("""
**Bagaimana efektivitas nilai transaksi (Average Order Value) pada kategori produk unggulan 'Bed Bath Table' 
di berbagai wilayah Brazil selama periode 2017-2018, dan wilayah mana yang menunjukkan potensi daya beli tertinggi?**
""")

# =========================
# HITUNG AOV
# =========================

bed_df = main_df[
    (main_df["product_category_name_english"] == "bed_bath_table") &
    (main_df["order_purchase_timestamp"].dt.year >= 2017)
]

aov_df = bed_df.groupby("customer_state").agg({
    "price": "sum",
    "order_id": "nunique"
}).reset_index()

aov_df["AOV"] = aov_df["price"] / aov_df["order_id"]
aov_df = aov_df.sort_values(by="AOV", ascending=False)

# =========================
# VISUALISASI AOV
# =========================

st.markdown("📊 **Visualisasi Average Order Value (AOV)**")

fig, ax = plt.subplots(figsize=(12, 6))
sns.barplot(data=aov_df.head(5), x="AOV", y="customer_state", color="#90CAF9")
ax.set_title("Top 5 States by AOV (Bed Bath Table)")
st.pyplot(fig)

# =========================
# TABEL AOV
# =========================

st.markdown("📋 **Tabel AOV per State**")
st.dataframe(aov_df.head(10))

# =========================
# INTERPRETASI
# =========================

st.markdown("""
📌 **Interpretasi:**
- AOV menunjukkan rata-rata nilai transaksi per order  
- Semakin tinggi AOV → semakin besar daya beli pelanggan di wilayah tersebut  

💡 **Kesimpulan:**
State dengan nilai AOV tertinggi menunjukkan potensi daya beli per transaksi yang paling besar terhadap produk *Bed Bath Table*.
""")

# =========================
# FOOTER
# =========================

st.caption("© 2026 Dicoding Submission")
