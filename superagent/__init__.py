"""
SuperAgent: Production-ready CLI-based AI automation platform.

A modular, extensible framework for orchestrating large language models,
tools, and autonomous workflows at scale.
"""

__version__ = "0.1.0"
__author__ = "SuperAgent Team"

from superagent.core.runtime import SuperAgentRuntime
from superagent.core.config import SuperAgentConfig

__all__ = ["SuperAgentRuntime", "SuperAgentConfig", "__version__"]
