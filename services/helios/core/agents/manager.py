import logging
import asyncio
from typing import Dict, Any, Callable
from helios.core.agents.crew import create_offensive_crew

logger = logging.getLogger(__name__)

class AgentManager:
    """
    Manages the lifecycle and execution of CrewAI agents.
    Handles streaming status updates back to the WebSocket client.
    """
    
    def __init__(self):
        pass

    async def execute_task(self, objective: str, update_callback: Callable[[str], None]) -> str:
        """
        Executes a CrewAI task asynchronously and streams status updates.
        """
        logger.info(f"Starting agent task: {objective}")
        
        # 1. Planning Phase
        await update_callback("Planning Phase: Breaking down objective into actionable steps...")
        await asyncio.sleep(1.5) # Simulate thinking/setup time
        
        # 2. Setup Crew
        try:
            crew = create_offensive_crew(objective)
            
            # 3. Action Phase
            await update_callback("Action Phase: Executing security tools based on plan...")
            
            # CrewAI kickoff is synchronous, so we run it in a threadpool to not block the async loop
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, crew.kickoff)
            
            # 4. Verify Phase
            await update_callback("Verify Phase: Analyzing tool outputs and ensuring objective is met...")
            await asyncio.sleep(1) # Simulate verification time
            
            return str(result)
            
        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            await update_callback(f"Error during execution: {str(e)}")
            return f"Agent execution failed: {str(e)}"

agent_manager = AgentManager()
