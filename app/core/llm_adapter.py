from typing import Any, List, Optional, Mapping
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, SystemMessage, HumanMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from pydantic import Field
import requests
import json

class OrchestratorChatModel(BaseChatModel):
    """
    Custom LangChain Chat Model that routes requests to the centralized AI Orchestrator.
    """
    orchestrator_url: str = Field(description="URL of the AI Orchestrator")
    origin_service: str = Field(description="Name of the service calling the orchestrator")
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    
    @property
    def _llm_type(self) -> str:
        return "md-ai-orchestrator-adapter"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        # 1. Convert Messages to Single Prompt & System Prompt
        prompt_parts = []
        system_prompt = None
        
        for m in messages:
            if isinstance(m, SystemMessage):
                # If we have multiple system messages, join them or pick last? 
                # Orchestrator prefers one. We'll join them if multiple.
                if system_prompt:
                    system_prompt += "\n" + m.content
                else:
                    system_prompt = m.content
            elif isinstance(m, HumanMessage):
                prompt_parts.append(f"User: {m.content}")
            elif isinstance(m, AIMessage):
                prompt_parts.append(f"AI: {m.content}")
            else:
                prompt_parts.append(f"{m.type}: {m.content}")
        
        full_prompt = "\n\n".join(prompt_parts)

        # 2. Prepare Payload
        # Priority: kwargs (bind) > self.field > default
        payload = {
            "origin": self.origin_service,
            "prompt": full_prompt,
            "system_prompt": system_prompt,
            "temperature": kwargs.get("temperature", self.temperature if self.temperature is not None else 0.7),
            "top_p": kwargs.get("top_p", self.top_p),
            "frequency_penalty": kwargs.get("frequency_penalty", self.frequency_penalty),
            "presence_penalty": kwargs.get("presence_penalty", self.presence_penalty),
            "max_steps": kwargs.get("max_steps", 5),
            "max_tokens": kwargs.get("max_tokens", 4000)
        }

        # 3. Call Orchestrator
        try:
            response = requests.post(f"{self.orchestrator_url}/execute", json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            ai_text = data.get("response", "")
            
            # 4. Return as ChatResult
            return ChatResult(generations=[ChatGeneration(message=AIMessage(content=ai_text))])
            
        except Exception as e:
            raise ValueError(f"Orchestrator Call Failed: {str(e)}")

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        return {"orchestrator_url": self.orchestrator_url}
