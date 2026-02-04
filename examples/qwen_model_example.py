# -*- coding: utf-8 -*-
"""Qwen 模型使用示例.

本示例展示如何使用 QwenChatModel 进行模型调用。
"""

import asyncio
from one_dragon_agent.core.agent.qwen import (
    QwenChatModel,
    QwenTokenManager,
    login_qwen_oauth,
)


async def example_basic_usage():
    """基本使用示例."""
    print("=== 基本使用示例 ===\n")

    # 首次使用需要进行 OAuth 认证
    print("1. 进行 OAuth 认证...")
    try:
        await login_qwen_oauth()
    except Exception as e:
        print(f"认证失败: {e}")
        return

    # 创建模型实例
    print("\n2. 创建模型实例...")
    model = QwenChatModel(model_name="coder-model")

    # 使用模型
    print("\n3. 调用模型...")
    try:
        response = model("你好，请用一句话介绍你自己。")
        print(f"模型回复: {response}")
    except Exception as e:
        print(f"模型调用失败: {e}")


async def example_multiple_models():
    """多模型类型示例."""
    print("\n=== 多模型类型示例 ===\n")

    # 代码模型
    coder_model = QwenChatModel(model_name="coder-model")
    print("代码模型创建成功")

    # 视觉模型（支持图像输入）
    vision_model = QwenChatModel(model_name="vision-model")
    print("视觉模型创建成功")


async def example_token_manager():
    """Token 管理器使用示例."""
    print("\n=== Token 管理器示例 ===\n")

    # 获取 token 管理器单例
    manager = QwenTokenManager.get_instance()
    print("Token 管理器实例获取成功")

    # 获取 access token
    try:
        token = await manager.get_access_token()
        print(f"Access token 获取成功: {token[:20]}...")
    except Exception as e:
        print(f"获取 token 失败: {e}")
        print("请先运行 OAuth 认证")
        return

    # 检查 token 是否有效
    print(f"Token 已自动启动后台刷新任务")


async def example_error_handling():
    """错误处理示例."""
    print("\n=== 错误处理示例 ===\n")

    from one_dragon_agent.core.agent.qwen import (
        QwenTokenNotAvailableError,
        QwenRefreshTokenInvalidError,
    )

    try:
        model = QwenChatModel()
        response = model("Hello!")
        print(f"响应: {response}")
    except QwenTokenNotAvailableError:
        print("错误: 未找到有效 token")
        print("解决方案: 请先运行 login_qwen_oauth() 进行认证")
    except QwenRefreshTokenInvalidError:
        print("错误: refresh_token 无效")
        print("解决方案: 请重新运行 login_qwen_oauth() 进行认证")
    except Exception as e:
        print(f"其他错误: {e}")


async def main():
    """主函数."""
    try:
        # 运行各个示例
        await example_basic_usage()
        await example_multiple_models()
        await example_token_manager()
        await example_error_handling()

    finally:
        # 始终在程序结束时关闭 token 管理器
        print("\n关闭 Token 管理器...")
        await QwenTokenManager.get_instance().shutdown()
        print("程序结束")


if __name__ == "__main__":
    asyncio.run(main())
