# -*- coding: utf-8 -*-
"""Qwen 模型使用示例.

本示例展示如何使用 QwenChatModel 进行模型调用。
"""

import asyncio
from one_dragon_agent.core.model.qwen import (
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
        response = await model([{"role": "user", "content": "你好，请用一句话介绍你自己。"}])
        # response 是一个 ChatResponse 对象，可以通过 .content 或 .text 获取内容
        print(f"模型回复: {response.content}")
    except Exception as e:
        print(f"模型调用失败: {e}")


async def example_stream_usage():
    """流式输出使用示例."""
    print("\n=== 流式输出示例 ===\n")

    # 创建支持流式输出的模型实例
    model = QwenChatModel(model_name="coder-model", stream=True)

    print("开始流式调用...")
    try:
        response_stream = await model([
            {"role": "user", "content": "请用三句话介绍 Python 语言的特点。"}
        ])

        # 流式响应是一个异步生成器，需要迭代获取
        print("模型回复（流式）: ", end="", flush=True)
        async for chunk in response_stream:
            if chunk.content:
                print(chunk.content, end="", flush=True)
        print()  # 换行
    except Exception as e:
        print(f"\n流式调用失败: {e}")


async def example_multiple_models():
    """多模型类型示例."""
    print("\n=== 多模型类型示例 ===\n")

    # 代码模型
    _ = QwenChatModel(model_name="coder-model")
    print("代码模型创建成功")

    # 视觉模型（支持图像输入）
    _ = QwenChatModel(model_name="vision-model")
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
    print("Token 已自动启动后台刷新任务")


async def example_error_handling():
    """错误处理示例."""
    print("\n=== 错误处理示例 ===\n")

    from one_dragon_agent.core.model.qwen import (
        QwenTokenNotAvailableError,
        QwenRefreshTokenInvalidError,
    )

    try:
        model = QwenChatModel()
        response = await model([{"role": "user", "content": "Hello!"}])
        print(f"响应: {response.content}")
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
        await example_stream_usage()
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
