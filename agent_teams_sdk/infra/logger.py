# @agent: session-260808-fleet-spruce | module: agent-teams-sdk-skeleton | ts: 2026-08-08T16:35+08:00
# 接口定义来源：跨项目接口开发需求-MemoryPalace-SelfBrain.md §5.1
import logging


class AgentLogger:
    """Agent 日志框架"""

    def __init__(self, name: str, level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level))
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            self.logger.addHandler(handler)

    def info(self, message: str, **kwargs) -> None:
        self.logger.info(message)

    def error(self, message: str, **kwargs) -> None:
        self.logger.error(message)

    def warning(self, message: str, **kwargs) -> None:
        self.logger.warning(message)

    def debug(self, message: str, **kwargs) -> None:
        self.logger.debug(message)
