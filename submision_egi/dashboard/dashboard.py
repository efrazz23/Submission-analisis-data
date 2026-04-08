import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import os

# --- 1. KONFIGURASI ---
st.set_page_config(page_title="Final Submission | Egi", layout="wide")

current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, "all_data.csv")

@st.cache_data
def load_data():
    if not os.path.exists(file_path): 
        return None
    df = pd.read_csv(file_path)
    if 'order_purchase_timestamp' in df.columns:
        df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'], errors='coerce')
    return df.dropna(subset=['order_purchase_timestamp'])

all_df = load_data()

# --- 2. LOGIKA DATA ---
if all_df is not None:
    # Sidebar Filter
    with st.sidebar:
        st.header("⚙️ Kontrol Data")
        min_d, max_d = all_df["order_purchase_timestamp"].min(), all_df["order_purchase_timestamp"].max()
        dates = st.date_input("Filter Periode", [min_d, max_d], min_value=min_d, max_value=max_d)
        
        if len(dates) == 2:
            main_df = all_df[(all_df["order_purchase_timestamp"] >= pd.to_datetime(dates[0])) & 
                             (all_df["order_purchase_timestamp"] <= pd.to_datetime(dates[1]))]
        else:
            main_df = all_df

    # --- 3. TAMPILAN DASHBOARD ---
    st.title("📊 E-Commerce Performance Analysis")
    st.info("Dashboard ini menyajikan jawaban atas dua pertanyaan riset utama mengenai performa penjualan.")

    # Ringkasan Metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Uniq Orders", f"{main_df.order_id.nunique():,}")
    c2.metric("Total Revenue", f"BRL {main_df.price.sum():,.0f}")
    c3.metric("Total Items Sold", f"{main_df.shape[0]:,}")

    st.markdown("---")

 # --- SOAL 1: VERSI FINAL (SP DI ATAS + INSIGHT SAMPING) ---
    st.header("1. Profitabilitas Produk Berdasarkan Wilayah")
    st.markdown("Analisis kategori produk dengan pendapatan tertinggi di 5 negara bagian dengan total revenue terbesar.")

    # 1. Hitung TOTAL REVENUE per state untuk menentukan urutan (SP, RJ, MG, dsb)
    state_revenue_order = main_df.groupby('customer_state')['price'].sum().sort_values(ascending=False).head(5).index
    
    # 2. Filter data hanya untuk 5 state tersebut
    top_states_df = main_df[main_df['customer_state'].isin(state_revenue_order)]
    
    # 3. Cari Produk terbaik di masing-masing state tersebut
    cat_col = 'product_category_name_english' if 'product_category_name_english' in main_df.columns else 'product_category_name'
    product_revenue_state = top_states_df.groupby(['customer_state', cat_col])['price'].sum().reset_index()
    
    # 4. Ambil kategori tertinggi per state dan PAKSA urutan sesuai state_revenue_order
    top_product_per_state = product_revenue_state.sort_values(['customer_state', 'price'], ascending=[True, False]).groupby('customer_state').head(1).copy()
    
    # Trik pengurutan:
    top_product_per_state['customer_state'] = pd.Categorical(top_product_per_state['customer_state'], categories=state_revenue_order, ordered=True)
    top_product_per_state = top_product_per_state.sort_values('customer_state').reset_index(drop=True)

    # --- LAYOUT KOLOM ---
    col_chart, col_desc = st.columns([2, 1]) 

    with col_chart:
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(
            x='price', 
            y='customer_state', 
            data=top_product_per_state, 
            palette='viridis',
            ax=ax
        )
        ax.set_title("Revenue & Kategori Produk Unggulan per State", fontsize=14)
        ax.set_xlabel("Total Revenue (BRL)")
        ax.set_ylabel("State")
        
        # Tambahkan label nama produk di dalam bar
        for i, p in enumerate(ax.patches):
            ax.annotate(f" {top_product_per_state[cat_col].iloc[i]}", 
                        (p.get_width(), p.get_y() + p.get_height()/2), 
                        va='center', fontsize=10, fontweight='bold')
        
        st.pyplot(fig)

    with col_desc:
        st.write("### 📌 Insight Wilayah")
        # Menampilkan deskripsi berdasarkan urutan grafik
        for index, row in top_product_per_state.iterrows():
            st.write(f"**{index+1}. {row['customer_state']}**")
            st.write(f"Kategori: `{row[cat_col]}`")
            st.write(f"Revenue: **BRL {row['price']:,.0f}**")
            st.write("---")
        
        st.info(f"💡 Wilayah **{top_product_per_state.customer_state.iloc[0]}** tetap menjadi pemimpin pasar secara keseluruhan.")
    # --- SOAL 2: ANALISIS AOV PADA PRODUK UNGGULAN ---
    st.header("2. Analisis AOV pada Kategori Produk Unggulan")
    st.markdown("Melihat sebaran Average Order Value (AOV) per wilayah khusus untuk kategori terpopuler.")
    
    # 1. Cari Kategori Unggulan (Paling banyak order)
    unggulan_name = main_df.groupby(cat_col).order_id.nunique().idxmax()
    unggulan_df = main_df[main_df[cat_col] == unggulan_name]
    
    # 2. Hitung AOV
    aov_geo = unggulan_df.groupby('customer_state').agg({'price': 'sum', 'order_id': 'nunique'})
    aov_geo['AOV'] = aov_geo['price'] / aov_geo['order_id']
    aov_geo = aov_geo.sort_values('AOV', ascending=False).head(10).reset_index()

    col_chart2, col_desc2 = st.columns([2, 1])

    with col_chart2:
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.barplot(x='AOV', y='customer_state', data=aov_geo, palette='flare', ax=ax)
        avg_aov = aov_geo['AOV'].mean()
        ax.axvline(avg_aov, color='red', linestyle='--', label='Rata-rata AOV')
        ax.set_title(f"AOV Wilayah - Kategori: {unggulan_name}", fontsize=14)
        st.pyplot(fig)

    with col_desc2:
        st.write(f"### 📈 Tren AOV {unggulan_name}")
        st.write(f"Kategori **{unggulan_name}** dipilih karena memiliki volume transaksi tertinggi.")
        st.success(f"**Kesimpulan:** Wilayah **{aov_geo.customer_state.iloc[0]}** memiliki nilai transaksi rata-rata tertinggi sebesar BRL {aov_geo.AOV.iloc[0]:,.2f}.")

