"""
Response Generator - Combines RAG retrieval with LLM generation.

This is the core of the chatbot - it retrieves relevant documents
and generates responses using OpenAI.
"""
import re
from typing import List, Dict, Optional, Tuple
from langchain_core.documents import Document

from app.rag.vector_store import VectorStoreManager
from app.rag.retrieval import hybrid_retrieve, _build_bm25_index
from app.rag.text_utils import normalize_turkish
from app.llm.openai_handler import OpenAIHandler
from app.llm.prompts import (
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
    CONTEXT_TEMPLATE,
    NO_CONTEXT_PROMPT
)
from app.utils.logger import setup_logger
from app.utils.cache_manager import get_cache_manager
from app.config import settings

logger = setup_logger("response_generator", "./logs/response_generator.log")


def _remove_qdms_blocks(text: str) -> str:
    """
    QDMS sayfa başlığı/altlığı meta-veri bloklarını metinden temizler.
    Blok yapısı: [Başlık]\nDoküman No:\nKYS.XXX\n...\nSayfa:\nN / M
    """
    lines = text.split('\n')
    to_remove: set = set()

    for i, line in enumerate(lines):
        if not re.match(r'\s*Doküman\s+No\s*:', line):
            continue

        block_start = i
        for j in range(i - 1, max(-1, i - 5), -1):
            s = lines[j].strip()
            if not s:
                block_start = j
            elif re.match(r'^[A-ZÇĞİÖŞÜ]', s) and len(s) > 10:
                block_start = j
                break
            else:
                break

        block_end = i
        for j in range(i + 1, min(len(lines), i + 15)):
            block_end = j
            s = lines[j].strip()
            if re.match(r'^\d+\s*/\s*\d+$', s):
                break

        for j in range(block_end + 1, min(len(lines), block_end + 3)):
            if not lines[j].strip():
                block_end = j
            else:
                break

        for j in range(block_start, block_end + 1):
            to_remove.add(j)

    if not to_remove:
        return text
    return '\n'.join(line for i, line in enumerate(lines) if i not in to_remove)


def _clean_embedded_titles(text: str, doc_title: str = "") -> str:
    """
    Sayfa geçişlerinde madde ortasına giren doküman başlıklarını temizler.
    """
    if not text or not doc_title:
        return text

    title_upper = re.sub(r'\s+', ' ', doc_title.strip()).upper()
    title_words = set(title_upper.split())

    cleaned_lines = []
    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped:
            cleaned_lines.append(line)
            continue
        if stripped.startswith("MADDE"):
            cleaned_lines.append(line)
            continue
        s_upper = re.sub(r'\s+', ' ', stripped).upper()
        s_words = set(s_upper.split())
        if (
            len(s_words) >= 3
            and len(s_words) <= len(title_words) + 3
            and len(s_words & title_words) >= len(title_words) * 0.7
            and re.match(r'^[A-ZÇĞİÖŞÜ\s,\-–()/]+$', stripped)
        ):
            continue
        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


_FIKRA_REF_SUFFIXES = r'(?:inci|[ıi]nc[iı]|üncü|nci|uncu|ıncı)'
_TR_NUM_WORDS = (
    r'(?:bir|iki|üç|dört|beş|altı|yedi|sekiz|dokuz|on|'
    r'yirmi|otuz|kırk|elli|altmış|yetmiş|seksen|doksan|yüz|sıfır)'
)
_BENT_INDENT = "\u00A0" * 6


