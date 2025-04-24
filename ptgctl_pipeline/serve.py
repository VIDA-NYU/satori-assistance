# # # from ptgctl_pipeline import PipelineServer
# # from ptgctl_pipeline.pipeline import PrintPipeline, GPTPipeline
# from ptgctl_pipeline.config import read_config
import asyncio


async def main():
    config = read_config()
    server = PipelineServer(config)

    # Users define their custom pipelines
    custom_pipeline_1 = GPTPipeline(prompt_message="Please generate anything about New York", input_stream_name="chat:user:message_channel1", output_stream_name="chat:assistant:message_channel1", sleep_time=0)
    
    custom_pipeline_2 = PrintPipeline(input_stream_name="chat:user:message_channel2", output_stream_name="chat:assistant:message_channel2", sleep_time=0)

    server.register_pipeline(custom_pipeline_1)
    server.register_pipeline(custom_pipeline_2)

    # Start server
    await server.start()
    
if __name__ == "__main__":
    # main()
    asyncio.run(main())