# -*- coding: utf-8 -*-
"""Qwen OAuth 完整流程测试.

测试整个流程：
1. 获取设备码
2. 等待用户授权
3. 保存 token
4. 测试 API 调用
"""
import asyncio
import time

import httpx

from one_dragon_alpha.core.model.qwen.oauth import (
    QwenOAuthClient,
    generate_pkce,
)
from one_dragon_alpha.core.model.qwen.token_manager import TokenPersistence


async def main():
    print("=" * 60)
    print("Qwen OAuth 完整流程测试")
    print("=" * 60)

    client = QwenOAuthClient()
    verifier, challenge = generate_pkce()

    # Step 1: Get device code
    print("\n步骤 1: 获取设备码")
    print("-" * 60)

    device = await client.get_device_code(challenge)

    print("\n请在浏览器中打开以下链接：")
    print("\n" + "=" * 60)
    print(f"\n{device.verification_uri_complete or device.verification_uri}")
    print(f"\n用户码: {device.user_code}")
    print(f"\n过期时间: {device.expires_in} 秒（{device.expires_in // 60} 分钟）")
    print("\n" + "=" * 60)

    # Step 2: Poll for token
    print("\n步骤 2: 等待授权...")
    print("-" * 60)

    start = time.time()
    poll_interval_ms = (device.interval or 2) * 1000
    timeout_ms = device.expires_in * 1000

    while time.time() - start < timeout_ms / 1000:
        print(".", end="", flush=True)
        result = await client.poll_device_token(
            device_code=device.device_code,
            code_verifier=verifier,
        )

        if result.status == "success":
            print("\n\n✅ 授权成功！")
            print(f"Access Token: {result.token.access_token[:30]}...")
            print(f"Refresh Token: {result.token.refresh_token[:30]}...")

            # Step 3: Save token
            print("\n步骤 3: 保存 Token")
            print("-" * 60)

            persistence = TokenPersistence()
            await persistence.save_token(result.token)
            print("✅ Token 已保存到 ~/.qwen/token.json")

            # Step 4: Test API call
            print("\n步骤 4: 测试 Qwen API 调用")
            print("-" * 60)
            print("发送消息: 'hi'")

            async with httpx.AsyncClient() as http_client:
                response = await http_client.post(
                    "https://portal.qwen.ai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {result.token.access_token}",
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
                    print(f"\n✅ 所有测试通过！")
                else:
                    print(f"\n❌ API 调用失败")
                    print(f"响应: {response.text[:200]}")

            return

        if result.status == "error":
            print(f"\n\n❌ OAuth 失败: {result.message}")
            return

        # Wait before next poll
        await asyncio.sleep(poll_interval_ms / 1000)

    print("\n\n❌ 超时")


asyncio.run(main())
