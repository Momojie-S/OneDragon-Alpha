# -*- coding: utf-8 -*-
"""测试 Qwen API 调用（使用已保存的 token）."""
import asyncio

import httpx

from one_dragon_alpha.core.model.qwen.token_manager import TokenPersistence


async def main():
    print("=" * 60)
    print("测试 Qwen API 调用")
    print("=" * 60)

    # Load token
    print("\n加载 Token...")
    persistence = TokenPersistence()
    token_data = await persistence.load_token()

    if token_data is None:
        print("❌ 未找到 token，请先运行 qwen_complete.py")
        return

    print(f"✅ Token 加载成功: {token_data.access_token[:30]}...")

    # Test API call
    print("\n测试 API 调用...")
    print("-" * 60)
    print("发送消息: 'hi'")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://portal.qwen.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {token_data.access_token}",
                "Content-Type": "application/json",
            },
            json={
                "model": "coder-model",
                "messages": [{"role": "user", "content": "hi"}],
            },
        )

        print(f"\n状态码: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            reply = data["choices"][0]["message"]["content"]
            print(f"\n✅ API 调用成功！")
            print(f"\nQwen 回复:")
            print(f"{reply}")
            print(f"\n✅ 测试通过！")
        else:
            print(f"\n❌ API 调用失败")
            print(f"响应: {response.text}")


asyncio.run(main())
