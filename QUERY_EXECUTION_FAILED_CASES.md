# ❌ Query execution failed 错误情况说明

## 错误触发位置

"❌ Query execution failed" 消息在 `ai_tutor/views.py` 的 `_format_result_summary` 方法中生成，当 `result['success']` 为 `False` 时显示。

## 所有可能导致失败的情况

### 1. 系统表查询失败（chatsql_system数据库）

**位置**: `ai_tutor/views.py` 的 `_execute_sql` 方法（第152-174行）

**可能原因**:
- **数据库连接失败**: 无法连接到 `chatsql_system` 数据库
- **SQL语法错误**: SQL语句语法不正确
- **表不存在**: 查询的表在 `chatsql_system` 中不存在
- **权限不足**: 数据库用户没有查询权限
- **执行异常**: 在执行SQL时发生未捕获的异常

**示例错误**:
```python
# 表不存在
(1146, "Table 'chatsql_system.xxx' doesn't exist")

# 语法错误
(1064, "You have an error in your SQL syntax...")

# 权限错误
(1142, "SELECT command denied to user...")
```

### 2. Problem数据库无法确定

**位置**: `ai_tutor/views.py` 的 `_execute_sql` 方法（第177-191行）

**触发条件**:
- `problem_database_name` 参数为 `None`
- 无法通过 `exercise_id` 从GCP获取problem信息
- 获取的problem信息中没有 `database_name` 字段

**返回的错误**:
```python
{
    'success': False,
    'error': 'Cannot determine problem database. Please specify the problem.',
    ...
}
```

### 3. SQLExecutor查询验证失败

**位置**: `exercises/services/executor.py` 的 `execute` 方法（第100-110行）

**验证规则**（`validate_query` 方法）:

#### 3.1 不是SELECT查询
- **错误**: "Only SELECT queries are allowed"
- **原因**: SQL不是以 `SELECT` 开头

#### 3.2 包含危险关键字
- **错误**: "Keyword 'XXX' is not allowed"
- **禁止的关键字**: `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `CREATE`, `TRUNCATE`, `GRANT`, `REVOKE`, `EXEC`
- **原因**: 查询中包含这些危险操作

#### 3.3 包含注释
- **错误**: "Comments are not allowed in queries"
- **原因**: SQL中包含 `--`、`/*` 或 `*/`

#### 3.4 多条语句
- **错误**: "Multiple statements are not allowed"
- **原因**: SQL中包含多个分号（`;`）

### 4. SQLExecutor数据库连接失败

**位置**: `exercises/services/executor.py` 的 `execute` 方法（第115-126行）

**可能原因**:
- **数据库不存在**: 指定的 `chatsql_problem_N` 数据库不存在
- **连接超时**: 连接数据库超时（5秒）
- **认证失败**: 用户名或密码错误
- **网络问题**: 无法连接到数据库服务器
- **端口错误**: 数据库端口不正确

**示例错误**:
```python
# 数据库不存在
(1049, "Unknown database 'chatsql_problem_999'")

# 连接超时
pymysql.err.OperationalError: (2003, "Can't connect to MySQL server...")

# 认证失败
(1045, "Access denied for user...")
```

### 5. SQLExecutor执行超时

**位置**: `exercises/services/executor.py` 的 `execute` 方法（第130行）

**限制**: `MAX_EXECUTION_TIME = 5` 秒

**可能原因**:
- 查询太复杂，执行时间超过5秒
- 数据库负载过高
- 查询涉及大量数据

**错误**: `pymysql.err.OperationalError` 或超时异常

### 6. SQLExecutor执行异常

**位置**: `exercises/services/executor.py` 的 `execute` 方法（第152-160行）

**捕获的异常类型**: `pymysql.MySQLError`

**常见错误**:
- **表不存在**: `(1146, "Table 'xxx' doesn't exist")`
- **列不存在**: `(1054, "Unknown column 'xxx' in 'field list'")`
- **语法错误**: `(1064, "You have an error in your SQL syntax...")`
- **数据类型错误**: `(1366, "Incorrect string value...")`
- **外键约束**: `(1452, "Cannot add or update a child row...")`
- **唯一约束**: `(1062, "Duplicate entry...")`

### 7. SQLExecutor初始化失败

**位置**: `ai_tutor/views.py` 的 `_execute_sql` 方法（第194-220行）

**可能原因**:
- **数据库配置无效**: `SQLExecutor(problem_database_name)` 初始化失败
- **ValueError**: 数据库名称格式不正确或不在允许的列表中
- **其他异常**: 初始化过程中的任何异常

**示例错误**:
```python
ValueError: "Invalid database for GCP: chatsql_problem_999"
```

## 错误处理流程

```
AI生成SQL
    ↓
_execute_sql() 被调用
    ↓
判断查询类型（系统表 vs 题目表）
    ↓
┌─────────────────┬──────────────────┐
│   系统表查询     │   题目表查询      │
│ (chatsql_system)│ (chatsql_problem_N)│
└─────────────────┴──────────────────┘
    ↓                    ↓
直接执行SQL      使用SQLExecutor
    ↓                    ↓
可能失败         验证 → 连接 → 执行
    ↓                    ↓
返回结果         可能失败
    ↓                    ↓
_format_result_summary()
    ↓
如果 success=False
    ↓
显示: "❌ Query execution failed"
```

## 常见错误场景

### 场景1: 表不存在
```sql
SELECT * FROM Products
```
**错误**: `(1146, "Table 'chatsql_system.Products' doesn't exist")`
**原因**: Products表不在chatsql_system中，应该在chatsql_problem_N中
**解决**: 系统已修复，会自动路由到正确的数据库

### 场景2: 包含危险操作
```sql
SELECT * FROM Products; DROP TABLE Products;
```
**错误**: "Multiple statements are not allowed"
**原因**: 包含多条语句，且包含DROP操作

### 场景3: 查询超时
```sql
SELECT * FROM LargeTable WHERE complex_condition...
```
**错误**: 执行超时（>5秒）
**原因**: 查询太复杂或数据量太大

### 场景4: 数据库连接失败
**错误**: `(2003, "Can't connect to MySQL server...")`
**原因**: 
- GCP数据库服务器不可用
- 网络连接问题
- 防火墙阻止连接

### 场景5: 权限不足
**错误**: `(1142, "SELECT command denied to user...")`
**原因**: 数据库用户没有查询权限

## 调试建议

1. **检查错误消息**: 查看返回的 `error` 字段，通常包含详细的错误信息
2. **检查数据库连接**: 确认GCP数据库服务器可访问
3. **检查SQL语法**: 验证SQL语句是否正确
4. **检查表名**: 确认表名拼写正确，且在正确的数据库中
5. **检查权限**: 确认数据库用户有足够的权限
6. **查看日志**: 检查Django日志获取更多详细信息

## 相关代码位置

- **错误消息生成**: `ai_tutor/views.py:225`
- **SQL执行**: `ai_tutor/views.py:139-220`
- **查询验证**: `exercises/services/executor.py:62-86`
- **查询执行**: `exercises/services/executor.py:88-164`

