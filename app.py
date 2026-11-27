import streamlit as st
import requests
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.exc import GeocoderServiceError
from datetime import datetime
from zoneinfo import ZoneInfo
import folium
from streamlit_folium import st_folium


# Geocoding
@st.cache_resource
def get_geocoder():
    geolocator = Nominatim(user_agent="taxifare-frontend")
    return RateLimiter(
        geolocator.geocode,
        min_delay_seconds=1,
        max_retries=0,
        swallow_exceptions=False
    )


@st.cache_data(ttl=3600)
def search_address(address):
    geocode = get_geocoder()

    return geocode(
        address.strip() + ", New York, USA",
        viewbox=[(40.49, -74.27), (40.92, -73.68)],
        bounded=True,
        timeout=10
    )


# API
url = "http://127.0.0.1:8000/predict"


# Interface
st.title("🚕 TaxiFare")
st.write("Estimate the price of your taxi ride in New York.")

col1, col2 = st.columns(2)

with col1:
    pickup_date = st.date_input("Pick-up date")

with col2:
    pickup_time = st.time_input("Pick-up time")


# Datetime conversion
pickup_datetime = datetime.combine(pickup_date, pickup_time)

pickup_datetime = pickup_datetime.replace(
    tzinfo=ZoneInfo("America/New_York")
)

pickup_datetime = pickup_datetime.astimezone(ZoneInfo("UTC"))

pickup_datetime = pickup_datetime.strftime("%Y-%m-%d %H:%M:%S UTC")


# Addresses
pickup_address = st.text_input(
    "Pick-up address",
    placeholder="Times Square"
)

dropoff_address = st.text_input(
    "Drop-off address",
    placeholder="Central Park"
)

passenger_count = st.selectbox(
    "Number of passengers",
    [1, 2, 3, 4]
)


# Fare prediction
if st.button("Calculate my fare", type="primary", use_container_width=True):

    if not pickup_address.strip() or not dropoff_address.strip():
        st.warning("Please enter both addresses.")
        st.stop()

    with st.spinner("Locating addresses..."):

        try:
            pickup_location = search_address(pickup_address)
            dropoff_location = search_address(dropoff_address)

        except GeocoderServiceError:
            st.error("The geocoding service is unavailable. Please try again later.")
            st.stop()

    if pickup_location is None or dropoff_location is None:
        st.warning("One or both addresses could not be found.")
        st.stop()

    with st.spinner("Calculating..."):

        params = {
            "pickup_datetime": pickup_datetime,
            "pickup_longitude": pickup_location.longitude,
            "pickup_latitude": pickup_location.latitude,
            "dropoff_longitude": dropoff_location.longitude,
            "dropoff_latitude": dropoff_location.latitude,
            "passenger_count": passenger_count
        }

        response = requests.get(url, params=params)
        prediction = response.json()["fare"]

    st.divider()
    st.success(f"Your estimated fare is ${prediction:.2f}!")


    # Map
    taxi_map = folium.Map(
        location=[pickup_location.latitude, pickup_location.longitude],
        zoom_start=13
    )

    folium.Marker(
        [pickup_location.latitude, pickup_location.longitude],
        tooltip="Pick-up",
        popup=pickup_location.address,
        icon=folium.Icon(color="green")
    ).add_to(taxi_map)

    folium.Marker(
        [dropoff_location.latitude, dropoff_location.longitude],
        tooltip="Drop-off",
        popup=dropoff_location.address,
        icon=folium.Icon(color="red")
    ).add_to(taxi_map)


    # Route
    routing_url = (
        "https://router.project-osrm.org/route/v1/driving/"
        f"{pickup_location.longitude},{pickup_location.latitude};"
        f"{dropoff_location.longitude},{dropoff_location.latitude}"
    )

    route_response = requests.get(
        routing_url,
        params={"overview": "full", "geometries": "geojson"},
        timeout=10
    )

    route_data = route_response.json()

    if route_data.get("code") == "Ok":

        coordinates = route_data["routes"][0]["geometry"]["coordinates"]

        route_points = [(lat, lon) for lon, lat in coordinates]

        folium.PolyLine(
            route_points,
            color="blue",
            weight=5,
            opacity=0.8
        ).add_to(taxi_map)

    taxi_map.fit_bounds([
        [pickup_location.latitude, pickup_location.longitude],
        [dropoff_location.latitude, dropoff_location.longitude]
    ])

    st_folium(
        taxi_map,
        width=700,
        height=450,
        returned_objects=[]
    )
