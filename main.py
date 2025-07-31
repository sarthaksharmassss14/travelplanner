import streamlit as st
from dotenv import load_dotenv
import requests
import os
import google.generativeai as genai
import streamlit.components.v1 as components
import base64
import time
import re
from planner import generate_itinerary, get_cost_estimates
from utils import get_weather_info


def clean_asterisks(text):
    text = re.sub(r'^\s*\*+\s*', '- ', text, flags=re.MULTILINE)
    text = re.sub(r'\*\*\*(.*?)\*\*\*', r'\1', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = text.replace('*', '')
    return text

# === LOAD ENV VARIABLES ===
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

# === PAGE SETUP ===
st.set_page_config(page_title="Travel Planner", layout="wide")
st.markdown("""
    <h1 style='
        text-align: center;
        font-size: 45px;
        background: -webkit-linear-gradient(45deg, #ff4b1f, #1fddff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: "Segoe UI", sans-serif;
    '>
        ✨ Your Next Trip Starts Here ✨
    </h1>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center;'>🌍 AI Travel Planner</h1>", unsafe_allow_html=True)
st.markdown("### Plan your custom trip with AI suggestions.")

# === INPUT FORM ===
with st.form("trip_form"):
    col1, col2 = st.columns(2)
    with col1:
        source_city = st.text_input("🏁Source City (correct spelling please)")
        
        days = st.number_input("📅Number of days", min_value=1, max_value=30)
        interests = st.text_input("💡Your interests (e.g., nature, food, history)")
    with col2:
        destination = st.text_input("📍Destination (correct spelling please)")
        travel_style = st.selectbox("🧭Travel style", ["Budget", "Mid-range", "Luxury"], index=0)
    submitted = st.form_submit_button("Generate Itinerary")



def fetch_destination_images(destination, count=5):
    headers = {
        "Authorization": PEXELS_API_KEY
    }

    # Focused keywords that yield clean architectural/landscape results
    keywords = ["fort", "palace", "landmark", "cityscape", "skyline", "architecture", "aerial view", "landscape"]
    queries = [f"{destination} {kw}" for kw in keywords]

    image_urls = []

    for query in queries:
        response = requests.get(
            "https://api.pexels.com/v1/search",
            params={
                "query": query,
                "per_page": 1,
                "orientation": "landscape"
            },
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            photos = data.get("photos", [])
            for photo in photos:
                image_urls.append(photo["src"]["large"])
                if len(image_urls) >= count:
                    break

        if len(image_urls) >= count:
            break

    return image_urls


# === ITINERARY GENERATION ===
if submitted:
    with st.spinner("🛫 Generating your personalized travel experience..."):
        time.sleep(2)
        try:
            # === Display destination images ===
            image_urls = fetch_destination_images(destination, count=5)

            if image_urls:
                st.markdown(f"### 📸 Slideshow of {destination} (using PEXELS)")
                slideshow_html = f"""
                    <div style="max-width: 700px; margin: auto; border-radius: 10px; overflow: hidden;">
                        <img id="slide" src="{image_urls[0]}" style="width: 100%; height: 400px; object-fit: cover; border-radius: 10px;">
                    </div>
                    <script>
                        const photos = {image_urls};
                        let index = 0;
                        setInterval(() => {{
                            index = (index + 1) % photos.length;
                            document.getElementById("slide").src = photos[index];
                        }}, 1500);
                    </script>
                """
                components.html(slideshow_html, height=420)
            else:
                st.warning("No safe images found for this destination.")

            # === Generate Gemini Itinerary with embedded costs ===
            with st.spinner("✈️ Generating itinerary (may take a minute)..."):
                cost_str, itinerary_str = generate_itinerary(destination, days, source_city, interests, travel_style)

            # === Add emojis dynamically ===
            def add_emojis(text):
                emoji_map = {
                    "hiking": "🥾", "beach": "🏖️", "museum": "🏛️", "temple": "🛕", "castle": "🏰",
                    "food": "🍜", "mountain": "⛰️", "shopping": "🛍️", "waterfall": "💧", "sunset": "🌇",
                    "nature": "🌿", "road trip": "🚗", "trek": "🥾", "kayak": "🛶", "spa": "💆",
                    "wine": "🍷", "boat": "⛵", "photography": "📸"
                }
                for keyword, emoji in emoji_map.items():
                    text = text.replace(keyword, f"{emoji} {keyword}")
                return text

            emoji_itinerary = add_emojis(itinerary_str)

            # === Display Itinerary ===
            st.markdown("### 📅 Itinerary")
            day_blocks = emoji_itinerary.split("### Day")

            for i, block in enumerate(day_blocks):
                if not block.strip():
                    continue
                day_title = f"Day {i}" if i > 0 else "Here is your personalised trip"
                with st.expander(f"📌 {day_title}"):
                    st.markdown("### " + block.strip().split("\n")[0])  # Subtitle
                    for line in block.strip().split("\n")[1:]:
                        if line.strip():
                            st.markdown(f"- {line.strip()}")

            # === Estimated Cost ===
            st.markdown("### 💰 Estimated Cost")
            st.markdown(clean_asterisks(cost_str))

            # === Weather Section ===
            weather_data, error = get_weather_info(destination)

            st.markdown("### 🌦️ Weather Forecast")
            if error:
                st.warning(error)
            elif weather_data:
                weather_card_html = f"""
                <div style="
                    background-color:#303134;
                    color:#F8FFFF;
                    border-radius: 1rem;
                    padding: 1.5rem;
                    font-family: Arial, sans-serif;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    margin-top: 2rem;
                    width: 100%;
                ">
                    <h4 style="font-size: 1.5rem; margin-bottom: 0.5rem;">📍 {destination.title()}</h4>
                    <p style="margin: 0.3rem 0;"><strong>🌤️ {weather_data['description']}</strong>, {weather_data['temperature']}°C</p>
                    <p style="margin: 0.3rem 0;">🤗 Feels like: {weather_data['feelslike']}°C</p>
                    <p style="margin: 0.3rem 0;">💧 Humidity: {weather_data['humidity']}% &nbsp; | &nbsp; 🌬️ Wind: {weather_data['wind_speed']} km/h</p>
                </div>
                """
                st.markdown(weather_card_html, unsafe_allow_html=True)
            else:
                st.info("Weather info not available.")

            
        except Exception as e:
            st.error(f"Something went wrong: {e}")
