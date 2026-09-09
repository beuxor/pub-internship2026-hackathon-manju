# Snowflake オープンデータ一覧

## 1. SNOWFLAKE_PUBLIC_DATA_FREE (Marketplace公開データ / 370ビュー)

データベース: `SNOWFLAKE_PUBLIC_DATA_FREE.PUBLIC_DATA_FREE`

### 人口・社会統計
| テーブル名 | 概要 |
|---|---|
| `AMERICAN_COMMUNITY_SURVEY_TIMESERIES` | 米国の人口推定・人口動態・社会・経済・住宅データ (複数地理レベル) |
| `DATACOMMONS_TIMESERIES` | 人口統計・経済・政府支出・環境統計 (Google Data Commons) |
| `CANADA_STATCAN_TIMESERIES` | カナダの経済・人口・社会データ (所得, GDP, 労働市場, 国勢調査等) |
| `UNITED_KINGDOM_TIMESERIES` | 英国の人口・人口動態・経済・死亡・小売・カード支出統計 |
| `IRS_INDIVIDUAL_INCOME_TIMESERIES` | 米国の個人所得税統計 (ZIP/郡/州レベル) |
| `IRS_MIGRATION_BY_CHARACTERISTIC_TIMESERIES` | 米国の移住データ (人口流動・所得変動・属性別) |
| `IRS_ORIGIN_DESTINATION_MIGRATION_TIMESERIES` | 米国の郡間・州間の人口移動フロー |
| `US_ECONOMIC_CENSUS_TIMESERIES` | 米国の企業・事業所に関する経済センサスデータ |
| `PUBLIC_HOLIDAY_CALENDAR` | 1970年以降の世界各国の公休日カレンダー |

### 雇用・労働
| テーブル名 | 概要 |
|---|---|
| `BUREAU_OF_LABOR_STATISTICS_EMPLOYMENT_TIMESERIES` | 米国の雇用・求人・離職・賃金 (LAUS, JOLTS, SAE) |
| `INTERNATIONAL_LABOUR_ORGANIZATION_TIMESERIES` | 世界の労働市場データ (雇用・失業・労働参加率等) |
| `US_DEPARTMENT_OF_LABOR_UNEMPLOYMENT_INSURANCE_CLAIMS_TIMESERIES` | 米国の失業保険申請件数 (週次) |
| `WARN_ACT_TIMESERIES` | 米国6州のWARN法に基づくレイオフ通知データ |

### 物価・消費者指標
| テーブル名 | 概要 |
|---|---|
| `BUREAU_OF_LABOR_STATISTICS_PRICE_TIMESERIES` | 米国CPI・平均価格データ (インフレ指標) |
| `EUROPEAN_CENTRAL_BANK_TIMESERIES` | 欧州の消費者物価指数・住宅価格 |

### 金融・経済
| テーブル名 | 概要 |
|---|---|
| `BANK_FOR_INTERNATIONAL_SETTLEMENTS_TIMESERIES` | 国際決済銀行 (BIS) の不動産・政策金利・信用・流動性データ |
| `FEDERAL_RESERVE_TIMESERIES` | FRBの借入・クレジットカード債務・工業生産・金利等 |
| `FINANCIAL_ECONOMIC_INDICATORS_TIMESERIES` | 小売売上・消費者信用・住宅ローン金利・GDP等の経済指標 |
| `FINANCIAL_ECONOMIC_INDICATORS_TIMESERIES_VINTAGE` | 経済指標 (リリース日追跡付き) |
| `INTERNATIONAL_MONETARY_FUND_TIMESERIES` | IMFの経済・金融指標 (商品価格, 国際収支, 政府財政等) |
| `OECD_TIMESERIES` | OECD加盟国の経済・人口・労働市場データ |
| `WORLD_BANK_TIMESERIES` | 世界銀行のESGパフォーマンス・経済状況・公共セクターデータ |
| `WORLD_TRADE_ORGANIZATION_TIMESERIES` | WTOの国際貿易統計 (貿易フロー, 関税率等) |
| `FX_RATES_TIMESERIES` | 為替レート (ECB, BIS, IMF等ソース) |
| `US_TREASURY_TIMESERIES` | 米国債利回り・貯蓄債券・歳入データ |
| `STOCK_PRICE_TIMESERIES` | 米国証券 (Nasdaq) の日次株価・出来高 |

### 不動産・住宅
| テーブル名 | 概要 |
|---|---|
| `FHFA_HOUSE_PRICE_TIMESERIES` | 1975年以降の米国住宅価格指数 |
| `FHFA_MORTGAGE_PERFORMANCE_TIMESERIES` | 住宅ローンパフォーマンスデータ |
| `FHFA_UNIFORM_APPRAISAL_TIMESERIES` | 一戸建て住宅の鑑定トレンド |
| `FREDDIE_MAC_HOUSING_TIMESERIES` | 住宅価格指数・住宅ローン金利 |
| `US_REAL_ESTATE_TIMESERIES` | 建設許可・建設支出データ |

