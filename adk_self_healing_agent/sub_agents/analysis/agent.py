"""Analysis agent for Bank of Anthos services."""

from google.adk.agents import Agent

from adk_self_healing_agent.sub_agents.analysis.prompt import ANALYSIS_AGENT_PROMPT
from adk_self_healing_agent.config import get_config

config = get_config()

analysis_agent = Agent(
    model=config.model.name,
    name="analysis_agent",
    description="Analyzes Bank of Anthos service issues and determines root causes from monitoring data",
    instruction=ANALYSIS_AGENT_PROMPT,
    tools=[],  # No tools - analysis only agent
)
