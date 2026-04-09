import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency
import os

# --- 1. KONFIGURASI ---
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

def create_bycity_df(df):
    # Cek nama kolom yang benar untuk city
    col = 'customer_city' if 'customer_city' in df.columns else 'city'
    bycity_df = df.groupby(by=col).customer_id.nunique().reset_index()
    bycity_df.rename(columns={"customer_id": "customer_count"}, inplace=True)
    return bycity_df.sort_values(by="customer_count", ascending=False)

def create_bystate_df(df):
    # Cek nama kolom yang benar untuk state
    col = 'customer_state' if 'customer_state' in df.columns else 'state'
    bystate_df = df.groupby(by=col).customer_id.nunique().reset_index()
    bystate_df.rename(columns={"customer_id": "customer_count"}, inplace=True)
    return bystate_df.sort_values(by="customer_count", ascending=False)

def create_delivery_time_df(df):
    delivery_df = df.dropna(subset=['order_purchase_timestamp', 'order_delivered_customer_date']).copy()
    delivery_df = delivery_df.drop_duplicates(subset=['order_id'])
    delivery_time = delivery_df["order_delivered_customer_date"] - delivery_df["order_purchase_timestamp"]
    delivery_df["delivery_time_days"] = delivery_time.apply(lambda x: x.total_seconds() / 86400)
    return delivery_df

def create_sum_order_items_df(df):
    # SOLUSI KEYERROR: Cek mana kolom kategori yang ada
    if 'product_category_name_english' in df.columns:
        cat_col = 'product_category_name_english'
    elif 'product_category_name' in df.columns:
        cat_col = 'product_category_name'
    else:
        # Jika tidak ada dua-duanya, kita buat dummy kategori agar tidak error
        return pd.DataFrame(columns=['category', 'order_id', 'price'])

    sum_order_items_df = df.groupby(cat_col).agg({
        "order_id": "count",
        "price": "sum"
    }).reset_index()
    sum_order_items_df.rename(columns={cat_col: "category"}, inplace=True)
    return sum_order_items_df.sort_values(by="price", ascending=False)

def create_rfm_df(df):
    # Gunakan customer_unique_id jika ada, jika tidak pakai customer_id biasa
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
    datetime_columns = ["order_purchase_timestamp", "order_delivered_customer_date"]
    for column in datetime_columns:
        if column in df.columns:
            df[column] = pd.to_datetime(df[column])
    return df

all_df = load_data()

# --- 4. FILTER ---
min_date = all_df["order_purchase_timestamp"].min().date()
max_date = all_df["order_purchase_timestamp"].max().date()

with st.sidebar:
    st.image("https://github.com/dicodingacademy/assets/raw/main/logo.png")
    try:
        # Menggunakan format tuple untuk default value agar lebih stabil
        date_range = st.date_input(
            label="Rentang Waktu",
            min_value=min_date,
            max_value=max_date,
            value=(min_date, max_date)
        )
        start_date, end_date = date_range
    except:
        start_date, end_date = min_date, max_date

main_df = all_df[(all_df["order_purchase_timestamp"].dt.date >= start_date) & 
                 (all_df["order_purchase_timestamp"].dt.date <= end_date)]

# --- 5. EXECUTION ---
daily_orders_df = create_daily_orders_df(main_df)
bycity_df = create_bycity_df(main_df)
bystate_df = create_bystate_df(main_df)
delivery_time_df = create_delivery_time_df(main_df)
sum_order_items_df = create_sum_order_items_df(main_df)
rfm_df = create_rfm_df(main_df)

# --- 6. UI DASHBOARD ---
st.header('E-Commerce Public Dashboard :sparkles:')

# 1. Metrics
col1, col2 = st.columns(2)
with col1:
    st.metric("Total orders", value=daily_orders_df.order_count.sum())
with col2:
    total_revenue = format_currency(daily_orders_df.revenue.sum(), "BRL", locale='pt_BR') 
    st.metric("Total Revenue", value=total_revenue)

# 2. Daily Orders Chart
fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(daily_orders_df["order_purchase_timestamp"], daily_orders_df["order_count"], marker='o', color="#90CAF9")
st.pyplot(fig)

# 3. Product Performance
st.subheader("Product Performance")
if not sum_order_items_df.empty:
    fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(35, 15))
    sns.barplot(x="order_id", y="category", data=sum_order_items_df.sort_values(by="order_id", ascending=False).head(5), palette="Blues_d", ax=ax[0])
    ax[0].set_title("Best Performing (Volume)", fontsize=50)
    
    sns.barplot(x="price", y="category", data=sum_order_items_df.head(5), palette="Blues_d", ax=ax[1])
    ax[1].set_title("Best Performing (Revenue)", fontsize=50)
    st.pyplot(fig)
else:
    st.write("Kolom kategori produk tidak ditemukan.")

# 4. RFM
st.subheader("RFM Analysis")
col1, col2, col3 = st.columns(3)
col1.metric("Avg Recency", value=f"{round(rfm_df.recency.mean(), 1)} Days")
col2.metric("Avg Frequency", value=f"{round(rfm_df.frequency.mean(), 2)}")
col3.metric("Avg Monetary", value=format_currency(rfm_df.monetary.mean(), "BRL", locale='pt_BR'))

st.caption('Copyright (c) 2026 | Egi Farhan')
