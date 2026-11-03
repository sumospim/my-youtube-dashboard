import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Multi-Channel YouTube Dashboard", layout="wide")
st.title("📊 Multi-Channel YouTube Video Analytics")

# !!! PASTE YOUR WORKING GOOGLE API KEY INSIDE THE QUOTES BELOW !!!
API_KEY = "AIzaSyA7Ufwzrb6MW5_YGOm3-QfmgPFnim6cnpg"

st.sidebar.header("⚙️ Dashboard Controls")

# Pre-loading your 4 exact channels into the default layout (with the case fix!)
default_channels = (
    "UCwvRev1mcushXXvbV8jEw7A\n"
    "UC416jGn4iRn5O_GMBY1WWpg\n"
    "UC0gbOyT2CQQn4BFxZtIJtCg\n"
    "UCIZ6GXgT9nbtZc5BWTfNuEg"
)

id_input = st.sidebar.text_area(
    "Paste your YouTube Channel IDs here (One ID per line):",
    value=default_channels
)

channel_ids = [line.strip() for line in id_input.split("\n") if line.strip()]

@st.cache_data(ttl=600)
def get_all_videos(api_key, id_list):
    if not id_list:
        return pd.DataFrame()
    
    youtube = build('youtube', 'v3', developerKey=api_key)
    all_videos = []
    
    for cid in id_list:
        try:
            # 1. Get Channel Name
            ch_req = youtube.channels().list(part="snippet", id=cid)
            ch_res = ch_req.execute()
            if not ch_res.get('items'):
                continue
            channel_name = ch_res['items']['snippet']['title']
            
            # 2. Get latest 50 videos from this channel
            search_req = youtube.search().list(
                part="snippet",
                channelId=cid,
                maxResults=50,
                type="video",
                order="date"
            )
            search_res = search_req.execute()
            
            video_ids = [item['id']['videoId'] for item in search_res.get('items', [])]
            
            if video_ids:
                # 3. Get exact stats (Views, Likes, Comments) for those videos
                stats_req = youtube.videos().list(
                    part="statistics,snippet",
                    id=",".join(video_ids)
                )
                stats_res = stats_req.execute()
                
                for v_item in stats_res.get('items', []):
                    all_videos.append({
                        'Channel': channel_name,
                        'Title': v_item['snippet']['title'],
                        'Published At': pd.to_datetime(v_item['snippet']['publishedAt']).strftime('%Y-%m-%d'),
                        'Views': int(v_item['statistics'].get('viewCount', 0)),
                        'Likes': int(v_item['statistics'].get('likeCount', 0)),
                        'Comments': int(v_item['statistics'].get('commentCount', 0)),
                        'Link': f"https://youtube.com{v_item['id']}"
                    })
        except Exception as e:
            st.error(f"Error reading channel {cid}: {e}")
            
    return pd.DataFrame(all_videos)

if not channel_ids:
    st.info("Please type or paste at least one Channel ID in the sidebar.")
else:
    try:
        df_videos = get_all_videos(API_KEY, channel_ids)
        
        if not df_videos.empty:
            # Dropdown interactive filter to look at one specific channel or ALL at once
            channel_options = ["All Channels"] + list(df_videos['Channel'].unique())
            selected_channel = st.selectbox("🎯 Filter Dashboard by Channel:", channel_options)
            
            filtered_df = df_videos if selected_channel == "All Channels" else df_videos[df_videos['Channel'] == selected_channel]
            
            # Chart 1: Top Performing Videos Across channels
            st.subheader("🔥 Top Videos by View Count")
            top_vids = filtered_df.sort_values(by="Views", ascending=False).head(15)
            fig = px.bar(top_vids, x='Views', y='Title', color='Channel', orientation='h', 
                         title="Top 15 Most Viewed Videos", text_auto='.s')
            fig.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
            
            # Master Interactive List
            st.subheader("📋 Complete Video Catalog List")
            st.markdown("*Click on any column header (like **Views**) to instantly sort from highest to lowest!*")
            
            # Display clean data table with links
            st.dataframe(
                filtered_df.sort_values(by="Views", ascending=False),
                column_config={
                    "Link": st.column_config.LinkColumn("Watch Video")
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.error("No videos found. Check your configuration or API quota rules.")
            
    except Exception as e:
        st.error(f"Error: {e}")
