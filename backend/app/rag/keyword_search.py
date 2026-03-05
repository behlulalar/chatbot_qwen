"""
Keyword search over mevzuat JSON: token match + RapidFuzz.
Öncelik hybrid'de; başlık / madde metni kelime eşleşmesi ile bulunur.
"""
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional

from rapidfuzz import fuzz
from langchain_core.documents import Document

from app.config import settings, resolve_json_directory
from app.rag.text_utils import normalize_for_match, tokenize, QUERY_STOPWORDS
from app.utils.logger import setup_logger

logger = setup_logger("keyword_search", "./logs/keyword_search.log")

# Sorguda "arge" / "ar-ge" dokümanda "ar ge" olarak geçer; token eşleşmesi için genişlet
QUERY_EXPAND = [("arge", "ar ge"), ("ar-ge", "ar ge"), ("ar ge", "ar ge")]

# Index: list of { "json_path", "article_index", "doc_title_norm", "article_title_norm", "content_norm" }
_index: List[Dict] = []
_json_dir: Optional[Path] = None


def _build_index(json_directory: Path) -> List[Dict]:
    index = []
    for json_path in sorted(json_directory.glob("*.json")):
        json_path = json_path.resolve()
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            logger.error(f"Error reading {json_path.name}: {e}")
            continue
        meta = data.get("metadata", {})
        doc_title = meta.get("title", "")
        doc_title_norm = normalize_for_match(doc_title)
        articles = data.get("articles") or []
        if not articles or (articles and articles[0].get("article_number") == "0"):
            full_text = (data.get("full_text") or "").strip()
            content_norm = normalize_for_match(full_text[:800])
            index.append({
                "json_path": str(json_path),
                "article_index": 0,
                "doc_title_norm": doc_title_norm,
                "article_title_norm": "",
                "content_norm": content_norm,
            })
            continue
        for i, art in enumerate(articles):
            art_title = art.get("article_title") or ""
            content = (art.get("content") or "").strip()
            content_norm = normalize_for_match((art_title + " " + content)[:800])
            article_title_norm = normalize_for_match(art_title)
            index.append({
                "json_path": str(json_path),
                "article_index": i,
                "doc_title_norm": doc_title_norm,
                "article_title_norm": article_title_norm,
                "content_norm": content_norm,
            })
    logger.info(f"Keyword index built: {len(index)} entries from {json_directory}")
    return index


def _get_index() -> Tuple[List[Dict], Path]:
    global _index, _json_dir
    json_dir = resolve_json_directory()
    if not json_dir.exists():
        logger.warning(f"JSON directory not found: {json_dir}")
        return [], json_dir
    if not _index or _json_dir != json_dir:
        _json_dir = json_dir
        _index = _build_index(json_dir)
    return _index, json_dir


def _load_documents(pairs: List[Tuple[str, int]], json_dir: Path) -> List[Document]:
    """(json_path, article_index) listesinden Document listesi yükle; sıra korunur."""
    from app.rag.document_loader import DocumentLoader
    loader = DocumentLoader(json_directory=str(json_dir))
    seen: set = set()
    order: List[Tuple[str, int]] = []
    for path, idx in pairs:
        path = str(Path(path).resolve())
        key = (path, idx)
        if key not in seen:
            seen.add(key)
            order.append((path, idx))
    documents = []
    for json_path_str, article_index in order:
        path = Path(json_path_str)
        if not path.is_absolute():
            path = (json_dir / path.name).resolve()
        if not path.exists():
            logger.warning(f"Keyword load: path does not exist: {path}")
            continue
        try:
            all_docs = loader.load_single(path)
        except Exception as e:
            logger.error(f"Error loading {path.name}: {e}")
            continue
        if 0 <= article_index < len(all_docs):
            documents.append(all_docs[article_index])
        else:
            logger.debug(f"Keyword load: article_index {article_index} out of range for {path.name} (len={len(all_docs)})")
    return documents


def _token_matches_in_text(tokens: List[str], text: str) -> int:
    """Token eşleşmesi: kısa tokenlar tam eşleşme, uzun tokenlar prefix (ilk 5 karakter) veya tam eşleşme."""
    count = 0
    for t in tokens:
        if len(t) <= 4:
            if t in text:
                count += 1
        else:
            stem = t[:5]
            if t in text or stem in text:
                count += 1
    return count


