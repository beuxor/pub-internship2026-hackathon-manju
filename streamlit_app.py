import math
import random
import streamlit as st
import pydeck as pdk
import pandas as pd
import numpy as np

st.set_page_config(page_title="都市当てゲーム", layout="wide")
conn = st.connection("snowflake")

DISTANCE_THRESHOLD_KM = 150


def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.asin(math.sqrt(a))


@st.cache_data
def build_click_grid():
    rows = []
    for lat in np.arange(24.0, 50.25, 0.5):
        for lon in np.arange(-125.0, -65.25, 0.5):
            rows.append({"lat": round(float(lat), 1), "lon": round(float(lon), 1)})
    return pd.DataFrame(rows)


@st.cache_data(ttl=3600)
def load_city_pool():
    df = conn.query("""
        WITH cities AS (
            SELECT gi.GEO_ID, gi.GEO_NAME AS CITY_NAME, pop.VALUE AS POPULATION
            FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.GEOGRAPHY_INDEX gi
            JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.DATACOMMONS_TIMESERIES pop
                ON gi.GEO_ID = pop.GEO_ID
                AND pop.VARIABLE_NAME = 'Total population, census.gov'
                AND pop.DATE = '2020-01-01'
            WHERE gi.LEVEL = 'City' AND pop.VALUE > 100000
        )
        SELECT
            c.GEO_ID, c.CITY_NAME, c.POPULATION,
            gi_state.GEO_NAME AS STATE_NAME
        FROM cities c
        JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.GEOGRAPHY_HIERARCHY gh
            ON c.GEO_ID = gh.GEO_ID
        JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.GEOGRAPHY_INDEX gi_state
            ON gh.PARENT_GEO_ID = gi_state.GEO_ID AND gi_state.LEVEL = 'State'
        ORDER BY c.POPULATION DESC
    """)
    return df.drop_duplicates(subset=["GEO_ID"])


@st.cache_data(ttl=3600)
def load_city_details(geo_id):
    stats = conn.query(f"""
        SELECT VARIABLE_NAME, VALUE
        FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.DATACOMMONS_TIMESERIES
        WHERE GEO_ID = '{geo_id}' AND DATE = '2020-01-01'
          AND VARIABLE_NAME IN (
            'Total population, census.gov',
            'Male population, census.gov',
            'Female population, census.gov',
            'Housing Units, census.gov',
            'Unemployment rate, bls.gov',
            'Population With a Bachelor''s Degree',
            'Households, census.gov',
            'Owner-Occupied Homes',
            'Renter-Occupied Homes'
          )
    """)
    return dict(zip(stats["VARIABLE_NAME"], stats["VALUE"]))


@st.cache_data(ttl=3600)
def load_city_weather(geo_id):
    weather = conn.query(f"""
        SELECT
            AVG(CASE WHEN VARIABLE_NAME = 'Mean temperature of place, noaa.gov' THEN VALUE END) AS AVG_TEMP,
            AVG(CASE WHEN VARIABLE_NAME = 'Mean rainfall of place' THEN VALUE END) AS AVG_RAINFALL,
            AVG(CASE WHEN VARIABLE_NAME = 'Mean snowfall of place' THEN VALUE END) AS AVG_SNOWFALL
        FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.DATACOMMONS_TIMESERIES
        WHERE GEO_ID = '{geo_id}'
          AND DATE >= '2019-01-01' AND DATE < '2021-01-01'
          AND VARIABLE_NAME IN (
            'Mean temperature of place, noaa.gov',
            'Mean rainfall of place',
            'Mean snowfall of place'
          )
    """)
    return weather.iloc[0].to_dict()


@st.cache_data(ttl=3600)
def load_city_airport_info(city_name):
    safe_name = city_name.replace("'", "''")
    df = conn.query(f"""
        SELECT
            a.AIRPORT_NAME,
            a.AIRPORT_ALPHA_CODE AS IATA,
            COUNT(DISTINCT t.DESTINATION_AIRPORT_ID) AS NUM_DESTINATIONS,
            SUM(t.VALUE) AS TOTAL_PASSENGERS
        FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.AIRPORT_INDEX a
        JOIN SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.US_DEPARTMENT_OF_TRANSPORTATION_TIMESERIES t
            ON a.AIRPORT_ID = t.ORIGIN_AIRPORT_ID
        WHERE a.AIRPORT_CITY_NAME = '{safe_name}'
            AND t.VARIABLE_NAME = 'Non-Stop Segment Passengers Transported'
            AND t.DATE >= '2019-01-01' AND t.DATE <= '2020-12-31'
            AND t.VALUE > 0
        GROUP BY a.AIRPORT_NAME, a.AIRPORT_ALPHA_CODE
        ORDER BY TOTAL_PASSENGERS DESC
        LIMIT 3
    """)
    return df


