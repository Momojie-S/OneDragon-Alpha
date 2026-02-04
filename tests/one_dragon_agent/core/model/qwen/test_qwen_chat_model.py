# -*- coding: utf-8 -*-
"""Tests for QwenChatModel class."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from one_dragon_agent.core.model.qwen.qwen_chat_model import QwenChatModel


@pytest.mark.timeout(10)
class TestQwenChatModelInit:
    """Test cases for QwenChatModel initialization."""

    async def test_init_with_default_model(self) -> None:
        """Test initialization with default model."""
        # Mock TokenManager
        with patch(
            "one_dragon_agent.core.model.qwen.qwen_chat_model.QwenTokenManager"
        ) as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.get_instance.return_value = mock_manager

            # Mock OpenAIChatModel parent class
            with patch(
                "one_dragon_agent.core.model.qwen.qwen_chat_model.OpenAIChatModel.__init__"
            ) as mock_parent_init:
                _ = QwenChatModel(model_name="coder-model")

                # Verify parent init was called with correct parameters
                mock_parent_init.assert_called_once()
                call_kwargs = mock_parent_init.call_args.kwargs

                # Model name should have qwen-portal prefix
                assert call_kwargs.get("model_name") == "qwen-portal/coder-model"
                # Token is a placeholder
                assert call_kwargs.get("api_key") == "qwen-oauth-placeholder"
                assert "portal.qwen.ai" in call_kwargs.get("client_args", {}).get("base_url", "")

    async def test_init_with_custom_model(self) -> None:
        """Test initialization with custom model name."""
        with patch(
            "one_dragon_agent.core.model.qwen.qwen_chat_model.QwenTokenManager"
        ) as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.get_instance.return_value = mock_manager

            with patch(
                "one_dragon_agent.core.model.qwen.qwen_chat_model.OpenAIChatModel.__init__"
            ) as mock_parent_init:
                _ = QwenChatModel(model_name="vision-model")

                call_kwargs = mock_parent_init.call_args.kwargs
                assert call_kwargs.get("model_name") == "qwen-portal/vision-model"

    async def test_init_uses_correct_base_url(self) -> None:
        """Test that initialization uses correct Qwen base URL."""
        with patch(
            "one_dragon_agent.core.model.qwen.qwen_chat_model.QwenTokenManager"
        ) as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.get_instance.return_value = mock_manager

            with patch(
                "one_dragon_agent.core.model.qwen.qwen_chat_model.OpenAIChatModel.__init__"
            ) as mock_parent_init:
                _ = QwenChatModel(model_name="coder-model")

                call_kwargs = mock_parent_init.call_args.kwargs
                base_url = call_kwargs.get("client_args", {}).get("base_url", "")

                assert "portal.qwen.ai" in base_url
                assert "/v1" in base_url

    async def test_init_gets_token_manager(self) -> None:
        """Test that initialization gets TokenManager instance."""
        with patch(
            "one_dragon_agent.core.model.qwen.qwen_chat_model.QwenTokenManager"
        ) as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.get_instance.return_value = mock_manager

            with patch(
                "one_dragon_agent.core.model.qwen.qwen_chat_model.OpenAIChatModel.__init__"
            ):
                _ = QwenChatModel(model_name="coder-model")

                # Verify get_instance was called
                mock_manager_class.get_instance.assert_called_once()


@pytest.mark.timeout(10)
class TestQwenChatModelIntegration:
    """Test cases for QwenChatModel integration."""

    async def test_supported_models(self) -> None:
        """Test that QwenChatModel supports expected models."""
        expected_models = ["coder-model", "vision-model"]

        for model_name in expected_models:
            mock_token = "test-token"

            with patch(
                "one_dragon_agent.core.model.qwen.qwen_chat_model.QwenTokenManager"
            ) as mock_manager_class:
                mock_manager = MagicMock()
                mock_manager.get_access_token = AsyncMock(return_value=mock_token)
                mock_manager_class.get_instance.return_value = mock_manager

                with patch(
                    "one_dragon_agent.core.model.qwen.qwen_chat_model.OpenAIChatModel.__init__"
                ):
                    # Should not raise an error
                    model = QwenChatModel(model_name=model_name)
                    assert model is not None

    async def test_model_name_format(self) -> None:
        """Test that model names are formatted correctly."""
        with patch(
            "one_dragon_agent.core.model.qwen.qwen_chat_model.QwenTokenManager"
        ) as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.get_instance.return_value = mock_manager

            with patch(
                "one_dragon_agent.core.model.qwen.qwen_chat_model.OpenAIChatModel.__init__"
            ) as mock_parent_init:
                # Test with model name (no prefix)
                _ = QwenChatModel(model_name="coder-model")
                call_kwargs1 = mock_parent_init.call_args.kwargs

                # Model name should have qwen-portal prefix added
                assert call_kwargs1.get("model_name") == "qwen-portal/coder-model"

    async def test_model_name_already_has_prefix(self) -> None:
        """Test that model names with prefix are not modified."""
        with patch(
            "one_dragon_agent.core.model.qwen.qwen_chat_model.QwenTokenManager"
        ) as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.get_instance.return_value = mock_manager

            with patch(
                "one_dragon_agent.core.model.qwen.qwen_chat_model.OpenAIChatModel.__init__"
            ) as mock_parent_init:
                # Test with model name that already has prefix
                _ = QwenChatModel(model_name="qwen-portal/coder-model")
                call_kwargs = mock_parent_init.call_args.kwargs

                # Model name should not be double-prefixed
                assert call_kwargs.get("model_name") == "qwen-portal/coder-model"


@pytest.mark.timeout(10)
class TestQwenChatModelErrorHandling:
    """Test cases for QwenChatModel error handling."""

    async def test_token_not_available_error(self) -> None:
        """Test that TokenNotAvailableError is raised when calling model."""
        from one_dragon_agent.core.model.qwen.oauth import QwenTokenNotAvailableError

        with patch(
            "one_dragon_agent.core.model.qwen.qwen_chat_model.QwenTokenManager"
        ) as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.get_access_token = AsyncMock(
                side_effect=QwenTokenNotAvailableError("No token available")
            )
            mock_manager_class.get_instance.return_value = mock_manager

            with patch(
                "one_dragon_agent.core.model.qwen.qwen_chat_model.OpenAIChatModel.__init__"
            ):
                model = QwenChatModel(model_name="coder-model")

                # Error should be raised when calling the model (not during init)
                with pytest.raises(QwenTokenNotAvailableError):
                    # Call _ensure_token which triggers token loading
                    model._ensure_token()

    async def test_token_refresh_error_during_call(self) -> None:
        """Test that token refresh errors during model call are propagated."""
        from one_dragon_agent.core.model.qwen.oauth import (
            QwenRefreshTokenInvalidError,
            QwenTokenNotAvailableError,
        )

        with patch(
            "one_dragon_agent.core.model.qwen.qwen_chat_model.QwenTokenManager"
        ) as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.get_access_token = AsyncMock(
                side_effect=QwenRefreshTokenInvalidError("Invalid refresh token")
            )
            mock_manager_class.get_instance.return_value = mock_manager

            with patch(
                "one_dragon_agent.core.model.qwen.qwen_chat_model.OpenAIChatModel.__init__"
            ):
                model = QwenChatModel(model_name="coder-model")

                # Error should be raised when calling the model
                with pytest.raises(QwenTokenNotAvailableError):
                    # Call _ensure_token which wraps the error
                    model._ensure_token()
