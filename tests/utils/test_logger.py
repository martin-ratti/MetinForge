import pytest
import logging
from unittest.mock import patch, MagicMock
from app.utils.logger import setup_logger, log_db_operation, log_import, log_user_action, logger


class TestSetupLogger:
    def test_logger_returns_logger_instance(self):
        result = setup_logger("TestLogger")
        assert isinstance(result, logging.Logger)
        assert result.name == "TestLogger"

    def test_logger_has_handlers(self):
        result = setup_logger("HandlerTest")
        assert len(result.handlers) > 0

    def test_logger_level_is_info(self):
        result = setup_logger("LevelTest")
        assert result.level == logging.INFO

    def test_default_logger_exists(self):
        assert logger is not None
        assert isinstance(logger, logging.Logger)


class TestLogDbOperation:
    def test_log_db_operation_basic(self):
        with patch.object(logger, 'info') as mock_info:
            log_db_operation("insert", "servers")
            mock_info.assert_called_once()
            msg = mock_info.call_args[0][0]
            assert "INSERT" in msg
            assert "servers" in msg

    def test_log_db_operation_with_count(self):
        with patch.object(logger, 'info') as mock_info:
            log_db_operation("update", "characters", count=5)
            msg = mock_info.call_args[0][0]
            assert "5 registros" in msg

    def test_log_db_operation_with_details(self):
        with patch.object(logger, 'info') as mock_info:
            log_db_operation("delete", "activities", details="evento 1")
            msg = mock_info.call_args[0][0]
            assert "evento 1" in msg


class TestLogImport:
    def test_log_import_success(self):
        with patch.object(logger, 'info') as mock_info:
            log_import("test.xlsx", accounts=3)
            mock_info.assert_called_once()
            msg = mock_info.call_args[0][0]
            assert "test.xlsx" in msg
            assert "3 cuentas" in msg

    def test_log_import_with_errors_uses_warning(self):
        with patch.object(logger, 'warning') as mock_warn:
            log_import("test.xlsx", accounts=3, errors=2)
            mock_warn.assert_called_once()
            msg = mock_warn.call_args[0][0]
            assert "2 errores" in msg


class TestLogUserAction:
    def test_log_user_action_basic(self):
        with patch.object(logger, 'info') as mock_info:
            log_user_action("click_import")
            mock_info.assert_called_once()
            msg = mock_info.call_args[0][0]
            assert "click_import" in msg

    def test_log_user_action_with_context(self):
        with patch.object(logger, 'info') as mock_info:
            log_user_action("change_event", context="Evento Febrero")
            msg = mock_info.call_args[0][0]
            assert "Evento Febrero" in msg