### 金融機関
| テーブル名 | 概要 |
|---|---|
| `FINANCIAL_INSTITUTION_ENTITIES` | FDIC規制下の米国金融機関インデックス |
| `FINANCIAL_INSTITUTION_TIMESERIES` | FDIC保険対象機関の財務指標 |
| `FINANCIAL_INSTITUTION_EVENTS` | FDIC機関の銀行イベント (分割・資産売却等) |
| `FINANCIAL_INSTITUTION_HIERARCHY` | FDIC金融機関の親子関係 |
| `FINANCIAL_BRANCH_ENTITIES` | 米国の銀行支店位置情報 |
| `FDIC_SUMMARY_OF_DEPOSITS_TIMESERIES` | FDIC保険銀行支店の預金データ |
| `FINANCIAL_CFPB_COMPLAINT` | 金融商品に関する消費者苦情 (CFPB) |

### SEC・証券
| テーブル名 | 概要 |
|---|---|
| `SEC_METRICS_TIMESERIES` | 主要企業の四半期/年次収益セグメント (10-Q/10-K) |
| `SEC_FISCAL_CALENDARS` | 企業の会計年度カレンダー |
| `SEC_NPORT_TIMESERIES` | ファンドの月次統計 (NPORT申請) |
| `SEC_INVESTMENT_ADVISERS_TIMESERIES` | 投資顧問のForm ADVデータ |
| `IRS_FORM990_TIMESERIES` | 非課税団体のForm 990財務・運営データ |
| `IRS_FORM990_INVESTMENTS` | Form 990の投資保有データ |
| `IRS_FORM990_LOANS_AND_NOTES` | Form 990のローン・債権データ |

### 企業情報
| テーブル名 | 概要 |
|---|---|
| `COMPANY_INDEX` | 企業マスター (CIK, EIN, PermID, LEI等のID紐付け) |
| `COMPANY_CHARACTERISTICS` | 約10万社の企業属性情報 |
| `COMPANY_RELATIONSHIPS` | 企業の親子・子会社関係 |
| `COMPANY_SECURITY_RELATIONSHIPS` | 企業と証券 (株式・債券等) のマッピング |
| `COMPANY_DOMAIN_RELATIONSHIPS` | 企業とドメイン/Webサイトのマッピング |
| `COMPANY_EVENT_TRANSCRIPT_ATTRIBUTES` | 企業イベント (決算発表等) のトランスクリプト |

### エネルギー
| テーブル名 | 概要 |
|---|---|
| `EIA_ENERGY_TIMESERIES` | 天然ガス・電力・石油の販売・生産・消費・輸出入統計 |
| `NRC_REACTOR_TIMESERIES` | 原子力発電所の運転データ |
| `NRC_EVENT_NOTIFICATION` | 原子力規制委員会のイベント報告 |

### 環境・気候
| テーブル名 | 概要 |
|---|---|
| `CLIMATE_WATCH_TIMESERIES` | 温室効果ガス排出量 (セクター・ガス別, 将来シナリオ含む) |
| `EUROPEAN_COMMISSION_EDGAR_TIMESERIES` | CO2, CH4, N2O, F-ガスの排出データ (国・産業別) |
| `OUR_WORLD_IN_DATA_TIMESERIES` | 世界のCO2排出データ (国・地域・セクター別) |
| `EPA_CAM_TIMESERIES` | EPA大気質市場排出データ (発電所) |

### 気象
| テーブル名 | 概要 |
|---|---|
| `NOAA_WEATHER_METRICS_TIMESERIES` | 日次グローバル気象データ (気温, 降水, 降雪, 積雪深 / 8万局以上) |
| `AWC_METAR_TIMESERIES` | 航空気象 METAR 観測データ |
| `AWC_TAF_TIMESERIES` | 航空気象 TAF 予報データ |
| `NWS_WEATHER_ALERT_EVENTS` | 米国気象警報・注意報 |
| `NWS_WEATHER_FORECAST_EVENTS` | 郡・ZIPコード別の天気予報 |
| `NWS_WEATHER_TIMESERIES` | 気象観測ステーションの時系列データ |
| `NOAA_NWRFC_WATER_SUPPLY_TIMESERIES` | 北西部の水資源予測・観測データ |

### 犯罪
| テーブル名 | 概要 |
|---|---|
| `FBI_CRIME_TIMESERIES` | FBI犯罪統計 (州・国レベル) |
| `URBAN_CRIME_TIMESERIES` | 主要都市の犯罪データ (履歴集計) |
| `URBAN_CRIME_INCIDENT_LOG` | 都市別の犯罪イベントログ |

