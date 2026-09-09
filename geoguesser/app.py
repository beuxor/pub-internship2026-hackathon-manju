"""🌍 シティゲッサー — 統計・気候・名物から都市の位置を当てるゲーム。

起動:
    uv run streamlit run geoguesser/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import folium
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit_folium import st_folium

# 直接 `streamlit run geoguesser/app.py` されても同階層モジュールを解決できるようにする。
sys.path.insert(0, str(Path(__file__).resolve().parent))

import game  # noqa: E402
from data import DEFAULT_SNOWFLAKE_TABLE, CityDataError, load_cities, to_records  # noqa: E402

st.set_page_config(page_title="シティゲッサー", page_icon="🌍", layout="wide")

PHASE_SETUP = "setup"
PHASE_GUESSING = "guessing"
PHASE_RESULT = "result"
PHASE_SUMMARY = "summary"


# ---------------------------------------------------------------------------
# セッション状態
# ---------------------------------------------------------------------------


def init_state() -> None:
    defaults: dict[str, Any] = {
        "phase": PHASE_SETUP,
        "rounds": [],
        "current": 0,
        "results": [],
        "hint_level": 1,
        "guess": None,
        "last_result": None,
        "map_nonce": 0,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def start_game(cities: list[dict[str, Any]], n: int, difficulty: str, seed: int | None) -> None:
    st.session_state.rounds = game.pick_rounds(cities, n, difficulty, seed)
    st.session_state.current = 0
    st.session_state.results = []
    st.session_state.hint_level = 1
    st.session_state.guess = None
    st.session_state.last_result = None
    st.session_state.map_nonce += 1
    st.session_state.phase = PHASE_GUESSING


def reset_game() -> None:
    st.session_state.phase = PHASE_SETUP
    st.session_state.rounds = []
    st.session_state.current = 0
    st.session_state.results = []
    st.session_state.hint_level = 1
    st.session_state.guess = None
    st.session_state.last_result = None


def advance_round() -> None:
    st.session_state.current += 1
    st.session_state.hint_level = 1
    st.session_state.guess = None
    st.session_state.last_result = None
    st.session_state.map_nonce += 1
    if st.session_state.current >= len(st.session_state.rounds):
        st.session_state.phase = PHASE_SUMMARY
    else:
        st.session_state.phase = PHASE_GUESSING


# ---------------------------------------------------------------------------
# 表示パーツ
# ---------------------------------------------------------------------------


def render_hints(city: dict[str, Any], level: int) -> None:
    hints = game.reveal_hints(city, level)

    st.markdown("#### 📋 この都市の手がかり")
    # 数値系は metric、文章系は本文で出す。
    numeric_labels = {"年平均気温", "年間降水量"}
    metrics = [h for h in hints if h["label"] in numeric_labels]
    texts = [h for h in hints if h["label"] not in numeric_labels]

    if metrics:
        cols = st.columns(len(metrics))
        for col, hint in zip(cols, metrics):
            col.metric(hint["label"], hint["value"])

    for hint in texts:
        st.markdown(f"**{hint['label']}**：{hint['value']}")

    remaining = game.MAX_HINT_LEVEL - level
    multiplier = game.hint_multiplier(level)
    st.caption(
        f"現在の得点係数 ×{multiplier:.2f}"
        + (f" ／ 追加できるヒントはあと {remaining} 段階" if remaining else " ／ 全ヒント開示済み")
    )


def guess_map(nonce: int, guess: tuple[float, float] | None) -> dict[str, Any] | None:
    m = folium.Map(location=[20, 0], zoom_start=2, min_zoom=1, world_copy_jump=True)

    if guess is not None:
        folium.Marker(
            location=list(guess),
            tooltip="ここに回答",
            icon=folium.Icon(color="blue", icon="map-pin", prefix="fa"),
        ).add_to(m)

    return st_folium(
        m,
        height=520,
        width=None,
        returned_objects=["last_clicked"],
        key=f"guess_map_{nonce}",
    )


def result_map(result: game.RoundResult, nonce: int) -> None:
    mid_lat = (result.true_lat + result.guess_lat) / 2
    mid_lon = (result.true_lon + result.guess_lon) / 2
    m = folium.Map(location=[mid_lat, mid_lon], zoom_start=2)

    folium.Marker(
        [result.guess_lat, result.guess_lon],
        tooltip="あなたの回答",
        icon=folium.Icon(color="blue", icon="map-pin", prefix="fa"),
    ).add_to(m)
    folium.Marker(
        [result.true_lat, result.true_lon],
        tooltip=f"正解: {result.city_name}",
        icon=folium.Icon(color="red", icon="flag", prefix="fa"),
    ).add_to(m)
    folium.PolyLine(
        [(result.guess_lat, result.guess_lon), (result.true_lat, result.true_lon)],
        color="#e4572e",
        weight=3,
        dash_array="8",
    ).add_to(m)

    m.fit_bounds(
        [
            (result.guess_lat, result.guess_lon),
            (result.true_lat, result.true_lon),
        ],
        padding=(40, 40),
    )
    st_folium(m, height=460, returned_objects=[], key=f"result_map_{nonce}")


def summary_map(results: list[game.RoundResult]) -> go.Figure:
    fig = go.Figure()

    for r in results:
        fig.add_trace(
            go.Scattergeo(
                lat=[r.guess_lat, r.true_lat],
                lon=[r.guess_lon, r.true_lon],
                mode="lines",
                line=dict(width=1.5, color="rgba(228, 87, 46, 0.6)"),
                showlegend=False,
                hoverinfo="skip",
            )
        )

    fig.add_trace(
        go.Scattergeo(
            lat=[r.guess_lat for r in results],
            lon=[r.guess_lon for r in results],
            mode="markers",
            name="あなたの回答",
            marker=dict(size=8, color="#3d7ea6", symbol="circle"),
            text=[f"{r.city_name}: {r.distance_km:,.0f} km" for r in results],
            hovertemplate="%{text}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scattergeo(
            lat=[r.true_lat for r in results],
            lon=[r.true_lon for r in results],
            mode="markers+text",
            name="正解",
            marker=dict(size=9, color="#e4572e", symbol="star"),
            text=[r.city_name for r in results],
            textposition="top center",
            textfont=dict(size=10),
            hovertemplate="%{text}<extra></extra>",
        )
    )

    fig.update_geos(
        projection_type="natural earth",
        showland=True,
        landcolor="#eef2f0",
        showocean=True,
        oceancolor="#d8e7f0",
        showcountries=True,
        countrycolor="#b9c4c9",
    )
    fig.update_layout(
        height=520,
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", y=-0.05),
    )
    return fig


# ---------------------------------------------------------------------------
# 画面
# ---------------------------------------------------------------------------


def render_scoreboard() -> None:
    results: list[game.RoundResult] = st.session_state.results
    total_rounds = len(st.session_state.rounds)
    stats = game.summarize(results)

    c1, c2, c3 = st.columns(3)
    c1.metric("累計スコア", f"{stats['total_score']:,}")
    c2.metric("進行", f"{len(results)} / {total_rounds} ラウンド")
    c3.metric(
        "平均誤差",
        f"{stats['avg_distance_km']:,.0f} km" if results else "—",
    )


def render_setup(cities_df: pd.DataFrame, source_label: str) -> None:
    st.markdown(
        """
        統計・気候・名物といった手がかりだけを見て、その都市が地球上のどこにあるかを
        **地図をクリック**して当てるゲームです。正解に近いほど高得点（最大 5,000 点）。
        """
    )

    counts = cities_df["difficulty"].value_counts()
    st.info(
        f"データ取得元 **{source_label}** ／ 収録 **{len(cities_df)} 都市**"
        f"（easy {counts.get('easy', 0)} ・ normal {counts.get('normal', 0)} ・ hard {counts.get('hard', 0)}）"
    )

    st.markdown("#### ルール")
    st.markdown(
        f"""
        - 各ラウンドで 1 都市が出題され、まず気候・人口規模のヒントが開示されます。
        - 「ヒントを追加」で産業・所得水準 → 名物・ランドマークまで開示できますが、
          得点係数が ×{game.HINT_PENALTY[1]:.2f} → ×{game.HINT_PENALTY[2]:.2f} に下がります。
        - 地図をクリックしてピンを立て、「この地点で回答」で確定します。
        - 正解から **{game.PERFECT_RADIUS_KM:.0f} km 以内で満点**、以降は距離に応じて指数関数的に減点。
        """
    )

    if st.button("▶ ゲームを開始", type="primary", width="stretch"):
        start_game(
            to_records(cities_df),
            st.session_state.cfg_rounds,
            st.session_state.cfg_difficulty,
            st.session_state.cfg_seed,
        )
        st.rerun()


def render_guessing() -> None:
    city: dict[str, Any] = st.session_state.rounds[st.session_state.current]
    round_no = st.session_state.current + 1
    total = len(st.session_state.rounds)

    st.subheader(f"ラウンド {round_no} / {total}")
    render_scoreboard()
    st.progress((round_no - 1) / total)

    left, right = st.columns([2, 3], gap="large")

    with left:
        render_hints(city, st.session_state.hint_level)

        if st.session_state.hint_level < game.MAX_HINT_LEVEL:
            if st.button("💡 ヒントを追加（得点係数が下がります）", width="stretch"):
                st.session_state.hint_level += 1
                st.rerun()

    with right:
        st.markdown("#### 🗺 地図をクリックして回答")
        map_state = guess_map(st.session_state.map_nonce, st.session_state.guess)

        clicked = (map_state or {}).get("last_clicked")
        if clicked:
            new_guess = (round(clicked["lat"], 4), round(clicked["lng"], 4))
            if new_guess != st.session_state.guess:
                st.session_state.guess = new_guess
                st.rerun()

        guess = st.session_state.guess
        if guess is None:
            st.info("地図上の任意の場所をクリックするとピンが立ちます。")
        else:
            st.success(f"選択中: 緯度 {guess[0]:.4f} / 経度 {guess[1]:.4f}")

        if st.button(
            "✅ この地点で回答",
            type="primary",
            disabled=guess is None,
            width="stretch",
        ):
            st.session_state.last_result = game.evaluate_guess(
                city, guess[0], guess[1], st.session_state.hint_level
            )
            st.session_state.results.append(st.session_state.last_result)
            st.session_state.phase = PHASE_RESULT
            st.session_state.map_nonce += 1
            st.rerun()


def render_result() -> None:
    result: game.RoundResult = st.session_state.last_result
    city: dict[str, Any] = st.session_state.rounds[st.session_state.current]
    total = len(st.session_state.rounds)
    is_last = st.session_state.current + 1 >= total

    st.subheader(f"ラウンド {st.session_state.current + 1} / {total} の結果")
    st.markdown(f"### 正解は **{result.city_name}**（{result.country}）")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("誤差", f"{result.distance_km:,.0f} km")
    c2.metric("素点", f"{result.base_score:,}")
    c3.metric(
        "獲得スコア",
        f"{result.score:,}",
        delta=(
            f"ヒント補正 {result.score - result.base_score:+,}"
            if result.score != result.base_score
            else None
        ),
    )
    c4.metric("評価", game.rank_label(result.score))

    left, right = st.columns([3, 2], gap="large")
    with left:
        result_map(result, st.session_state.map_nonce)
    with right:
        st.markdown("#### 🔎 全ての手がかり（答え合わせ）")
        for hint in game.reveal_hints(city, game.MAX_HINT_LEVEL):
            st.markdown(f"**{hint['label']}**：{hint['value']}")
        st.caption(
            f"正確な座標: 緯度 {result.true_lat:.4f} / 経度 {result.true_lon:.4f}"
            f"　｜　人口 {int(city['population']):,} 人"
            f"　｜　1人当たり GDP {int(city['gdp_per_capita']):,} ドル"
        )

    label = "🏁 最終結果を見る" if is_last else "➡ 次のラウンドへ"
    if st.button(label, type="primary", width="stretch"):
        advance_round()
        st.rerun()


def render_summary() -> None:
    results: list[game.RoundResult] = st.session_state.results
    stats = game.summarize(results)

    st.subheader("🏁 最終結果")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("総合スコア", f"{stats['total_score']:,} / {stats['max_possible']:,}")
    c2.metric("平均誤差", f"{stats['avg_distance_km']:,.0f} km")
    c3.metric("最も惜しい", f"{stats['best_distance_km']:,.0f} km")
    c4.metric("最も遠い", f"{stats['worst_distance_km']:,.0f} km")

    rate = stats["total_score"] / stats["max_possible"] if stats["max_possible"] else 0
    st.progress(rate, text=f"得点率 {rate:.1%}")

    st.markdown("#### ラウンドごとの成績")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "ラウンド": i + 1,
                    "都市": r.city_name,
                    "国・地域": r.country,
                    "誤差 (km)": round(r.distance_km, 1),
                    "使用ヒント段階": r.hint_level,
                    "素点": r.base_score,
                    "獲得スコア": r.score,
                    "評価": game.rank_label(r.score),
                }
                for i, r in enumerate(results)
            ]
        ),
        hide_index=True,
        width="stretch",
    )

    st.markdown("#### 回答と正解の対応")
    st.plotly_chart(summary_map(results), width="stretch")

    if st.button("🔄 もう一度プレイ", type="primary", width="stretch"):
        reset_game()
        st.rerun()


# ---------------------------------------------------------------------------
# エントリポイント
# ---------------------------------------------------------------------------


def main() -> None:
    init_state()

    st.title("🌍 シティゲッサー")
    st.caption("統計・気候・名物から都市の位置を推理して地図をクリック")

    with st.sidebar:
        st.header("⚙️ 設定")
        in_game = st.session_state.phase != PHASE_SETUP

        st.selectbox(
            "ラウンド数",
            options=[3, 5, 10],
            index=1,
            key="cfg_rounds",
            disabled=in_game,
        )
        st.selectbox(
            "難易度",
            options=["all", *game.DIFFICULTIES],
            index=0,
            format_func=lambda d: {
                "all": "すべて",
                "easy": "やさしい",
                "normal": "ふつう",
                "hard": "むずかしい",
            }[d],
            key="cfg_difficulty",
            disabled=in_game,
        )
        seed_fixed = st.checkbox("乱数シードを固定（同じ出題を再現）", value=False, disabled=in_game)
        st.session_state.cfg_seed = (
            st.number_input("シード", min_value=0, max_value=99999, value=42, disabled=in_game)
            if seed_fixed
            else None
        )

        st.divider()
        st.subheader("データ取得元")
        use_snowflake = st.checkbox("Snowflake のテーブルを使う", value=False, disabled=in_game)
        table = st.text_input(
            "テーブル／ビュー名",
            value=DEFAULT_SNOWFLAKE_TABLE,
            disabled=in_game or not use_snowflake,
        )

        st.divider()
        if st.button("🔄 リセット", width="stretch"):
            reset_game()
            st.rerun()

    try:
        cities_df, source_label = load_cities(
            source="snowflake" if use_snowflake else "json",
            table=table,
        )
    except CityDataError as exc:
        st.error(f"都市データを読み込めませんでした: {exc}")
        st.stop()

    phase = st.session_state.phase
    if phase == PHASE_SETUP:
        render_setup(cities_df, source_label)
    elif phase == PHASE_GUESSING:
        render_guessing()
    elif phase == PHASE_RESULT:
        render_result()
    else:
        render_summary()


main()