def _expand_query_tokens(query_norm: str) -> List[str]:
    """Sorgu normalize metninden token listesi üret; arge -> ar ge gibi genişletmeler uygula."""
    expanded = query_norm
    for old, new in QUERY_EXPAND:
        expanded = expanded.replace(old, new)
    tokens = [t for t in expanded.split() if len(t) > 1]
    tokens = [t for t in tokens if t not in QUERY_STOPWORDS]
    if not tokens:
        tokens = [t for t in expanded.split() if len(t) > 1]
    return tokens


def keyword_search(
    query: str,
    top_k: int = 5,
    min_token_match: int = 1,
    json_directory: Optional[str] = None,
) -> List[Tuple[Document, float]]:
    """
    Sorguyu normalize + tokenize et; index üzerinde token eşleşmesi + RapidFuzz skoru ile ara.
    Dönen sıra skora göre (yüksek önce). Format: [(doc, score), ...]
    """
    if not query or not query.strip():
        return []
    json_dir = resolve_json_directory(json_directory) if json_directory else resolve_json_directory()
    index, _ = _get_index()
    if not index:
        logger.warning("Keyword search: index is empty (no JSON dir or no files)")
        return []

    query_norm = normalize_for_match(query)
    tokens = _expand_query_tokens(query_norm)
    if not tokens:
        tokens = tokenize(query, remove_stopwords=False)
    if not tokens:
        return []
    logger.debug(f"Keyword query_norm={query_norm[:80]!r}, tokens={tokens[:15]}")

    scored: List[Tuple[float, str, int]] = []
    for entry in index:
        text = " ".join(
            filter(None, [
                entry["doc_title_norm"],
                entry["article_title_norm"],
                entry["content_norm"],
            ])
        )
        if not text:
            continue
        token_matches = _token_matches_in_text(tokens, text)
        if token_matches < min_token_match:
            continue
        ratio = fuzz.token_set_ratio(query_norm, text)
        score = token_matches * 20 + ratio
        # Alakalı yönergeyi üste taşı: soruda AR-GE/komisyon + görevleri varsa, doc başlığı ve madde başlığı eşleşmesine ek puan
        doc_title_norm = entry.get("doc_title_norm") or ""
        article_title_norm = entry.get("article_title_norm") or ""
        if ("ar" in tokens or "ge" in tokens) and ("ar ge" in doc_title_norm or "ar-ge" in doc_title_norm):
            score += 80
        if "gorevleri" in tokens and "gorevleri" in article_title_norm:
            score += 60
        if "komisyon" in doc_title_norm and ("komisyon" in query_norm or "gorevleri" in query_norm):
            score += 40
        # E-posta şifre değiştirme: E-POSTA_YÖNERGESİ Madde 9'da öğrenci/personel prosedürü var
        if ("eposta" in query_norm or "e posta" in query_norm) and "sifre" in query_norm:
            if "e posta" in doc_title_norm or "eposta" in doc_title_norm:
                score += 90
        scored.append((score, entry["json_path"], entry["article_index"]))

    scored.sort(key=lambda x: -x[0])
    top_pairs = [(path, idx) for _, path, idx in scored[: top_k * 2]]
    # Net yönerge eşleşmesi varsa (örn. AR-GE) sadece o yönergeye ait maddeleri döndür
    if scored and top_pairs and scored[0][0] >= 150:
        best_path = top_pairs[0][0]
        same_doc = [(p, i) for p, i in top_pairs if p == best_path]
        if len(same_doc) >= 2:
            top_pairs = same_doc[: top_k]
    if not scored:
        logger.info(f"Keyword: no scored entries for query (tokens={tokens[:10]})")
        return []
    docs = _load_documents(top_pairs, json_dir)
    if not docs and top_pairs:
        logger.warning(f"Keyword: 0 docs loaded for {len(top_pairs)} pairs (paths exist?)")
    score_map = {(path, idx): score for score, path, idx in scored}
    scored_docs = []
    for i, (path, idx) in enumerate(top_pairs):
        if i < len(docs):
            s = score_map.get((path, idx), 0)
            scored_docs.append((docs[i], s))
    scored_docs.sort(key=lambda x: x[1], reverse=True)
    logger.info(f"Keyword query={query[:60]!r} -> {len(scored_docs)} docs (scored={len(scored)}, pairs={len(top_pairs)})")
    return scored_docs[:top_k]
