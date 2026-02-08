-- 创建通用模型配置表
-- 版本: 001
-- 日期: 2025-02-06

CREATE TABLE IF NOT EXISTS model_configs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '配置 ID',
    name VARCHAR(255) UNIQUE NOT NULL COMMENT '配置名称（用户自定义）',
    provider VARCHAR(50) NOT NULL COMMENT '模型提供商（openai/qwen/deepseek等）',
    base_url TEXT NOT NULL COMMENT 'API baseUrl',
    api_key TEXT NOT NULL COMMENT 'API密钥（明文存储，数据库不对外暴露）',
    models JSON NOT NULL COMMENT '模型列表（JSON数组）',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_name (name),
    INDEX idx_provider (provider),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='通用模型配置表';
