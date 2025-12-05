# 诊断Submissions不保存的问题

## 快速检查清单

### 1. 检查用户是否已登录

**方法1: 检查浏览器**
- 打开浏览器开发者工具 (F12)
- 查看 Application/Storage → Cookies
- 查找 `sessionid` cookie
- 如果不存在，说明用户未登录

**方法2: 检查API响应**
- 打开浏览器开发者工具 → Network标签
- 提交一个查询
- 查看 `/api/exercises/{id}/submit/` 请求
- 检查请求头中是否有 `Cookie: sessionid=...`
- 检查响应状态码和内容

### 2. 检查Django日志

启动Django服务器时，查看控制台输出，寻找：
- `=== Submission Save Debug ===`
- `Session user_id: ...`
- `user_id is None` (如果看到这个，说明用户未登录)
- `Successfully saved submission` (如果看到这个，说明保存成功)

### 3. 实时监控数据库

在一个终端运行：
```bash
source venv/bin/activate
python check_live_submissions.py
```

然后在浏览器中提交查询，观察是否有新记录出现。

### 4. 手动测试

运行测试脚本：
```bash
source venv/bin/activate
python test_submit_debug.py
```

这会直接测试保存函数，如果这个成功但浏览器提交不成功，说明是session问题。

## 常见问题及解决方案

### 问题1: user_id is None

**症状**: 日志显示 `user_id is None`

**原因**: 用户未登录或session未正确传递

**解决方案**:
1. 确保用户已登录（前端显示已登录状态）
2. 检查前端请求是否包含 `credentials: 'include'`
3. 检查CORS配置是否正确

### 问题2: 函数调用成功但数据库没有变化

**症状**: 日志显示 `Successfully saved submission` 但数据库没有新记录

**原因**: 可能是事务问题或数据库连接问题

**解决方案**:
1. 检查数据库连接是否正常
2. 检查是否有其他进程在回滚事务
3. 运行 `check_live_submissions.py` 实时监控

### 问题3: 前端请求失败

**症状**: 浏览器控制台显示错误

**解决方案**:
1. 检查网络请求是否成功（状态码200）
2. 检查响应内容
3. 查看浏览器控制台的错误信息

## 调试步骤

1. **启动Django服务器并查看日志**:
   ```bash
   python manage.py runserver
   ```
   观察控制台输出

2. **在另一个终端运行监控脚本**:
   ```bash
   python check_live_submissions.py
   ```

3. **在浏览器中提交查询**:
   - 确保已登录
   - 点击Submit按钮
   - 观察两个终端的输出

4. **检查结果**:
   - 如果监控脚本显示新记录 → 保存成功
   - 如果Django日志显示 `user_id is None` → 登录问题
   - 如果Django日志显示错误 → 查看具体错误信息

## 验证保存是否成功

运行检查脚本：
```bash
python check_submissions.py
```

这会显示submissions表中的所有记录。

