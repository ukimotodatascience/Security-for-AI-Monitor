import re
from typing import List, Dict, Any, Set

# 8つのセキュリティカテゴリ定義
CATEGORIES = {
    1: {
        "id": 1,
        "name": "入力検証",
        "key": "input_validation",
        "attacks": [
            "SQLi",
            "XSS",
            "コマンドインジェクション",
            "SSRF",
            "RCE",
            "パストラバーサル",
        ],
        "owasp": ["A03"],
        "asvs": "V5",
    },
    2: {
        "id": 2,
        "name": "認証",
        "key": "authentication",
        "attacks": [
            "パスワードスプレー",
            "クレデンシャルスタッフィング",
            "AITM",
            "MFAバイパス",
            "ログイン迂回",
        ],
        "owasp": ["A07"],
        "asvs": "V2",
    },
    3: {
        "id": 3,
        "name": "認可・アクセス制御",
        "key": "authorization",
        "attacks": ["IDOR", "BOLA", "BFLA", "権限昇格", "アクセス制御不備"],
        "owasp": ["A01"],
        "asvs": "V4",
    },
    4: {
        "id": 4,
        "name": "セッション管理",
        "key": "session_management",
        "attacks": [
            "CSRF",
            "セッション固定",
            "セッションハイジャック",
            "クッキー保護不備",
        ],
        "owasp": ["A07"],
        "asvs": "V3",
    },
    5: {
        "id": 5,
        "name": "データ保護・暗号",
        "key": "data_protection",
        "attacks": ["平文保存", "弱い暗号", "TLS不備", "鍵漏洩", "情報漏洩"],
        "owasp": ["A02"],
        "asvs": "V6 V8 V9",
    },
    6: {
        "id": 6,
        "name": "設定・構成",
        "key": "configuration",
        "attacks": ["デフォルト設定", "ヘッダ不備", "公開バケット", "設定ミス"],
        "owasp": ["A05"],
        "asvs": "V14",
    },
    7: {
        "id": 7,
        "name": "依存・サプライチェーン",
        "key": "dependency_supply_chain",
        "attacks": [
            "既知CVE",
            "typosquatting",
            "polyfill.io汚染",
            "悪意あるパッケージ",
        ],
        "owasp": ["A06"],
        "asvs": "V10",
    },
    8: {
        "id": 8,
        "name": "ロギング・ロジック",
        "key": "logging_logic",
        "attacks": ["ログ不在", "監視不在", "ロジック悪用", "仕様の悪用"],
        "owasp": ["A09", "A04"],
        "asvs": "V7 V11",
    },
}

# CWE IDからカテゴリIDへのマッピング
CWE_MAP = {
    # 1. 入力検証
    "CWE-20": 1,  # Improper Input Validation
    "CWE-74": 1,  # Injection
    "CWE-77": 1,  # Command Injection
    "CWE-78": 1,  # OS Command Injection
    "CWE-79": 1,  # XSS
    "CWE-89": 1,  # SQLi
    "CWE-90": 1,  # LDAP Injection
    "CWE-91": 1,  # XML Injection
    "CWE-94": 1,  # Code Injection
    "CWE-95": 1,  # Eval Injection
    "CWE-917": 1,  # Expression Language Injection
    "CWE-918": 1,  # SSRF
    "CWE-22": 1,  # Path Traversal
    "CWE-23": 1,  # Relative Path Traversal
    # 2. 認証
    "CWE-287": 2,  # Improper Authentication
    "CWE-306": 2,  # Missing Authentication for Critical Function
    "CWE-307": 2,  # Improper Restriction of Excessive Authentication Attempts
    "CWE-521": 2,  # Weak Password Requirements
    "CWE-290": 2,  # Authentication Bypass by Spoofing
    # 3. 認可・アクセス制御
    "CWE-285": 3,  # Improper Authorization
    "CWE-862": 3,  # Missing Authorization
    "CWE-863": 3,  # Incorrect Authorization
    "CWE-639": 3,  # IDOR / BOLA
    "CWE-269": 3,  # Improper Privilege Management
    "CWE-250": 3,  # Execution with Unnecessary Privileges
    "CWE-284": 3,  # Improper Access Control
    # 4. セッション管理
    "CWE-352": 4,  # CSRF
    "CWE-384": 4,  # Session Fixation
    "CWE-613": 4,  # Insufficient Session Expiration
    "CWE-614": 4,  # Sensitive Cookie in HTTPS Session Without 'Secure' Attribute
    # 5. データ保護・暗号
    "CWE-311": 5,  # Missing Encryption of Sensitive Data
    "CWE-312": 5,  # Cleartext Storage of Sensitive Information
    "CWE-319": 5,  # Cleartext Transmission of Sensitive Information
    "CWE-326": 5,  # Inadequate Encryption Strength
    "CWE-327": 5,  # Use of a Broken or Risky Cryptographic Algorithm
    "CWE-295": 5,  # Improper Certificate Validation
    "CWE-798": 5,  # Use of Hard-coded Credentials
    "CWE-522": 5,  # Insufficiently Protected Credentials
    "CWE-922": 5,  # Insecure Storage of Sensitive Information
    # 6. 設定・構成
    "CWE-16": 6,  # Configuration
    "CWE-2": 6,  # Environment
    "CWE-693": 6,  # Protection Mechanism Failure
    "CWE-1004": 6,  # Sensitive Cookie Without 'HttpOnly' Attribute
    "CWE-209": 6,  # Generation of Error Message Containing Sensitive Information
    "CWE-532": 6,  # Insertion of Sensitive Information into Log File
    "CWE-732": 6,  # Incorrect Permission Assignment for Critical Resource
    "CWE-1188": 6,  # Insecure Default Initialization
    # 7. 依存・サプライチェーン
    "CWE-1395": 7,  # Dependency on Vulnerable Third-Party Component
    "CWE-1104": 7,  # Use of Unmaintained Third-Party Component
    "CWE-829": 7,  # Inclusion of Functionality from Untrusted Control Sphere
    "CWE-937": 7,  # OWASP Top 10 2013: Using Components with Known Vulnerabilities
    # 8. ロギング・ロジック
    "CWE-778": 8,  # Insufficient Logging
    "CWE-840": 8,  # Business Logic Error
    "CWE-841": 8,  # Improper Behavioral Order
}