def _format_article_text(text: str, doc_title: str = "") -> str:
    """
    Madde içeriğini temiz ve düzenli formata dönüştür.

    Pipeline:
      1. QDMS meta-veri bloklarını sil
      2. Gömülü doküman başlıklarını sil
      3. Tüm satır kırıklarını birleştir (PDF line-wrap → düz metin)
      4. Fıkra numaralarını (N) → N. formatına çevir + yeni satır
      5. Bent işaretlerini (a, b, ç...) girintili ayrı satıra al
      6. İlk fıkra numarası yoksa ekle
      7. Son temizlik
    """
    if not text or not text.strip():
        return text

    out = _remove_qdms_blocks(text)
    out = _clean_embedded_titles(out, doc_title)

    out = re.sub(r'\s*\n+\s*', ' ', out)
    out = re.sub(r' {2,}', ' ', out)

    _lq = '\u2039'
    _rq = '\u203a'
    out = re.sub(
        r'(' + _TR_NUM_WORDS + r'\s+)\((\d+)\)',
        f'\\1{_lq}\\2{_rq}', out, flags=re.IGNORECASE
    )

    out = re.sub(
        r'\s*\((\d+)\)(?!\s*' + _FIKRA_REF_SUFFIXES + r')',
        r'\n\1. ', out
    )

    out = out.replace(_lq, '(').replace(_rq, ')')

    out = re.sub(
        r'(?<=\s)([a-zçğıöşü])\)\s(?!bendi|bent)',
        f'\n{_BENT_INDENT}\\1) ', out
    )
    out = re.sub(
        r'^([a-zçğıöşü])\)\s(?!bendi|bent)',
        f'{_BENT_INDENT}\\1) ', out
    )

    stripped = out.strip()
    if re.search(r'\n\s*2\.\s', stripped) and not re.match(r'^1\.', stripped):
        out = '1. ' + out.strip()

    out = re.sub(r'\n{2,}', '\n', out)
    out = re.sub(r'^\s+$', '', out, flags=re.MULTILINE)

    return re.sub(r'^\n+', '', out).rstrip()