### 農業
| テーブル名 | 概要 |
|---|---|
| `US_DEPARTMENT_OF_AGRICULTURE_COMMODITIES_TIMESERIES` | 世界の農産物生産・供給・流通データ (国別) |

### 製造業
| テーブル名 | 概要 |
|---|---|
| `UNITED_NATIONS_INDUSTRIAL_DEVELOPMENT_ORGANIZATION_TIMESERIES` | 国別の製造業セクター統計 (2016-2023) |

### ヘルスケア
| テーブル名 | 概要 |
|---|---|
| `NPPES_PROVIDER_ADDRESSES` | 米国の医療プロバイダー住所情報 |
| `NPPES_NUCC_TAXONOMY` | 医療プロバイダーの専門分類 |
| `NPPES_NUCC_MEDICARE_TAXONOMY_CROSSWALK` | Medicare分類とのクロスウォーク |
| `NPPES_PROVIDER_TAXONOMY_AND_LICENSE_NUMBERS` | 医療プロバイダーの資格・ライセンス |
| `NPPES_PROVIDER_LICENSE_NUMBERS` | 医療プロバイダーのライセンス番号 |

### 住所・地理
| テーブル名 | 概要 |
|---|---|
| `US_ADDRESSES` | 米国の住所データ (緯度/経度座標付き) |
| `USPS_ADDRESS_CHANGE_TIMESERIES` | USPS住所変更リクエスト (ZIPコード集計) |
| `GEOGRAPHY_HIERARCHY` | 地理エンティティの階層関係 |
| `GEOGRAPHY_OVERLAPS` | 地理エンティティの重複関係 |

### テクノロジー
| テーブル名 | 概要 |
|---|---|
| `GITHUB_EVENTS` | GitHubパブリックリポジトリのイベント (push, fork, issue, PR等) |
| `GITHUB_REPOS` | GitHubリポジトリの集約データ |
| `GITHUB_STARS` | GitHubリポジトリのスター数推移 |
| `IMEI_TAC_DEVICE` | 携帯端末のブランド・モデルとTACコードの対照表 |

### 交通
| テーブル名 | 概要 |
|---|---|
| `US_DEPARTMENT_OF_TRANSPORTATION_TIMESERIES` | 月次国内ノンストップ区間データ (航空キャリア) |

### 年金・福利厚生
| テーブル名 | 概要 |
|---|---|
| `US_DEPARTMENT_OF_LABOR_FORM_5500_SCHEDULE_H_TIMESERIES` | 大規模年金・福利厚生プランの財務状況 |
| `US_DEPARTMENT_OF_LABOR_FORM_5500_SCHEDULE_SB_TIMESERIES` | 単一雇用主確定給付年金のアクチュアリー情報 |

### ホームレス
| テーブル名 | 概要 |
|---|---|
| `HOUSING_URBAN_DEVELOPMENT_TIMESERIES` | 2007年以降の米国ホームレス推定数 (州・CoC別) |

### カタログ・辞書
| テーブル名 | 概要 |
|---|---|
| `PUBLIC_DATA_CATALOG` | Snowflake Public Data全テーブルのメタデータカタログ |
| `PUBLIC_DATA_DICTIONARY` | Snowflake Public Data全テーブルのデータ辞書 |
| `PUBLIC_DATA_VARIABLE_CATALOG` | Snowflake Public Data全変数のカタログ |
| `CALENDAR_INDEX` | 共通カレンダー (日/週/月/四半期/年 + Retail 4-5-4) |

> 各主要テーブルには `_ATTRIBUTES` (属性定義) および `_PIT` (Point-in-Time履歴追跡) の補助ビューも用意されています。

---

## 2. INTERNSHIP_SHARE_DB (共有データベース / 10テーブル)

| スキーマ | テーブル名 | 行数 | 概要 |
|---|---|---|---|
| `RAKUTEN_EC` | `DELIVERABLE_EC_MALL_PURCHASE` | 1,694,437 | ECモール購買データ |
| `TRAINING` | `ACCESS_LOG` | 5,539,909 | アクセスログ |
| `TRAINING` | `CUSTOMERS` | 62,662 | 顧客マスター |
| `TRAINING` | `EMPLOYEES` | 200 | 従業員マスター |
| `TRAINING` | `ITEMS` | 387 | 商品マスター |
| `TRAINING` | `ORDERS` | 49,518 | 注文データ |
| `TRAINING` | `ORDER_DETAILS` | 50,909 | 注文明細データ |
| `TRAINING` | `SHOPS` | 30 | 店舗マスター |
| `TRAINING` | `SHOPS_2` | 40 | 店舗マスター2 |
| `TRAINING` | `WEB_PAGES` | 807 | Webページマスター |
