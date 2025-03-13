import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

st.set_page_config(page_title="Dashboard Utama",layout="wide")

# --- Load Data from Google Sheets ---
scope = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
client = gspread.authorize(creds)

sheet_id = "1RIW01gtWUobcaug5KtkmNC3KEeGgcAJ-6dKmk-VamTY"
sheet = client.open_by_key(sheet_id)
worksheet = sheet.sheet1
data = worksheet.get_all_records()
df = pd.DataFrame(data)

# Convert Date column
df['Date'] = pd.to_datetime(df['Date'])
df['Status'] = df['Status'].astype(str).str.title()
df['Nama Perusahaan'] = df['Nama Perusahaan'].astype(str).str.upper()

# --- Sidebar Filters ---
st.sidebar.header("🔍 Filter Data")

# 1. Date Range Filter
min_date = df['Date'].min()
max_date = df['Date'].max()

start_date = st.sidebar.date_input("Start Date", min_date)
end_date = st.sidebar.date_input("End Date", max_date)

# 2. Nama Perusahaan Filter
company_options = ['All'] + sorted(df['Nama Perusahaan'].dropna().unique().tolist())
selected_companies = st.sidebar.multiselect("Nama Perusahaan", company_options, default=['All'])

# 3. Ekspor / Impor Filter
ekspor_options = ['All'] + sorted(df['Ekspor / Impor'].dropna().unique().tolist())
selected_ekspor = st.sidebar.multiselect("Ekspor / Impor", ekspor_options, default=['All'])

# 4. 20 Feet / 40 Feet Filter
container_options = ['All'] + sorted(df['20 Feet / 40 Feet'].dropna().unique().tolist())
selected_container = st.sidebar.multiselect("20 Feet / 40 Feet", container_options, default=['All'])

st.sidebar.markdown("---")
st.sidebar.page_link("pages/Status.py", label="➡️ Cek Status Driver")

# Filter by Date range
df_filtered = df[
    (df['Date'] >= pd.to_datetime(start_date)) &
    (df['Date'] <= pd.to_datetime(end_date))
]

# Filter Nama Perusahaan
if 'All' not in selected_companies:
    df_filtered = df_filtered[df_filtered['Nama Perusahaan'].isin(selected_companies)]

# Filter Ekspor / Impor
if 'All' not in selected_ekspor:
    df_filtered = df_filtered[df_filtered['Ekspor / Impor'].isin(selected_ekspor)]

# Filter 20 Feet / 40 Feet
if 'All' not in selected_container:
    df_filtered = df_filtered[df_filtered['20 Feet / 40 Feet'].isin(selected_container)]

df = df_filtered


st.markdown("""
    <style>
        .metric-container {
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 15px;
            border-radius: 10px;
            min-width: 150px;
            min-height: 100px;
            color: white;
        }
        .confirm-bg { background-color: #007BFF; } /* Blue */
        .opportunity-bg { background-color: #28A745; } /* Green */
        .weak-bg { background-color: #DC3545; } /* Red */
        .metric-title { font-size: 24px; font-weight: bold; }
        .metric-value { font-size: 20px; font-weight: bold; }
        .metric-delta { font-size: 20px; opacity: 0.8; }
    </style>
""", unsafe_allow_html=True)


# with col2:
#     st.markdown(f"""
#         <div class='metric-container opportunity-bg'>
#             <div class='metric-title'>Opportunity</div>
#             <div class='metric-value'>{count_opportunity}</div>
#             <div class='metric-delta'>{formatted_fee_opportunity}</div>
#         </div>
#     """, unsafe_allow_html=True)

# with col3:
#     st.markdown(f"""
#         <div class='metric-container weak-bg'>
#             <div class='metric-title'>Weak</div>
#             <div class='metric-value'>{count_weak}</div>
#             <div class='metric-delta'>{formatted_fee_weak}</div>
#         </div>
#     """, unsafe_allow_html=True)
    
    
now = datetime.now()
current_month = now.month
current_year = now.year

