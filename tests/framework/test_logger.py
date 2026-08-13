# @agent: session-260808-young-raven | module: agent-teams-sdk-docs-tests | ts: 2026-08-08T16:43+08:00
"""AgentLogger 单元测试

覆盖：
- info / warning / error / debug 不抛异常
- 重复初始化不重复加 handler
- 自定义日志级别
"""
import logging

from agent_teams_sdk.infra.logger import AgentLogger


# ─── 基础日志方法 ───

class TestLoggingMethods:
    """各日志级别方法不抛异常"""

    def test_info_does_not_raise(self, caplog):
        """info 方法正常记录日志"""
        logger = AgentLogger("test-info")
        with caplog.at_level(logging.INFO, logger="test-info"):
            logger.info("这是一条 info 消息")
        assert "这是一条 info 消息" in caplog.text

    def test_warning_does_not_raise(self, caplog):
        """warning 方法正常记录日志"""
        logger = AgentLogger("test-warning")
        with caplog.at_level(logging.WARNING, logger="test-warning"):
            logger.warning("这是一条 warning 消息")
        assert "这是一条 warning 消息" in caplog.text

    def test_error_does_not_raise(self, caplog):
        """error 方法正常记录日志"""
        logger = AgentLogger("test-error")
        with caplog.at_level(logging.ERROR, logger="test-error"):
            logger.error("这是一条 error 消息")
        assert "这是一条 error 消息" in caplog.text

    def test_debug_does_not_raise(self, caplog):
        """debug 方法正常记录日志"""
        logger = AgentLogger("test-debug", level="DEBUG")
        with caplog.at_level(logging.DEBUG, logger="test-debug"):
            logger.debug("这是一条 debug 消息")
        assert "这是一条 debug 消息" in caplog.text

    def test_methods_accept_kwargs(self, caplog):
        """日志方法接受额外 kwargs 不报错"""
        logger = AgentLogger("test-kwargs", level="DEBUG")
        with caplog.at_level(logging.DEBUG, logger="test-kwargs"):
            # 不应抛出 TypeError
            logger.info("msg", extra_key="extra_val", another=123)
            logger.error("err", code=500)
            logger.warning("warn", context={"a": 1})
            logger.debug("dbg", detail="x")
        assert "msg" in caplog.text


# ─── 重复初始化 ───

class TestDuplicateInit:
    """重复初始化不重复添加 handler"""

    def test_no_duplicate_handlers(self):
        """同一 name 多次初始化，handler 不重复添加"""
        name = "test-no-dup"
        # 先清理可能存在的旧 logger
        old_logger = logging.getLogger(name)
        old_logger.handlers.clear()

        logger1 = AgentLogger(name)
        logger2 = AgentLogger(name)

        # 两次初始化应共享同一个 logging.Logger 实例
        assert logger1.logger is logger2.logger
        # handler 只应有一个
        assert len(logger1.logger.handlers) == 1

    def test_handler_count_after_multiple_inits(self):
        """多次初始化后 handler 数量仍为 1"""
        name = "test-handler-count"
        logging.getLogger(name).handlers.clear()

        for _ in range(5):
            AgentLogger(name)

        logger = logging.getLogger(name)
        assert len(logger.handlers) == 1


# ─── 日志级别 ───

class TestLogLevel:
    """自定义日志级别"""

    def test_custom_level_debug(self, caplog):
        """level='DEBUG' 时 debug 消息可见"""
        logger = AgentLogger("test-level-debug", level="DEBUG")
        with caplog.at_level(logging.DEBUG, logger="test-level-debug"):
            logger.debug("debug visible")
        assert "debug visible" in caplog.text

    def test_default_level_is_info(self):
        """默认级别为 INFO"""
        logger = AgentLogger("test-default-level")
        assert logger.logger.level == logging.INFO

    def test_set_level_changes_effective_level(self):
        """设置级别后 effective level 变化"""
        logger = AgentLogger("test-set-level", level="WARNING")
        assert logger.logger.level == logging.WARNING

        logger2 = AgentLogger("test-set-level-2", level="ERROR")
        assert logger2.logger.level == logging.ERROR

    def test_set_level_debug(self):
        """level='DEBUG' 正确设置"""
        logger = AgentLogger("test-debug-level", level="DEBUG")
        assert logger.logger.level == logging.DEBUG

    def test_set_level_error(self):
        """level='ERROR' 正确设置"""
        logger = AgentLogger("test-error-level", level="ERROR")
        assert logger.logger.level == logging.ERROR
