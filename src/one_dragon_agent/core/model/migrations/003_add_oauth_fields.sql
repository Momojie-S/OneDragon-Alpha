-- 添加 OAuth 相关字段到 model_configs 表
-- 版本: 003
-- 日期: 2026-02-11
-- 说明: 支持 Qwen 等 OAuth 2.0 认证的模型提供商

-- 添加 OAuth 访问令牌字段（明文存储）
ALTER TABLE model_configs ADD COLUMN oauth_access_token TEXT DEFAULT NULL COMMENT 'OAuth 访问令牌';

-- 添加 OAuth 令牌类型字段
ALTER TABLE model_configs ADD COLUMN oauth_token_type VARCHAR(50) DEFAULT NULL COMMENT 'OAuth 令牌类型（如 Bearer）';

-- 添加 OAuth 刷新令牌字段（明文存储）
ALTER TABLE model_configs ADD COLUMN oauth_refresh_token TEXT DEFAULT NULL COMMENT 'OAuth 刷新令牌';

-- 添加 OAuth 令牌过期时间字段（毫秒时间戳）
ALTER TABLE model_configs ADD COLUMN oauth_expires_at BIGINT DEFAULT NULL COMMENT 'OAuth 访问令牌过期时间戳（毫秒）';

-- 添加 OAuth 授权范围字段
ALTER TABLE model_configs ADD COLUMN oauth_scope VARCHAR(500) DEFAULT NULL COMMENT 'OAuth 授权范围（如 openid profile email）';

-- 添加 OAuth 元数据字段（JSON 格式）
ALTER TABLE model_configs ADD COLUMN oauth_metadata JSON DEFAULT NULL COMMENT 'OAuth 额外元数据（JSON 格式，如 resource_url 等）';

-- 创建索引以支持 token 过期检查
CREATE INDEX idx_oauth_expires_at ON model_configs(oauth_expires_at);
