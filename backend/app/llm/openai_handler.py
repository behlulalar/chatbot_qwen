"""
OpenAI Handler - Manages OpenAI API interactions.
"""
from typing import List, Dict, Optional, Generator, Any, cast
import time
from openai import OpenAI
from openai.types.chat import ChatCompletion

from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger("openai_handler", "./logs/openai_handler.log")


class OpenAIHandler:
    """
    Handles OpenAI API calls for chat completion.
    
    Features:
    - Chat completions
    - Streaming support
    - Token counting
    - Cost tracking
    
    Usage:
        handler = OpenAIHandler()
        response = handler.chat_completion(messages)
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ):
        """
        Initialize OpenAI handler.
        
        Args:
            api_key: OpenAI API key
            model: Model name
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response
        """
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.model_name
        self.temperature = temperature if temperature is not None else settings.temperature
        self.max_tokens = max_tokens or settings.max_tokens
        self.base_url = getattr(settings, "llm_base_url", None)  # Ollama: http://localhost:11434/v1
        
        if self.base_url:
            # Ollama yerel model; büyük context ile 2–3 dakika sürebilir
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key or "ollama",
                timeout=180.0,
            )
        else:
            self.client = OpenAI(api_key=self.api_key)
        
        backend = "Ollama (local)" if self.base_url else "OpenAI"
        logger.info(f"OpenAIHandler initialized: model={self.model}, backend={backend}, temp={self.temperature}")
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Dict:
        """
        Get chat completion from OpenAI.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Override default temperature
            max_tokens: Override default max tokens
            stream: Enable streaming
        
        Returns:
            Response dictionary with 'content', 'tokens', 'cost', 'time'
        """
        temp = temperature if temperature is not None else self.temperature
        max_tok = max_tokens if max_tokens is not None else self.max_tokens
        max_tok = max_tok or 2000
        
        start_time = time.time()
        
        try:
            logger.debug(f"Calling {self.model}: {len(messages)} messages, max_tokens={max_tok}")
            
            raw = self.client.chat.completions.create(
                model=self.model,
                messages=cast(Any, messages),
                temperature=temp,
                max_tokens=max_tok,
                stream=stream
            )
            
            if stream:
                return raw  # type: ignore[return-value]
            
            response = cast(ChatCompletion, raw)
            # Extract response (Ollama bazen None dönebilir)
            content = (response.choices[0].message.content or "").strip() if response.choices else ""
            if not content and response.choices:
                content = getattr(response.choices[0].message, "content", "") or ""

            # Token usage
            usage = response.usage
            prompt_tokens = usage.prompt_tokens if usage else 0
            completion_tokens = usage.completion_tokens if usage else 0
            total_tokens = usage.total_tokens if usage else 0
            
            # Calculate cost (approximate)
            cost = self._calculate_cost(prompt_tokens, completion_tokens)
            
            # Response time
            response_time = time.time() - start_time
            
            logger.info(f"API call successful: {total_tokens} tokens, {response_time:.2f}s, ${cost:.4f}")
            
            return {
                "content": content,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "cost": cost,
                "response_time": response_time,
                "model": self.model
            }
        
        except Exception as e:
            logger.error(f"OpenAI API error: {e}", exc_info=True)
            raise
    
    def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Generator[str, None, None]:
        """
        Get streaming chat completion.
        
        Args:
            messages: List of message dicts
            temperature: Override default temperature
            max_tokens: Override default max tokens
        
        Yields:
            Content chunks as they arrive
        """
        temp = temperature if temperature is not None else self.temperature
        max_tok = max_tokens if max_tokens is not None else self.max_tokens
        max_tok = max_tok or 2000
        
        try:
            logger.debug(f"Starting streaming: {self.model}, max_tokens={max_tok}")
            
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=cast(Any, messages),
                temperature=temp,
                max_tokens=max_tok,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    yield content
            
            logger.debug("Streaming completion finished")
        
        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            raise
    
    def _calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Calculate approximate cost based on token usage.
        Local models (Ollama vb.): 0
        """
        if self.base_url or "ollama" in (self.api_key or "").lower():
            return 0.0

        model = self.model.lower()
        if "gpt-4o-mini" in model:
            prompt_cost = (prompt_tokens / 1_000_000) * 0.15
            completion_cost = (completion_tokens / 1_000_000) * 0.60
        elif "gpt-4o" in model:
            prompt_cost = (prompt_tokens / 1_000_000) * 2.50
            completion_cost = (completion_tokens / 1_000_000) * 10.00
        elif "gpt-4" in model:
            prompt_cost = (prompt_tokens / 1_000_000) * 30.00
            completion_cost = (completion_tokens / 1_000_000) * 60.00
        else:
            prompt_cost = (prompt_tokens / 1_000_000) * 0.50
            completion_cost = (completion_tokens / 1_000_000) * 1.50

        return prompt_cost + completion_cost
    
    def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken (falls back to estimate if unavailable)."""
        try:
            import tiktoken
            enc = tiktoken.encoding_for_model(self.model)
            return len(enc.encode(text))
        except Exception:
            return len(text) // 3
    
    def format_messages(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> List[Dict[str, str]]:
        """
        Format messages for OpenAI API.
        
        Args:
            system_prompt: System instruction
            user_message: User's question
            conversation_history: Optional previous messages
        
        Returns:
            Formatted messages list
        """
        messages = [{"role": "system", "content": system_prompt}]
        
        if conversation_history:
            messages.extend(conversation_history)
        
        messages.append({"role": "user", "content": user_message})
        
        return messages
