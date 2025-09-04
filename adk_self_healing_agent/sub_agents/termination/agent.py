"""Termination agent for Bank of Anthos services."""

from google.adk.agents import Agent

from adk_self_healing_agent.sub_agents.termination.prompt import TERMINATION_CHECKER_PROMPT
from adk_self_healing_agent.config import get_config

config = get_config()

termination_agent = Agent(
    model=config.model.name,
    name="termination_agent",
    description="Determines when the healing loop should terminate",
    instruction=TERMINATION_CHECKER_PROMPT,
    tools=[],
)
