import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import os

# --- 1. KONFIGURASI & STYLE ---
st.set_page_config(page_title="E-Commerce Dashboard | Egi Farhan", layout="wide")
sns.set(style='dark')

# --- 2. HELPER FUNCTIONS (Gaya Dicoding) ---

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

def create_bystate_df(df):
    bystate_df = df.groupby(by="customer_state").customer_id.nunique().reset_index()
    bystate_df.rename(columns={"customer_id": "customer_count"}, inplace=True)
    return bystate_df

def create_rfm_df(df):
    rfm_df = df.groupby(by="customer_id", as_index=False).agg({
        "order_purchase_timestamp": "max",
        "order_id": "nunique",
        "price": "sum"
    })
    rfm_df.columns = ["customer_id", "max_order_timestamp", "frequency", "monetary"]
    
    # Menghitung Recency
    rfm_df["max_order_timestamp"] = rfm_df["max_order_timestamp"].dt.date
    recent_date = df["order_purchase_timestamp"].dt.date.max()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days)
    
    return rfm_df

# --- 3. LOAD DATA ---
current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, "all_data.csv")

@st.cache_data
def load_data():
    if not os.path.exists(file_path):
        return None
    df = pd.read_csv(file_path)
    # Konversi kolom waktu
    if 'order_purchase_timestamp' in df.columns:
        df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'])
    return df

all_df = load_data()

# --- 4. SIDEBAR (FILTER) ---
if all_df is not None:
    min_date = all_df["order_purchase_timestamp"].min()
    max_date = all_df["order_purchase_timestamp"].max()

    with st.sidebar:
        # Logo Resmi Dicoding Collection
        st.image("https://raw.githubusercontent.com/dicodingacademy/dicoding_datasets/main/logo_dicoding_collection.png", width=150)
        
        # Input Rentang Waktu
        date_range = st.date_input(
            label='Rentang Waktu',
            min_value=min_date,
            max_value=max_date,
            value=[min_date, max_date]
        )

    # --- 5. PROSES FILTER DATA ---
    if isinstance(date_range, list) and len(date_range) == 2:
        start_date, end_date = date_range
        # Filter menggunakan .dt.date agar sinkron dengan input streamlit
        main_df = all_df[(all_df["order_purchase_timestamp"].dt.date >= start_date) & 
                         (all_df["order_purchase_timestamp"].dt.date <= end_date)]
    else:
        main_df = all_df

    # --- 6. MENYIAPKAN DATAFRAME UNTUK VISUALISASI ---
    daily_orders_df = create_daily_orders_df(main_df)
    bystate_df = create_bystate_df(main_df)
    rfm_df = create_rfm_df(main_df)

    # --- 7. MAIN DASHBOARD ---
    st.header('E-Commerce Dashboard :sparkles:')
    
    # Daily Orders Section
    st.subheader('Daily Orders')
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total orders", value=daily_orders_df.order_count.sum())
    with col2:
        total_rev = daily_orders_df.revenue.sum()
        st.metric("Total Revenue", value=f"BRL {total_rev:,.2f}")

    fig, ax = plt.subplots(figsize=(16, 8))
    ax.plot(daily_orders_df["order_purchase_timestamp"], daily_orders_df["order_count"], marker='o', linewidth=2, color="#90CAF9")
    ax.tick_params(axis='y', labelsize=20)
    ax.tick_params(axis='x', labelsize=15)
    st.pyplot(fig)

    # Customer Demographics (By State)
    st.subheader("Customer Demographics")
    fig, ax = plt.subplots(figsize=(20, 10))
    # Integritas Visual: Highlight tertinggi
    colors = ["#90CAF9" if i == 0 else "#D3D3D3" for i in range(8)]
    
    top_state_df = bystate_df.sort_values(by="customer_count", ascending=False).head(8)
    sns.barplot(x="customer_count", y="customer_state", data=top_state_df, palette=colors, ax=ax)
    ax.set_title("Number of Customer by States", loc="center", fontsize=30)
    ax.set_ylabel(None)
    ax.set_xlabel(None)
    ax.tick_params(axis='y', labelsize=20)
    ax.tick_params(axis='x', labelsize=15)
    st.pyplot(fig)

    # RFM Analysis Section
    st.subheader("Best Customer Based on RFM Parameters")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Average Recency (days)", value=round(rfm_df.recency.mean(), 1))
    with col2:
        st.metric("Average Frequency", value=round(rfm_df.frequency.mean(), 2))
    with col3:
        st.metric("Average Monetary", value=f"BRL {rfm_df.monetary.mean():,.2f}")

    fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(35, 15))
    colors = ["#90CAF9"] * 5

    # Plot Recency
    sns.barplot(y="recency", x="customer_id", data=rfm_df.sort_values(by="recency", ascending=True).head(5), palette=colors, ax=ax[0])
    ax[0].set_title("By Recency (days)", loc="center", fontsize=50)
    ax[0].tick_params(axis='x', labelrotation=45)

    # Plot Frequency
    sns.barplot(y="frequency", x="customer_id", data=rfm_df.sort_values(by="frequency", ascending=False).head(5), palette=colors, ax=ax[1])
    ax[1].set_title("By Frequency", loc="center", fontsize=50)
    ax[1].tick_params(axis='x', labelrotation=45)

    # Plot Monetary
    sns.barplot(y="monetary", x="customer_id", data=rfm_df.sort_values(by="monetary", ascending=False).head(5), palette=colors, ax=ax[2])
    ax[2].set_title("By Monetary", loc="center", fontsize=50)
    ax[2].tick_params(axis='x', labelrotation=45)

    st.pyplot(fig)

    st.caption('Copyright © 2026 | Egi Farhan')

else:
    st.error("File all_data.csv tidak ditemukan!")