class ResponseGenerator:
    """
    Generates responses using RAG + LLM.
    
    Pipeline:
    1. User asks question
    2. Retrieve relevant documents from vector store
    3. Format context from retrieved docs
    4. Send to LLM with prompt
    5. Return response with sources
    
    Usage:
        generator = ResponseGenerator()
        response = generator.generate_response("Ödül nasıl alınır?")
    """

    # Tek kelime / kısa test veya anlamsız sorgular (retrieval'a girmeden no_context dön)
    _NONSENSE_OR_TEST_QUERIES = frozenset({
        "deneme", "test", "asdf", "asdfg", "asdfgh", "try", "naber", "napim", "random",
    })
    
    def __init__(
        self,
        vector_store_manager: Optional[VectorStoreManager] = None,
        openai_handler: Optional[OpenAIHandler] = None,
        retrieval_k: int = 7,
        max_distance_threshold: float = 1.5,
        enable_cache: bool = True
    ):
        """
        Initialize response generator.
        
        Args:
            vector_store_manager: Vector store manager instance
            openai_handler: OpenAI handler instance
            retrieval_k: Number of documents to retrieve
            max_distance_threshold: Maximum distance threshold for relevance
            enable_cache: Enable response caching
        """
        self.vector_store = vector_store_manager or VectorStoreManager()
        self.llm = openai_handler or OpenAIHandler()
        self.retrieval_k = retrieval_k
        self.max_distance_threshold = max_distance_threshold
        self.enable_cache = enable_cache
        
        # Initialize cache manager
        self.cache = get_cache_manager() if enable_cache else None
        
        # Cache TTL from settings
        self.response_cache_ttl = getattr(settings, 'RESPONSE_CACHE_TTL', 1800)  # 30 min default
        
        # Initialize vector store
        self.vector_store.create_or_load()
        try:
            _build_bm25_index(self.vector_store)
        except Exception as e:
            logger.warning(f"BM25 index build failed at init: {e}")

        cache_status = "enabled" if enable_cache else "disabled"
        logger.info(f"ResponseGenerator initialized: k={retrieval_k}, max_distance={max_distance_threshold}, cache={cache_status}")
    
    def generate_response(
        self,
        question: str,
        conversation_history: Optional[List[Dict]] = None,
        include_sources: bool = True
    ) -> Dict:
        """
        Generate response for user question.
        
        Args:
            question: User's question
            conversation_history: Previous conversation (optional)
            include_sources: Include source documents in response
        
        Returns:
            Dictionary with 'answer', 'sources', 'metadata'
        """
        logger.info(f"Generating response for: '{question}'")
        
        # Step 0: Check cache (only for standalone questions without history)
        if self.enable_cache and self.cache and not conversation_history:
            cache_key = self.cache._generate_key("response", question.lower().strip())
            cached_response = self.cache.get(cache_key)
            
            if cached_response:
                logger.info(f"Cache HIT for question: '{question[:50]}...'")
                cached_response['metadata']['cached'] = True
                return cached_response
        
        # Step 1: Check for meta questions (about the chatbot itself)
        meta_response = self._check_meta_question(question)
        if meta_response:
            logger.info("Returning meta response (about chatbot)")
            return meta_response

        # Step 1.5: Reject nonsensical / too-short / test queries
        cleaned = re.sub(r'[^\w]', '', question)
        if len(cleaned) < 5:
            logger.info(f"Query too short after cleaning ({len(cleaned)} chars), returning no-context")
            return self._no_context_response(question)
        # Tek kelime test/anlamsız sorgular (örn. "deneme" → sınav mevzuatı getirmesin)
        q_normalized = normalize_turkish(question).strip()
        q_words = set(q_normalized.split())
        if len(q_words) <= 2 and q_normalized in self._NONSENSE_OR_TEST_QUERIES:
            logger.info(f"Test/nonsense query detected: {question!r}, returning no-context")
            return self._no_context_response(question)

        retrieval_query = self._build_retrieval_query(question, conversation_history)

        import time
        start_time = time.time()

        retrieved_docs, llm_answer = self._retrieve_documents(retrieval_query)

        if not retrieved_docs:
            logger.warning("No relevant documents found")
            return self._no_context_response(question)

        answer_text = self._build_combined_answer(retrieved_docs, llm_answer)

        response_time = time.time() - start_time
        response = {
            "answer": answer_text,
            "sources": self._format_sources(retrieved_docs) if include_sources else [],
            "metadata": {
                "retrieved_docs": len(retrieved_docs),
                "tokens": 0,
                "cost": 0.0,
                "response_time": response_time,
                "model": self.llm.model
            }
        }

        logger.info(f"Direct response: {len(retrieved_docs)} docs, {response_time:.2f}s")

        if self.enable_cache and self.cache and not conversation_history:
            cache_key = self.cache._generate_key("response", question.lower().strip())
            self.cache.set(cache_key, response, ttl=self.response_cache_ttl)

        return response
    
    @staticmethod
    def _build_retrieval_query(
        question: str,
        conversation_history: Optional[List[Dict]] = None,
    ) -> str:
        """
        Build retrieval query. Each question is treated independently.
        Only enrich with previous context for very clear follow-up phrases.
        """
        if not conversation_history:
            return question

        q = question.strip().lower()
        is_followup = (
            q.startswith("peki")
            or q.startswith("ya ")
            or q.startswith("aynı şekilde")
            or q in ("bu konuda", "bununla ilgili", "devamı", "detay ver")
        )

        if not is_followup:
            return question

        prev_user_msgs = [
            m["content"] for m in conversation_history if m.get("role") == "user"
        ]
        if not prev_user_msgs:
            return question

        last_user = prev_user_msgs[-1]
        combined = f"{last_user} {question}"
        logger.debug(f"Retrieval query enriched: '{combined[:80]}'")
        return combined

    _LLM_JUDGE_SYSTEM = (
        "Sen SUBU Mevzuat Asistanı'sın. Kullanıcı bir soru soruyor ve arama sistemi "
        "aday maddeler buluyor. Görevin:\n"
        "1. Her maddenin soruyla ALAKALI mı ALAKASIZ mı olduğunu belirle\n"
        "2. Alakalı maddelere dayanarak soruyu kısa ve net cevapla (2-4 cümle)\n\n"
        "FORMAT (bu formatı kesinlikle takip et):\n"
        "ALAKALI: 1, 3\n"
        "ALAKASIZ: 2\n"
        "CEVAP: [Sorunun kısa ve net cevabı, alakalı maddelere dayanarak]\n\n"
        "KURALLAR:\n"
        "- Eğer bir madde sorunun konusuyla doğrudan veya dolaylı olarak ilgiliyse ALAKALI say. "
        "Örneğin 'vefat' sorusunda 'üniversiteden ayrılma/kayıt silme' maddesi alakalıdır.\n"
        "- Sadece soruyla hiç ilgisi olmayan maddeler ALAKASIZ olmalı\n"
        "- Eğer soru anlamsız, tek kelimelik bir test (ör: 'deneme', 'test', 'asdf') veya "
        "üniversite mevzuatıyla alakasız ise (ör: 'hava nasıl', 'iphone var mı') "
        "tüm maddeleri ALAKASIZ say\n"
        "- Hiçbir madde alakalı değilse: ALAKALI: YOK yazıp CEVAP satırını yazma\n"
        "- Cevabı sadece verilen kaynaklara dayandır, bilgi uydurma\n"
        "- Cevap kısa olsun, detaylar zaten tam metin olarak eklenecek"
    )

    def _llm_judge(
        self,
        question: str,
        results: List[Tuple[Document, float]],
    ) -> Tuple[List[Tuple[Document, float]], str]:
        """
        LLM tek çağrıda hem alakalılık filtresi hem kısa cevap üretir.
        Returns: (filtered_results, llm_answer)
        llm_answer boş olabilir (hiç alakalı yoksa veya hata durumunda).
        """
        if not results:
            return [], ""

        items = []
        for i, (doc, _score) in enumerate(results, 1):
            meta = doc.metadata
            title = meta.get("title", "")[:60]
            article_num = meta.get("article_number", "?")
            article_title = meta.get("article_title", "")
            preview = doc.page_content[:500].replace("\n", " ")
            items.append(
                f"{i}. [{title} - Madde {article_num} ({article_title})]\n{preview}"
            )

        user_prompt = (
            f'Soru: "{question}"\n\n'
            f"Bulunan maddeler:\n\n" + "\n\n".join(items) + "\n\n"
            f"Yukarıdaki formata göre cevapla:"
        )

        try:
            messages = [
                {"role": "system", "content": self._LLM_JUDGE_SYSTEM},
                {"role": "user", "content": user_prompt},
            ]
            response = self.llm.chat_completion(
                messages=messages,
                temperature=0.1,
                max_tokens=300,
            )
            raw_text = response.get("content", "")
            llm_time = response.get("response_time", 0)
            logger.info(
                f"LLM judge: {llm_time:.1f}s, "
                f"tokens={response.get('total_tokens', 0)}, "
                f"response='{raw_text.strip()[:150]}'"
            )

            relevant_indices: list[int] = []
            llm_answer = ""

            for line in raw_text.strip().split("\n"):
                line = line.strip()
                if line.upper().startswith("ALAKALI:"):
                    content = line.split(":", 1)[1].strip()
                    if "YOK" in content.upper():
                        relevant_indices = []
                        break
                    for part in re.split(r'[,\s]+', content):
                        digits = "".join(c for c in part if c.isdigit())
                        if digits:
                            relevant_indices.append(int(digits))
                elif line.upper().startswith("CEVAP:"):
                    llm_answer = line.split(":", 1)[1].strip()
                elif llm_answer and not line.upper().startswith("ALAKASIZ"):
                    llm_answer += " " + line

            filtered = [
                results[idx - 1]
                for idx in relevant_indices
                if 1 <= idx <= len(results)
            ]

            kept_info = [
                f"Md{d.metadata.get('article_number', '?')}"
                for d, _ in filtered
            ]
            logger.info(
                f"LLM judge result: {len(results)} → {len(filtered)} "
                f"(kept={kept_info}, answer_len={len(llm_answer)})"
            )

            return filtered, llm_answer

        except Exception as e:
            logger.warning(f"LLM judge failed ({e}), keeping all results")
            return results, ""

    def _retrieve_documents(self, question: str) -> Tuple[List[Tuple[Document, float]], str]:
        """
        Returns: (filtered_docs, llm_answer)
        Pipeline: retrieval → score cutoff → context filter → LLM judge
        """
        logger.debug(f"Retrieving documents for: '{question}'")

        results = hybrid_retrieve(
            query=question,
            retrieval_k=self.retrieval_k,
            vector_store_manager=self.vector_store
        )
        for i, (doc, score) in enumerate(results[:7]):
            logger.debug(
                f"  RAW [{i+1}] score={score:.4f} | "
                f"{doc.metadata.get('title','')[:40]} | "
                f"Madde {doc.metadata.get('article_number','?')} - "
                f"{doc.metadata.get('article_title','')[:30]}"
            )

        filtered_results = self._apply_score_cutoff(results)

        context_results = self._filter_by_context(question, filtered_results)

        if not context_results:
            logger.info("No results after pre-filters")
            return [], ""

        final_results, llm_answer = self._llm_judge(question, context_results)

        logger.info(
            f"Retrieval pipeline: raw={len(results)} → score={len(filtered_results)} "
            f"→ context={len(context_results)} → llm={len(final_results)}"
        )

        return final_results[:self.retrieval_k], llm_answer

    @staticmethod
    def _apply_score_cutoff(
        results: List[Tuple[Document, float]],
        max_threshold: float = 0.55,
        adaptive_margin: float = 0.40,
        gap_threshold: float = 0.25,
    ) -> List[Tuple[Document, float]]:
        """
        Ön eleme filtresi — geniş tutar, asıl hassas filtrelemeyi LLM yapar.
        1. Mutlak üst sınır (max_threshold)
        2. En iyi skora göre adaptif sınır (best + adaptive_margin)
        3. Ardışık skorlar arası büyük boşluk tespiti (gap) — sadece kötü skorlarda
        """
        if not results:
            return []

        best_score = results[0][1]
        adaptive_limit = best_score + adaptive_margin

        gap_cut = len(results)
        for i in range(1, len(results)):
            gap = results[i][1] - results[i - 1][1]
            if gap > gap_threshold and results[i][1] > 0.40:
                gap_cut = i
                logger.debug(
                    f"Gap detected at position {i}: "
                    f"score[{i-1}]={results[i-1][1]:.4f} → score[{i}]={results[i][1]:.4f} "
                    f"(gap={gap:.4f})"
                )
                break

        effective_threshold = min(max_threshold, adaptive_limit)

        filtered = []
        for i, (doc, score) in enumerate(results):
            if i >= gap_cut:
                break
            if score > effective_threshold:
                break
            filtered.append((doc, score))

        if not filtered and results:
            filtered = [results[0]]

        if len(filtered) != len(results):
            kept_info = " | ".join(
                f"Md{d.metadata.get('article_number','?')}={s:.4f}"
                for d, s in filtered
            )
            dropped_info = " | ".join(
                f"Md{d.metadata.get('article_number','?')}={s:.4f}"
                for d, s in results[len(filtered):]
            )
            logger.info(
                f"Score cutoff: {len(results)} → {len(filtered)} "
                f"(threshold={effective_threshold:.3f}, gap_cut@{gap_cut}) "
                f"KEPT=[{kept_info}] DROPPED=[{dropped_info}]"
            )

        return filtered
    
    def _filter_by_context(self, question: str, results: List[Tuple[Document, float]]) -> List[Tuple[Document, float]]:
        """
        Filter documents based on context match with question.
        Uses pre-computed normalized metadata from document_loader when available.
        """
        q = normalize_turkish(question)
        filtered = []

        logger.debug(f"Documents before context filter: {len(results)}")

        for doc, score in results:
            title = doc.metadata.get('title_normalized') or normalize_turkish(doc.metadata.get('title', ''))
            should_include = True

            if "kiyafet" in title:
                if "kiyafet" not in q and "uniform" not in q and "giyim" not in q:
                    should_include = False

            if should_include and ("yurt disi" in title or "yurt disindan" in title or "uluslararasi" in title):
                if "yurt disi" not in q and "yabanci" not in q and "international" not in q and "degisim" not in q:
                    should_include = False

            if should_include and "lisans" in q and "lisansustu" not in q and "yuksek lisans" not in q:
                if "lisansustu" in title or "yuksek lisans" in title or "master" in title or "doktora" in title:
                    should_include = False

            if should_include and ("lisansustu" in q or "yuksek lisans" in q or "doktora" in q):
                if "lisans" in title and "lisansustu" not in title and "yuksek lisans" not in title:
                    should_include = False

            if should_include and ("mezuniyet" in q or "mezun" in q):
                if "sart" in q or "kosul" in q or "nasil" in q or "gerek" in q:
                    if "diploma" in title and ("duzenleme" in title or "duzenlen" in title):
                        should_include = False
                if ("basvuru" in title or "kabul" in title) and "mezuniyet" not in title:
                    should_include = False

            if should_include and "basvuru" in q and "mezuniyet" not in q:
                if "mezuniyet" in title and "basvuru" not in title:
                    should_include = False

            if should_include:
                filtered.append((doc, score))
            else:
                logger.debug(f"Filtered out: {doc.metadata.get('title','')[:40]} Md {doc.metadata.get('article_number','')}")

        logger.debug(f"Context filter: {len(results)} → {len(filtered)} documents")
        return filtered

    @staticmethod
    def _filter_by_title_relevance(
        question: str,
        results: List[Tuple[Document, float]],
    ) -> List[Tuple[Document, float]]:
        """
        Soru ile madde başlığı arasındaki keyword örtüşmesini kontrol eder.
        En iyi eşleşmeye göre belirgin şekilde düşük olan sonuçları filtreler.
        """
        if len(results) <= 1:
            return results

        q_norm = normalize_turkish(question)
        stop = {
            "nedir", "neler", "nasil", "bilgi", "verir", "misin", "musun",
            "istiyorum", "hakkinda", "olan", "icin", "ile", "gibi", "kadar",
            "bana", "bir", "ben", "seni", "size", "sorusu", "vermek",
        }
        q_words = [w for w in q_norm.split() if len(w) > 2 and w not in stop]

        if not q_words:
            return results

        def _title_match(doc) -> float:
            at = normalize_turkish(doc.metadata.get("article_title", "") or "")
            t_words = at.split()
            if not t_words:
                return 0.0
            matches = 0
            for qw in q_words:
                for tw in t_words:
                    if len(qw) >= 4 and len(tw) >= 4:
                        if qw[:4] == tw[:4]:
                            matches += 1
                            break
                    elif qw == tw:
                        matches += 1
                        break
            return matches / len(q_words)

        scored = [(doc, score, _title_match(doc)) for doc, score in results]
        best_tm = max(s[2] for s in scored)

        if best_tm < 0.4:
            return results

        filtered = []
        for doc, score, tm in scored:
            if tm >= best_tm * 0.6:
                filtered.append((doc, score))
            else:
                logger.info(
                    f"Title relevance filter: dropped Md{doc.metadata.get('article_number', '?')} "
                    f"'{doc.metadata.get('article_title', '')}' "
                    f"(match={tm:.2f}, best={best_tm:.2f})"
                )

        if not filtered:
            filtered = [results[0]]

        return filtered
    
    @staticmethod
    def _build_combined_answer(
        retrieved_docs: List[Tuple[Document, float]],
        llm_answer: str = "",
    ) -> str:
        """
        Combine LLM's brief answer with full source text.
        Structure: LLM summary → separator → full article text → citation
        """
        source_parts = []
        citations = []

        for doc, score in retrieved_docs:
            meta = doc.metadata
            title = meta.get('title', '')
            article_num = meta.get('article_number', '')

            content = doc.page_content.strip()

            if content.startswith("MADDE"):
                first_line_end = content.find("\n")
                if first_line_end > 0:
                    header_line = content[:first_line_end].strip()
                    body = _format_article_text(
                        content[first_line_end:].strip(), doc_title=title
                    )
                    source_parts.append(f"**{header_line}**\n\n{body}")
                else:
                    source_parts.append(f"**{content}**")
            else:
                article_title = meta.get('article_title', '')
                header = f"**MADDE {article_num}**"
                if article_title:
                    header += f" - {article_title}"
                body = _format_article_text(content, doc_title=title)
                source_parts.append(f"{header}\n\n{body}")

            citations.append(f"{title}, Madde {article_num}")

        source_text = "\n\n---\n\n".join(source_parts)
        citation_line = "**Kaynak:** " + " | ".join(citations)

        if llm_answer:
            return (
                f"{llm_answer}\n\n"
                f"---\n\n"
                f"**İlgili Mevzuat:**\n\n"
                f"{source_text}\n\n"
                f"{citation_line}"
            )

        return f"{source_text}\n\n{citation_line}"

    @staticmethod
    def _build_source_appendix(retrieved_docs: List[Tuple[Document, float]]) -> str:
        """
        Build programmatic appendix with full source text.
        Guarantees the user sees complete, unmodified article text
        regardless of LLM behavior.
        """
        parts = []
        citations = []

        for doc, score in retrieved_docs:
            meta = doc.metadata
            title = meta.get('title', 'Bilinmeyen Kaynak')
            article_num = meta.get('article_number', '')
            article_title = meta.get('article_title', '')

            header = f"**MADDE {article_num}**"
            if article_title:
                header += f" - {article_title}"

            parts.append(f"{header}\n\n{doc.page_content}")
            citations.append(f"{title}, Madde {article_num}")

        source_text = "\n\n---\n\n".join(parts)
        citation_line = "\n\n**Kaynak:** " + " | ".join(citations)

        return source_text + citation_line

    def _format_context(self, retrieved_docs: List[Tuple[Document, float]]) -> str:
        """
        Format retrieved documents as context for LLM.
        
        Args:
            retrieved_docs: List of (Document, score) tuples
        
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for doc, score in retrieved_docs:
            metadata = doc.metadata
            
            context_part = CONTEXT_TEMPLATE.format(
                source=metadata.get('title', 'Bilinmeyen Kaynak'),
                article_number=metadata.get('article_number', 'N/A'),
                content=doc.page_content
            )
            
            context_parts.append(context_part)
        
        return "\n".join(context_parts)
    
    def _format_sources(self, retrieved_docs: List[Tuple[Document, float]]) -> List[Dict]:
        """
        Format source information for response.
        
        Args:
            retrieved_docs: List of (Document, score) tuples
        
        Returns:
            List of source dictionaries
        """
        sources = []
        
        for doc, score in retrieved_docs:
            metadata = doc.metadata
            
            source = {
                "title": metadata.get('title', 'Bilinmeyen'),
                "article_number": metadata.get('article_number', 'N/A'),
                "article_title": metadata.get('article_title', ''),
                "relevance_score": round(1 - score, 3),  # Convert distance to similarity
                "preview": doc.page_content[:200] + "..."
            }
            
            sources.append(source)
        
        return sources
    
    def _check_meta_question(self, question: str) -> Optional[Dict]:
        """
        Check if question is about the chatbot itself (meta question).
        
        Args:
            question: User's question
        
        Returns:
            Response dict if meta question, None otherwise
        """
        question_lower = question.lower().strip()
        # Normalize for matching (evli miisin = evli misin)
        q_norm = normalize_turkish(question).strip()

        meta_phrases = [
            "sen kimsin", "kim sin", "kimsin", "sen nesin",
            "nasıl çalışırsın", "nasıl çalışıyorsun",
            "ne yaparsın", "ne yapıyorsun", "ne işe yararsın",
            "kim yaptı seni", "kim geliştirdi", "kim yarattı",
            "nasıl yapıldın", "hangi teknoloji",
            "kendin hakkında", "kendini tanıt",
            # Asistanı hedefleyen kişisel sorular (mevzuat değil, bana soruyor)
            "evli misin", "sen evli", "evli miisin", "evli mi sin",
            "cocugun var", "cocuklarin var", "cocuk var mi", "çocukların var",
            "ise sahip misin", "işe sahip misin", "bi işe sahip",
            "evlilik dusunur", "evlilik düşünür", "evlilik düsünür müsün",
        ]

        _greeting_re = re.compile(
            r'^(merhaba|selam|hello|hi|hey|helo)[\s!?.,:;]*$', re.IGNORECASE
        )

        is_meta = (
            _greeting_re.match(question_lower) is not None
            or any(phrase in question_lower for phrase in meta_phrases)
            or any(phrase in q_norm for phrase in meta_phrases)
        )
        
        if is_meta:
            if _greeting_re.match(question_lower):
                answer = """Merhaba! 👋

