-- 更新 model_configs 表的 datetime 列精度
-- 版本: 002
-- 日期: 2026-02-07
--
-- 问题: DATETIME 列只支持到秒精度，导致乐观锁失败
-- 解决方案: 使用 DATETIME(6) 支持微秒精度

-- 修改 created_at 列
ALTER TABLE model_configs MODIFY COLUMN created_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6) COMMENT '创建时间';

-- 修改 updated_at 列
ALTER TABLE model_configs MODIFY COLUMN updated_at DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '更新时间';
