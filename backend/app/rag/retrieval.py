"""
Hybrid retrieval: BM25 (keyword) + Vector (semantic) search.
Sonuçlar RRF (Reciprocal Rank Fusion) ile birleştirilir.
"""
from __future__ import annotations

from typing import List, Tuple, Optional

from langchain_core.documents import Document
from rank_bm25 import BM25Okapi

from app.rag.text_utils import normalize_turkish
from app.rag.vector_store import VectorStoreManager
from app.utils.logger import setup_logger

logger = setup_logger("retrieval", "./logs/retrieval.log")

# ---------------------------------------------------------------------------
# BM25 Index — startup'ta bir kez yüklenir, sonra cache'de tutulur
# ---------------------------------------------------------------------------
_bm25_index: Optional[BM25Okapi] = None
_bm25_docs: List[Tuple[Document, float]] = []  # (doc, dummy_score) listesi


def _tokenize_for_bm25(text: str) -> List[str]:
    """
    Türkçe metni BM25 için tokenize et.
    normalize_turkish + split + min 2 karakter filtresi.
    """
    normalized = normalize_turkish(text)
    tokens = normalized.split()
    return [t for t in tokens if len(t) >= 2]


def _build_bm25_index(vector_store_manager: VectorStoreManager) -> None:
    """
    ChromaDB'deki tüm chunk'ları okuyup BM25 index oluştur.
    Uygulama başlangıcında bir kez çalışır.
    """
    global _bm25_index, _bm25_docs

    logger.info("Building BM25 index from ChromaDB...")

    try:
        if not vector_store_manager.vectorstore:
            logger.warning("BM25: vectorstore yok, index oluşturulamadı.")
            return
        # ChromaDB'den tüm dökümanları çek
        collection = vector_store_manager.vectorstore._collection
        result = collection.get(include=["documents", "metadatas"])

        raw_docs = result.get("documents") or []
        raw_metas = result.get("metadatas") or []

        if not raw_docs:
            logger.warning("BM25: ChromaDB boş, index oluşturulamadı.")
            return

        # Document nesneleri oluştur
        docs = []
        for content, meta in zip(raw_docs, raw_metas):
            docs.append(Document(page_content=content, metadata=meta or {}))

        # Tokenize
        tokenized_corpus = [_tokenize_for_bm25(doc.page_content) for doc in docs]

        _bm25_index = BM25Okapi(tokenized_corpus)
        _bm25_docs = [(doc, 0.0) for doc in docs]

        logger.info(f"BM25 index built: {len(docs)} chunks indexed.")

    except Exception as e:
        logger.error(f"BM25 index build failed: {e}", exc_info=True)
        _bm25_index = None
        _bm25_docs = []


def _bm25_search(query: str, k: int) -> List[Tuple[Document, float]]:
    """
    BM25 ile keyword araması yap.
    Dönen skor: normalize edilmiş BM25 skoru (0-1 arası, yüksek = iyi).
    """
    if _bm25_index is None or not _bm25_docs:
        logger.debug("BM25 index yok, keyword search atlandı.")
        return []

    query_tokens = _tokenize_for_bm25(query)
    if not query_tokens:
        return []

    scores = _bm25_index.get_scores(query_tokens)

    # Skoru normalize et (0-1 arası)
    _max = max(scores)
    max_score = _max if _max > 0 else 1.0
    normalized_scores = scores / max_score

    # En yüksek k sonucu al
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]

    results = []
    for idx in top_indices:
        if normalized_scores[idx] > 0.01:  # Çok düşük skorları at
            doc, _ = _bm25_docs[idx]
            # BM25 skoru yüksek = iyi, ama vektör skoru düşük = iyi
            # RRF için distance formatına çevir: 1 - normalized_score
            bm25_distance = 1.0 - float(normalized_scores[idx])
            results.append((doc, bm25_distance))

    logger.debug(f"BM25 search: {len(results)} results for query '{query[:40]}'")
    return results