Ben **SUBU Mevzuat Asistanı**. Sakarya Uygulamalı Bilimler Üniversitesi'nin mevzuat, yönerge ve prosedürleri hakkında size yardımcı olmak için buradayım.

**Size nasıl yardımcı olabilirim:**
- Üniversite yönergelerini sorgulayabilirsiniz
- Akademik ve idari prosedürler hakkında bilgi alabilirsiniz
- Öğrenci işleri, personel ve eğitim süreçleri hakkında soru sorabilirsiniz

Örnek sorular:
- "Akademik personele ödül nasıl verilir?"
- "Lisansüstü öğrencilerin azami süreleri nedir?"
- "Bilimsel araştırma projesi nasıl başvurulur?"

Sorunuzu sorun, size yardımcı olayım! 😊"""
            
            else:
                answer = """Ben **SUBU Mevzuat Asistanı**. Sakarya Uygulamalı Bilimler Üniversitesi için geliştirilmiş yapay zeka destekli bir yardımcıyım.

**Kimim?**
- İsim: SUBU Mevzuat Asistanı
- Görev: Üniversite mevzuatları hakkında bilgi vermek
- Teknoloji: Yapay zeka tabanlı RAG (Retrieval-Augmented Generation) sistemi

**Nasıl Çalışırım?**
1. Sorunuzu alıyorum
2. Üniversite yönergelerini tarayıp en ilgili bölümleri buluyorum
3. Sadece resmi mevzuatlara dayanarak cevap veriyorum
4. Her cevabımda kaynak ve madde numarasını belirtiyorum

