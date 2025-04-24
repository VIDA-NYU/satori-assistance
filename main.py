import argparse
import asyncio
from runtime.pipeline_factory import PipelineFactory
from runtime.agent_factory import AgentFactory
from ptgctl_pipeline.ptgctl_pipeline import PipelineServer
from ptgctl_pipeline.ptgctl_pipeline.config import read_config


def parse_args():
    parser = argparse.ArgumentParser(description="Run a Satori AR Agent.")
    parser.add_argument(
        "--agent-config",
        type=str,
        default="configs/agents/guidance.yaml",
        help="Path to the agent YAML configuration file."
    )
    parser.add_argument(
        "--server-config",
        type=str,
        default="shoyu",
        help="ptgctl server configuration profile (e.g., 'shoyu', 'local')"
    )
    return parser.parse_args()


async def main():
    args = parse_args()

    # Read ptgctl server config
    server_config = read_config(args.server_config)
    server = PipelineServer(server_config)

    # Load agent and register pipelines
    agent = AgentFactory.from_yaml(args.agent_config, server)
    await agent.start()


if __name__ == "__main__":
    asyncio.run(main())
