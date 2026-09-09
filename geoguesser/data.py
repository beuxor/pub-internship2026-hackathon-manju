"""都市データのローダー。

既定はリポジトリ内の ``cities.json``。Snowflake に同じスキーマのテーブルを用意した場合は
``load_cities(source="snowflake", table=...)`` で切り替えられる。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

DATA_PATH = Path(__file__).with_name("cities.json")

#: 必須列。Snowflake から読む場合もこのスキーマに揃える。
REQUIRED_COLUMNS = (
    "name",
    "country",
    "lat",
    "lon",
    "population",
    "gdp_per_capita",
    "climate",
    "avg_temp_c",
    "annual_precip_mm",
    "industries",
    "specialties",
    "landmark_hint",
    "difficulty",
)

NUMERIC_COLUMNS = (
    "lat",
    "lon",
    "population",
    "gdp_per_capita",
    "avg_temp_c",
    "annual_precip_mm",
)

DEFAULT_SNOWFLAKE_TABLE = "GEOGUESSER_CITIES"


class CityDataError(RuntimeError):
    """都市データの取得・検証に失敗した。"""


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    """列名を小文字に揃え、必須列の存在と型を検証する。"""
    df = df.rename(columns={c: str(c).lower() for c in df.columns})

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise CityDataError(f"必須列が不足しています: {', '.join(missing)}")

    df = df.loc[:, list(REQUIRED_COLUMNS)].copy()

    for col in NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    before = len(df)
    df = df.dropna(subset=["name", "lat", "lon"])
    if len(df) < before:
        st.warning(f"座標または都市名が欠けた {before - len(df)} 件を除外しました。")

    # 緯度経度が地球上にあるか。
    df = df[df["lat"].between(-90, 90) & df["lon"].between(-180, 180)]

    if df.empty:
        raise CityDataError("有効な都市データが 0 件です。")

    df["difficulty"] = df["difficulty"].fillna("normal").astype(str).str.lower()
    return df.reset_index(drop=True)


@st.cache_data(show_spinner=False)
def load_cities_from_json(path: str | None = None) -> pd.DataFrame:
    """同梱の JSON から読み込む。"""
    target = Path(path) if path else DATA_PATH
    if not target.exists():
        raise CityDataError(f"都市データが見つかりません: {target}")

    with target.open(encoding="utf-8") as f:
        records: list[dict[str, Any]] = json.load(f)

    return _normalize(pd.DataFrame(records))


@st.cache_data(show_spinner="Snowflake から都市データを取得中…")
def load_cities_from_snowflake(table: str = DEFAULT_SNOWFLAKE_TABLE) -> pd.DataFrame:
    """Snowflake のテーブル／ビューから読み込む。

    ``st.connection("snowflake")`` を使うため、``.snowflake/config.toml`` か
    ``.streamlit/secrets.toml`` に接続情報が必要。
    """
    conn = st.connection("snowflake")
    columns = ", ".join(c.upper() for c in REQUIRED_COLUMNS)
    # テーブル名は識別子なのでバインドできない。呼び出し側で信頼できる値を渡す前提。
    df = conn.query(f"SELECT {columns} FROM {table}", ttl=600)
    return _normalize(df)


def load_cities(
    source: str = "json",
    table: str = DEFAULT_SNOWFLAKE_TABLE,
    path: str | None = None,
) -> tuple[pd.DataFrame, str]:
    """都市データを取得し ``(DataFrame, 実際に使った取得元の説明)`` を返す。

    Snowflake の取得に失敗した場合は JSON にフォールバックする。
    """
    if source == "snowflake":
        try:
            return load_cities_from_snowflake(table), f"Snowflake: {table}"
        except Exception as exc:  # 接続失敗・権限不足・テーブル未作成など
            st.warning(
                f"Snowflake から読めなかったため同梱 JSON に切り替えました（{exc}）"
            )

    return load_cities_from_json(path), f"JSON: {(Path(path) if path else DATA_PATH).name}"


def to_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    """ロジック層が扱いやすい dict のリストに変換する。"""
    return df.to_dict(orient="records")