**Nelerde Yardımcı Olabilirim?**
- Akademik personel prosedürleri
- Öğrenci işleri ve eğitim süreçleri
- İdari işlemler ve başvurular
- Üniversite yönergeleri
- Bilimsel araştırma projeleri

**Önemli:** Sadece resmi mevzuatlardaki bilgileri kullanırım. Kaynaklarda olmayan bilgiler vermem.

Size nasıl yardımcı olabilirim? 😊"""
            
            return {
                "answer": answer,
                "sources": [],
                "metadata": {
                    "retrieved_docs": 0,
                    "tokens": 0,
                    "cost": 0.0,
                    "response_time": 0.0,
                    "model": "meta_response",
                    "no_context": True
                }
            }
        
        return None
    
    def _no_context_response(self, question: str) -> Dict:
        """Return a template response when no relevant documents found (no LLM call)."""
        return {
            "answer": NO_CONTEXT_PROMPT.format(question=question),
            "sources": [],
            "metadata": {
                "retrieved_docs": 0,
                "tokens": 0,
                "cost": 0.0,
                "response_time": 0.0,
                "model": "template",
                "no_context": True
            }
        }
    
    def generate_response_stream(self, question: str):
        """
        Generate streaming response for real-time UI.
        Uses LLM for relevance + brief answer, then appends full source text.
        """
        logger.info(f"Generating streaming response for: '{question}'")

        retrieved_docs, llm_answer = self._retrieve_documents(question)

        if not retrieved_docs:
            yield (
                "Bu soruyla ilgili üniversite mevzuatlarında bilgi bulamadım.\n\n"
                "Ben **SUBU Mevzuat Asistanı**'yım ve sadece Sakarya Uygulamalı Bilimler "
                "Üniversitesi'nin yönetmelik, yönerge ve prosedürleri hakkında bilgi verebilirim.\n\n"
                "**Örnek sorular:**\n"
                "- \"Tek ders sınavı hakkında bilgi verir misin?\"\n"
                "- \"Üniversiteden ayrılma prosedürü nedir?\"\n"
                "- \"Devamsızlık sınırı ne kadar?\"\n"
                "- \"Staj yönergesi hakkında bilgi ver\""
            )
            return

        answer = self._build_combined_answer(retrieved_docs, llm_answer)
        yield answer
