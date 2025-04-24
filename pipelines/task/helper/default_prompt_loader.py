
import yaml

def load_default_system_prompt(prompt_file_path):
    """
    Load the default system prompt from a YAML file.

    :param prompt_file_path: Path to the YAML file containing the system prompt.
    :type prompt_file_path: str
    :return: The system prompt as a string.
    :rtype: str
    """
    with prompt_file_path.open() as f:
        prompt_config = yaml.safe_load(f)
    return prompt_config['system_prompt']