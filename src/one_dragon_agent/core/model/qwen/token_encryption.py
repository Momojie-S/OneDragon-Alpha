# -*- coding: utf-8 -*-
"""Token 加密工具模块.

本模块提供 Token 加密和解密功能，使用 Fernet 对称加密算法。
用于安全存储 OAuth access_token 和 refresh_token。
"""

import os
from typing import Final

from cryptography.fernet import Fernet, InvalidToken

from one_dragon_agent.core.system.log import get_logger

logger = get_logger(__name__)

# 默认加密密钥（仅用于开发环境，生产环境必须设置环境变量）
_DEFAULT_ENCRYPTION_KEY: Final[bytes] = b'dZ3f6Y8xK2mP9qW4tR7uJ1nB5cV8sL2='

# 环境变量名称
_ENCRYPTION_KEY_ENV: Final[str] = "TOKEN_ENCRYPTION_KEY"


class TokenEncryption:
    """Token 加密工具类.

    使用 Fernet 对称加密算法对敏感信息进行加密和解密。
    Fernet 提供：
    - 加密 + 签名（确保数据完整性）
    - 时间戳验证（防止重放攻击）
    - 使用 AES-128-CBC 加密

    Attributes:
        _cipher: Fernet 加密器实例

    Examples:
        >>> enc = TokenEncryption()
        >>> encrypted = enc.encrypt("my_secret_token")
        >>> decrypted = enc.decrypt(encrypted)
        >>> assert decrypted == "my_secret_token"
    """

    def __init__(self, encryption_key: str | None = None) -> None:
        """初始化 Token 加密工具.

        Args:
            encryption_key: Fernet 加密密钥（44 字符 base64 编码字符串）。
                如果未提供，则从环境变量 TOKEN_ENCRYPTION_KEY 读取。
                如果环境变量也未设置，则使用默认密钥（不推荐）。

        Raises:
            ValueError: 如果提供的密钥格式无效。

        """
        key = encryption_key or os.getenv(_ENCRYPTION_KEY_ENV)

        if key is None:
            logger.warning(
                f"未设置环境变量 {_ENCRYPTION_KEY_ENV}，使用默认密钥。"
                "生产环境必须设置独立的加密密钥！"
            )
            key = _DEFAULT_ENCRYPTION_KEY.decode()

        try:
            # 确保 key 是 bytes 类型
            if isinstance(key, str):
                key_bytes = key.encode()
            else:
                key_bytes = key

            self._cipher = Fernet(key_bytes)
        except Exception as e:
            msg = f"无效的加密密钥格式: {e}"
            raise ValueError(msg) from e

    def encrypt(self, plaintext: str) -> str:
        """加密明文字符串.

        Args:
            plaintext: 要加密的明文字符串（如 access_token、refresh_token）。

        Returns:
            加密后的 base64 编码字符串。

        Raises:
            ValueError: 如果 plaintext 不是字符串。

        """
        if not isinstance(plaintext, str):
            msg = f"加密输入必须是字符串，收到: {type(plaintext)}"
            raise ValueError(msg)

        try:
            # Fernet.encrypt 返回 bytes，转换为 str 存储
            encrypted_bytes = self._cipher.encrypt(plaintext.encode())
            return encrypted_bytes.decode()
        except Exception as e:
            logger.error(f"加密失败: {e}")
            raise

    def decrypt(self, ciphertext: str) -> str:
        """解密密文字符串.

        Args:
            ciphertext: 加密后的 base64 编码字符串。

        Returns:
            解密后的明文字符串。

        Raises:
            InvalidToken: 如果密文无效或已被篡改。
            ValueError: 如果 ciphertext 不是字符串。

        """
        if not isinstance(ciphertext, str):
            msg = f"解密输入必须是字符串，收到: {type(ciphertext)}"
            raise ValueError(msg)

        try:
            # Fernet.decrypt 需要 bytes，输入先转换为 bytes
            decrypted_bytes = self._cipher.decrypt(ciphertext.encode())
            return decrypted_bytes.decode()
        except InvalidToken as e:
            logger.error(f"解密失败: 密文无效或已被篡改")
            raise
        except Exception as e:
            logger.error(f"解密失败: {e}")
            raise

    @staticmethod
    def generate_key() -> str:
        """生成新的 Fernet 加密密钥.

        Returns:
            44 字符的 base64 编码密钥字符串。

        Examples:
            >>> key = TokenEncryption.generate_key()
            >>> print(f"设置环境变量: export TOKEN_ENCRYPTION_KEY={key}")
        """
        return Fernet.generate_key().decode()


# 默认加密器实例（单例模式）
_default_instance: TokenEncryption | None = None


def get_token_encryption() -> TokenEncryption:
    """获取默认的 Token 加密器实例（单例）.

    Returns:
        TokenEncryption 实例。

    Examples:
        >>> enc = get_token_encryption()
        >>> encrypted = enc.encrypt("secret")
    """
    global _default_instance
    if _default_instance is None:
        _default_instance = TokenEncryption()
    return _default_instance


def reset_token_encryption() -> None:
    """重置默认加密器实例（用于测试）.

    测试后应调用此方法以清除缓存的实例。
    """
    global _default_instance
    _default_instance = None
