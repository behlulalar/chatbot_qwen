"""
OpenAI Handler - Manages OpenAI API interactions.
"""
from typing import List, Dict, Optional, Generator
import time
from openai import OpenAI

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
        api_key: str = None,
        model: str = None,
        temperature: float = None,
        max_tokens: int = None
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
        
        self.client = OpenAI(api_key=self.api_key)
        
        logger.info(f"OpenAIHandler initialized: model={self.model}, temp={self.temperature}")
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = None,
        max_tokens: int = None,
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
        
        start_time = time.time()
        
        try:
            logger.debug(f"Calling OpenAI API: {self.model}, {len(messages)} messages")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temp,
                max_tokens=max_tok,
                stream=stream
            )
            
            if stream:
                return response
            
            # Extract response
            content = response.choices[0].message.content
            
            # Token usage
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens
            total_tokens = response.usage.total_tokens
            
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
        temperature: float = None,
        max_tokens: int = None
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
        
        try:
            logger.debug(f"Starting streaming completion: {self.model}")
            
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
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
        
        Pricing (as of 2024):
        - GPT-4-turbo: $0.01/1K prompt, $0.03/1K completion
        - GPT-3.5-turbo: $0.0005/1K prompt, $0.0015/1K completion
        
        Args:
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
        
        Returns:
            Estimated cost in USD
        """
        if "gpt-4" in self.model.lower():
            prompt_cost = (prompt_tokens / 1000) * 0.01
            completion_cost = (completion_tokens / 1000) * 0.03
        else:  # GPT-3.5 and others
            prompt_cost = (prompt_tokens / 1000) * 0.0005
            completion_cost = (completion_tokens / 1000) * 0.0015
        
        return prompt_cost + completion_cost
    
    def count_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        
        This is a rough estimate: ~4 chars = 1 token for English,
        ~2-3 chars = 1 token for Turkish.
        
        Args:
            text: Text to count tokens for
        
        Returns:
            Estimated token count
        """
        # Rough estimation for Turkish
        # More accurate: use tiktoken library
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
