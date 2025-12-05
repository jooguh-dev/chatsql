# AI数据库路由修复

## 问题描述

AI助手在执行SQL查询时，尝试在错误的数据库中查找表。例如：
- 错误：在 `chatsql_system` 数据库中查找 `Products` 表
- 正确：`Products` 表应该在对应的 `chatsql_problem_N` 数据库中（如 `chatsql_problem_1`）

## 数据库结构

系统使用多个数据库：

1. **chatsql_system** (系统数据库)
   - `submissions` - 用户提交记录
   - `problems` - 题目元数据
   - `problem_tables` - 题目表定义

2. **chatsql_problem_N** (题目数据库)
   - 每个题目有独立的数据库（如 `chatsql_problem_1`, `chatsql_problem_2`）
   - 包含题目相关的实际表（如 `Products`, `Customers` 等）

## 修复内容

### 1. 更新 `ai_tutor/views.py`

#### 修改 `post` 方法：
- 从 `get_problem_from_gcp` 获取 `database_name`
- 将 `database_name` 传递给 `get_ai_response` 和 `_execute_sql`

#### 修改 `_execute_sql` 方法：
- 添加 `problem_database_name` 和 `exercise_id` 参数
- 智能路由SQL查询：
  - 如果查询 `submissions`, `problems`, `problem_tables` → 使用 `chatsql_system` 数据库
  - 如果查询其他表（如 `Products`, `Customers`）→ 使用对应的 `chatsql_problem_N` 数据库
- 使用 `SQLExecutor` 来执行problem数据库的查询

### 2. 更新 `ai_tutor/services/openai_service.py`

#### 修改 `_build_student_prompt` 函数：
- 添加 `problem_database_name` 参数
- 在prompt中说明数据库结构：
  - 系统表在 `chatsql_system` 数据库
  - 题目表在对应的 `chatsql_problem_N` 数据库
  - 系统会自动路由查询到正确的数据库

#### 修改 `get_ai_response` 函数：
- 添加 `problem_database_name` 参数
- 将 `problem_database_name` 传递给 `_build_student_prompt`

## 工作流程

1. **接收请求** → `ExerciseAIView.post()`
2. **获取problem信息** → `get_problem_from_gcp(exercise_id)`
3. **提取database_name** → `problem['database_name']` (如 `chatsql_problem_1`)
4. **调用AI** → `get_ai_response(..., problem_database_name=...)`
5. **AI生成SQL** → 基于数据库结构信息生成正确的SQL
6. **执行SQL** → `_execute_sql(sql_query, problem_database_name, exercise_id)`
7. **智能路由**：
   - 检测SQL中的表名
   - 如果是系统表 → 使用 `chatsql_system`
   - 如果是题目表 → 使用对应的 `chatsql_problem_N`

## 示例

### 查询submissions（系统表）
```sql
SELECT COUNT(*) FROM submissions 
WHERE user_id=1 AND status='correct'
```
→ 自动路由到 `chatsql_system` 数据库

### 查询Products（题目表）
```sql
SELECT * FROM Products WHERE price > 100
```
→ 自动路由到对应的 `chatsql_problem_N` 数据库（如 `chatsql_problem_1`）

## 测试

修复后，AI助手应该能够：
1. ✅ 正确查询 `submissions` 表（在 `chatsql_system` 中）
2. ✅ 正确查询题目相关的表（在对应的 `chatsql_problem_N` 中）
3. ✅ 根据表名自动选择正确的数据库
4. ✅ 在prompt中说明数据库结构，帮助AI生成正确的SQL

## 注意事项

- AI生成的SQL不需要包含数据库名（如 `chatsql_system.submissions`），系统会自动路由
- 如果无法确定problem的数据库，会返回友好的错误信息
- 使用 `SQLExecutor` 确保查询安全（只允许SELECT，防止危险操作）

