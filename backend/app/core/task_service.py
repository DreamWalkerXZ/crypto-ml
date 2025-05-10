from typing import Dict, Optional
import uuid
from datetime import datetime
from app.schemas.backtest import BacktestResult

class TaskStatus:
    """Task status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class Task:
    """Task class representing a single backtesting task"""
    
    def __init__(self, task_id: str, params: dict):
        """
        Initialize a new task
        
        Args:
            task_id: Unique identifier for the task
            params: Task parameters dictionary
        """
        self.task_id = task_id
        self.params = params
        self.status = TaskStatus.PENDING
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.result: Optional[BacktestResult] = None
        self.error: Optional[str] = None

class TaskService:
    """Service for managing backtesting tasks"""
    
    def __init__(self):
        """Initialize the task service with an empty task dictionary"""
        self.tasks: Dict[str, Task] = {}

    def create_task(self, params: dict) -> str:
        """
        Create a new backtesting task
        
        Args:
            params: Task parameters dictionary
            
        Returns:
            str: Unique task identifier
        """
        task_id = str(uuid.uuid4())
        self.tasks[task_id] = Task(task_id, params)
        return task_id

    def get_task(self, task_id: str) -> Optional[Task]:
        """
        Retrieve a task by its ID
        
        Args:
            task_id: Unique task identifier
            
        Returns:
            Optional[Task]: Task object if found, None otherwise
        """
        return self.tasks.get(task_id)

    def update_task_status(self, task_id: str, status: str, result: Optional[BacktestResult] = None, error: Optional[str] = None):
        """
        Update the status and related information of a task
        
        Args:
            task_id: Unique task identifier
            status: New status for the task
            result: Optional backtest result
            error: Optional error message
        """
        task = self.tasks.get(task_id)
        if task:
            task.status = status
            if status == TaskStatus.RUNNING:
                task.started_at = datetime.now()
            elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                task.completed_at = datetime.now()
                task.result = result
                task.error = error

# Global task service instance
task_service = TaskService() 