# --- ANALISIS LANJUTAN (OPSIONAL): RFM ANALYSIS ---
    st.markdown("---")
    st.header("🎯 Analisis Lanjutan: RFM Analysis")
    st.markdown("Mengukur loyalitas pelanggan berdasarkan Recency (Kebaruan), Frequency (Frekuensi), dan Monetary (Nilai Ekonomi).")

    # Menghitung parameter RFM
    # Kita asumsikan 'customer_unique_id' sebagai identitas pelanggan
    rfm_df = main_df.groupby(by="customer_unique_id", as_index=False).agg({
        "order_purchase_timestamp": "max", # Mengambil tanggal order terakhir
        "order_id": "nunique",             # Menghitung jumlah order
        "price": "sum"                     # Menghitung total revenue
    })

    # Mengubah nama kolom
    rfm_df.columns = ["customer_id", "max_order_timestamp", "frequency", "monetary"]

    # Menghitung recency (dalam hari)
    recent_date = main_df["order_purchase_timestamp"].max()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days)
    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)

    # Tampilkan 3 Grafik RFM
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("By Recency (days)")
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.barplot(y="recency", x="customer_id", data=rfm_df.sort_values(by="recency", ascending=True).head(5), palette="mako", ax=ax)
        ax.set_xticks([]) # Sembunyikan ID pelanggan agar tidak berantakan
        st.pyplot(fig)

    with col2:
        st.subheader("By Frequency")
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.barplot(y="frequency", x="customer_id", data=rfm_df.sort_values(by="frequency", ascending=False).head(5), palette="mako", ax=ax)
        ax.set_xticks([])
        st.pyplot(fig)

    with col3:
        st.subheader("By Monetary")
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.barplot(y="monetary", x="customer_id", data=rfm_df.sort_values(by="monetary", ascending=False).head(5), palette="mako", ax=ax)
        ax.set_xticks([])
        st.pyplot(fig)

    st.info("💡 **Insight RFM:** Analisis ini menunjukkan siapa pelanggan paling berharga (Monetary tertinggi) dan pelanggan mana yang sudah lama tidak berbelanja (Recency tinggi).")
    
    st.markdown("---")
    st.caption("Copyright © 2026 | Analisis Data Egi Farhan")
