"""Project initialization module for Vertex AI setup."""

import vertexai

from firstagent.utils.config import config


def init_vertex_ai():
    """Initialize Vertex AI client with project and location from config."""
    client = vertexai.Client(
        project=config.project_id,
        location=config.location,
    )
    return client


def initialize():
    """Initialize Vertex AI client."""
    return init_vertex_ai()

