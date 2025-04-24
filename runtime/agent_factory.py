import os
import yaml
from .pipeline_factory import PipelineFactory
from .agent import Agent

class AgentFactory:
    @classmethod
    def from_yaml(cls, path, server):
        base_dir = os.path.dirname(path)
        with open(path, 'r') as f:
            config_data = yaml.safe_load(f)

        agent_config = config_data.get('agent', {})
        global_stream_map = agent_config.get("stream_map", {})
        global_args = agent_config.get("global_args", {})
        pipeline_entries = agent_config.get("pipelines", [])

        # Inject global stream_map into each pipeline
        for i, entry in enumerate(pipeline_entries):
            if isinstance(entry, dict) and "ref" in entry:
                # will be handled in PipelineFactory
                entry.setdefault("overrides", {})
                entry["overrides"]["stream_map"] = {
                    **global_stream_map,
                    **entry["overrides"].get("stream_map", {})
                }
                entry["overrides"]["config"] = {
                    **global_args,
                    **entry["overrides"].get("config", {})
                }

                

        factory = PipelineFactory.from_pipeline_entries(pipeline_entries, base_dir)
        pipelines = factory.build_all()

        return Agent(server=server, pipelines=pipelines, config=agent_config)
