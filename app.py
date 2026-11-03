import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import plotly.express as px

# 1. Page Configuration
st.set_page_config(page_title="Multi-Channel YouTube Dashboard", layout="wide")
st.title("📊 Multi-Channel YouTube Analytics Hub")

# !!! PASTE YOUR GOOGLE API KEY INSIDE THE QUOTES BELOW !!!
API_KEY = "AizaSyBH7K7rtWUHQtldCj6JqfyHwrDOww5iEbw"

# 2. Easy UI Input for Channel IDs
st.sidebar.header("⚙️ Dashboard Controls")
id_input = st.sidebar.text_area(
    "Paste your YouTube Channel IDs here (One ID per line):",
    value="UCX6OQ3DkcsbYNE6H8uQQuVA\nUCBJycsmduvYEL83R_U4JriQ\nUCHnyfMqiRRG1u-2MsSQLbXA"
)

# Convert text box lines into a clean list
channel_ids = [line.strip() for line in id_input.split("\n") if line.strip()]

@st.cache_data(ttl=600) # Caches data for 10 mins to save your API limits
def get_multi_channel_stats(api_key, id_list):
    if not id_list:
        return pd.DataFrame()
    youtube = build('youtube', 'v3', developerKey=api_key)
    request = youtube.channels().list(
        part="snippet,statistics",
        id=",".join(id_list)
    )
    response = request.execute()
    
    all_data = []
    for item in response.get('items', []):
        all_data.append({
            'Channel': item['snippet']['title'],
            'Subscribers': int(item['statistics']['subscriberCount']),
            'Total Views': int(item['statistics']['viewCount']),
            'Total Videos': int(item['statistics']['videoCount']),
            'Avg Views/Video': int(int(item['statistics']['viewCount']) / int(item['statistics']['videoCount']))
        })
    return pd.DataFrame(all_data)

# 3. Build UI Layout
if API_KEY == "AizaSyBH7K7rtWUHQtldCj6JqfyHwrDOww5iEbw" or not API_KEY:
    st.warning("Please replace 'PASTE_YOUR_ACTUAL_GOOGLE_KEY_HERE' on line 10 of your app.py with your real Google key.")
elif not channel_ids:
    st.info("Please type or paste at least one Channel ID in the sidebar.")
else:
    try:
        df = get_multi_channel_stats(API_KEY, channel_ids)
        
        if not df.empty:
            # Row 1: Unified Comparison Grid
            st.subheader("⚡ Quick Compare")
            cols = st.columns(len(df))
            for idx, row in df.iterrows():
                with cols[idx]:
                    st.info(f"### {row['Channel']}")
                    st.metric("Subscribers", f"{row['Subscribers']:,}")
                    st.metric("Total Views", f"{row['Total Views']:,}")
                    st.metric("Avg Views per Video", f"{row['Avg Views/Video']:,}")

            st.markdown("---")
            
            # Row 2: Live Charts
            st.subheader("📈 Visual Benchmarks")
            chart_col1, chart_col2 = st.columns(2)
            
            with chart_col1:
                fig_subs = px.bar(df, x='Channel', y='Subscribers', color='Channel', title="Subscriber Comparison")
                st.plotly_chart(fig_subs, use_container_width=True)
                
            with chart_col2:
                fig_views = px.bar(df, x='Channel', y='Avg Views/Video', color='Channel', title="Channel Efficiency (Avg Views / Video)")
                st.plotly_chart(fig_views, use_container_width=True)

            # Row 3: Raw Table
            st.subheader("📋 Master Data Table")
            st.dataframe(df.set_index('Channel'), use_container_width=True)
        else:
            st.error("No data found. Please double-check that your Channel IDs are correct.")
        
    except Exception as e:
        st.error(f"Failed to fetch YouTube stats: {e}")
