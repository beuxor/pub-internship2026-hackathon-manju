"""ジオゲッサー風ゲームのロジック層。

UI に依存しない純粋な関数だけを置く。距離計算・採点・出題抽選・ヒントの段階開示を担当する。
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any, Iterable, Sequence

# ---------------------------------------------------------------------------
# 定数
# ---------------------------------------------------------------------------

EARTH_RADIUS_KM = 6371.0088

#: 満点。GeoGuessr と同じく 1 ラウンド 5000 点。
MAX_SCORE = 5000

#: この距離以内なら満点扱い。
PERFECT_RADIUS_KM = 25.0

#: 指数減衰のスケール。大きいほど遠くても点が残る。
DECAY_SCALE_KM = 1500.0

#: 開示したヒント段階ごとの得点係数。index = 追加開示した回数。
HINT_PENALTY = (1.0, 0.85, 0.7)

#: ヒントの最大段階（1 = 初期表示のみ）。
MAX_HINT_LEVEL = len(HINT_PENALTY)

DIFFICULTIES = ("easy", "normal", "hard")


# ---------------------------------------------------------------------------
# データ構造
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RoundResult:
    """1 ラウンドの回答結果。"""

    city_name: str
    country: str
    true_lat: float
    true_lon: float
    guess_lat: float
    guess_lon: float
    distance_km: float
    hint_level: int
    base_score: int
    score: int


# ---------------------------------------------------------------------------
# 距離
# ---------------------------------------------------------------------------


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """2 地点間の大円距離を km で返す。"""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = phi2 - phi1
    d_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    # 浮動小数の丸めで a がわずかに 1 を超えることがあるためクランプする。
    a = min(1.0, max(0.0, a))
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


# ---------------------------------------------------------------------------
# 採点
# ---------------------------------------------------------------------------


def score_from_distance(distance_km: float) -> int:
    """距離から素点を算出する。

    - ``PERFECT_RADIUS_KM`` 以内は満点。
    - それ以降は ``MAX_SCORE * exp(-d / DECAY_SCALE_KM)`` で減衰する。
    """
    if distance_km <= PERFECT_RADIUS_KM:
        return MAX_SCORE
    return int(round(MAX_SCORE * math.exp(-distance_km / DECAY_SCALE_KM)))


def hint_multiplier(hint_level: int) -> float:
    """ヒント段階に対する得点係数を返す。``hint_level`` は 1 以上。"""
    index = max(0, min(len(HINT_PENALTY) - 1, hint_level - 1))
    return HINT_PENALTY[index]


def evaluate_guess(
    city: dict[str, Any],
    guess_lat: float,
    guess_lon: float,
    hint_level: int = 1,
) -> RoundResult:
    """回答地点を採点して :class:`RoundResult` を返す。"""
    distance = haversine_km(
        float(city["lat"]), float(city["lon"]), guess_lat, guess_lon
    )
    base = score_from_distance(distance)
    final = int(round(base * hint_multiplier(hint_level)))

    return RoundResult(
        city_name=str(city["name"]),
        country=str(city["country"]),
        true_lat=float(city["lat"]),
        true_lon=float(city["lon"]),
        guess_lat=guess_lat,
        guess_lon=guess_lon,
        distance_km=distance,
        hint_level=hint_level,
        base_score=base,
        score=final,
    )


def rank_label(score: int) -> str:
    """得点に応じた評価ラベル。"""
    if score >= 4500:
        return "🏆 パーフェクト級"
    if score >= 3000:
        return "🎯 かなり近い"
    if score >= 1500:
        return "🙂 惜しい"
    if score >= 500:
        return "😐 大陸は合っている？"
    return "🌍 地球のどこかではある"


# ---------------------------------------------------------------------------
# 出題
# ---------------------------------------------------------------------------


def pick_rounds(
    cities: Sequence[dict[str, Any]],
    n: int,
    difficulty: str | Iterable[str] | None = None,
    seed: int | None = None,
) -> list[dict[str, Any]]:
    """出題する都市を重複なしで抽選する。

    ``difficulty`` に ``None`` か ``"all"`` を渡すと全難易度から選ぶ。
    候補が ``n`` に足りない場合は候補すべてを返す。
    """
    pool = list(cities)

    if difficulty and difficulty != "all":
        wanted = {difficulty} if isinstance(difficulty, str) else set(difficulty)
        filtered = [c for c in pool if c.get("difficulty") in wanted]
        # 該当が無い難易度指定でゲームが始められなくなるのを避ける。
        if filtered:
            pool = filtered

    rng = random.Random(seed)
    rng.shuffle(pool)
    return pool[: max(1, min(n, len(pool)))]


# ---------------------------------------------------------------------------
# ヒントの段階開示
# ---------------------------------------------------------------------------


def _population_band(population: int) -> str:
    """人口を帯で表現する（正確な値はネタバレになりうるためぼかす）。"""
    millions = population / 1_000_000
    if millions >= 20:
        return "都市圏人口 2,000万人超（世界最大級）"
    if millions >= 10:
        return "都市圏人口 1,000万〜2,000万人"
    if millions >= 5:
        return "都市圏人口 500万〜1,000万人"
    if millions >= 1:
        return "都市圏人口 100万〜500万人"
    return "都市圏人口 100万人未満"


def _gdp_band(gdp_per_capita: int) -> str:
    if gdp_per_capita >= 60000:
        return "1人当たり GDP 6万ドル超（最上位の高所得圏）"
    if gdp_per_capita >= 35000:
        return "1人当たり GDP 3.5万〜6万ドル（高所得圏）"
    if gdp_per_capita >= 15000:
        return "1人当たり GDP 1.5万〜3.5万ドル（上位中所得圏）"
    if gdp_per_capita >= 5000:
        return "1人当たり GDP 5千〜1.5万ドル（中所得圏）"
    return "1人当たり GDP 5千ドル未満（低所得圏）"


def reveal_hints(city: dict[str, Any], level: int) -> list[dict[str, str]]:
    """``level`` 段階までのヒントを返す。

    - Lv1: 気候・気温・降水量・人口規模帯
    - Lv2: 主要産業・所得水準
    - Lv3: 名物とランドマーク
    """
    level = max(1, min(MAX_HINT_LEVEL, level))

    tiers: list[list[dict[str, str]]] = [
        [
            {"label": "気候区分", "value": str(city["climate"])},
            {"label": "年平均気温", "value": f"{float(city['avg_temp_c']):.1f} ℃"},
            {
                "label": "年間降水量",
                "value": f"{int(city['annual_precip_mm']):,} mm",
            },
            {"label": "人口規模", "value": _population_band(int(city["population"]))},
        ],
        [
            {"label": "主要産業", "value": str(city["industries"])},
            {"label": "経済水準", "value": _gdp_band(int(city["gdp_per_capita"]))},
        ],
        [
            {"label": "名物・名産", "value": str(city["specialties"])},
            {"label": "地形・ランドマーク", "value": str(city["landmark_hint"])},
        ],
    ]

    revealed: list[dict[str, str]] = []
    for tier in tiers[:level]:
        revealed.extend(tier)
    return revealed


def summarize(results: Sequence[RoundResult]) -> dict[str, float | int]:
    """全ラウンドの集計。"""
    if not results:
        return {
            "rounds": 0,
            "total_score": 0,
            "max_possible": 0,
            "avg_distance_km": 0.0,
            "best_distance_km": 0.0,
            "worst_distance_km": 0.0,
        }

    distances = [r.distance_km for r in results]
    return {
        "rounds": len(results),
        "total_score": sum(r.score for r in results),
        "max_possible": MAX_SCORE * len(results),
        "avg_distance_km": sum(distances) / len(distances),
        "best_distance_km": min(distances),
        "worst_distance_km": max(distances),
    }
