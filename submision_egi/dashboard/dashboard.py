import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency

# =========================
# CONFIG STYLE
# =========================
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
# LOAD DATA
# =========================

all_df = pd.read_csv("all_data.csv")

datetime_columns = [
    "order_purchase_timestamp",
    "order_delivered_customer_date"
]

for col in datetime_columns:
    all_df[col] = pd.to_datetime(all_df[col])

all_df.sort_values(by="order_purchase_timestamp", inplace=True)

# =========================
# SIDEBAR FILTER
# =========================

min_date = all_df["order_purchase_timestamp"].min()
max_date = all_df["order_purchase_timestamp"].max()

with st.sidebar:
    st.image("logo.png")  # Pastikan file ada di folder dashboard

    start_date, end_date = st.date_input(
        "Pilih Rentang Tanggal",
        value=(min_date.date(), max_date.date()),
        min_value=min_date.date(),
        max_value=max_date.date()
    )

# =========================
# FILTER DATA (FIX UTAMA)
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

st.header("📊 E-Commerce Public Dashboard")

# =========================
# DAILY ORDERS
# =========================

st.subheader("Daily Orders")

col1, col2 = st.columns(2)

with col1:
    total_orders = daily_orders_df["order_count"].sum()
    st.metric("Total Orders", total_orders)

with col2:
    total_revenue = format_currency(
        daily_orders_df["revenue"].sum(),
        "USD",
        locale="en_US"
    )
    st.metric("Total Revenue", total_revenue)

fig, ax = plt.subplots(figsize=(12, 6))
ax.plot(
    daily_orders_df["order_purchase_timestamp"],
    daily_orders_df["order_count"],
    marker='o'
)
ax.set_title("Daily Orders Trend")
st.pyplot(fig)

# =========================
# DEMOGRAPHICS
# =========================

st.subheader("Customer Demographics")

color_main = "#4CAF50"

col1, col2 = st.columns(2)

with col1:
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(
        data=bystate_df.head(5),
        x="customer_count",
        y="customer_state",
        color=color_main
    )
    ax.set_title("Top 5 States")
    st.pyplot(fig)

with col2:
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(
        data=bycity_df.head(5),
        x="customer_count",
        y="customer_city",
        color=color_main
    )
    ax.set_title("Top 5 Cities")
    st.pyplot(fig)

st.caption("Demografi berdasarkan order dengan status delivered.")

# =========================
# DELIVERY TIME
# =========================

st.subheader("Delivery Time Analysis")

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "Average Delivery (Days)",
        round(delivery_time_df["delivery_time_days"].mean(), 1)
    )

with col2:
    st.metric(
        "Max Delivery Delay (Days)",
        delivery_time_df["delivery_time_days"].max()
    )

fig, ax = plt.subplots(figsize=(10, 5))
sns.histplot(
    delivery_time_df["delivery_time_days"],
    bins=30
)
ax.set_title("Distribution of Delivery Time")
st.pyplot(fig)

# =========================
# PRODUCT PERFORMANCE
# =========================

st.subheader("Best Performing Product Categories")

col1, col2 = st.columns(2)

with col1:
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(
        data=sum_order_items_df.head(5),
        x="order_id",
        y="product_category_name",
        color=color_main
    )
    ax.set_title("Top by Volume")
    st.pyplot(fig)

with col2:
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(
        data=sum_order_items_df.head(5),
        x="price",
        y="product_category_name",
        color=color_main
    )
    ax.set_title("Top by Revenue")
    st.pyplot(fig)

# =========================
# RFM ANALYSIS
# =========================

st.subheader("RFM Analysis")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Avg Recency", round(rfm_df["recency"].mean(), 1))

with col2:
    st.metric("Avg Frequency", round(rfm_df["frequency"].mean(), 2))

with col3:
    st.metric(
        "Avg Monetary",
        format_currency(rfm_df["monetary"].mean(), "USD", locale="en_US")
    )

# Top customers
fig, ax = plt.subplots(figsize=(10, 5))
top_customers = rfm_df.sort_values(by="monetary", ascending=False).head(5)
sns.barplot(
    data=top_customers,
    x="monetary",
    y="customer_id",
    color=color_main
)
ax.set_title("Top Customers by Monetary")
st.pyplot(fig)

# =========================
# FOOTER
# =========================

st.caption("© 2026 Dicoding Submission Dashboard")
