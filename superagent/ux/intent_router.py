"""
Intent Router - NL2Task classification and routing.
"""

from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

from superagent.core.logger import get_logger
from superagent.llm.provider import UnifiedLLMProvider
from superagent.llm.models import LLMRequest, Message

logger = get_logger(__name__)


class IntentType(str, Enum):
    """Types of user intents."""
    CHAT = "chat"  # General conversation
    CODE_WRITE = "code_write"  # Write new code
    CODE_EDIT = "code_edit"  # Edit existing code
    CODE_REVIEW = "code_review"  # Review code
    FILE_READ = "file_read"  # Read file contents
    FILE_WRITE = "file_write"  # Write to file
    SEARCH = "search"  # Search codebase/web
    EXECUTE = "execute"  # Execute command/script
    PLAN = "plan"  # Create execution plan
    EXPLAIN = "explain"  # Explain code/concept
    DEBUG = "debug"  # Debug issue
    TEST = "test"  # Write/run tests
    REFACTOR = "refactor"  # Refactor code
    UNKNOWN = "unknown"  # Could not determine


class Intent(BaseModel):
    """Resolved user intent."""
    type: IntentType
    confidence: float  # 0.0 to 1.0
    parameters: Dict[str, Any] = {}
    reasoning: str = ""


class IntentRouter:
    """
    Natural language to task intent router.
    
    Uses LLM to classify user input into actionable intents.
    """
    
    INTENT_CLASSIFICATION_PROMPT = """You are an intent classification system for a developer AI assistant.

Analyze the user's input and classify it into one of these intent types:

- chat: General conversation, questions, greetings
- code_write: Request to write new code from scratch
- code_edit: Request to modify existing code
- code_review: Request to review code quality
- file_read: Request to read file contents
- file_write: Request to write to a file
- search: Request to search codebase or web
- execute: Request to run a command or script
- plan: Request to create a multi-step plan
- explain: Request to explain code or concepts
- debug: Request to debug an issue
- test: Request to write or run tests
- refactor: Request to refactor code
- unknown: Cannot determine intent

User input: {user_input}

Context files: {context_files}

Respond with JSON:
{{
  "type": "intent_type",
  "confidence": 0.95,
  "parameters": {{}},
  "reasoning": "brief explanation"
}}"""
    
    def __init__(self, llm_provider: UnifiedLLMProvider):
        """
        Initialize intent router.
        
        Args:
            llm_provider: LLM provider for classification
        """
        self.llm_provider = llm_provider
        logger.info("Intent router initialized")
    
    async def route(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Intent:
        """
        Route user input to intent.
        
        Args:
            user_input: Natural language input
            context: Optional context (files, history, etc.)
        
        Returns:
            Resolved intent
        """
        context = context or {}
        context_files = context.get("context_files", [])
        
        # Build prompt
        prompt = self.INTENT_CLASSIFICATION_PROMPT.format(
            user_input=user_input,
            context_files=", ".join(context_files) if context_files else "none",
        )
        
        # Call LLM
        try:
            response = await self.llm_provider.generate(
                LLMRequest(
                    messages=[Message(role="user", content=prompt)],
                    temperature=0.1,  # Low temperature for consistent classification
                    max_tokens=500,
                )
            )
            
            # Parse response
            import json
            result = json.loads(response.content)
            
            intent = Intent(
                type=IntentType(result["type"]),
                confidence=result["confidence"],
                parameters=result.get("parameters", {}),
                reasoning=result.get("reasoning", ""),
            )
            
            logger.info(f"Classified intent: {intent.type} ({intent.confidence:.2f})")
            return intent
            
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            return Intent(
                type=IntentType.UNKNOWN,
                confidence=0.0,
                reasoning=f"Classification error: {str(e)}",
            )
