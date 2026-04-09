import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency
import os

sns.set(style='darkgrid')

# =========================
# HELPER FUNCTIONS
# =========================

def create_daily_orders_df(df):
    df = df.copy()
    df.set_index("order_purchase_timestamp", inplace=True)

    daily_orders_df = df.resample("D").agg({
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

    rfm_df.columns = [
        "customer_id",
        "max_order_timestamp",
        "frequency",
        "monetary"
    ]

    recent_date = df["order_purchase_timestamp"].max()

    rfm_df["recency"] = (
        recent_date - rfm_df["max_order_timestamp"]
    ).dt.days

    return rfm_df.drop(columns=["max_order_timestamp"])


# =========================
# LOAD DATA
# =========================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(BASE_DIR, "all_data.csv")

all_df = pd.read_csv(file_path)

all_df["order_purchase_timestamp"] = pd.to_datetime(all_df["order_purchase_timestamp"])
all_df["order_delivered_customer_date"] = pd.to_datetime(all_df["order_delivered_customer_date"])

# =========================
# SIDEBAR
# =========================

min_date = all_df["order_purchase_timestamp"].min()
max_date = all_df["order_purchase_timestamp"].max()

with st.sidebar:
    st.image("https://github.com/dicodingacademy/assets/raw/main/logo.png")
    st.header("Filter Data")

    start_date, end_date = st.date_input(
        "Pilih Rentang Tanggal",
        value=(min_date.date(), max_date.date())
    )

# FILTER
main_df = all_df[
    (all_df["order_purchase_timestamp"] >= pd.to_datetime(start_date)) &
    (all_df["order_purchase_timestamp"] <= pd.to_datetime(end_date))
]

# PREPARE
daily_orders_df = create_daily_orders_df(main_df)
bycity_df = create_bycity_df(main_df)
bystate_df = create_bystate_df(main_df)
delivery_time_df = create_delivery_time_df(main_df)
sum_order_items_df = create_sum_order_items_df(main_df)
rfm_df = create_rfm_df(main_df)

# =========================
# DASHBOARD
# =========================

st.title("📊 E-Commerce Data Analysis Dashboard")
st.markdown("Dashboard ini menampilkan analisis performa e-commerce berdasarkan data transaksi pelanggan.")

# =========================
# DAILY ORDERS
# =========================

st.header("📈 Daily Orders & Revenue")

st.markdown("Menampilkan tren jumlah pesanan dan total pendapatan per hari.")

col1, col2 = st.columns(2)

with col1:
    st.metric("Total Orders", daily_orders_df["order_count"].sum())

with col2:
    st.metric(
        "Total Revenue",
        format_currency(daily_orders_df["revenue"].sum(), "USD", locale="en_US")
    )

fig, ax = plt.subplots()
ax.plot(daily_orders_df["order_purchase_timestamp"], daily_orders_df["order_count"])
ax.set_title("Tren Jumlah Order Harian")
ax.set_xlabel("Tanggal")
ax.set_ylabel("Jumlah Order")
st.pyplot(fig)

st.info("Insight: Terlihat adanya fluktuasi jumlah order yang menunjukkan pola musiman dalam transaksi.")

# =========================
# DEMOGRAFI
# =========================

st.header("🌍 Customer Demographics")

st.markdown("Distribusi pelanggan berdasarkan kota dan negara bagian.")

col1, col2 = st.columns(2)

with col1:
    fig, ax = plt.subplots()
    sns.barplot(data=bystate_df.head(5), x="customer_count", y="customer_state")
    ax.set_title("Top 5 States")
    st.pyplot(fig)

with col2:
    fig, ax = plt.subplots()
    sns.barplot(data=bycity_df.head(5), x="customer_count", y="customer_city")
    ax.set_title("Top 5 Cities")
    st.pyplot(fig)

st.info("Insight: Beberapa wilayah memiliki konsentrasi pelanggan yang lebih tinggi.")

# =========================
# DELIVERY
# =========================

st.header("🚚 Delivery Time Analysis")

st.markdown("Analisis waktu pengiriman pesanan ke pelanggan.")

st.metric("Rata-rata Hari Pengiriman", round(delivery_time_df["delivery_time_days"].mean(), 1))

fig, ax = plt.subplots()
sns.histplot(delivery_time_df["delivery_time_days"], bins=30)
ax.set_title("Distribusi Waktu Pengiriman")
st.pyplot(fig)

st.info("Insight: Sebagian besar pengiriman berada dalam rentang waktu tertentu.")

# =========================
# PRODUCT
# =========================

st.header("🛒 Product Performance")

st.markdown("Kategori produk dengan performa terbaik berdasarkan revenue.")

fig, ax = plt.subplots()
sns.barplot(
    data=sum_order_items_df.head(5),
    x="price",
    y="product_category_name_english"
)
ax.set_title("Top Product Categories by Revenue")
st.pyplot(fig)

st.info("Insight: Beberapa kategori produk mendominasi total pendapatan.")

# =========================
# RFM
# =========================

st.header("👥 RFM Analysis")

st.markdown("Analisis perilaku pelanggan berdasarkan Recency, Frequency, dan Monetary.")

st.metric("Rata-rata Recency", round(rfm_df["recency"].mean(), 1))

st.info("Insight: Pelanggan dengan recency rendah berarti lebih baru melakukan transaksi.")

# =========================
# FOOTER
# =========================

st.caption("© 2026 Dicoding Submission Dashboard")
