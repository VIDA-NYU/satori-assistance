# Version Amiga
# The folder contains the code deployed on the 09/05/2024 user study, still in development
# The version is named as Amiga, which is friend in Espagnol, also the name of my flamingo plushie friend
# from .dalle_pipeline import DallePipeline, DallePipelineAnim
# from .summary import SummaryPipeline
# from .assemble_pipeline_gpt import AssemblePipelineGPTfast, AssemblePipelineGPT

# def register_amiga_pipelines(server):
#     summary_pipeline = SummaryPipeline()
#     assemble_pipeline_gpt = AssemblePipelineGPT(text_always=True)
#     assemble_pipeline_gpt_fast = AssemblePipelineGPTfast()
#     dalle_pipeline = DallePipeline()
    
#     server.register_pipeline(assemble_pipeline_gpt)
#     server.register_pipeline(assemble_pipeline_gpt_fast)
#     server.register_pipeline(summary_pipeline)
#     server.register_pipeline(dalle_pipeline)
#     return server

"""
Init file for DALL-E rendering pipelines.

Exports:
- DallePipeline: single-image generation
- DallePipelineAnim: multi-frame animation rendering
- format_protobuf_bytes: utility for formatting image sequences
"""

from .dalle_image_pipeline import DallePipeline
from .dalle_animation_pipeline import DallePipelineAnim
from .image_sequence_pb2 import ImageSequence, ImageData
