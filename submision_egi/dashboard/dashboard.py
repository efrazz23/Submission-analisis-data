import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency
import os

# Konfigurasi Dasar
st.set_page_config(page_title="E-Commerce Public Dashboard", layout="wide")
sns.set(style='dark')

# --- HELPER FUNCTIONS ---

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
    sum_order_items_df = df.groupby("product_category_name").agg({
        "order_id": "count",
        "price": "sum"
    }).reset_index()
    return sum_order_items_df.sort_values(by="price", ascending=False)

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

# --- LOAD DATA ---
current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, "all_data.csv")

all_df = pd.read_csv(file_path)
datetime_columns = ["order_purchase_timestamp", "order_delivered_customer_date"]
for column in datetime_columns:
    all_df[column] = pd.to_datetime(all_df[column])

all_df.sort_values(by="order_purchase_timestamp", inplace=True)

# --- SIDEBAR FILTER ---
min_date = all_df["order_purchase_timestamp"].min().date()
max_date = all_df["order_purchase_timestamp"].max().date()

with st.sidebar:
    st.image("https://github.com/dicodingacademy/assets/raw/main/logo.png")
    
    # Perbaikan: Menangani input tanggal agar tidak error saat proses filter
    date_range = st.date_input(
        label="Rentang Waktu",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date)
    )

# Pastikan user memilih rentang yang lengkap
if len(date_range) == 2:
    start_date, end_date = date_range
    main_df = all_df[(all_df["order_purchase_timestamp"].dt.date >= start_date) & 
                     (all_df["order_purchase_timestamp"].dt.date <= end_date)]
    
    # --- MENYIAPKAN DATA ---
    daily_orders_df = create_daily_orders_df(main_df)
    bycity_df = create_bycity_df(main_df)
    bystate_df = create_bystate_df(main_df)
    delivery_time_df = create_delivery_time_df(main_df)
    sum_order_items_df = create_sum_order_items_df(main_df)
    rfm_df = create_rfm_df(main_df)

    # --- VISUALISASI ---
    st.header('E-Commerce Public Dashboard :sparkles:')

    # 1. Daily Orders
    st.subheader('Daily Orders')
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total orders", value=daily_orders_df.order_count.sum())
    with col2:
        total_revenue = format_currency(daily_orders_df.revenue.sum(), "USD", locale='es_CO') 
        st.metric("Total Revenue", value=total_revenue)

    fig, ax = plt.subplots(figsize=(16, 8))
    ax.plot(daily_orders_df["order_purchase_timestamp"], daily_orders_df["order_count"], marker='o', linewidth=2, color="#90CAF9")
    st.pyplot(fig)

    # 2. Customer Demographics
    st.subheader("Customer Demographics")
    col1, col2 = st.columns(2)
    with col1:
        fig, ax = plt.subplots(figsize=(20, 10))
        sns.barplot(x="customer_count", y="customer_state", data=bystate_df.head(5), palette="Blues_d", ax=ax)
        ax.set_title("Number of Customer by States", fontsize=30)
        st.pyplot(fig)
    with col2:
        fig, ax = plt.subplots(figsize=(20, 10))
        sns.barplot(x="customer_count", y="customer_city", data=bycity_df.head(5), palette="Blues_d", ax=ax)
        ax.set_title("Number of Customer by City", fontsize=30)
        st.pyplot(fig)

    # 3. Delivery Time
    st.subheader("Delivery Time Analysis")
    col1, col2 = st.columns(2)
    col1.metric("Avg Delivery Time (Days)", value=round(delivery_time_df['delivery_time_days'].mean(), 1))
    col2.metric("Max Delivery Delay (Days)", value=round(delivery_time_df['delivery_time_days'].max(), 1))

    # 4. Product Performance
    st.subheader("Best Performing Product Categories")
    fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(35, 15))
    colors = ["#90CAF9", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]
    
    sns.barplot(x="order_id", y="product_category_name", data=sum_order_items_df.sort_values(by="order_id", ascending=False).head(5), palette=colors, ax=ax[0])
    ax[0].set_title("By Volume (Items Sold)", fontsize=50)
    
    sns.barplot(x="price", y="product_category_name", data=sum_order_items_df.head(5), palette=colors, ax=ax[1])
    ax[1].set_title("By Revenue ($)", fontsize=50)
    ax[1].invert_xaxis()
    ax[1].yaxis.tick_right()
    st.pyplot(fig)

    # 5. RFM Analysis
    st.subheader("Best Customer Based on RFM Parameters")
    col1, col2, col3 = st.columns(3)
    col1.metric("Average Recency (days)", value=round(rfm_df.recency.mean(), 1))
    col2.metric("Average Frequency", value=round(rfm_df.frequency.mean(), 2))
    col3.metric("Average Monetary", value=format_currency(rfm_df.monetary.mean(), "USD", locale='es_CO'))

    fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(35, 15))
    top_r = rfm_df.sort_values(by="recency", ascending=True).head(5)
    sns.barplot(y="recency", x="customer_id", data=top_r, palette=colors, ax=ax[0])
    ax[0].set_xticklabels(top_r['customer_id'].str[:5], rotation=45)
    
    top_f = rfm_df.sort_values(by="frequency", ascending=False).head(5)
    sns.barplot(y="frequency", x="customer_id", data=top_f, palette=colors, ax=ax[1])
    ax[1].set_xticklabels(top_f['customer_id'].str[:5], rotation=45)

    top_m = rfm_df.sort_values(by="monetary", ascending=False).head(5)
    sns.barplot(y="monetary", x="customer_id", data=top_m, palette=colors, ax=ax[2])
    ax[2].set_xticklabels(top_m['customer_id'].str[:5], rotation=45)
    st.pyplot(fig)

    st.caption('Copyright (c) Dicoding Submission 2026')

else:
    st.info("Silakan pilih rentang waktu di sidebar.")
