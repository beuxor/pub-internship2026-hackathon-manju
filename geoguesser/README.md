# 🌍 シティゲッサー

統計・気候・名物といった手がかりだけから、その都市が地球上のどこにあるかを
**地図をクリックして**当てるゲームです。正解に近いほど高得点（1 ラウンド最大 5,000 点）。

## 起動

```bash
uv sync
uv run streamlit run geoguesser/app.py
```

ブラウザで http://localhost:8501 が開きます。

## 遊び方

1. サイドバーでラウンド数（3 / 5 / 10）と難易度を選び、**ゲームを開始**。
2. 出題都市の手がかりが段階的に開示されます。

   | 段階 | 開示される情報 | 得点係数 |
   | --- | --- | --- |
   | Lv1（初期） | 気候区分・年平均気温・年間降水量・人口規模帯 | ×1.00 |
   | Lv2 | 主要産業・1人当たり GDP の水準 | ×0.85 |
   | Lv3 | 名物・名産・地形とランドマーク | ×0.70 |

   「💡 ヒントを追加」で次の段階へ進めますが、得点係数が下がります。
3. 地図上の任意の場所をクリックしてピンを立て、**この地点で回答**で確定。
4. 正解地点と回答地点、その間を結ぶ線と誤差・獲得スコアが表示されます。
5. 全ラウンド終了後、総合スコア・平均誤差・ラウンド別成績・世界地図での俯瞰が出ます。

## 採点式

```
素点 = 5000                          (誤差 ≤ 25 km)
素点 = 5000 * exp(-誤差km / 1500)     (それ以外)
獲得スコア = 素点 * ヒント段階の得点係数
```

減衰スケール 1,500 km は GeoGuessr の世界マップとほぼ同じ設定です。目安:

| 誤差 | 素点 |
| --- | --- |
| 25 km 以内 | 5,000 |
| 100 km | 4,678 |
| 500 km | 3,583 |
| 1,500 km | 1,839 |
| 5,000 km | 178 |

## ファイル構成

| ファイル | 役割 |
| --- | --- |
| `app.py` | Streamlit の UI とゲーム進行（`setup → guessing → result → summary`） |
| `game.py` | UI 非依存のロジック。距離計算・採点・出題抽選・ヒント段階開示 |
| `data.py` | 都市データのローダー（JSON / Snowflake）とスキーマ検証 |
| `cities.json` | 収録都市データ（40 都市） |

## 都市を追加する

`cities.json` に以下の形で 1 件追加するだけです。アプリの再起動で反映されます。

```json
{
  "name": "都市名",
  "country": "国・地域名",
  "lat": 35.6895,
  "lon": 139.6917,
  "population": 37400000,
  "gdp_per_capita": 43000,
  "climate": "温暖湿潤気候 (Cfa)",
  "avg_temp_c": 16.4,
  "annual_precip_mm": 1600,
  "industries": "電子機器、自動車、金融、出版",
  "specialties": "握り寿司、そば、もんじゃ焼き、抹茶菓子",
  "landmark_hint": "赤白に塗られた電波塔と、堀に囲まれた旧城郭が同じ市街地に共存する",
  "difficulty": "easy"
}
```

- `difficulty` は `easy` / `normal` / `hard`。
- **`industries` / `specialties` / `landmark_hint` / `climate` に都市名・国名を書かないこと。**
  そのままヒントとして表示されるため答えが割れます（例: 「上海蟹」→「秋に出回る毛蟹」）。
- 追加後、ネタバレ混入がないかは次で確認できます。

  ```bash
  uv run python -c "
  import json
  cities = json.load(open('geoguesser/cities.json', encoding='utf-8'))
  leak = [(c['name'], t) for c in cities for t in (c['name'], c['country'])
          if t in c['climate'] + c['industries'] + c['specialties'] + c['landmark_hint']]
  print(leak or 'ネタバレなし')
  "
  ```

## Snowflake のテーブルから読む（任意）

既定は同梱の `cities.json` ですが、サイドバーの **「Snowflake のテーブルを使う」** を
オンにすると `st.connection("snowflake")` 経由でテーブル／ビューから読み込みます。
列名は `cities.json` のキーと同じ（大文字小文字は問わない）にしてください。

```sql
CREATE OR REPLACE TABLE GEOGUESSER_CITIES (
  NAME              STRING,
  COUNTRY           STRING,
  LAT               FLOAT,
  LON               FLOAT,
  POPULATION        NUMBER,
  GDP_PER_CAPITA    NUMBER,
  CLIMATE           STRING,
  AVG_TEMP_C        FLOAT,
  ANNUAL_PRECIP_MM  NUMBER,
  INDUSTRIES        STRING,
  SPECIALTIES       STRING,
  LANDMARK_HINT     STRING,
  DIFFICULTY        STRING
);
```

接続情報はリポジトリ直下の `.snowflake/config.toml`（セットアップ手順は最上位の
`README.md` 参照）を使います。接続に失敗した場合は警告を出して自動的に JSON へ
フォールバックするため、ゲーム自体は必ず起動します。
