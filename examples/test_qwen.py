# -*- coding: utf-8 -*-
"""Qwen OAuth 简单测试."""
import asyncio
import time

from one_dragon_alpha.core.model.qwen.oauth import (
    QwenOAuthClient,
    generate_pkce,
)


async def main():
    print("=" * 60)
    print("Qwen OAuth 测试")
    print("=" * 60)

    client = QwenOAuthClient()
    verifier, challenge = generate_pkce()

    print(f"\n生成的 verifier 长度: {len(verifier)}")
    print(f"生成的 verifier: {verifier[:20]}...")
    print(f"生成的 challenge: {challenge[:20]}...")

    # Get device code
    print("\n步骤 1: 获取设备码")
    print("-" * 60)

    device = await client.get_device_code(challenge)

    print("\n请在浏览器中打开以下链接：")
    print("\n" + "=" * 60)
    print(f"\n{device.verification_uri_complete or device.verification_uri}")
    print(f"\n用户码: {device.user_code}")
    print(f"\n过期时间: {device.expires_in} 秒")
    print("\n" + "=" * 60)

    # Poll for token
    print("\n步骤 2: 等待授权...")
    print("-" * 60)

    start = time.time()
    poll_interval_ms = (device.interval or 2) * 1000
    timeout_ms = device.expires_in * 1000

    while time.time() - start < timeout_ms / 1000:
        print(f"轮询中... ({int(time.time() - start)}秒)", flush=True)
        result = await client.poll_device_token(
            device_code=device.device_code,
            code_verifier=verifier,
        )

        if result.status == "success":
            print("\n✅ 成功！")
            print(f"Access Token: {result.token.access_token[:30]}...")
            print(f"Refresh Token: {result.token.refresh_token[:30]}...")
            return

        if result.status == "error":
            print(f"\n❌ 错误: {result.message}")
            return

        # Wait before next poll
        await asyncio.sleep(poll_interval_ms / 1000)

    print("\n❌ 超时")


asyncio.run(main())
