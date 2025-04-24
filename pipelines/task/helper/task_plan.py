"""
Task Plan Loader

Provides utility function for loading predefined task plans from a YAML configuration file.
"""

import yaml
from pathlib import Path

DEFAULT_TASK_PLAN_PATH = Path(__file__).parent / "task_plans.yaml"

def load_task_plan(task_name: str, path: str = None):
    """
    Load a named task plan from a YAML configuration file.

    :param task_name: Name of the task to load (e.g., 'coffee', 'ns').
    :type task_name: str
    :param path: Optional path to a specific YAML file. Defaults to 'task_plans.yaml' in the current directory.
    :type path: str or None
    :return: Dictionary representing the task plan.
    :rtype: dict
    """
    task_path = Path(path) if path else DEFAULT_TASK_PLAN_PATH
    with task_path.open("r") as f:
        all_plans = yaml.safe_load(f)
    return all_plans.get(task_name, {})