@st.cache_data(ttl=3600)
def load_city_centroid(geo_id):
    result = conn.query(f"""
        SELECT VALUE AS WKT
        FROM SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE.GEOGRAPHY_CHARACTERISTICS
        WHERE GEO_ID = '{geo_id}' AND RELATIONSHIP_TYPE = 'coordinates_wkt'
        LIMIT 1
    """)
    if result.empty:
        return None, None
    wkt = result.iloc[0]["WKT"]
    inner = wkt.replace("POLYGON", "").replace("(", "").replace(")", "").strip()
    coords = inner.split(",")
    lons, lats = [], []
    for c in coords:
        parts = c.strip().split()
        if len(parts) == 2:
            try:
                lons.append(float(parts[0]))
                lats.append(float(parts[1]))
            except ValueError:
                continue
    if not lats:
        return None, None
    return sum(lats) / len(lats), sum(lons) / len(lons)


# --- Session State ---
if "round" not in st.session_state:
    st.session_state.round = 0
    st.session_state.score = 0
    st.session_state.total_points = 0
    st.session_state.total = 0
    st.session_state.city = None
    st.session_state.answered = False
    st.session_state.guess_lat = None
    st.session_state.guess_lon = None

pool = load_city_pool()

if st.session_state.city is None:
    city_row = pool.iloc[random.randint(0, len(pool) - 1)]
    st.session_state.city = city_row.to_dict()
    st.session_state.answered = False
    st.session_state.guess_lat = None
    st.session_state.guess_lon = None
    st.session_state.round += 1

city = st.session_state.city

# --- Header ---
st.title("🗺️ 都市当てゲーム")
st.caption("SNOWFLAKE_PUBLIC_DATA_FREE の統計データをもとに、どのアメリカの都市かを当てよう！")

hcol1, hcol2, hcol3 = st.columns(3)
with hcol1:
    st.metric("ラウンド", st.session_state.round)
with hcol2:
    st.metric("正解数", f"{st.session_state.score} / {st.session_state.total}")
with hcol3:
    st.metric("合計ポイント", f"{st.session_state.total_points:,}")

st.divider()

# --- Load all hint data ---
details = load_city_details(city["GEO_ID"])
weather = load_city_weather(city["GEO_ID"])
airports = load_city_airport_info(city["CITY_NAME"])

# --- Display all hints ---
st.subheader("ヒント")

col_a, col_b, col_c = st.columns(3)

with col_a:
    st.markdown("##### 📊 人口・住宅")
    pop = details.get("Total population, census.gov")
    if pop:
        st.write(f"- 人口: **{int(pop):,}人**")
    male = details.get("Male population, census.gov")
    female = details.get("Female population, census.gov")
    if male and female:
        total = male + female
        st.write(f"- 男性 {male / total * 100:.1f}% / 女性 {female / total * 100:.1f}%")
    housing = details.get("Housing Units, census.gov")
    if housing:
        st.write(f"- 住宅戸数: {int(housing):,}")
    owner = details.get("Owner-Occupied Homes")
    renter = details.get("Renter-Occupied Homes")
    if owner and renter:
        st.write(f"- 持ち家率: {owner / (owner + renter) * 100:.1f}%")

with col_b:
    st.markdown("##### 🌤️ 気象・経済")
    avg_temp = weather.get("AVG_TEMP")
    avg_rain = weather.get("AVG_RAINFALL")
    avg_snow = weather.get("AVG_SNOWFALL")
    if avg_temp is not None and not math.isnan(avg_temp):
        st.write(f"- 平均気温: **{avg_temp:.1f}°C**")
    if avg_rain is not None and not math.isnan(avg_rain):
        st.write(f"- 平均降水量: {avg_rain:.1f} mm/月")
    if avg_snow is not None and not math.isnan(avg_snow):
        st.write(f"- 平均降雪量: {avg_snow:.2f} mm/月")
    unemp = details.get("Unemployment rate, bls.gov")
    if unemp:
        st.write(f"- 失業率: {unemp * 100:.1f}%")
    bachelor = details.get("Population With a Bachelor's Degree")
    if bachelor and pop:
        st.write(f"- 大卒率: {bachelor / pop * 100:.1f}%")

