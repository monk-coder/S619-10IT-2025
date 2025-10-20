"""
OpenRouter API client for DeepSeek V3 integration
"""
import logging
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from config import config
from prompts import (
    summary_system_prompt,
    image_extraction_system_prompt,
    contextual_answer_system_prompt,
    instructor_system_prompt,
)

logger = logging.getLogger(__name__)


class OpenRouterClient:
    """Client for OpenRouter API"""
    
    def __init__(self):
        """Initialize OpenRouter client"""
        self.client = AsyncOpenAI(
            api_key=config.openrouter_api_key,
            base_url=config.openrouter_base_url,
            default_headers={
                "HTTP-Referer": "https://github.com/yourusername/telegram-bot",
                "X-Title": "Telegram Educational Bot",
            }
        )
        self.model = config.model_name
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        stream: bool = False
    ) -> tuple[str, int]:
        """
        Generate a response using DeepSeek via OpenRouter
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            system_prompt: Optional system prompt to prepend
            max_tokens: Maximum tokens for the response
            temperature: Temperature for generation
            stream: Whether to stream the response
        
        Returns:
            Tuple of (response_text, tokens_used)
        """
        try:
            # Prepare messages
            formatted_messages = []
            
            # Add system prompt if provided
            if system_prompt:
                formatted_messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            # Add conversation messages
            formatted_messages.extend(messages)
            
            # Log the request (without sensitive data)
            logger.info(f"Sending request to OpenRouter with {len(formatted_messages)} messages")
            
            # Make the API call
            if stream:
                # For streaming responses
                response_text = ""
                total_tokens = 0
                
                stream = await self.client.chat.completions.create(
                    model=self.model,
                    messages=formatted_messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stream=True
                )
                
                async for chunk in stream:
                    if chunk.choices[0].delta.content:
                        response_text += chunk.choices[0].delta.content
                
                # Estimate tokens for streaming (rough estimate)
                total_tokens = len(response_text.split()) * 1.3  # Rough token estimate
                
                return response_text, int(total_tokens)
            else:
                # Non-streaming response
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=formatted_messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stream=False
                )
                
                response_text = response.choices[0].message.content
                tokens_used = response.usage.total_tokens if response.usage else 0
                
                logger.info(f"Received response from OpenRouter, tokens used: {tokens_used}")
                
                return response_text, tokens_used
                
        except Exception as e:
            logger.error(f"Error generating response from OpenRouter: {e}")
            raise
    
    async def generate_summary(self, text: str, max_length: int = 500) -> str:
        """
        Generate a summary of the given text
        
        Args:
            text: Text to summarize
            max_length: Maximum length of the summary in characters
        
        Returns:
            Summary text
        """
        try:
            system_prompt = summary_system_prompt(max_length)

            messages = [
                {"role": "user", "content": f"Please summarize this text:\n\n{text}"}
            ]
            
            response, _ = await self.generate_response(
                messages=messages,
                system_prompt=system_prompt,
                max_tokens=max_length // 2,  # Rough estimate
                temperature=0.5  # Lower temperature for more focused summaries
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return "Error generating summary"
    
    async def extract_from_image_description(self, image_description: str) -> str:
        """
        Extract and structure information from an image description
        
        Args:
            image_description: Description of the image content
        
        Returns:
            Structured extraction
        """
        try:
            system_prompt = image_extraction_system_prompt()

            messages = [
                {"role": "user", "content": f"Extract and structure the key information from this image:\n\n{image_description}"}
            ]
            
            response, _ = await self.generate_response(
                messages=messages,
                system_prompt=system_prompt,
                temperature=0.3  # Low temperature for accurate extraction
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error extracting from image: {e}")
            return "Error processing image content"
    
    async def answer_with_context(
        self,
        question: str,
        context: str,
        custom_instructions: Optional[str] = None
    ) -> str:
        """
        Answer a question based on provided context
        
        Args:
            question: User's question
            context: Context information (notes, documents, etc.)
            custom_instructions: Optional custom instructions from user profile
        
        Returns:
            Answer based on context
        """
        try:
            system_prompt = contextual_answer_system_prompt(custom_instructions)
            
            messages = [
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
            ]
            
            response, _ = await self.generate_response(
                messages=messages,
                system_prompt=system_prompt,
                temperature=0.5
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error answering with context: {e}")
            return "Error generating answer"
    
    async def instructor_mode(
        self,
        topic: str,
        question: str,
        level: str = "intermediate",
        custom_instructions: Optional[str] = None
    ) -> str:
        """
        Generate educational content in instructor mode
        
        Args:
            topic: Topic of instruction
            question: Specific question or area to cover
            level: Difficulty level (beginner, intermediate, advanced)
            custom_instructions: Optional custom instructions
        
        Returns:
            Educational response
        """

        try:
            system_prompt = instructor_system_prompt(topic, level, custom_instructions)
            
            messages = [
                {"role": "user", "content": question}
            ]
            
            response, _ = await self.generate_response(
                messages=messages,
                system_prompt=system_prompt,
                temperature=0.6
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error in instructor mode: {e}")
            return "Error generating educational content"


# Global client instance
openrouter_client = OpenRouterClient()
