import streamlit as st
import requests

url = "http://127.0.0.1:8000" + "/predict"

st.title("🚕 TaxiFare")
st.write("Estimate the price of your taxi ride in New York.")

def main() -> None:
    print("Hello from taxifare-frontend!")


pickup_datetime = st.selectbox("Select your datetime", ["2013-10-23 17:00:00 UTC", "2013-10-23 17:30:00 UTC"])

pickup_longitude = st.slider("Select your pick-up longitude", min_value = -73.000000, max_value = -73.999999)
pickup_latitude = st.slider("Select your pick-up latitude", min_value = -40.000000, max_value = -40.999999)
dropoff_longitude = st.slider("Select your drop-off longitude", min_value = -73.000000, max_value = -73.999999)
dropoff_latitude = st.slider("Select your drop-off latitude", min_value = -40.000000, max_value = -40.999999)

passenger_count = st.selectbox("Number of passengers", [1, 2, 3, 4])

params = {
    "pickup_datetime" : pickup_datetime,
    "pickup_longitude" : pickup_longitude,
    "pickup_latitude" : pickup_latitude,
    "dropoff_longitude" : dropoff_longitude,
    "dropoff_latitude" : dropoff_latitude,
    "passenger_count" : passenger_count
}


if st.button("Calculate my fare", type="primary", use_container_width=True):
    with st.spinner("Calculating..."):
        response = requests.get(url, params=params)
        prediction = response.json()["fare"]

    st.divider()
    st.success(f"Your fare will cost ${prediction}!")
