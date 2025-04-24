import yaml
import importlib
import os
import inspect

def deep_merge(base, overrides):
    if not overrides:
        return base
    result = base.copy()
    for key, value in overrides.items():
        if isinstance(value, dict) and key in result:
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result

def load_config_with_files(config, base_dir):
    for key, value in config.items():
        if isinstance(value, str):
            path = os.path.join(base_dir, value)
            if os.path.exists(path) and os.path.isfile(path):
                with open(path, 'r', encoding='utf-8') as f:
                    config[key] = f.read()
    return config

class PipelineFactory:
    def __init__(self, pipeline_configs):
        self.pipeline_configs = pipeline_configs

    @classmethod
    def from_pipeline_yaml(cls, path):
        base_dir = os.path.dirname(path)
        with open(path, 'r') as f:
            config_data = yaml.safe_load(f)
        config_data["config"] = load_config_with_files(config_data.get("config", {}), base_dir)
        return cls([config_data])

    @classmethod
    def from_pipeline_entries(cls, entries, base_dir):
        pipelines = []
        for entry in entries:
            if isinstance(entry, str) and entry.endswith('.yaml'):
                with open(os.path.join(base_dir, entry), 'r') as pf:
                    pipeline_cfg = yaml.safe_load(pf)
                pipelines.append(pipeline_cfg)
            elif isinstance(entry, dict):
                if 'ref' in entry:
                    with open(os.path.join(base_dir, entry['ref']), 'r') as pf:
                        pipeline_cfg = yaml.safe_load(pf)
                    pipeline_cfg = deep_merge(entry.get('overrides', {}), pipeline_cfg)
                    pipelines.append(pipeline_cfg)
                else:
                    pipelines.append(entry)
        for entry in pipelines:
            entry["config"] = load_config_with_files(entry.get("config", {}), base_dir)
        return cls(pipelines)

    def _load_class(self, class_path):
        module_name, class_name = class_path.rsplit(".", 1)
        module = importlib.import_module(module_name)
        return getattr(module, class_name)

    def build_all(self):
        pipelines = []
        for entry in self.pipeline_configs:
            cls = self._load_class(entry['class'])

            sig = inspect.signature(cls.__init__)
            accepted_keys = set(sig.parameters.keys()) - {"self", "args", "kwargs"}
            filtered_config = {
                k: v for k, v in entry.get("config", {}).items() if k in accepted_keys
            }

            pipeline = cls(
                stream_map=entry.get("stream_map", {}),
                **filtered_config,
            )
            pipelines.append(pipeline)
        return pipelines
