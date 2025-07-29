from typing import Dict, List, Any, Optional, TypedDict
from langgraph.graph import StateGraph  
from langchain_core.tools import BaseTool
from config.llm_config import llm_config
import logging

class AgentState(TypedDict):
    """State schema for agent execution"""
    input: str
    result: Optional[str]

class BaseHealthcareAgent:
    """Base class for all healthcare agents using LangGraph"""
    
    def __init__(self, agent_name: str, system_prompt: str, tools: List[BaseTool]):
        self.agent_name = agent_name
        self.system_prompt = system_prompt
        self.tools = tools
        self.llm = llm_config.get_groq_llm()
        self.logger = logging.getLogger(f"{__name__}.{agent_name}")
        self.graph = self._build_graph()
    
    def _build_graph(self):
        # Define the agent's main step as a function node
        def agent_step(state: AgentState) -> AgentState:
            input_data = state.get("input", "")
            # Here you would use self.llm, self.tools, self.system_prompt, etc.
            # For now, just echo the input and prompt for demonstration
            # You can expand this logic to use your LLM and tools as needed
            result = f"Prompt: {self.system_prompt}\nInput: {input_data}"
            return {"result": result, "input": input_data}
        
        graph = StateGraph(AgentState)
        graph.add_node("agent_step", agent_step)
        graph.set_entry_point("agent_step")
        return graph
    
    def execute(self, input_data: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            state = {"input": input_data}
            if context:
                state.update(context)
            result = self.graph.run(state)
            self.logger.info(f"{self.agent_name} executed successfully")
            return {
                'success': True,
                'result': result.get('result'),
                'agent': self.agent_name
            }
        except Exception as e:
            self.logger.error(f"{self.agent_name} execution failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'agent': self.agent_name
            }
    
    def get_tools(self) -> List[BaseTool]:
        """Get agent tools"""
        return self.tools
    
    def add_tool(self, tool: BaseTool):
        """Add tool to agent"""
        self.tools.append(tool)
        # Rebuild the graph if tools change
        self.graph = self._build_graph()