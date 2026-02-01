"""
Response Generator - Combines RAG retrieval with LLM generation.

This is the core of the chatbot - it retrieves relevant documents
and generates responses using OpenAI.
"""
from typing import List, Dict, Optional, Tuple
from langchain.schema import Document

from app.rag.vector_store import VectorStoreManager
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


def normalize_turkish(text: str) -> str:
    """
    Normalize Turkish text for comparison.
    
    Converts Turkish I/İ to ASCII i for consistent matching.
    CRITICAL: Must replace BEFORE lowercasing to avoid combining characters!
    """
    import unicodedata
    
    # STEP 1: Replace Turkish characters BEFORE lowercasing
    # This prevents "İ" → "i̇" (combining dot) problem
    turkish_map = {
        'İ': 'I',  # Turkish capital I with dot → ASCII capital I
        'ı': 'i',  # Turkish lowercase dotless i → ASCII i
        'Ğ': 'G',
        'ğ': 'g',
        'Ü': 'U',
        'ü': 'u',
        'Ş': 'S',
        'ş': 's',
        'Ö': 'O',
        'ö': 'o',
        'Ç': 'C',
        'ç': 'c'
    }
    
    result = text
    for turkish, ascii_char in turkish_map.items():
        result = result.replace(turkish, ascii_char)
    
    # STEP 2: Now safe to lowercase
    result = result.lower()
    
    # STEP 3: Remove any remaining combining diacritics
    result = unicodedata.normalize('NFD', result)
    result = ''.join(char for char in result if unicodedata.category(char) != 'Mn')
    
    return result


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
    
    def __init__(
        self,
        vector_store_manager: VectorStoreManager = None,
        openai_handler: OpenAIHandler = None,
        retrieval_k: int = 5,
        max_distance_threshold: float = 1.0,
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
        
        # Step 1: Retrieve relevant documents
        retrieved_docs = self._retrieve_documents(question)
        
        if not retrieved_docs:
            logger.warning("No relevant documents found")
            return self._no_context_response(question)
        
        # Step 2: Format context
        context = self._format_context(retrieved_docs)
        
        # Step 3: Create prompt
        user_prompt = USER_PROMPT_TEMPLATE.format(
            question=question,
            context=context
        )
        
        # Step 4: Call LLM
        messages = self.llm.format_messages(
            system_prompt=SYSTEM_PROMPT,
            user_message=user_prompt,
            conversation_history=conversation_history
        )
        
        llm_response = self.llm.chat_completion(messages)
        
        # Step 5: Format response
        response = {
            "answer": llm_response["content"],
            "sources": self._format_sources(retrieved_docs) if include_sources else [],
            "metadata": {
                "retrieved_docs": len(retrieved_docs),
                "tokens": llm_response["total_tokens"],
                "cost": llm_response["cost"],
                "response_time": llm_response["response_time"],
                "model": llm_response["model"]
            }
        }
        
        logger.info(f"Response generated: {llm_response['total_tokens']} tokens, ${llm_response['cost']:.4f}")
        
        # Step 6: Cache response (only for standalone questions without history)
        if self.enable_cache and self.cache and not conversation_history:
            cache_key = self.cache._generate_key("response", question.lower().strip())
            self.cache.set(cache_key, response, ttl=self.response_cache_ttl)
            logger.debug(f"Cached response for: '{question[:50]}...'")
        
        return response
    
    def _retrieve_documents(self, question: str) -> List[Tuple[Document, float]]:
        """
        Retrieve relevant documents from vector store.
        
        Args:
            question: User's question
        
        Returns:
            List of (Document, score) tuples
        """
        logger.debug(f"Retrieving documents for: '{question}'")
        
        # Enhance query for better retrieval
        enhanced_query = self._enhance_query(question)
        
        # Search with scores
        results = self.vector_store.search_with_score(
            query=enhanced_query,
            k=self.retrieval_k * 2  # Get more, then filter aggressively
        )
        
        # Filter by distance threshold
        # ChromaDB returns distance scores: lower = more similar
        # Typically good matches are < 0.8, excellent < 0.6
        filtered_results = [
            (doc, score) for doc, score in results
            if score <= self.max_distance_threshold
        ]
        
        # AGGRESSIVE FILTER: Check document relevance to query
        # Filter out documents with wrong context (e.g., "lisansüstü" when asking about "lisans")
        final_results = self._filter_by_context(question, filtered_results)
        
        logger.debug(f"Retrieved {len(final_results)} documents (filtered from {len(results)} → {len(filtered_results)} → {len(final_results)})")
        
        return final_results[:self.retrieval_k]  # Return only top k
    
    def _enhance_query(self, question: str) -> str:
        """
        Enhance query for better semantic search.
        
        Adds context and distinguishes similar terms like "lisans" vs "lisansüstü".
        
        Args:
            question: Original question
        
        Returns:
            Enhanced query
        """
        question_lower = normalize_turkish(question)
        
        # Distinguish "lisans" from "lisansüstü"
        # Note: After normalize, "lisansüstü" → "lisansustu", "yüksek" → "yuksek"
        if "lisansustu" in question_lower or "yuksek lisans" in question_lower or "master" in question_lower or "doktora" in question_lower:
            # Graduate level query
            enhanced = question + " lisansüstü yüksek lisans master doktora"
        elif "lisans" in question_lower and "lisansustu" not in question_lower:
            # Undergraduate level query - explicitly exclude graduate
            enhanced = question + " lisans ön lisans undergraduate bachelor -lisansüstü"
        else:
            enhanced = question
        
        # Add context for common terms with more specificity
        # HARF NOTLARI - Grade letters (AA, BA, BB, CB, CC, DC, DD, FD, FF)
        # Note: "notu" → "notu", "not" stays as "not"
        if any(grade in question_lower for grade in ["aa", "ba", "bb", "cb", "cc", "dc", "dd", "fd", "ff"]) and "not" in question_lower:
            # Asking about specific grade letter (e.g., "BB notu ne", "AA kaç puan")
            enhanced += " harf notları başarı notları tablosu puan karşılıkları bağıl değerlendirme not sistemi katsayı"
        elif "harf not" in question_lower or "basari not" in question_lower or "not sistemi" in question_lower:
            # Asking about grading system
            enhanced += " harf notları başarı notları tablosu puan karşılıkları bağıl değerlendirme AA BA BB CB CC DC DD FD FF katsayı"
        elif "yaz okulu" in question_lower or "yaz ogreti" in question_lower:
            # Summer school - explicitly exclude dress code and other unrelated topics
            enhanced += " yaz okulu yaz öğretimi dönem ders -kıyafet -giyim"
        elif "mezuniyet" in question_lower or "mezun" in question_lower:
            # Distinguish between graduation requirements vs diploma procedures
            # Note: After normalize, "şart" → "sart", "koşul" → "kosul", "nasıl" → "nasil"
            if "sart" in question_lower or "kosul" in question_lower or "nasil" in question_lower or "gerek" in question_lower:
                # User asking about requirements/conditions - NOT just diploma types
                enhanced += " mezuniyet şartları koşulları eğitim öğretim tamamlama ders kredi başarı -diploma düzenleme"
            else:
                enhanced += " mezuniyet şartları diploma"
        elif "basvuru" in question_lower:
            enhanced += " başvuru kabul kayıt"
        
        logger.debug(f"Enhanced query: '{enhanced}'")
        return enhanced
    
    def _filter_by_context(self, question: str, results: List[Tuple[Document, float]]) -> List[Tuple[Document, float]]:
        """
        Filter documents based on context match with question.
        
        Prevents mixing up "lisans" with "lisansüstü" and similar confusions.
        
        Args:
            question: User's question
            results: Retrieved documents
        
        Returns:
            Filtered documents
        """
        question_lower = normalize_turkish(question)
        filtered = []
        
        # DEBUG: Log all retrieved documents
        logger.debug(f"Documents before context filter: {len(results)}")
        for i, (doc, score) in enumerate(results):
            doc_title = doc.metadata.get('title', 'Unknown')[:50]
            logger.debug(f"  [{i+1}] score={score:.3f} | {doc_title}")
        
        for doc, score in results:
            title_raw = doc.metadata.get('title', '')
            title = normalize_turkish(title_raw)
            content = normalize_turkish(doc.page_content)
            
            # Check for context mismatch
            should_include = True
            
            # Rule 0a: CRITICAL - Exclude irrelevant topic documents
            # Exclude "kıyafet" (dress code) documents when asking about unrelated topics
            # Note: After normalize, "kıyafet" → "kiyafet"
            if "kiyafet" in title or "kiyafet" in content[:100]:
                # Only include if explicitly asking about dress code
                if "kiyafet" not in question_lower and "uniform" not in question_lower and "giyim" not in question_lower:
                    logger.debug(f"Excluding dress code document for unrelated query: {title[:50]}")
                    should_include = False
            
            # Rule 0b: CRITICAL - Exclude "yurt dışı" (international student) documents for domestic student questions
            # Note: After normalize, "ş" → "s", "ı" → "i", "ü" → "u"
            # "yurt dışı" → "yurt disi", "yabancı" → "yabanci", "uluslararası" → "uluslararasi"
            if "yurt disi" in title or "yurt disindan" in title or "uluslararasi" in title:
                if "yurt disi" not in question_lower and "yabanci" not in question_lower and "international" not in question_lower:
                    logger.debug(f"Excluding yurt dışı document for domestic query: {title[:50]}")
                    should_include = False
            
            # Rule 1: If asking about "lisans" (not "lisansüstü"), exclude "lisansüstü" documents
            # Note: After normalize_turkish(), "ü" becomes "u", "ş" becomes "s"
            # "lisansüstü" → "lisansustu", "yüksek" → "yuksek"
            if "lisans" in question_lower and "lisansustu" not in question_lower and "yuksek lisans" not in question_lower:
                if "lisansustu" in title or "yuksek lisans" in title or "master" in title or "doktora" in title:
                    logger.debug(f"Excluding lisansüstü document: {title[:50]}")
                    should_include = False
                elif "lisansustu" in content[:200]:  # Check beginning of content
                    logger.debug(f"Excluding lisansüstü content: {title[:50]}")
                    should_include = False
            
            # Rule 2: If asking about "lisansüstü", only include graduate-level documents
            if "lisansustu" in question_lower or "yuksek lisans" in question_lower or "doktora" in question_lower:
                if "lisansustu" not in title and "yuksek lisans" not in title and "lisansustu" not in content[:200]:
                    # This might be undergraduate content
                    if "lisans" in title and "lisansustu" not in title:
                        logger.debug(f"Excluding lisans document for lisansüstü query: {title[:50]}")
                        should_include = False
            
            # Rule 3: If asking about "mezuniyet ŞARTLARI/KOŞULLARI", exclude diploma procedure documents
            if "mezuniyet" in question_lower or "mezun" in question_lower:
                # If asking about graduation REQUIREMENTS/CONDITIONS (not just diploma)
                # Note: After normalize_turkish(), "şart" becomes "sart", "koşul" becomes "kosul"
                if "sart" in question_lower or "kosul" in question_lower or "nasil" in question_lower or "gerek" in question_lower:
                    logger.debug(f"Checking diploma filter for: {title[:60]}")
                    has_diploma = "diploma" in title
                    # Note: After normalize, "düzenleme" → "duzenleme", "düzenlen" → "duzenlen"
                    has_duzenlen = ("duzenleme" in title or "duzenlen" in title)
                    logger.debug(f"  has_diploma={has_diploma}, has_duzenlen={has_duzenlen}")
                    if has_diploma and has_duzenlen:
                        logger.debug(f"Excluding diploma procedure document for graduation requirements query: {title[:50]}")
                        should_include = False
                # Exclude başvuru/kabul focused documents
                # Note: After normalize, "başvuru" → "basvuru"
                if ("basvuru" in title or "kabul" in title) and "mezuniyet" not in title and "mezun" not in title:
                    logger.debug(f"Excluding başvuru/kabul document for mezuniyet query: {title[:50]}")
                    should_include = False
            
            # Rule 4: If asking about "başvuru", exclude pure "mezuniyet" documents
            if "basvuru" in question_lower and "mezuniyet" not in question_lower:
                if "mezuniyet" in title and "basvuru" not in title:
                    logger.debug(f"Excluding mezuniyet document for başvuru query: {title[:50]}")
                    should_include = False
            
            if should_include:
                filtered.append((doc, score))
        
        logger.debug(f"Context filter: {len(results)} → {len(filtered)} documents")
        return filtered
    
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
        
        # Meta question keywords
        meta_keywords = [
            "sen kimsin", "kim sin", "kimsin", "sen nesin",
            "nasıl çalışırsın", "nasıl çalışıyorsun",
            "ne yaparsın", "ne yapıyorsun", "ne işe yararsın",
            "kim yaptı seni", "kim geliştirdi", "kim yarattı",
            "nasıl yapıldın", "hangi teknoloji",
            "kendin hakkında", "kendini tanıt",
            "merhaba", "selam", "hello", "hi"
        ]
        
        # Check if question contains meta keywords
        is_meta = any(keyword in question_lower for keyword in meta_keywords)
        
        if is_meta:
            # Generate appropriate response based on question
            if any(word in question_lower for word in ["merhaba", "selam", "hello", "hi"]):
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
- Teknoloji: OpenAI GPT tabanlı RAG (Retrieval-Augmented Generation) sistemi

**Nasıl Çalışırım?**
1. Sorunuzu alıyorum
2. 77 üniversite yönergesini tarayıp en ilgili bölümleri buluyorum
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
        """
        Generate response when no relevant documents found.
        
        Args:
            question: User's question
        
        Returns:
            Response dictionary
        """
        messages = self.llm.format_messages(
            system_prompt=SYSTEM_PROMPT,
            user_message=NO_CONTEXT_PROMPT.format(question=question)
        )
        
        llm_response = self.llm.chat_completion(messages)
        
        return {
            "answer": llm_response["content"],
            "sources": [],
            "metadata": {
                "retrieved_docs": 0,
                "tokens": llm_response["total_tokens"],
                "cost": llm_response["cost"],
                "response_time": llm_response["response_time"],
                "model": llm_response["model"],
                "no_context": True
            }
        }
    
    def generate_response_stream(self, question: str):
        """
        Generate streaming response (for real-time UI).
        
        Args:
            question: User's question
        
        Yields:
            Response chunks
        """
        logger.info(f"Generating streaming response for: '{question}'")
        
        # Retrieve documents
        retrieved_docs = self._retrieve_documents(question)
        
        if not retrieved_docs:
            yield "Üzgünüm, bu soruyla ilgili mevzuatlarda bilgi bulamadım."
            return
        
        # Format context
        context = self._format_context(retrieved_docs)
        
        # Create prompt
        user_prompt = USER_PROMPT_TEMPLATE.format(
            question=question,
            context=context
        )
        
        # Stream response
        messages = self.llm.format_messages(
            system_prompt=SYSTEM_PROMPT,
            user_message=user_prompt
        )
        
        for chunk in self.llm.chat_completion_stream(messages):
            yield chunk
