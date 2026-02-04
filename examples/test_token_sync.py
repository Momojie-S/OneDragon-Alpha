# -*- coding: utf-8 -*-
"""测试 Token 同步逻辑."""
import asyncio

from one_dragon_alpha.core.model.qwen.token_manager import TokenPersistence


async def main():
    print("=" * 60)
    print("测试 Token 同步逻辑")
    print("=" * 60)

    persistence = TokenPersistence()

    print("\n检查 Token 文件:")
    print("-" * 60)
    print(f"我们的位置: {persistence._token_path}")
    print(f"存在: {persistence._token_path.exists()}")

    print(f"\nQwen CLI 位置: {persistence._qwen_cli_token_path}")
    print(f"存在: {persistence._qwen_cli_token_path.exists()}")

    print("\n尝试加载 Token:")
    print("-" * 60)

    token = await persistence.load_token()

    if token:
        print(f"✅ Token 加载成功!")
        print(f"Access Token: {token.access_token[:30]}...")
        print(f"Refresh Token: {token.refresh_token[:30]}...")
        print(f"过期时间: {token.expires_at}")
    else:
        print("❌ 未找到 Token")
        print("\n请运行以下命令进行认证:")
        print("  uv run --env-file .env python examples/qwen_complete.py")


asyncio.run(main())
