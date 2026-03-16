import streamlit as st
import pymongo
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure the dashboard layout
st.set_page_config(page_title="Smart Dustbin Dashboard", page_icon="♻️", layout="wide")
st.title("♻️ Automated Waste Segregation Dashboard")

# Connect to MongoDB (cached so it doesn't reconnect on every button click)
@st.cache_resource
def init_connection():
    MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    return pymongo.MongoClient(MONGO_URI)

try:
    client = init_connection()
    db = client.smart_dustbin
    collection = db.sensor_readings
    
    # Fetch all data
    cursor = collection.find()
    data = list(cursor)

    if data:
        # Convert MongoDB data to a Pandas DataFrame for easy charting
        df = pd.DataFrame(data)
        
        # --- Top Metrics Row ---
        st.subheader("Today's Overview")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Items Processed", len(df))
        col2.metric("🔵 Plastics", len(df[df['waste_category'] == 'Plastic']))
        col3.metric("🧲 Metals", len(df[df['waste_category'] == 'Metal']))
        col4.metric("🟤 Other Waste", len(df[df['waste_category'] == 'Other']))
        
        st.markdown("---")
        
        # --- Charts & Tables Row ---
        chart_col, table_col = st.columns(2)
        
        with chart_col:
            st.subheader("Waste Distribution")
            category_counts = df['waste_category'].value_counts()
            st.bar_chart(category_counts)
            
        with table_col:
            st.subheader("Live Sensor Feed")
            # Drop the MongoDB internal ID before displaying
            display_df = df.drop(columns=['_id'])
            st.dataframe(display_df.tail(10), use_container_width=True)
            
    else:
        st.info("📡 Database connected, but no data found. Waiting for ESP32 to send waste logs...")

except Exception as e:
    st.error(f"Failed to connect to MongoDB. Error: {e}")