# キーワード正規表現の定義（大文字小文字無視）
KEYWORDS_MAP = {
    1: re.compile(
        r"(sql\s*injection|\bsqli\b|cross\s*site\s*scripting|\bxss\b|command\s*injection|\bssrf\b|server\s*side\s*request\s*forgery|path\s*traversal|directory\s*traversal|\bxxe\b|xml\s*external\s*entity|input\s*validation|remote\s*code\s*execution|\brce\b|deserialization|untrusted\s*data|injected|injecting)",
        re.IGNORECASE,
    ),
    2: re.compile(
        r"(authentication|authn|password|credential|login|\bmfa\b|\btotp\b|oauth|\bjwt\b|json\s*web\s*token|sign\s*in|sign-in|identity|adversary\s*in\s*the\s*middle|\baitm\b|brute\s*force|bruteforce|multifactor|multi-factor|passcode|credential\s*stuffing|password\s*spray)",
        re.IGNORECASE,
    ),
    3: re.compile(
        r"(authorization|authz|privilege|\bidor\b|\bbola\b|\bbfla\b|access\s*control|permission|\brbac\b|\babac\b|escalation|unauthorized\s*access|bypass\s*access|broken\s*object\s*level|broken\s*function\s*level)",
        re.IGNORECASE,
    ),
    4: re.compile(
        r"(\bsession\b|\bcsrf\b|\bxsrf\b|cross\s*site\s*request\s*forgery|cookie|hijack|fixation|session\s*token|session\s*id|session\s*fixation|session\s*hijacking)",
        re.IGNORECASE,
    ),
    5: re.compile(
        r"(encryption|decryption|cryptographic|cipher|\btls\b|\bssl\b|plaintext|cleartext|private\s*key|secret\s*leak|credential\s*leak|leakage|data\s*exposure|information\s*disclosure|eavesdropping|hardcoded\s*secret|hard-coded)",
        re.IGNORECASE,
    ),
    6: re.compile(
        r"(misconfiguration|default\s*credential|default\s*password|default\s*setting|security\s*header|cors|cross\s*origin|bucket|\bs3\b|exposed\s*bucket|publicly\s*accessible|improper\s*setting|default\s*initialization|error\s*message)",
        re.IGNORECASE,
    ),
    7: re.compile(
        r"(\b(?:vulnerable|software|package|project|third-party|external)\s*dependenc(?:y|ies)\b|supply\s*chain|\bnpm\b|\bpypi\b|\bmaven\b|\bcargo\b|\b(?:malicious|vulnerable|third-party)\s*package\b|third-party|third\s*party|vulnerable\s*version|typosquatting|\b(?:dependency|package|supply\s*chain)\s*poisoning\b|polyfill|malicious\s*package|malicious\s*dependency)",
        re.IGNORECASE,
    ),
    8: re.compile(
        r"(logging|monitoring|audit|logic\s*flaw|business\s*logic|abuse|workflow|insufficient\s*log|insufficient\s*monitoring|tampering|logic\s*bypass)",
        re.IGNORECASE,
    ),
}

# 日本語キーワードの定義（補助的）
JA_KEYWORDS_MAP = {
    1: re.compile(
        r"(入力検証|インジェクション|クロスサイト|スクリプティング|コマンド注入|トラバーサル|強制ブラウズ|外部実体)",
        re.IGNORECASE,
    ),
    2: re.compile(
        r"(認証|パスワード|ログイン|多要素|資格情報|中間者攻撃|ブルートフォース|総当たり)",
        re.IGNORECASE,
    ),
    3: re.compile(
        r"(認可|アクセス制御|権限昇格|権限奪取|特権|アクセス権)", re.IGNORECASE
    ),
    4: re.compile(
        r"(セッション|クッキー|ハイジャック|固定化|リクエスト強要)", re.IGNORECASE
    ),
    5: re.compile(r"(暗号|平文|情報漏洩|漏洩|データ露出|秘密鍵|暴露)", re.IGNORECASE),
    6: re.compile(
        r"(設定不備|設定ミス|デフォルト設定|初期設定|公開バケット|バケット公開|ヘッダ欠如)",
        re.IGNORECASE,
    ),
    7: re.compile(
        r"(依存関係|依存ライブラリ|外部依存|サプライチェーン|外部パッケージ|サードパーティパッケージ|サードパーティ|ライブラリ|パッケージ汚染|サプライチェーン汚染|polyfill汚染|タイポスクワッティング)",
        re.IGNORECASE,
    ),
    8: re.compile(
        r"(ロギング|ログ|監視|ロジック|業務ロジック|設計の不備|監査証跡)", re.IGNORECASE
    ),
}


