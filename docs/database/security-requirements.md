# 数据库安全要求

## 核心原则

**数据库严禁对外暴露，仅允许内网访问。**

## 网络隔离

- MySQL 绑定到内网 IP（如 `10.0.0.1`），不要使用 `0.0.0.0`
- 防火墙仅允许内网访问 3306 端口
- 云数据库安全组仅允许内网访问

## API Key 安全

- API key 明文存储在数据库中
- 数据库不对外暴露，通过内网访问保障安全
- 前端不可查看 API key
- GET 接口不返回 `api_key` 字段

## 访问控制

创建专用数据库用户，仅授予必要权限：

```sql
CREATE USER 'onedragon_app'@'%' IDENTIFIED BY 'strong_password';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX ON onedragon.* TO 'onedragon_app'@'%';
```

## 备份

- 每天自动备份
- 备份文件加密存储
- 存储在异地

## 部署检查清单

- [ ] MySQL 仅绑定内网 IP
- [ ] 防火墙仅允许内网访问 3306
- [ ] 云数据库安全组仅允许内网访问
- [ ] 创建专用数据库用户（不使用 root）
- [ ] 使用强密码（16 位以上）
- [ ] 配置每日自动备份
- [ ] 备份文件加密存储
