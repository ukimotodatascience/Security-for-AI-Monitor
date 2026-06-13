import os
import json
import hashlib
import time
import re
import logging
import httpx

logger = logging.getLogger("Translator")


def is_likely_english(text: str) -> bool:
    """Checks if the text contains any Japanese characters.

    If it does, we assume it's already translated or in Japanese.
    Also ensures the text actually contains some letters to avoid translating pure numbers/symbols.
    """
    if not text or not isinstance(text, str):
        return False
    # Check for Hiragana, Katakana, and Kanji
    if re.search(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]", text):
        return False
    # Check if there are alphabetical characters
    if not re.search(r"[a-zA-Z]", text):
        return False
    return True


class Translator:
    def __init__(self, cache_dir: str = "data/processed"):
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, "translation_cache.json")
        self.cache = {}
        self.load_cache()

    def load_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self.cache = json.load(f)
                logger.info(f"Loaded {len(self.cache)} translations from cache.")
            except Exception as e:
                logger.error(f"Failed to load translation cache: {e}")
        else:
            self.cache = {}

    def save_cache(self):
        os.makedirs(self.cache_dir, exist_ok=True)
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(self.cache)} translations to cache file.")
        except Exception as e:
            logger.error(f"Failed to save translation cache: {e}")

    def translate(
        self, text: str, target_lang: str = "ja", source_lang: str = "en"
    ) -> str:
        if not text or not isinstance(text, str):
            return ""
        text_stripped = text.strip()
        if not text_stripped:
            return ""

        # Use MD5 hash of the original text as key
        key = hashlib.md5(text_stripped.encode("utf-8")).hexdigest()
        if key in self.cache:
            return self.cache[key]

        # Call Google gtx API
        url = "https://translate.googleapis.com/translate_a/single"
        params = {"client": "gtx", "sl": source_lang, "tl": target_lang, "dt": "t"}
        data = {"q": text_stripped}

        for attempt in range(3):
            try:
                # Respect rate limits and avoid aggressive requests
                time.sleep(0.1)
                response = httpx.post(url, params=params, data=data, timeout=10.0)
                if response.status_code == 200:
                    result = response.json()
                    translated_sentences = []
                    if result and len(result) > 0 and result[0]:
                        for item in result[0]:
                            if item and len(item) > 0 and item[0]:
                                translated_sentences.append(item[0])
                        translated_text = "".join(translated_sentences)

                        # Save to cache
                        self.cache[key] = translated_text
                        return translated_text
                elif response.status_code == 429:
                    logger.warning(
                        f"Rate limited by Translation API. Attempt {attempt + 1}/3. Waiting..."
                    )
                    time.sleep(2.0)
            except Exception as e:
                logger.error(
                    f"Translation request error (attempt {attempt + 1}/3): {e}"
                )
                time.sleep(1.0)

        # Fallback to original text if translation failed
        return text_stripped