def _rrf_merge(
    vector_results: List[Tuple[Document, float]],
    bm25_results: List[Tuple[Document, float]],
    k_rrf: int = 60,
    vector_weight: float = 0.6,
    bm25_weight: float = 0.4,
) -> List[Tuple[Document, float]]:
    """
    Reciprocal Rank Fusion ile vektör ve BM25 sonuçlarını birleştir.

    RRF skoru = Σ weight / (k_rrf + rank)
    Yüksek RRF skoru = daha alakalı.
    Sonuç olarak distance formatında döner (1 - rrf_score) — düşük = iyi.
    """
    # Dökümanları unique key ile tanımla: title + article_number + chunk_index
    def doc_key(doc: Document) -> str:
        return (
            doc.metadata.get("title", "")
            + "|"
            + str(doc.metadata.get("article_number", ""))
            + "|"
            + str(doc.metadata.get("chunk_index", 0))
        )

    rrf_scores: dict[str, float] = {}
    doc_map: dict[str, Document] = {}

    # Vektör sonuçları — sıralama zaten score'a göre (düşük = iyi)
    for rank, (doc, score) in enumerate(vector_results):
        key = doc_key(doc)
        rrf_scores[key] = rrf_scores.get(key, 0.0) + vector_weight / (k_rrf + rank + 1)
        doc_map[key] = doc

    # BM25 sonuçları — sıralama distance'a göre (düşük = iyi = yüksek BM25 skoru)
    for rank, (doc, score) in enumerate(bm25_results):
        key = doc_key(doc)
        rrf_scores[key] = rrf_scores.get(key, 0.0) + bm25_weight / (k_rrf + rank + 1)
        doc_map[key] = doc

    # RRF skoruna göre sırala (yüksek = iyi)
    sorted_keys = sorted(rrf_scores.keys(), key=lambda k: rrf_scores[k], reverse=True)

    # Distance formatına çevir: 1 - normalized_rrf_score
    max_rrf = rrf_scores[sorted_keys[0]] if sorted_keys else 1.0
    results = []
    for key in sorted_keys:
        doc = doc_map[key]
        # normalize: 0 = mükemmel, 1 = alakasız
        distance = 1.0 - (rrf_scores[key] / max_rrf)
        results.append((doc, distance))

    return results


def _enhance_query_for_vector(question: str) -> str:
    """Vector araması için sorguyu zenginleştir."""
    q = normalize_turkish(question)
    enhanced = question
    if "lisansustu" in q or "yuksek lisans" in q or "master" in q or "doktora" in q:
        enhanced = question + " lisansüstü yüksek lisans master doktora"
    elif "lisans" in q and "lisansustu" not in q:
        enhanced = question + " lisans ön lisans -lisansüstü"
    if "harf not" in q or "basari not" in q or "not sistemi" in q:
        enhanced += " harf notları başarı notları tablo bağıl değerlendirme"
    if "gecme notu" in q or "ders gecme" in q:
        enhanced += " bağıl değerlendirme geçme notu tablo"
    if "yaz okulu" in q or "yaz ogreti" in q:
        enhanced += " yaz okulu yaz öğretimi"
    if "mezuniyet" in q or "mezun" in q:
        enhanced += " mezuniyet şartları koşulları"
    if "basvuru" in q:
        enhanced += " başvuru kabul kayıt"
    if ("sifre" in q or "eposta" in q or "e-posta" in q) and ("degistir" in q or "yenile" in q or "talep" in q):
        enhanced += " e-posta şifre değiştirme öğrenci personel fakülte meslek yüksekokulu TYS"
    if "ar ge" in q or "arge" in q or "ar-ge" in q or ("komisyon" in q and "gorev" in q):
        enhanced += " ar ge komisyon görevleri bilimsel araştırma"
    return enhanced


def invalidate_bm25_index() -> None:
    """BM25 indeksini sıfırla (yeni doküman eklendiğinde çağrılmalı)."""
    global _bm25_index, _bm25_docs
    _bm25_index = None
    _bm25_docs = []
    logger.info("BM25 index invalidated — will rebuild on next query.")


