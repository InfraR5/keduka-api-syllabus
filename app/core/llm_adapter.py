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
        # 1. Convert Messages to Single Prompt (Orchestrator simplistic interface)
        # In a more advanced version, Orchestrator could accept messages[]
        prompt_parts = []
        for m in messages:
            if isinstance(m, SystemMessage):
                prompt_parts.append(f"System: {m.content}")
            elif isinstance(m, HumanMessage):
                prompt_parts.append(f"User: {m.content}")
            elif isinstance(m, AIMessage):
                prompt_parts.append(f"AI: {m.content}")
            else:
                prompt_parts.append(f"{m.type}: {m.content}")
        
        full_prompt = "\n\n".join(prompt_parts)

        # 2. Prepare Payload
        payload = {
            "origin": self.origin_service,
            "prompt": full_prompt,
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
