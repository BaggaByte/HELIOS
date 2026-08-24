import os
import logging
from typing import Dict, Any, List

from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from litellm import completion

logger = logging.getLogger(__name__)

# Configure LiteLLM to use a mock local model for now to satisfy CrewAI requirements
# In a real scenario, this would point to the OpenVINO local server
os.environ["OPENAI_API_BASE"] = "http://localhost:8000/v1"
os.environ["OPENAI_API_KEY"] = "sk-mock-key"
os.environ["MODEL_NAME"] = "openai/phi-4" # LiteLLM syntax
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"
os.environ["XDG_CONFIG_HOME"] = os.path.join(os.path.dirname(__file__), ".crewai_config")
os.environ["HOME"] = os.environ["XDG_CONFIG_HOME"]
os.environ["USERPROFILE"] = os.environ["XDG_CONFIG_HOME"]

class ScanTool(BaseTool):
    name: str = "Scan Tool"
    description: str = "Executes a reconnaissance scan on a target."

    def _run(self, target: str) -> str:
        return f"Scan completed for {target}. Found open ports: 80, 443."

class KnowledgeBaseTool(BaseTool):
    name: str = "Knowledge Base Tool"
    description: str = "Searches the knowledge base for information."

    def _run(self, query: str) -> str:
        return f"Found information related to: {query}."

scan_tool = ScanTool()
kb_tool = KnowledgeBaseTool()

def create_offensive_crew(objective: str) -> Crew:
    """Creates a Plan-Act-Observe-Verify crew for an offensive objective."""
    
    # 1. Planner Agent
    planner = Agent(
        role="Senior Offensive Security Planner",
        goal="Break down the user's objective into a step-by-step actionable plan.",
        backstory="You are an expert penetration tester who plans operations meticulously before executing any tools.",
        verbose=True,
        allow_delegation=False,
    )
    
    # 2. Executor Agent (Act)
    executor = Agent(
        role="Security Tool Executor",
        goal="Execute the plan exactly as specified by using the available tools.",
        backstory="You are a precise operator who runs security tools and collects the raw output.",
        tools=[scan_tool, kb_tool],
        verbose=True,
        allow_delegation=False,
    )
    
    # 3. Verifier Agent (Observe & Verify)
    verifier = Agent(
        role="Quality Assurance & Verification Analyst",
        goal="Observe the output from the executor and verify if it satisfies the original objective.",
        backstory="You critically analyze outputs to ensure they meet the goal. If not, you determine what needs to be redone.",
        verbose=True,
        allow_delegation=False,
    )
    
    # Tasks
    plan_task = Task(
        description=f"Create a step-by-step plan to achieve this objective: {objective}",
        expected_output="A numbered list of specific steps to execute.",
        agent=planner,
    )
    
    act_task = Task(
        description="Execute the steps outlined in the plan using the provided tools. Collect all outputs.",
        expected_output="Raw output from the executed tools.",
        agent=executor,
        context=[plan_task]
    )
    
    verify_task = Task(
        description=f"Review the tool outputs and verify if they successfully achieve the original objective: {objective}. Summarize the final results.",
        expected_output="A final summary of the findings, confirming the objective was met.",
        agent=verifier,
        context=[plan_task, act_task]
    )
    
    # Create Crew
    crew = Crew(
        agents=[planner, executor, verifier],
        tasks=[plan_task, act_task, verify_task],
        process=Process.sequential,
        verbose=True
    )
    
    return crew
