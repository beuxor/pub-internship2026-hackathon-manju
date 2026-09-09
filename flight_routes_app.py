import os
import streamlit as st
import pydeck as pdk
import pandas as pd

st.set_page_config(page_title="US Flight Routes Map", layout="wide")
st.title("US Flight Routes Map")

connection_name = os.getenv("SNOWFLAKE_DEFAULT_CONNECTION_NAME") or "default"
conn = st.connection("snowflake", connection_name=connection_name)


@st.cache_data(ttl=600)
def load_dates():
    df = conn.query("""
        SELECT DISTINCT DATE
        FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.US_DEPARTMENT_OF_TRANSPORTATION_TIMESERIES
        WHERE VARIABLE_NAME = 'Non-Stop Segment Passengers Transported'
        ORDER BY DATE DESC
    """)
    return df["DATE"].tolist()


@st.cache_data(ttl=600)
def load_carriers(selected_date):
    df = conn.query(f"""
        SELECT DISTINCT c.CARRIER_NAME
        FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.US_DEPARTMENT_OF_TRANSPORTATION_TIMESERIES t
        JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.AIRCRAFT_CARRIER_INDEX c
          ON t.AIRCRAFT_CARRIER_ID = c.AIRCRAFT_CARRIER_ID
        WHERE t.VARIABLE_NAME = 'Non-Stop Segment Passengers Transported'
          AND t.DATE = '{selected_date}'
        ORDER BY c.CARRIER_NAME
    """)
    return df["CARRIER_NAME"].tolist()


@st.cache_data(ttl=600)
def load_routes(selected_date, carrier_name, top_n):
    df = conn.query(f"""
        SELECT
            o.AIRPORT_NAME        AS ORIGIN_NAME,
            o.AIRPORT_ALPHA_CODE  AS ORIGIN_IATA,
            o.AIRPORT_LATITUDE    AS ORIGIN_LAT,
            o.AIRPORT_LONGITUDE   AS ORIGIN_LON,
            d.AIRPORT_NAME        AS DEST_NAME,
            d.AIRPORT_ALPHA_CODE  AS DEST_IATA,
            d.AIRPORT_LATITUDE    AS DEST_LAT,
            d.AIRPORT_LONGITUDE   AS DEST_LON,
            c.CARRIER_NAME,
            t.VALUE               AS PASSENGERS
        FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.US_DEPARTMENT_OF_TRANSPORTATION_TIMESERIES t
        JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.AIRPORT_INDEX o
          ON t.ORIGIN_AIRPORT_ID = o.AIRPORT_ID
        JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.AIRPORT_INDEX d
          ON t.DESTINATION_AIRPORT_ID = d.AIRPORT_ID
        JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.AIRCRAFT_CARRIER_INDEX c
          ON t.AIRCRAFT_CARRIER_ID = c.AIRCRAFT_CARRIER_ID
        WHERE t.VARIABLE_NAME = 'Non-Stop Segment Passengers Transported'
          AND t.DATE = '{selected_date}'
          AND c.CARRIER_NAME = '{carrier_name}'
          AND o.AIRPORT_LATITUDE IS NOT NULL
          AND d.AIRPORT_LATITUDE IS NOT NULL
        ORDER BY t.VALUE DESC
        LIMIT {top_n}
    """)
    return df


dates = load_dates()

col1, col2, col3 = st.columns(3)
with col1:
    selected_date = st.selectbox("Month", dates, index=0)
with col2:
    carriers = load_carriers(selected_date)
    default_carrier = carriers.index("Southwest Airlines Co.") if "Southwest Airlines Co." in carriers else 0
    carrier = st.selectbox("Airline", carriers, index=default_carrier)
with col3:
    top_n = st.slider("Top N routes", min_value=10, max_value=200, value=50, step=10)

routes = load_routes(selected_date, carrier, top_n)

if routes.empty:
    st.warning("No routes found for this selection.")
    st.stop()

st.caption(f"Showing top {len(routes)} routes for **{carrier}** in **{selected_date}**")

max_pax = routes["PASSENGERS"].max()
routes["norm"] = routes["PASSENGERS"] / max_pax

airports_origin = routes[["ORIGIN_NAME", "ORIGIN_IATA", "ORIGIN_LAT", "ORIGIN_LON"]].rename(
    columns={"ORIGIN_NAME": "name", "ORIGIN_IATA": "iata", "ORIGIN_LAT": "lat", "ORIGIN_LON": "lon"}
)
airports_dest = routes[["DEST_NAME", "DEST_IATA", "DEST_LAT", "DEST_LON"]].rename(
    columns={"DEST_NAME": "name", "DEST_IATA": "iata", "DEST_LAT": "lat", "DEST_LON": "lon"}
)
airports = pd.concat([airports_origin, airports_dest]).drop_duplicates(subset=["iata"])

arc_layer = pdk.Layer(
    "ArcLayer",
    data=routes,
    get_source_position=["ORIGIN_LON", "ORIGIN_LAT"],
    get_target_position=["DEST_LON", "DEST_LAT"],
    get_source_color=[0, 128, 255, 160],
    get_target_color=[255, 80, 80, 160],
    get_width="norm * 4 + 1",
    pickable=True,
    auto_highlight=True,
)

scatter_layer = pdk.Layer(
    "ScatterplotLayer",
    data=airports,
    get_position=["lon", "lat"],
    get_radius=30000,
    get_fill_color=[41, 181, 232, 200],
    pickable=True,
    auto_highlight=True,
)

text_layer = pdk.Layer(
    "TextLayer",
    data=airports,
    get_position=["lon", "lat"],
    get_text="iata",
    get_size=12,
    get_color=[255, 255, 255, 220],
    get_alignment_baseline="'bottom'",
    get_pixel_offset=[0, -15],
)

view_state = pdk.ViewState(
    latitude=39.0,
    longitude=-98.0,
    zoom=3.5,
    pitch=30,
)

deck = pdk.Deck(
    layers=[arc_layer, scatter_layer, text_layer],
    initial_view_state=view_state,
    tooltip={
        "text": "{ORIGIN_IATA} → {DEST_IATA}\nPassengers: {PASSENGERS}"
    },
    map_style="mapbox://styles/mapbox/dark-v10",
)

st.pydeck_chart(deck, use_container_width=True, height=650)

col_a, col_b = st.columns(2)
with col_a:
    st.subheader("Top Routes")
    display_df = routes[["ORIGIN_IATA", "DEST_IATA", "PASSENGERS"]].copy()
    display_df.columns = ["Origin", "Destination", "Passengers"]
    display_df["Passengers"] = display_df["Passengers"].astype(int)
    st.dataframe(display_df, use_container_width=True, hide_index=True)
with col_b:
    st.subheader("Airports")
    st.metric("Unique airports", len(airports))
    st.metric("Total passengers", f"{int(routes['PASSENGERS'].sum()):,}")
