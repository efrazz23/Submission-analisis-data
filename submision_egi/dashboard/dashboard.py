import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency
import os  # ⬅️ TAMBAHAN PENTING

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
    df = df[df["order_status"] == "delivered"]

    bycity_df = df.groupby("customer_city")["customer_id"].nunique().reset_index()
    bycity_df.rename(columns={"customer_id": "customer_count"}, inplace=True)

    return bycity_df.sort_values(by="customer_count", ascending=False)


def create_bystate_df(df):
    df = df[df["order_status"] == "delivered"]

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
    sum_df = df.groupby("product_category_name").agg({
        "order_id": "count",
        "price": "sum"
    }).reset_index()

    return sum_df.sort_values(by="price", ascending=False)


def create_rfm_df(df):
    rfm_df = df.groupby("customer_unique_id").agg({
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
# LOAD DATA (INI YANG DIPERBAIKI 🔥)
# =========================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(BASE_DIR, "all_data.csv")

# Safety biar gak crash
if not os.path.exists(file_path):
    st.error("File all_data.csv tidak ditemukan di folder dashboard!")
    st.stop()

all_df = pd.read_csv(file_path)

# =========================
# DATA CLEANING
# =========================

datetime_columns = [
    "order_purchase_timestamp",
    "order_delivered_customer_date"
]

for col in datetime_columns:
    all_df[col] = pd.to_datetime(all_df[col])

all_df.sort_values(by="order_purchase_timestamp", inplace=True)

# =========================
# SIDEBAR
# =========================

min_date = all_df["order_purchase_timestamp"].min()
max_date = all_df["order_purchase_timestamp"].max()

with st.sidebar:
    st.image(os.path.join(BASE_DIR, "logo.png"))  # ⬅️ FIX LOGO

    start_date, end_date = st.date_input(
        "Pilih Rentang Tanggal",
        value=(min_date.date(), max_date.date()),
        min_value=min_date.date(),
        max_value=max_date.date()
    )

# =========================
# FILTER (SUDAH BENAR ✅)
# =========================

main_df = all_df[
    (all_df["order_purchase_timestamp"] >= pd.to_datetime(start_date)) &
    (all_df["order_purchase_timestamp"] <= pd.to_datetime(end_date))
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

st.header("📊 E-Commerce Dashboard")

st.subheader("Daily Orders")

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
st.pyplot(fig)

st.caption("© 2026 Submission")