if current_month == 1:
    last_month = 12
    last_year = current_year - 1
else:
    last_month = current_month - 1
    last_year = current_year

# Filter BEFORE grouping
df_selesai = df[df['Status'] == 'Selesai']

df_this_month = df_selesai[
    (df_selesai['Date'].dt.month == current_month) &
    (df_selesai['Date'].dt.year == current_year)
]

df_last_month = df_selesai[
    (df_selesai['Date'].dt.month == last_month) &
    (df_selesai['Date'].dt.year == last_year)
]

# Group and count
total_this_month = df_this_month['Driver'].count()
total_last_month = df_last_month['Driver'].count()

# Percentage change
# Safely calculate change_value and handle None or NaN
try:
    change_value = total_this_month - total_last_month
    if pd.isna(change_value):
        change_value = 0
except:
    change_value = 0

if total_last_month == 0:
    percentage_change = "∞%" if total_this_month > 0 else "0%"
else:
    percentage_change = f"{(change_value / total_last_month) * 100:.1f}%"

col1, col2, col3 = st.columns([0.5, 0.5, 0.5])
# Determine color and icon
if change_value > 0:
    delta_color = "green"
    delta_icon = "▲"
elif change_value < 0:
    delta_color = "red"
    delta_icon = "▼"
else:
    delta_color = "gray"
    delta_icon = "•"

# Combine display text
delta_display = f"{delta_icon} {percentage_change} ({change_value:+})"
delta_color = "green" if change_value >= 0 else "red"

# Safely handle if df_this_month is empty
if not df_this_month.empty:
    unique_company_this_month = df_this_month['Nama Perusahaan'].nunique()
    top_company = df_this_month['Nama Perusahaan'].value_counts().idxmax()
    
    unique_plat_this_month = df_this_month['Plat'].nunique()
    top_plat = df_this_month['Plat'].value_counts().idxmax()
else:
    unique_company_this_month = 0
    top_company = "No Data"
    unique_plat_this_month = 0
    top_plat = "No Data"

# Display Cards
with col1:
    st.markdown(f"""
        <div class='metric-container confirm-bg'>
            <div class='metric-title'>Total Selesai</div>
            <div class='metric-value'>{total_this_month}</div>
            <div class='metric-delta' style='color:{delta_color};'>{delta_display}</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
        <div class='metric-container confirm-bg'>
            <div class='metric-title'>Total Perusahaan</div>
            <div class='metric-value'>{unique_company_this_month}</div>
            <div class='metric-delta'>{top_company}</div>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
        <div class='metric-container confirm-bg'>
            <div class='metric-title'>Total Mobil</div>
            <div class='metric-value'>{unique_plat_this_month}</div>
            <div class='metric-delta'>{top_plat}</div>
        </div>
    """, unsafe_allow_html=True)

# Colors
warm_green = '#88B04B'
color_map = {
    'Green': '#88B04B',
    'Yellow': '#FFD700',
    'Red': '#D94F4F'
}

# --- Line Chart: Status 'Selesai' Over Time ---
df_grouped = df.groupby(['Date', 'Status'])['Driver'].count().reset_index(name='Count')
df_selesai_time = df_grouped[df_grouped['Status'] == 'Selesai']

fig_line = px.line(
    df_selesai_time,
    x='Date',
    y='Count',
    # title='📈 Selesai Status Over Time',
    color_discrete_sequence=[warm_green]
)
fig_line.update_layout(
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    xaxis=dict(
        rangeselector=dict(
            buttons=list([
                dict(count=7, label="7d", step="day", stepmode="backward"),
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=3, label="3m", step="month", stepmode="backward"),
                dict(step="all")
            ])
        ),
        rangeslider=dict(visible=True, bgcolor='#e5ecf6'),
        type="date"
    )
)

# --- Bar Chart: Top 10 Drivers with 'Selesai' Status ---
top_drivers = df[df['Status'] == 'Selesai']['Name'].value_counts().nlargest(10).reset_index()
top_drivers.columns = ['Name', 'Total Selesai']

