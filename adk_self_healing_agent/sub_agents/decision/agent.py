"""Decision agent for Bank of Anthos services."""

from google.adk.agents import Agent
from adk_self_healing_agent.config import get_config
from adk_self_healing_agent.sub_agents.decision.prompt import DECISION_AGENT_PROMPT
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams, StdioServerParameters
from dotenv import load_dotenv
import os
from adk_self_healing_agent.tools.adk_tools import (
    restart_deployment_tool,
    scale_deployment_tool,
    send_alert_tool,
)


load_dotenv()

JIRA_URL = os.getenv("JIRA_URL")
JIRA_USERNAME = os.getenv("JIRA_USERNAME")
JIRA_TOKEN = os.getenv("JIRA_TOKEN")
MODEL = os.getenv("GOOGLE_GENAI_MODEL")

def create_jira_tools():
    """Create Jira MCP tools with error handling."""
    try:
        # Check if all required Jira config is present
        if not all([JIRA_URL, JIRA_USERNAME, JIRA_TOKEN]):
            print("⚠️  Jira configuration incomplete - skipping Jira integration")
            return None
            
        jira_tools = MCPToolset(
            connection_params=StdioConnectionParams(
                server_params = StdioServerParameters(
                    command='uvx',
                    args=[
                        "mcp-atlassian", 
                        f"--jira-url={JIRA_URL}",
                        f"--jira-username={JIRA_USERNAME}",
                        f"--jira-token={JIRA_TOKEN}",
                        f"--oauth-cloud-id={os.getenv('ATLASSIAN_OAUTH_CLOUD_ID')}",
                    ],
                ),
            ),
            # Load all available Jira tools - agent will use efficiently based on prompt guidance
            # tool_filter = ['getJiraIssue', 'editJiraIssue', 'createJiraIssue', 'getTransitionsForJiraIssue', 'transitionJiraIssue', 'lookupJiraAccountId', 'searchJiraIssuesUsingJql', 'addCommentToJiraIssue', 'getJiraIssueRemoteIssueLinks', 'getVisibleJiraProjects', 'getJiraProjectIssueTypesMetadata']
        )
        
        print("✅ Jira MCP tools configured successfully")
        return jira_tools
        
    except Exception as e:
        print(f"⚠️  Failed to initialize Jira tools: {e}")
        print("   Continuing without Jira integration...")
        return None


def create_decision_agent() -> Agent:
    """Create decision agent with tools based on autopilot configuration."""
    config = get_config()
    
    # Get allowed tools based on autopilot configuration
    tools = config.autopilot.get_allowed_actions()
    
    # Try to add Jira tools with error handling
    jira_tools = create_jira_tools()
    if jira_tools:
        agent_tools = tools + [jira_tools]
        description = "Makes healing decisions and executes remediation actions for Bank of Anthos services with Jira integration"
    else:
        agent_tools = tools
        description = "Makes healing decisions and executes remediation actions for Bank of Anthos services (Jira integration unavailable)"
    
    return Agent(
        model=config.model.name,
        name="decision_agent",
        description=description,
        instruction=DECISION_AGENT_PROMPT,
        tools=agent_tools,
    )


# Create the agent instance
decision_agent = create_decision_agent()
