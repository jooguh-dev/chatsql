# GCP Cloud SQL 配置指南

本文档说明如何配置项目以连接到GCP Cloud SQL MySQL实例。

## 数据库结构

GCP Cloud SQL MySQL 实例 (`chatsql-instance`) 包含以下数据库：

```
chatsql-instance
│
├── chatsql_system          (系统主数据库)
│   ├── problems            (题目元数据表)
│   ├── problem_tables      (题目表定义表)
│   └── user_submissions    (用户提交记录表)
│
├── chatsql_problem_1       (题目1独立数据库)
│   └── Products            (题目1的实际表)
│
├── chatsql_problem_2       (题目2独立数据库)
│   └── Customer            (题目2的实际表)
│
├── chatsql_problem_6       (题目6独立数据库)
│   └── Views               (题目6的实际表)
│
└── chatsql_problem_N       (题目N独立数据库)
    └── TableName           (题目N的实际表)
```

## 环境变量配置

在项目根目录创建 `.env` 文件，添加以下配置：

```bash
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,localhost,127.0.0.1

# OpenAI Configuration (可选)
OPENAI_MODE=mock
OPENAI_API_KEY=your_openai_api_key_here

# ============================================
# GCP Cloud SQL Configuration
# ============================================
GCP_DB_HOST=your-gcp-cloud-sql-instance-ip-or-hostname
GCP_DB_USER=your-gcp-db-user
GCP_DB_PASSWORD=your-gcp-db-password
GCP_DB_PORT=3306
# 可选：GCP实例连接名称 (格式: project:region:instance)
# GCP_INSTANCE_CONNECTION_NAME=your-project:your-region:chatsql-instance
```

## 配置说明

### 1. GCP_DB_HOST
- GCP Cloud SQL实例的IP地址或主机名
- 可以在GCP控制台的Cloud SQL实例详情页面找到
- 格式示例: `34.123.45.67` 或 `chatsql-instance.region.gcp.cloud`

### 2. GCP_DB_USER
- 数据库用户名
- 确保该用户有访问 `chatsql_system` 和所有 `chatsql_problem_N` 数据库的权限

### 3. GCP_DB_PASSWORD
- 数据库用户密码

### 4. GCP_DB_PORT
- MySQL端口，默认为 `3306`

### 5. GCP_INSTANCE_CONNECTION_NAME (可选)
- GCP实例连接名称
- 格式: `project-id:region:instance-name`
- 如果使用Cloud SQL Proxy，可能需要此配置

## 数据库连接逻辑

1. **主数据库 (chatsql_system)**: 
   - Django的默认数据库连接
   - 存储系统表：`problems`, `problem_tables`, `user_submissions` 等

2. **题目数据库 (chatsql_problem_N)**:
   - 动态连接，根据 `DatabaseSchema` 模型中的 `db_name` 字段确定
   - 例如：如果 `db_name = 'chatsql_problem_1'`，系统会自动连接到 `chatsql_problem_1` 数据库
   - 在 `exercises/models.py` 的 `DatabaseSchema` 模型中设置 `db_name` 字段

## 设置步骤

1. **创建 `.env` 文件**:
   ```bash
   cp .env.example .env  # 如果存在.env.example
   # 或手动创建.env文件
   ```

2. **填写GCP连接信息**:
   编辑 `.env` 文件，填入上述GCP配置

3. **运行数据库迁移**:
   ```bash
   python manage.py migrate
   ```

4. **创建超级用户** (可选):
   ```bash
   python manage.py createsuperuser
   ```

5. **启动服务器**:
   ```bash
   python manage.py runserver
   ```

## 验证连接

启动Django服务器后，检查日志确认是否成功连接到GCP数据库。如果出现连接错误，请检查：

1. GCP Cloud SQL实例是否正在运行
2. 防火墙规则是否允许来自应用服务器的连接
3. 数据库用户权限是否正确
4. 环境变量是否正确设置

## 注意事项

- 确保GCP Cloud SQL实例允许来自应用服务器的IP地址连接
- 如果使用Cloud SQL Proxy，需要先启动代理服务
- 生产环境建议使用SSL连接（可在settings.py中配置）
- 确保数据库用户有足够的权限访问所有需要的数据库

## 故障排除

### 连接超时
- 检查GCP防火墙规则
- 确认实例IP地址正确
- 检查网络连接

### 权限错误
- 确认数据库用户有访问所有数据库的权限
- 检查用户密码是否正确

### 数据库不存在
- 确保 `chatsql_system` 数据库已创建
- 确保所有需要的 `chatsql_problem_N` 数据库已创建

