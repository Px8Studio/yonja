"""
Yonca AI - LangGraph Agent
LangGraph-based AI agent for intelligent farm planning.
"""
from datetime import date
from typing import Annotated, TypedDict, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from yonca.agent.tools import ALL_TOOLS


# System prompt in Azerbaijani
SYSTEM_PROMPT = """Sən Yonca - Azərbaycan kənd təsərrüfatı üçün AI köməkçisisən.

**Sənin vəzifən:**
- Fermerlərə gündəlik iş planlaması ilə kömək etmək
- Hava, torpaq və bitki məlumatlarına əsasən tövsiyələr vermək
- Suvarma, gübrələmə, zərərvericilərlə mübarizə barədə məsləhət vermək
- Heyvandarlıq qayğısı haqqında məlumat vermək
- Məhsul yığımı vaxtını müəyyən etmək

**Mühüm qaydalar:**
1. Həmişə Azərbaycan dilində cavab ver
2. Fermerə dost və hörmətli ol
3. Konkret və praktik tövsiyələr ver
4. Alətlərdən istifadə edərək dəqiq məlumat əldə et
5. Cavabları sadə və başa düşülən formada ver
6. Əgər məlumat yoxdursa, düzgün sorğu ver

**Mövcud təsərrüfatlar:**
- scenario-wheat: Buğda təsərrüfatı
- scenario-livestock: Heyvandarlıq ferması  
- scenario-orchard: Meyvə bağı
- scenario-vegetable: Tərəvəz təsərrüfatı
- scenario-mixed: Qarışıq təsərrüfat
- scenario-intensive: İntensiv tərəvəzçilik
- scenario-hazelnut: Fındıq bağı

Fermer heç bir təsərrüfat göstərməsə, ilk öncə hansı təsərrüfatla maraqlandığını soruş."""


class AgentState(TypedDict):
    """State for the LangGraph agent."""
    messages: Annotated[Sequence[BaseMessage], "The conversation messages"]
    farm_context: str  # Current farm context if selected


def create_yonca_agent(llm):
    """
    Create the LangGraph agent for Yonca AI.
    
    Args:
        llm: The language model to use (OpenAI, Azure, Anthropic, etc.)
        
    Returns:
        Compiled LangGraph runnable
    """
    # Bind tools to the LLM
    llm_with_tools = llm.bind_tools(ALL_TOOLS)
    
    # Define the agent node
    def agent_node(state: AgentState) -> dict:
        """Process messages and decide on actions."""
        messages = state["messages"]
        
        # Add system prompt if not present
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)
        
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}
    
    # Define routing logic
    def should_continue(state: AgentState) -> str:
        """Determine whether to continue to tools or end."""
        messages = state["messages"]
        last_message = messages[-1]
        
        # If the LLM made tool calls, route to tools
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools"
        
        # Otherwise, end
        return END
    
    # Build the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(ALL_TOOLS))
    
    # Set entry point
    workflow.set_entry_point("agent")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            END: END,
        }
    )
    
    # Add edge from tools back to agent
    workflow.add_edge("tools", "agent")
    
    # Compile the graph
    return workflow.compile()


class YoncaAgent:
    """
    High-level wrapper for the Yonca AI agent.
    Supports multiple LLM backends.
    """
    
    def __init__(self, llm=None, llm_provider: str = "openai", api_key: str = None, model_name: str = None):
        """
        Initialize the Yonca AI agent.
        
        Args:
            llm: Optional pre-configured LLM instance
            llm_provider: Provider name ("openai", "azure", "anthropic", "ollama")
            api_key: API key for the provider
            model_name: Model name to use
        """
        if llm:
            self.llm = llm
        else:
            self.llm = self._create_llm(llm_provider, api_key, model_name)
        
        self.graph = create_yonca_agent(self.llm)
        self.conversation_history: list[BaseMessage] = []
    
    def _create_llm(self, provider: str, api_key: str = None, model_name: str = None):
        """Create an LLM instance based on provider."""
        if provider == "gemini":
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model=model_name or "gemini-2.0-flash",
                google_api_key=api_key,
                temperature=0.7,
            )
        
        elif provider == "ollama":
            from langchain_ollama import ChatOllama
            return ChatOllama(
                model=model_name or "qwen2.5:7b",  # Best for Azerbaijani
                temperature=0.7,
            )
        
        else:
            raise ValueError(f"Unknown LLM provider: {provider}. Supported: gemini, ollama")
    
    def chat(self, message: str) -> str:
        """
        Send a message and get a response.
        
        Args:
            message: User message in Azerbaijani
            
        Returns:
            AI response in Azerbaijani
        """
        # Add user message to history
        self.conversation_history.append(HumanMessage(content=message))
        
        # Run the agent
        result = self.graph.invoke({
            "messages": self.conversation_history,
            "farm_context": "",
        })
        
        # Extract final AI message
        final_messages = result.get("messages", [])
        
        # Find the last AI message that isn't a tool call
        ai_response = None
        for msg in reversed(final_messages):
            if isinstance(msg, AIMessage) and msg.content and not getattr(msg, 'tool_calls', []):
                ai_response = msg.content
                break
        
        if ai_response:
            # Add AI response to history (for context)
            self.conversation_history.append(AIMessage(content=ai_response))
            return ai_response
        
        return "Bağışlayın, sorğunuzu başa düşə bilmədim. Zəhmət olmasa yenidən cəhd edin."
    
    def reset(self):
        """Reset conversation history."""
        self.conversation_history = []
    
    def get_history(self) -> list[dict]:
        """Get conversation history as list of dicts."""
        history = []
        for msg in self.conversation_history:
            if isinstance(msg, HumanMessage):
                history.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                history.append({"role": "assistant", "content": msg.content})
        return history


# Convenience function for creating agents
def create_gemini_agent(api_key: str = None, model: str = "gemini-2.0-flash") -> YoncaAgent:
    """Create a Yonca agent using Google Gemini."""
    return YoncaAgent(llm_provider="gemini", api_key=api_key, model_name=model)


def create_ollama_agent(model: str = "qwen2.5:7b") -> YoncaAgent:
    """
    Create a Yonca agent using local Ollama.
    
    Recommended models for Azerbaijani:
    - qwen2.5:7b  - Best balance of speed and quality
    - qwen2.5:14b - Higher quality, slower
    - qwen2.5:3b  - Faster, lighter
    - aya:8b      - Cohere's multilingual model
    """
    return YoncaAgent(llm_provider="ollama", model_name=model)