with col_c:
    st.markdown("##### ✈️ 空港")
    if airports.empty:
        st.write("主要空港データなし")
    else:
        for _, row in airports.iterrows():
            iata = row["IATA"] if row["IATA"] else "N/A"
            st.write(
                f"- **{row['AIRPORT_NAME']}** ({iata}): "
                f"{int(row['NUM_DESTINATIONS'])}路線, "
                f"{int(row['TOTAL_PASSENGERS']):,}人"
            )

st.divider()

# --- Map (Guess or Result) ---
if not st.session_state.answered:
    st.subheader("👆 地図をクリックして都市の場所を当てよう")
    st.caption("ホバーで座標を確認、クリックで回答を送信")

    grid = build_click_grid()

    grid_layer = pdk.Layer(
        "ScatterplotLayer",
        id="grid",
        data=grid,
        get_position=["lon", "lat"],
        get_radius=25000,
        get_fill_color=[150, 180, 255, 12],
        pickable=True,
        auto_highlight=True,
        highlight_color=[255, 200, 0, 200],
    )

    view = pdk.ViewState(latitude=39.0, longitude=-98.0, zoom=3.5, pitch=0)
    deck = pdk.Deck(
        layers=[grid_layer],
        initial_view_state=view,
        tooltip={"text": "緯度: {lat}  経度: {lon}"},
    )

    event = st.pydeck_chart(
        deck,
        on_select="rerun",
        selection_mode="single-object",
        use_container_width=True,
        height=550,
    )

    selected_objects = {}
    if event and hasattr(event, "selection") and event.selection:
        selected_objects = event.selection.get("objects", {}) if isinstance(event.selection, dict) else getattr(event.selection, "objects", {})

    picked = selected_objects.get("grid", [])
    if picked:
        st.session_state.guess_lat = picked[0]["lat"]
        st.session_state.guess_lon = picked[0]["lon"]
        st.session_state.answered = True
        st.session_state.total += 1
        st.rerun()

else:
    # --- Result ---
    actual_lat, actual_lon = load_city_centroid(city["GEO_ID"])
    guess_lat = st.session_state.guess_lat
    guess_lon = st.session_state.guess_lon

    if actual_lat is None:
        st.error("都市の座標を取得できませんでした。スキップします...")
    else:
        dist = haversine(guess_lat, guess_lon, actual_lat, actual_lon)
        points = max(0, int(1000 - dist))
        st.session_state.total_points += points
        if dist <= DISTANCE_THRESHOLD_KM:
            st.session_state.score += 1

        answer_city = city["CITY_NAME"]
        answer_state = city["STATE_NAME"]

        if dist <= DISTANCE_THRESHOLD_KM:
            st.success(
                f"**正解！** 答えは **{answer_city}, {answer_state}** でした。"
                f"距離: **{dist:.0f} km** — +{points} pts"
            )
        else:
            st.error(
                f"**答えは {answer_city}, {answer_state}** でした。"
                f"あなたの回答との距離: **{dist:.0f} km** — +{points} pts"
            )

        map_points = pd.DataFrame(
            [
                {"lat": actual_lat, "lon": actual_lon, "label": f"正解: {answer_city}", "r": 0, "g": 200, "b": 0},
                {"lat": guess_lat, "lon": guess_lon, "label": "あなたの回答", "r": 255, "g": 80, "b": 80},
            ]
        )
        line_data = pd.DataFrame(
            [{"s_lon": guess_lon, "s_lat": guess_lat, "e_lon": actual_lon, "e_lat": actual_lat}]
        )

        answer_layer = pdk.Layer(
            "ScatterplotLayer",
            data=map_points,
            get_position=["lon", "lat"],
            get_radius=40000,
            get_fill_color=["r", "g", "b", 200],
            pickable=True,
        )
        line_layer = pdk.Layer(
            "LineLayer",
            data=line_data,
            get_source_position=["s_lon", "s_lat"],
            get_target_position=["e_lon", "e_lat"],
            get_color=[255, 255, 0, 180],
            get_width=3,
        )
        text_layer = pdk.Layer(
            "TextLayer",
            data=map_points,
            get_position=["lon", "lat"],
            get_text="label",
            get_size=14,
            get_color=[255, 255, 255, 255],
            get_pixel_offset=[0, -25],
        )

        mid_lat = (actual_lat + guess_lat) / 2
        mid_lon = (actual_lon + guess_lon) / 2
        deck = pdk.Deck(
            layers=[answer_layer, line_layer, text_layer],
            initial_view_state=pdk.ViewState(latitude=mid_lat, longitude=mid_lon, zoom=4, pitch=0),
            tooltip={"text": "{label}"},
        )
        st.pydeck_chart(deck, use_container_width=True, height=550)

    if st.button("次の都市へ →", type="primary"):
        st.session_state.city = None
        st.rerun()
