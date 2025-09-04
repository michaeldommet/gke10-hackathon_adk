"""Bank of Anthos Self-Healing Agent using Agent Development Kit"""

import logging
from google.adk.agents import Agent

from adk_self_healing_agent import prompt
from adk_self_healing_agent.config import get_config

from adk_self_healing_agent.sub_agents.monitoring.agent import monitoring_agent
from adk_self_healing_agent.sub_agents.analysis.agent import analysis_agent
from adk_self_healing_agent.sub_agents.decision.agent import decision_agent
from adk_self_healing_agent.sub_agents.termination.agent import termination_agent

# Suppress authentication warnings for development
logging.getLogger('google.adk.tools.authenticated_tool.base_authenticated_tool').setLevel(logging.ERROR)

config = get_config()

root_agent = Agent(
    model=config.model.name,
    name="root_agent", 
    description="A Bank of Anthos Self-Healing Agent using multiple specialized sub-agents",
    instruction=prompt.ROOT_AGENT_PROMPT,
    sub_agents=[
        monitoring_agent,
        analysis_agent,
        decision_agent,
        termination_agent,
    ],
)