def classify_item(item: Dict[str, Any], category_type: str) -> List[int]:
    """CWE ID、OWASPマッピング、キーワードに基づいて、対象セキュリティ項目を

    8つのカテゴリ（1〜8）に分類します。多重分類を許容します。

    Args:
        item: 辞書化されたセキュリティデータ (CVE, ArXiv, RSS等)
        category_type: アイテムの種別 ("cves", "arxiv", "rss_articles", "rss_news", "ghsa_advisories")

    Returns:
        該当するカテゴリID (1〜8) のリスト。
    """
    matched: Set[int] = set()

    # --- 1. カテゴリ自体の性質による自動付与 ---
    # (無条件でのカテゴリ7付与は廃止し、実際のCWEやキーワードのシグナルに依存します)

    # --- 2. CWE IDに基づくマッピング ---
    # cve_ids またはネストされた cwes から CWE を抽出
    cwe_ids = item.get("cwe_ids", [])
    if not cwe_ids and "cwes" in item:
        cwe_ids = [c.get("cwe_id") for c in item["cwes"] if c.get("cwe_id")]

    for cwe_id in cwe_ids:
        if not cwe_id:
            continue
        cwe_str = str(cwe_id).strip().upper()
        # CWE-MAPに直接合致するか
        if cwe_str in CWE_MAP:
            matched.add(CWE_MAP[cwe_str])
        else:
            # 前方一致での部分判定 (例: CWE-79.xxx)
            for k, v in CWE_MAP.items():
                if cwe_str.startswith(k + "."):
                    matched.add(v)

    # --- 3. OWASP Top 10 マッピングに基づく判定 ---
    owasp_list = item.get("owasp_mapping", [])
    for owasp in owasp_list:
        if not owasp:
            continue
        owasp_str = str(owasp).strip().upper()

        # A01 -> 3. 認可・アクセス制御
        if "A01" in owasp_str:
            matched.add(3)
        # A02 -> 5. データ保護・暗号
        elif "A02" in owasp_str:
            matched.add(5)
        # A03 -> 1. 入力検証
        elif "A03" in owasp_str:
            matched.add(1)
        # A05 -> 6. 設定・構成
        elif "A05" in owasp_str:
            matched.add(6)
        # A06 -> 7. 依存・サプライチェーン
        elif "A06" in owasp_str:
            matched.add(7)
        # A07 -> 2. 認証 もしくは 4. セッション管理 (キーワードで精緻化、デフォルトは両方)
        elif "A07" in owasp_str:
            matched.add(2)
            matched.add(4)
        # A09, A04 -> 8. ロギング・ロジック
        elif "A09" in owasp_str or "A04" in owasp_str:
            matched.add(8)

    # --- 4. テキストキーワードに基づく判定 ---
    # 解析対象テキストを結合
    text_parts = []

    # 各種データモデルのタイトルや説明文を取得
    title = (
        item.get("title") or item.get("summary")
        if category_type == "ghsa_advisories"
        else item.get("title")
    )
    description = item.get("description") or item.get("summary")

    # 翻訳テキストもあれば対象に含める
    title_ja = item.get("title_ja")
    description_ja = item.get("description_ja") or item.get("summary_ja")

    if title:
        text_parts.append(str(title))
    if description:
        text_parts.append(str(description))
    if title_ja:
        text_parts.append(str(title_ja))
    if description_ja:
        text_parts.append(str(description_ja))

    # CVEの場合、影響を受けるパッケージ名やベンダー名もキーワードの補助にする
    if category_type == "cves":
        cpe_names = item.get("cpe_names", [])
        text_parts.extend([str(cpe) for cpe in cpe_names])
    elif category_type == "ghsa_advisories":
        pkg = item.get("affected_package")
        if pkg:
            text_parts.append(str(pkg))

    combined_text = "\n".join(text_parts)

    if combined_text:
        # 英語キーワードマッチング
        for cat_id, pattern in KEYWORDS_MAP.items():
            if pattern.search(combined_text):
                matched.add(cat_id)

        # 日本語キーワードマッチング
        for cat_id, pattern in JA_KEYWORDS_MAP.items():
            if pattern.search(combined_text):
                matched.add(cat_id)

    # --- 5. フォールバック判定 ---
    # 何にもマッチしなかった場合は空のままにします。
    return sorted(list(matched))
