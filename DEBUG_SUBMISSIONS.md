# 排查Submissions表没有数据的步骤

## 快速诊断

运行调试脚本：
```bash
source venv/bin/activate
python debug_submissions.py
```

## 常见问题及解决方案

### 问题1: 用户未认证 (最常见)

**症状**: `user_id` 为 `None`，函数直接返回

**原因**: `SubmitQueryView` 没有认证要求，如果用户未登录，`request.user.is_authenticated` 为 `False`

**检查方法**:
1. 查看Django日志，寻找 "user_id is None" 的警告
2. 检查前端是否发送了认证信息（cookies/session）

**解决方案**:
- 确保用户已登录
- 或者修改代码允许匿名用户（不推荐）

### 问题2: exercise_id不存在

**症状**: 日志显示 "exercise_id does not exist in problems table"

**原因**: 提交的 `exercise_id` 在 `problems` 表中不存在

**检查方法**:
```sql
SELECT id FROM problems WHERE id = <exercise_id>;
```

**解决方案**: 确保 `exercise_id` 对应 `problems` 表中的有效ID

### 问题3: 数据库连接问题

**症状**: 连接错误或事务失败

**检查方法**:
- 运行 `debug_submissions.py` 的步骤1
- 检查 `.env` 文件中的GCP数据库配置

### 问题4: 外键约束失败

**症状**: 插入时外键约束错误

**检查方法**:
- 运行 `debug_submissions.py` 的步骤3和4
- 确保 `exercise_id` 和 `user_id` 都存在

### 问题5: 错误被静默捕获

**症状**: 有错误但被try-except捕获，没有显示

**检查方法**:
- 查看Django日志文件
- 检查控制台输出

## 调试步骤

### 步骤1: 运行调试脚本
```bash
python debug_submissions.py
```

### 步骤2: 检查Django日志
查看Django运行时的日志输出，寻找：
- "Attempting to save submission"
- "user_id is None"
- "Failed to save submission"
- "Successfully saved submission"

### 步骤3: 手动测试插入
```bash
python check_submissions.py
```

### 步骤4: 检查前端请求
在浏览器开发者工具中：
1. 打开Network标签
2. 提交一个查询
3. 检查请求是否包含认证信息（cookies）
4. 检查响应状态码

### 步骤5: 验证用户认证
```python
# 在Django shell中
python manage.py shell

from django.contrib.auth.models import User
from django.db import connection

# 检查用户
users = User.objects.all()
print(f"Users: {list(users.values('id', 'username'))}")

# 检查problems
with connection.cursor() as cursor:
    cursor.execute('USE chatsql_system')
    cursor.execute('SELECT id, title FROM problems LIMIT 5')
    print(f"Problems: {cursor.fetchall()}")
```

## 代码检查清单

- [ ] `SubmitQueryView` 是否正确调用 `save_submission_to_gcp`
- [ ] `user_id` 是否为 `None`（检查认证）
- [ ] `exercise_id` 是否存在于 `problems` 表
- [ ] `user_id` 是否存在于 `users` 表
- [ ] 数据库连接是否正常
- [ ] 事务是否提交（`connection.commit()`）
- [ ] 是否有异常被捕获但没有记录

## 临时解决方案

如果需要允许匿名用户提交（不推荐用于生产环境），可以修改 `save_submission_to_gcp` 函数：

```python
# 在 save_submission_to_gcp 函数中
if user_id is None:
    # 使用一个默认用户ID（需要确保该用户存在）
    user_id = 1  # 或者从配置中获取
    logger.warning("Using default user_id for anonymous submission")
```

## 查看实时日志

在Django开发服务器运行时，日志会输出到控制台。查找包含以下关键词的日志：
- `=== Submission Save Debug ===`
- `user_id=`
- `exercise_id=`
- `Successfully saved submission`
- `Cannot save submission`

