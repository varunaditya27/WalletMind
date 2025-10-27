"""
Agent Loop - Continuous Agent Decision-Making

Runs agents autonomously on a schedule:
- Periodic financial analysis
- Scheduled transactions
- Proactive recommendations
- Pattern-based triggers
- Goal-oriented planning
"""

from typing import Dict, Any, List, Optional, Callable
import asyncio
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TriggerType(str, Enum):
    """Agent trigger types"""
    SCHEDULED = "scheduled"  # Fixed schedule
    PATTERN = "pattern"      # Pattern detected
    GOAL = "goal"            # Goal-based
    EVENT = "event"          # External event
    THRESHOLD = "threshold"  # Threshold crossed


class AgentTask:
    """Agent task definition"""
    def __init__(
        self,
        task_id: str,
        wallet_address: str,
        agent_type: str,
        trigger_type: TriggerType,
        interval: Optional[int] = None,
        enabled: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.task_id = task_id
        self.wallet_address = wallet_address
        self.agent_type = agent_type
        self.trigger_type = trigger_type
        self.interval = interval  # Seconds for scheduled tasks
        self.enabled = enabled
        self.metadata = metadata or {}
        
        self.created_at = datetime.utcnow()
        self.last_run: Optional[datetime] = None
        self.next_run: Optional[datetime] = None
        self.run_count = 0
        self.success_count = 0
        self.failure_count = 0
        
        # Calculate next run for scheduled tasks
        if trigger_type == TriggerType.SCHEDULED and interval:
            self.next_run = datetime.utcnow() + timedelta(seconds=interval)
    
    def should_run(self) -> bool:
        """Check if task should run now"""
        if not self.enabled:
            return False
        
        if self.trigger_type != TriggerType.SCHEDULED:
            # Non-scheduled tasks are triggered externally
            return False
        
        if not self.next_run:
            return False
        
        return datetime.utcnow() >= self.next_run
    
    def mark_completed(self, success: bool):
        """Mark task as completed"""
        self.last_run = datetime.utcnow()
        self.run_count += 1
        
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
        
        # Schedule next run
        if self.trigger_type == TriggerType.SCHEDULED and self.interval:
            self.next_run = datetime.utcnow() + timedelta(seconds=self.interval)


class AgentLoop:
    """
    Background service for continuous agent operation.
    
    Features:
    - Scheduled agent execution
    - Pattern-based triggers
    - Goal-oriented planning
    - Proactive recommendations
    - Event-driven actions
    """
    
    def __init__(
        self,
        orchestrator: Any,
        memory_service: Optional[Any] = None,
        reputation_updator: Optional[Any] = None,
        check_interval: int = 30  # Check every 30 seconds
    ):
        """
        Initialize agent loop
        
        Args:
            orchestrator: Agent orchestrator
            memory_service: Memory service for context
            reputation_updator: Reputation service for tracking
            check_interval: Seconds between task checks
        """
        self.orchestrator = orchestrator
        self.memory_service = memory_service
        self.reputation_updator = reputation_updator
        self.check_interval = check_interval
        
        # Task management
        self.tasks: Dict[str, AgentTask] = {}
        
        # Event handlers
        self.event_handlers: Dict[str, Callable] = {}
        
        # Loop state
        self.is_running = False
        self.loop_task: Optional[asyncio.Task] = None
        
        logger.info("Agent loop initialized")
    
    async def start(self):
        """Start agent loop"""
        if self.is_running:
            logger.warning("Loop already running")
            return
        
        self.is_running = True
        self.loop_task = asyncio.create_task(self._main_loop())
        logger.info("Agent loop started")
    
    async def stop(self):
        """Stop agent loop"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.loop_task:
            self.loop_task.cancel()
            try:
                await self.loop_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Agent loop stopped")
    
    def add_task(
        self,
        task_id: str,
        wallet_address: str,
        agent_type: str,
        trigger_type: TriggerType,
        interval: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentTask:
        """
        Add agent task
        
        Args:
            task_id: Unique task ID
            wallet_address: Wallet address
            agent_type: Agent type
            trigger_type: Trigger type
            interval: Interval in seconds (for scheduled)
            metadata: Task metadata
        
        Returns:
            Created AgentTask
        """
        if task_id in self.tasks:
            logger.warning(f"Task {task_id} already exists")
            return self.tasks[task_id]
        
        task = AgentTask(
            task_id=task_id,
            wallet_address=wallet_address,
            agent_type=agent_type,
            trigger_type=trigger_type,
            interval=interval,
            metadata=metadata
        )
        
        self.tasks[task_id] = task
        logger.info(f"Added task {task_id} ({trigger_type.value})")
        
        return task
    
    def remove_task(self, task_id: str) -> bool:
        """
        Remove agent task
        
        Args:
            task_id: Task ID
        
        Returns:
            True if removed
        """
        if task_id in self.tasks:
            del self.tasks[task_id]
            logger.info(f"Removed task {task_id}")
            return True
        return False
    
    def enable_task(self, task_id: str):
        """Enable task"""
        task = self.tasks.get(task_id)
        if task:
            task.enabled = True
            logger.info(f"Enabled task {task_id}")
    
    def disable_task(self, task_id: str):
        """Disable task"""
        task = self.tasks.get(task_id)
        if task:
            task.enabled = False
            logger.info(f"Disabled task {task_id}")
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get task information
        
        Args:
            task_id: Task ID
        
        Returns:
            Task info or None
        """
        task = self.tasks.get(task_id)
        
        if not task:
            return None
        
        return {
            "task_id": task.task_id,
            "wallet_address": task.wallet_address,
            "agent_type": task.agent_type,
            "trigger_type": task.trigger_type.value,
            "interval": task.interval,
            "enabled": task.enabled,
            "metadata": task.metadata,
            "created_at": task.created_at.isoformat(),
            "last_run": task.last_run.isoformat() if task.last_run else None,
            "next_run": task.next_run.isoformat() if task.next_run else None,
            "run_count": task.run_count,
            "success_count": task.success_count,
            "failure_count": task.failure_count
        }
    
    def get_all_tasks(
        self,
        wallet_address: Optional[str] = None,
        agent_type: Optional[str] = None,
        enabled_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get all tasks with optional filters
        
        Args:
            wallet_address: Filter by wallet
            agent_type: Filter by agent type
            enabled_only: Only enabled tasks
        
        Returns:
            List of task info
        """
        results = []
        
        for task_id, task in self.tasks.items():
            if wallet_address and task.wallet_address != wallet_address:
                continue
            if agent_type and task.agent_type != agent_type:
                continue
            if enabled_only and not task.enabled:
                continue
            
            info = self.get_task(task_id)
            if info:
                results.append(info)
        
        return results
    
    def register_event_handler(
        self,
        event_type: str,
        handler: Callable
    ):
        """
        Register event handler
        
        Args:
            event_type: Event type
            handler: Async handler function
        """
        self.event_handlers[event_type] = handler
        logger.info(f"Registered handler for event: {event_type}")
    
    async def trigger_event(
        self,
        event_type: str,
        data: Dict[str, Any]
    ):
        """
        Trigger event-based tasks
        
        Args:
            event_type: Event type
            data: Event data
        """
        # Find event-triggered tasks
        event_tasks = [
            task for task in self.tasks.values()
            if task.trigger_type == TriggerType.EVENT and task.enabled
        ]
        
        if not event_tasks:
            return
        
        logger.info(f"Event {event_type} triggered {len(event_tasks)} tasks")
        
        # Run tasks
        for task in event_tasks:
            try:
                await self._execute_task(task, context={"event": event_type, "data": data})
            except Exception as e:
                logger.error(f"Error executing event task {task.task_id}: {e}")
        
        # Call registered handler
        if event_type in self.event_handlers:
            try:
                handler = self.event_handlers[event_type]
                await handler(data)
            except Exception as e:
                logger.error(f"Error in event handler for {event_type}: {e}")
    
    async def _main_loop(self):
        """Main agent loop"""
        logger.info("Main loop started")
        
        while self.is_running:
            try:
                await self._check_and_run_tasks()
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                await asyncio.sleep(self.check_interval)
        
        logger.info("Main loop stopped")
    
    async def _check_and_run_tasks(self):
        """Check and run due tasks"""
        due_tasks = [task for task in self.tasks.values() if task.should_run()]
        
        if not due_tasks:
            return
        
        logger.debug(f"Running {len(due_tasks)} due tasks")
        
        for task in due_tasks:
            try:
                await self._execute_task(task)
            except Exception as e:
                logger.error(f"Error executing task {task.task_id}: {e}")
    
    async def _execute_task(
        self,
        task: AgentTask,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Execute agent task
        
        Args:
            task: Agent task
            context: Additional context
        """
        logger.info(f"Executing task {task.task_id} for {task.wallet_address}")
        
        start_time = datetime.utcnow()
        
        try:
            # Build request based on task type
            request = self._build_request(task, context)
            
            # Get conversation context if available
            if self.memory_service:
                recent_context = await self.memory_service.get_recent(
                    wallet_address=task.wallet_address,
                    limit=5
                )
                request["context"] = recent_context
            
            # Execute through orchestrator
            result = await self.orchestrator.process_request(
                user_request=request.get("description", "Scheduled task"),
                wallet_address=task.wallet_address,
                network=request.get("network", "sepolia"),
                context=request.get("context")
            )
            
            success = result.get("approved", False)
            
            # Record performance
            if self.reputation_updator:
                response_time = (datetime.utcnow() - start_time).total_seconds()
                self.reputation_updator.record_decision(
                    agent_id=f"{task.wallet_address}_{task.agent_type}",
                    agent_type=task.agent_type,
                    success=success,
                    response_time=response_time
                )
            
            task.mark_completed(success=success)
            
            logger.info(f"Task {task.task_id} completed: success={success}")
            
        except Exception as e:
            logger.error(f"Task {task.task_id} failed: {e}")
            task.mark_completed(success=False)
    
    def _build_request(
        self,
        task: AgentTask,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build agent request from task
        
        Args:
            task: Agent task
            context: Additional context
        
        Returns:
            Request dict
        """
        request = {
            "task_id": task.task_id,
            "agent_type": task.agent_type,
            "trigger_type": task.trigger_type.value,
            "metadata": task.metadata
        }
        
        # Add task-specific fields
        if task.trigger_type == TriggerType.SCHEDULED:
            request["description"] = task.metadata.get(
                "description",
                f"Scheduled {task.agent_type} task"
            )
        elif task.trigger_type == TriggerType.GOAL:
            request["description"] = f"Goal: {task.metadata.get('goal', 'Unknown')}"
        elif task.trigger_type == TriggerType.EVENT:
            request["description"] = f"Event-triggered task"
            if context:
                request.update(context)
        
        return request
    
    def get_stats(self) -> Dict[str, Any]:
        """Get loop statistics"""
        total_tasks = len(self.tasks)
        enabled_tasks = sum(1 for t in self.tasks.values() if t.enabled)
        total_runs = sum(t.run_count for t in self.tasks.values())
        total_successes = sum(t.success_count for t in self.tasks.values())
        
        # Trigger type distribution
        trigger_counts = {}
        for task in self.tasks.values():
            trigger = task.trigger_type.value
            trigger_counts[trigger] = trigger_counts.get(trigger, 0) + 1
        
        return {
            "total_tasks": total_tasks,
            "enabled_tasks": enabled_tasks,
            "total_runs": total_runs,
            "total_successes": total_successes,
            "success_rate": round((total_successes / total_runs * 100) if total_runs > 0 else 0, 2),
            "trigger_distribution": trigger_counts,
            "is_running": self.is_running,
            "check_interval": self.check_interval
        }


# Singleton instance
_agent_loop: Optional[AgentLoop] = None


def get_agent_loop(
    orchestrator: Any,
    memory_service: Optional[Any] = None,
    reputation_updator: Optional[Any] = None
) -> AgentLoop:
    """Get or create singleton AgentLoop instance"""
    global _agent_loop
    
    if _agent_loop is None:
        _agent_loop = AgentLoop(
            orchestrator=orchestrator,
            memory_service=memory_service,
            reputation_updator=reputation_updator
        )
    
    return _agent_loop