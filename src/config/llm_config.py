"""
LLM Configuration Module

This module handles the configuration and initialization of language models
used by the healthcare agents.
"""

import os
import logging
from typing import Optional
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseLanguageModel
from config.settings import Config

logger = logging.getLogger(__name__)

class LLMConfig:
    """Configuration manager for Language Models"""
    
    def __init__(self):
        self.config = Config()
        self._groq_llm: Optional[ChatGroq] = None
        self._openai_llm: Optional[ChatOpenAI] = None
        
    def get_groq_llm(self) -> ChatGroq:
        """Get or create Groq LLM instance"""
        if self._groq_llm is None:
            api_key = self.config.GROQ_API_KEY
            if not api_key:
                raise ValueError("GROQ_API_KEY is required but not set")
            
            try:
                self._groq_llm = ChatGroq(
                    groq_api_key=api_key,
                    model_name=self.config.GROQ_MODEL,
                    temperature=self.config.LLM_TEMPERATURE,
                    max_tokens=self.config.LLM_MAX_TOKENS
                )
                logger.info(f"Groq LLM initialized with model: {self.config.GROQ_MODEL}")
            except Exception as e:
                logger.error(f"Failed to initialize Groq LLM: {str(e)}")
                raise
        
        return self._groq_llm
    
    def get_openai_llm(self) -> ChatOpenAI:
        """Get or create OpenAI LLM instance"""
        if self._openai_llm is None:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY is required but not set")
            
            try:
                self._openai_llm = ChatOpenAI(
                    openai_api_key=api_key,
                    model_name=os.getenv('OPENAI_MODEL', 'gpt-4'),
                    temperature=self.config.LLM_TEMPERATURE,
                    max_tokens=self.config.LLM_MAX_TOKENS
                )
                logger.info(f"OpenAI LLM initialized with model: {os.getenv('OPENAI_MODEL', 'gpt-4')}")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI LLM: {str(e)}")
                raise
        
        return self._openai_llm
    
    def get_default_llm(self) -> BaseLanguageModel:
        """Get the default LLM (Groq)"""
        return self.get_groq_llm()
    
    def reset_llm_instances(self):
        """Reset LLM instances (useful for testing)"""
        self._groq_llm = None
        self._openai_llm = None
        logger.info("LLM instances reset")

# Global LLM configuration instance
llm_config = LLMConfig()