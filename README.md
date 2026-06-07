# Security-for-AI-Monitor

AIシステム特有のセキュリティ脅威、脆弱性、関連ツール、および最新の学術論文などの情報を各種外部ソースから統合的に収集し、監視するためのデータ収集パイプラインです。

---

## 1. データパイプライン全体の概要とデータフロー

本システムは、Notion データベース（または未設定時のモックフォールバックデータ）に定義された「監視キーワード」「監視製品」「情報ソース」の設定データを入力とし、外部の多様なセキュリティ情報源・学術情報源からデータを収集します。

```mermaid
graph TD
    subgraph Notion (設定入力)
        Keywords[監視キーワード]
        Products[監視製品]
        Sources[情報ソース]
    end

    subgraph 外部データソース (API / RSS / GitHub)
        NVD[NVD API]
        CISA[CISA KEV Feed]
        ATLAS[MITRE ATLAS GitHub]
        ArXiv[arXiv API]
        GitHub[GitHub Repos/Search API]
        GHSA[GitHub Advisories API]
        FIRST[FIRST EPSS API]
        CWE[MITRE CWE API]
        RSS[RSS / Atom Feeds]
    end

    subgraph 保存データ (data/raw/*.parquet)
        cve[CVEModel]
        cpe[CPEModel]
        kev[KEVModel]
        tactic[ATLASTacticModel]
        technique[ATLASTechniqueModel]
        casestudy[ATLASCaseStudyModel]
        arxiv[ArXivModel]
        github[GitHubRepoModel]
        ghsa[GHSAModel]
        epss[EPSSModel]
        cwe_data[CWEModel]
        art[ArticleModel]
        news[NewsModel]
    end

    %% データフローの紐付け
    Keywords -->|キーワード検索| NVD
    Keywords -->|キーワード検索| ArXiv

    Products -->|製品名・ベンダーで取得/検索| GitHub
    Products -->|該当パッケージ/キーワードでフィルタ| GHSA

    Sources -->|RSSクロール| RSS

    %% 外部データから保存
    NVD --> cve
    NVD --> cpe
    CISA --> kev
    ATLAS --> tactic
    ATLAS --> technique
    ATLAS --> casestudy
    ArXiv --> arxiv
    GitHub --> github
    GHSA --> ghsa
    RSS -->|Typeがrss, blog等| art
    RSS -->|Typeがnews等| news

    %% 依存解決処理
    cve -->|CVE ID抽出| FIRST
    ghsa -->|CVE ID抽出| FIRST
    kev -->|CVE ID抽出| FIRST
    FIRST --> epss


    cve -->|CWE ID抽出| CWE
    CWE --> cwe_data
```

### 依存関係解決の流れ（パイプライン後半の処理）
* **EPSSスコアの取得**: NVD CVE、GitHub Advisories (GHSA)、および CISA KEV で収集されたすべての CVE ID リストに基づき、FIRST EPSS API からバッチで悪用確率スコアを取得して `epss.parquet` に保存します。
* **CWE詳細情報の取得**: 収集された CVE データに含まれる CWE ID から、新規の ID のみを選択し、MITRE CWE API から脆弱性タイプの定義や対策詳細を取得して `cwes.parquet` に保存します。

---

## 2. 各データの収集方法とフィルタリング基準

各データモデルの取得元、取得方法、およびフィルタリング条件のまとめです。詳細は各 Fetcher モジュール（[src/](src/) 配下）で実装されています。

