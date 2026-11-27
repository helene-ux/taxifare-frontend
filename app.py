import streamlit as st
import requests
from geopy.geocoders import Photon
from streamlit_searchbox import st_searchbox
from datetime import datetime
from zoneinfo import ZoneInfo
import folium
from streamlit_folium import st_folium

@st.cache_data(ttl=3600)
def search_address(searchterm):

    if len(searchterm.strip()) < 3:
        return []

    locations = geolocator.geocode(
        searchterm + ", New York, USA",
        exactly_one=False,
        limit=5,
        bbox=[(40.49, -74.27), (40.92, -73.68)]
    )

    if not locations:
        return []

    return [
        (location.address, location)
        for location in locations
    ]

geolocator = Photon(user_agent="taxifare-frontend")

url = "https://taxifare-api-473520241787.europe-west1.run.app" + "/predict"

st.title("🚕 TaxiFare")
st.write("Estimate the price of your taxi ride in New York.")

#pickup_datetime = st.selectbox("Select your datetime", ["2013-10-23 17:00:00 UTC", "2013-10-23 17:30:00 UTC"])
col1, col2 = st.columns(2)

with col1:
    pickup_date = st.date_input("Pick-up date")

with col2:
    pickup_time = st.time_input("Pick-up time")

pickup_datetime = datetime.combine(pickup_date, pickup_time)

pickup_datetime = pickup_datetime.replace(
    tzinfo=ZoneInfo("America/New_York")
)

pickup_datetime = pickup_datetime.astimezone(ZoneInfo("UTC"))

pickup_datetime = pickup_datetime.strftime("%Y-%m-%d %H:%M:%S UTC")

pickup_location = st_searchbox(
    search_address,
    placeholder="Search for a pick-up address",
    label="Pick-up address",
    key="pickup"
)

dropoff_location = st_searchbox(
    search_address,
    placeholder="Search for a drop-off address",
    label="Drop-off address",
    key="dropoff"
)

passenger_count = st.selectbox("Number of passengers", [1, 2, 3, 4])

if st.button("Calculate my fare", type="primary", use_container_width=True):

    if pickup_location is None or dropoff_location is None:
        st.warning("Please select both addresses.")
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

    st_folium(taxi_map, width=700, height=450, returned_objects=[])
