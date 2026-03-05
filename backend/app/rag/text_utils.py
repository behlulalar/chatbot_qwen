"""
Text normalization and tokenization for RAG (keyword + vector).
Lowercase + ASCII for consistent matching; tokenize with stopword filter.
"""
import re
import unicodedata
from typing import List

# Türkçe karakter → ASCII (önce büyük/küçük dönüşümü öncesi uygulanmalı)
TURKISH_MAP = {
    "İ": "I",
    "ı": "i",
    "Ğ": "G",
    "ğ": "g",
    "Ü": "U",
    "ü": "u",
    "Ş": "S",
    "ş": "s",
    "Ö": "O",
    "ö": "o",
    "Ç": "C",
    "ç": "c",
}


def normalize_turkish(text: str) -> str:
    """Türkçe metni lowercase + ASCII yap (İ→i, ş→s vb.)."""
    if not text:
        return ""
    result = text
    for turkish, ascii_char in TURKISH_MAP.items():
        result = result.replace(turkish, ascii_char)
    result = result.lower()
    result = unicodedata.normalize("NFD", result)
    result = "".join(c for c in result if unicodedata.category(c) != "Mn")
    return result


def normalize_for_match(text: str) -> str:
    """Eşleşme için: normalize_turkish + noktalama boşluk."""
    if not text:
        return ""
    s = normalize_turkish(text.strip())
    s = re.sub(r"[^\w\s]", " ", s, flags=re.UNICODE)
    s = re.sub(r"\s+", " ", s).strip()
    return s


# Sorgu tokenize edilirken çıkarılacak stopword'ler (eşleşme zorunlu değil)
QUERY_STOPWORDS = frozenset({
    "nedir", "neler", "nasil", "ne", "mi", "mu", "mı", "bir", "bu", "ile", "icin", "için",
    "var", "yok", "varmi", "varmı", "var mi", "hakkinda", "hakkında", "olan", "ise", "gibi",
    "kadar", "kac", "kacdir", "kaç", "kaçtır", "puandir", "almam", "gerek", "gerekir",
    "dir", "dur", "dır", "dür", "mu", "mi", "mı", "mü",
})


def tokenize(text: str, remove_stopwords: bool = False) -> List[str]:
    """
    Metni kelimelere böl; 1 karakteri at, isteğe stopword çıkar.
    """
    if not text:
        return []
    s = normalize_for_match(text)
    tokens = [t for t in s.split() if len(t) > 1]
    if remove_stopwords:
        tokens = [t for t in tokens if t not in QUERY_STOPWORDS]
    return tokens
