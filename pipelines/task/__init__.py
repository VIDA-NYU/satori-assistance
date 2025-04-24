from .task_control_pipeline import TaskControlPipeline 
from .task_planner_pipeline import TaskPlannerPipeline
from .step_checkpoint_pipeline import StepCheckpointTestPipeline
from .gpt_guidance_pipeline import GPTGuidancePipeline
from .gpt_action_pipeline import GPTActionPredictionPipeline
from ..frame_selector import FrameSelectorPipeline

def register_task_planner_pipelines(server, task_name="coffee"):
    task_control_pipeline = TaskControlPipeline(task_name=task_name)
    # step_checkpoint_pipeline = StepCheckpointTestPipeline()
    gpt_guidance_pipeline = GPTGuidancePipeline()
    # gpt_action_pipeline = GPTActionPredictionPipeline()
    
    frame_selector_pipeline = FrameSelectorPipeline()
    server.register_pipeline(frame_selector_pipeline)
    
    server.register_pipeline(task_control_pipeline)
    
    # server.register_pipeline(step_checkpoint_pipeline)
    server.register_pipeline(gpt_guidance_pipeline)
    # server.register_pipeline(gpt_action_pipeline)
    return server

    """
Guidance Pipelines Package

This package contains pipeline modules for task tracking, GPT-based visual assistance,
and procedural step-level prediction.
"""

# __all__ = [
#     "TaskControlPipeline",
#     "GPTGuidancePipeline",
#     "GPTActionPredictionPipeline"
# ]