def _deduplicate_by_article(
    results: List[Tuple[Document, float]],
) -> List[Tuple[Document, float]]:
    """
    Aynı (source, article_number) çiftinden gelen chunk'ları BİRLEŞTİR.
    - Aynı maddenin farklı chunk'ları tek bir Document'ta merge edilir
    - Farklı dokümanlardan gelen aynı numaralı maddeler ayrı tutulur
    - Skor olarak en iyi (en düşük) chunk skoru kullanılır
    """
    from collections import OrderedDict

    groups: OrderedDict[str, List[Tuple[Document, float]]] = OrderedDict()

    for doc, score in results:
        key = (
            doc.metadata.get("source", "")
            + "|"
            + str(doc.metadata.get("article_number", ""))
        )
        if key not in groups:
            groups[key] = []
        groups[key].append((doc, score))

    deduped: List[Tuple[Document, float]] = []
    merged_count = 0

    for key, group in groups.items():
        if len(group) == 1:
            deduped.append(group[0])
        else:
            group.sort(key=lambda x: x[0].metadata.get("chunk_index", 0))
            best_score = min(s for _, s in group)
            contents = [d.page_content for d, _ in group]
            merged_content = _merge_chunk_contents(contents)
            merged_meta = group[0][0].metadata.copy()
            merged_meta.pop("chunk_index", None)
            merged_meta.pop("is_chunked", None)
            merged_meta["character_count"] = len(merged_content)
            merged_doc = Document(page_content=merged_content, metadata=merged_meta)
            deduped.append((merged_doc, best_score))
            merged_count += 1

    if merged_count > 0 or len(deduped) < len(results):
        logger.debug(
            f"Dedup: {len(results)} → {len(deduped)} "
            f"({merged_count} articles had chunks merged)"
        )

    return deduped


def _merge_chunk_contents(contents: List[str]) -> str:
    """Birden fazla chunk'ın içeriğini birleştir, tekrar eden başlıkları kaldır."""
    if len(contents) == 1:
        return contents[0]

    first_line = contents[0].split("\n")[0].strip()
    merged_parts = [contents[0]]

    for content in contents[1:]:
        lines = content.split("\n")
        if lines and lines[0].strip() == first_line:
            merged_parts.append("\n".join(lines[1:]).strip())
        else:
            merged_parts.append(content)

    return "\n\n".join(p for p in merged_parts if p.strip())


def hybrid_retrieve(
    query: str,
    retrieval_k: int = 15,
    vector_store_manager: Optional[VectorStoreManager] = None,
) -> List[Tuple[Document, float]]:
    """
    Hybrid retrieval: BM25 + Vector, RRF ile birleştirilir.

    retrieval_k: response_generator'ın istediği nihai doküman sayısı.
    İçeride her iki arama da 3*retrieval_k ile çalışır, RRF + dedup sonrası
    en iyi sonuçlar döner (filtreleme response_generator'da yapılır).
    """
    global _bm25_index

    vs = vector_store_manager or VectorStoreManager()
    vs.create_or_load()

    if _bm25_index is None:
        _build_bm25_index(vs)

    search_k = retrieval_k * 3

    vector_docs: List[Tuple[Document, float]] = []
    try:
        enhanced_q = _enhance_query_for_vector(query)
        logger.debug(f"Vector query: {enhanced_q!r}")
        vector_docs = vs.search_with_score(enhanced_q, k=search_k)
    except Exception as e:
        logger.warning(f"Vector search failed: {e}")

    bm25_docs = _bm25_search(query, k=search_k)

    logger.debug(f"Vector: {len(vector_docs)} results | BM25: {len(bm25_docs)} results")
    for i, (doc, score) in enumerate(vector_docs[:3]):
        logger.debug(f"  VEC [{i+1}] score={score:.3f} | {doc.metadata.get('title','N/A')[:35]} | Madde {doc.metadata.get('article_number','N/A')}")
    for i, (doc, score) in enumerate(bm25_docs[:3]):
        logger.debug(f"  BM25 [{i+1}] dist={score:.3f} | {doc.metadata.get('title','N/A')[:35]} | Madde {doc.metadata.get('article_number','N/A')}")

    if vector_docs and bm25_docs:
        merged = _rrf_merge(vector_docs, bm25_docs, vector_weight=0.6, bm25_weight=0.4)
    elif vector_docs:
        merged = vector_docs
    else:
        merged = bm25_docs

    deduped = _deduplicate_by_article(merged)

    logger.info(
        f"Hybrid retrieval: vector={len(vector_docs)}, bm25={len(bm25_docs)}, "
        f"merged={len(merged)}, deduped={len(deduped)}"
    )

    return deduped[:search_k]