| データ種別 | 取得元 (ソース) | 取得方法 (通信プロトコル/API) | フィルタリング・抽出ロジック |
| :--- | :--- | :--- | :--- |
| **CVE** / **CPE** | [NVD API](https://nvd.nist.gov/developers/v2) | HTTPS GET | ・`keywords` に合致する脆弱性を検索（1件あたり最大50件）<br>・直近14日間の最新CVEを収集（最大100件）<br>・各CVEの構成情報から影響のある製品（CPE）を抽出 |
| **CISA KEV** | [CISA KEV Feed](https://www.cisa.gov/known-exploited-vulnerabilities-catalog) | HTTPS GET (JSONフィード) | ・CISAが公開する「既知の悪用された脆弱性」の全データを一括取得 |
| **MITRE ATLAS** | [mitre-atlas/atlas-data](https://github.com/mitre-atlas/atlas-data) | HTTPS GET (YAMLファイル) | ・ATLAS v6の最新データ（YAML）をダウンロードし、AIセキュリティに関する攻撃戦術・手法・事例情報に構造化してパース |
| **arXiv 論文** | [arXiv API](https://arxiv.org/help/api) | HTTPS GET (XMLフィード) | ・`keywords` を検索クエリ（例: `all:"prompt injection"`）に設定し、最新の関連論文を最大20件ずつ取得 |
| **GitHub Repo** | [GitHub API](https://api.github.com) | HTTPS GET (Repos / Search API) | ・`products` で定義されたリポジトリ (`vendor/product_name`) を直接取得<br>・製品名キーワードで検索し、周辺ツール・関連リポジトリを最大5件取得 |
| **GHSA** | [GitHub Advisories API](https://api.github.com/advisories) | HTTPS GET | ・最新のアドバイザリを取得し、影響を受けるパッケージ名が `products` の製品名/エイリアス/ベンダーと一致するもの、または説明文にAIセキュリティ関連キーワード（`prompt injection`等）を含むものにフィルタリング |
| **EPSS** | [FIRST EPSS API](https://www.first.org/epss/api) | HTTPS GET | ・今回パイプラインで収集されたすべての CVE ID のリストに基づき、50件ずつのバッチでスコアを取得 |
| **CWE** | [MITRE CWE API](https://cwe-api.mitre.org) | HTTPS GET | ・収集された CVE の `cwe_ids` のうち、まだローカル（Parquet）に保存されていない新規の CWE ID に限定して詳細定義を取得 |
| **RSS 記事** / **ニュース** | 各種 RSS / Atom フィード | HTTPS GET (XMLフィード) | ・`sources` で定義されたアクティブなRSSフィードから記事を取得<br>・ソースのTypeが `news` / `news_media` なら **News**、それ以外は **Article** に分類保存 |

---

## 3. データモデルとカラム定義

本システムで収集・蓄積する各モデルのデータスキーマです。詳細な定義は [src/models.py](src/models.py) に記述されています。

<details>
<summary>Notion 設定データ (入力)</summary>

#### NotionSourceModel
情報収集対象とするRSSフィード等の設定情報。
* `source_id` (str): ソースの一意な識別子 (Notion Page ID または任意ID)
* `name` (str): ソース名
* `url` (str): フィードURL
* `type` (str): ソース種別 (`rss`, `vendor_blog`, `news`, `news_media`, `official`, `research_blog` など)
* `status` (str): アクティブ状態 (`active` / `inactive`)
* `score` (Optional[int]): 信頼度スコア
* `last_checked_at` (Optional[datetime]): 最終巡回日時
* `created_at` (datetime): Notion上の作成日時
* `updated_at` (datetime): Notion上の更新日時

#### AIKeywordModel
CVEや学術論文検索のためのキーワード設定。
* `keyword` (str): 監視キーワード（例: `prompt injection`）
* `category` (str): 脅威カテゴリ
* `weight` (float): キーワードの重要度（0.0 〜 1.0）
* `status` (str): アクティブ状態 (`active` / `inactive`)
* `created_at` (datetime): 作成日時
* `updated_at` (datetime): 更新日時

#### AIProductModel
監視対象とするAI製品および主要ライブラリの設定。
* `product_name` (str): 製品名（例: `llama-index`）
* `vendor` (str): 開発ベンダーまたはGitHubオーナー（例: `run-llama`）
* `category` (str): カテゴリ（例: `LLM Framework`）
* `aliases` (List[str]): 製品の別名や関連パッケージ（例: `['llamaindex']`）
* `weight` (float): 重要度重み
* `status` (str): アクティブ状態 (`active` / `inactive`)
</details>

<details>
<summary>脆弱性・パッケージ関連データ</summary>

#### CVEModel
NVD APIから取得した脆弱性情報。
* `cve_id` (str): CVE 識別番号（例: `CVE-2024-XXXX`）
* `published_at` (datetime): 公開日時
* `last_modified_at` (datetime): 最終更新日時
* `description` (str): 脆弱性の詳細説明（英語）
* `cvss_version` (Optional[str]): CVSS のバージョン (`v2.0`, `v3.0`, `v3.1`, `v4.0` など)
* `cvss_base_score` (Optional[float]): CVSS 基本値スコア (0.0 〜 10.0)
* `cvss_base_label` (Optional[str]): 深刻度レベル (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL` など)
* `cwe_ids` (List[str]): 関連する CWE ID のリスト
* `cpe_names` (List[str]): 影響を受ける CPE 名のリスト

#### CPEModel
CVEに関連する影響製品（CPE）の詳細情報。
* `cve_id` (str): 関連する CVE ID
* `cpe_name` (str): CPE 2.3 URI文字列
* `vulnerable` (bool): 該当製品構成が脆弱であるか否か
* `vendor` (str): ベンダー名
* `product` (str): 製品名
* `version_start` (Optional[str]): 影響開始バージョン（このバージョンを超える / 排他的な下限）
* `version_end` (Optional[str]): 影響終了バージョン（このバージョン未満 / 排他的な上限）
* `version_start_including` (Optional[str]): 影響開始バージョン（このバージョン以上 / 包含的な下限）
* `version_end_including` (Optional[str]): 影響終了バージョン（このバージョン以下 / 包含的な上限）


#### EPSSModel
FIRST APIから取得した悪用可能性予測スコア。
* `cve_id` (str): 対象の CVE ID
* `epss` (float): EPSS スコア（実際に悪用される確率、0.0 〜 1.0）
* `percentile` (float): 全脆弱性中の悪用可能性パーセンタイル値 (0.0 〜 1.0)
* `date` (date): スコア算出日

#### KEVModel
CISAカタログから取得した「既知の悪用された脆弱性」の情報。
* `cve_id` (str): 対象の CVE ID
* `product` (str): 影響を受ける製品名
* `vulnerablity_name` (str): 脆弱性の一般名称（Pydanticモデル定義およびParquetファイル上は、実名である `vulnerablity_name` のスペルで保存されます）
* `added_date` (date): カタログ追加日
* `due_date` (date): 対策期限
* `known_ransomware_campaign_use` (str): ランサムウェアキャンペーンでの悪用有無
* `required_action` (str): 推奨される対策アクション
* `notes` (Optional[str]): 備考・補足情報

#### GHSAModel
GitHub Security Advisories から取得したAI製品に関連するアドバイザリ情報。
* `advisory_id` (str): アドバイザリの一意な識別子
* `ghsa_id` (str): GHSA ID (例: `GHSA-xxxx-xxxx-xxxx`)
* `cve_id` (Optional[str]): 関連する CVE ID
* `summary` (str): 脆弱性の概要
* `severity` (str): 深刻度レベル
* `affected_package` (str): 影響を受けるパッケージ名
* `patched_versions` (Optional[str]): 修正済みバージョン
* `published_at` (datetime): 公開日時
* `updated_at` (datetime): 更新日時
* `url` (str): 詳細情報の GitHub URL

#### CWEModel
MITRE から取得した共通脆弱性タイプ（CWE）の詳細定義。
* `cwe_id` (str): CWE ID (例: `CWE-79`)
* `name` (str): 脆弱性タイプの名称
* `description` (str): 脆弱性タイプの説明
* `abstraction` (str): 抽象化レベル (`Class`, `Base`, `Variant` など)
* `status` (str): 定義のステータス
</details>

<details>
<summary>技術情報・セキュリティニュース</summary>

#### ArXivModel
arXiv APIから取得した関連学術論文。
* `arxiv_id` (str): arXiv 論文ID
* `title` (str): 論文タイトル
* `authors` (List[str]): 著者リスト
* `summary` (str): 論文の要約
* `published_at` (datetime): 論文の公開日時
* `updated_at` (datetime): 最終更新日時
* `categories` (List[str]): カテゴリ分類（例: `cs.CR`, `cs.LG`）
* `pdf_url` (str): PDFのダウンロードURL
* `abs_url` (str): 概要ページのURL
* `keywords_matched` (List[str]): マッチしたキーワード
* `owasp_mapping` (List[str]): 関連する OWASP Top 10 カテゴリ
* `mitre_mapping` (List[str]): 関連する MITRE ATLAS の戦術/手法
* `importance_score` (Optional[float]): 論文の重要度スコア

#### GitHubRepoModel
GitHub APIから取得した製品および関連ツールの活動状況。
* `repo_id` (str): リポジトリの一意なID
* `full_name` (str): リポジトリ名 (`owner/repo`)
* `description` (Optional[str]): リポジトリの説明
* `html_url` (str): GitHubのURL
* `stars` (int): スター数
* `forks` (int): フォーク数
* `language` (Optional[str]): 主要な使用言語
* `topics` (List[str]): トピック（タグ）一覧
* `created_at` (datetime): 作成日時
* `updated_at` (datetime): 更新日時
* `pushed_at` (Optional[str]): 最終プッシュ日時
* `matched_keywords` (List[str]): 合致したキーワード
* `category` (Optional[str]): カテゴリ分類

#### ArticleModel
技術ブログなどのRSSフィードから収集した記事。
* `article_id` (str): 記事の一意なID
* `title` (str): 記事タイトル
* `url` (str): 記事のURL
* `source_name` (str): 情報ソース名
* `source_type` (str): 情報ソースのタイプ
* `published_at` (datetime): 記事の公開日時
* `fetched_at` (datetime): クロール日時
* `summary` (Optional[str]): 記事の要約（テキスト）
* `category` (Optional[str]): カテゴリ
* `owasp_mapping` (List[str]): OWASPマッピング
* `mitre_mapping` (List[str]): MITREマッピング
* `nist_mapping` (List[str]): NISTマッピング
* `importance_score` (Optional[float]): 記事の重要度スコア

#### NewsModel
メディア・ニュース等のRSSフィードから収集した記事。
* `news_id` (str): ニュースの一意なID
* `title` (str): ニュースタイトル
* `url` (str): ニュースのURL
* `source` (str): 配信ソース名
* `published_at` (datetime): ニュースの公開日時
* `summary` (Optional[str]): ニュースの要約
* `mentioned_cve` (List[str]): 本文中で言及されている CVE ID
* `mentioned_products` (List[str]): 言及されている製品名
* `mentioned_threat_actors` (List[str]): 言及されている攻撃アクター名
* `category` (Optional[str]): カテゴリ
* `importance_score` (Optional[float]): 重要度スコア
</details>

<details>
<summary>MITRE ATLAS (AI攻撃手法ナレッジ)</summary>

#### ATLASTacticModel
MITRE ATLAS の攻撃戦術（AML.TAXXXX）情報。
* `tactic_id` (str): 戦術ID (例: `AML.TA0001`)
* `name` (str): 戦術名
* `description` (str): 戦術の説明

#### ATLASTechniqueModel
MITRE ATLAS の攻撃手法（AML.TXXXX）情報。
* `technique_id` (str): 手法ID (例: `AML.T0001`)
* `tactic_id` (str): 関連する戦術ID
* `name` (str): 手法名
* `description` (str): 手法の説明
* `mitigations` (List[str]): 緩和策（対策）のリスト
* `examples` (List[str]): 具体的な悪用事例のリスト

#### ATLASCaseStudyModel
MITRE ATLAS に登録されている実際の攻撃・インシデント事例。
* `case_id` (str): 事例ID (例: `AML.CS0001`)
* `title` (str): 事例のタイトル
* `summary` (str): 事例の概要・説明
* `related_techniques` (List[str]): 使用された攻撃手法のIDリスト
* `url` (str): MITRE ATLASの事例ページURL
</details>