fig_driver = px.bar(
    top_drivers,
    x='Name',
    y='Total Selesai',
    # title='🧑‍✈️ Top 10 Drivers with Most Selesai Status',
    text='Total Selesai',
    color_discrete_sequence=[warm_green]
)
fig_driver.update_layout(
    xaxis_tickangle=-45,
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    xaxis_title='Driver Name',
    yaxis_title='Total Selesai'
)
fig_driver.update_traces(marker_line_color='black', marker_line_width=1)

# --- Bar Chart: Top 10 Plat and Perusahaan ---
df_selesai = df[df['Status'] == 'Selesai']

top_plat = df_selesai['Plat'].value_counts().nlargest(10).reset_index()
top_plat.columns = ['Plat', 'Total Selesai']

fig_top_plat = px.bar(
    top_plat,
    x='Plat',
    y='Total Selesai',
    # title='🚘 Top 10 Plat with Selesai Status',
    text='Total Selesai',
    color_discrete_sequence=[warm_green]
)
fig_top_plat.update_traces(marker_line_color='black', marker_line_width=1)

top_perusahaan = df_selesai.groupby('Nama Perusahaan').size().nlargest(10).reset_index(name='Total Selesai')

fig_perusahaan = px.bar(
    top_perusahaan,
    x='Nama Perusahaan',
    y='Total Selesai',
    # title='🏢 Top 10 Perusahaan with Selesai Status',
    text='Total Selesai',
    color_discrete_sequence=[warm_green]
)
fig_perusahaan.update_traces(marker_line_color='black', marker_line_width=1)

# --- Pie Chart: Status Color Distribution ---
status_color_grouped = df.groupby('Status Color')['Driver'].count().reset_index(name='Count')

fig_pie = px.pie(
    status_color_grouped,
    names='Status Color',
    values='Count',
    color='Status Color',
    color_discrete_map=color_map
)

fig_pie.update_traces(textinfo='label+percent', pull=[0.05] * len(status_color_grouped))
fig_pie.update_layout(showlegend=False)

Export = df.groupby('Ekspor / Impor')['Driver'].count().reset_index(name='Count')

fig_import = px.pie(
    Export,
    names='Ekspor / Impor',
    values='Count',
    color='Ekspor / Impor',
)

fig_import.update_traces(textinfo='label+percent', pull=[0.05] * len(status_color_grouped))
fig_import.update_layout(showlegend=False)

feet = df.groupby('20 Feet / 40 Feet')['Driver'].count().reset_index(name='Count')

fig_feet = px.pie(
    feet,
    names='20 Feet / 40 Feet',
    values='Count',
    color='20 Feet / 40 Feet',
)

fig_feet.update_traces(textinfo='label+percent', pull=[0.05] * len(status_color_grouped))
fig_feet.update_layout(showlegend=False)

st.subheader("📈 Selesai Status")
with st.container(border=True):
        st.plotly_chart(fig_line, use_container_width=True)
        
# --- Layout Rendering ---
col1, col2 = st.columns([0.5, 0.5])

with col1:
    st.subheader("🧑‍✈️Top 10")
    with st.container(border=True):
        tab1, tab2, tab3 = st.tabs(["Top Drivers", "Plat", "Perusahaan"])
        with tab1:
            st.plotly_chart(fig_driver, use_container_width=True)

        with tab2:
        
            st.plotly_chart(fig_top_plat, use_container_width=True)
            
        with tab3:
        
            st.plotly_chart(fig_perusahaan, use_container_width=True)

with col2:
    st.subheader("Presentase")
    with st.container(border=True):
        tab4, tab5, tab6 = st.tabs(["Color", "Ekspor / Impor", "20 Feet / 40 Feet"])
        with tab4:
            st.plotly_chart(fig_pie, use_container_width=True)
        with tab5:
            st.plotly_chart(fig_import, use_container_width=True)
        with tab6:
            st.plotly_chart(fig_feet, use_container_width=True)
