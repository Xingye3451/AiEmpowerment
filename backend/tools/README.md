# 后台管理工具

本目录包含一系列用于后台管理和维护的工具脚本。

## 数据库工具

### 检查数据库 (check_db.py)

用于检查数据库结构和内容，特别是用户表。

```bash
python tools/check_db.py
```

输出包括：

- 数据库路径和是否存在
- 用户表结构
- 用户数据详情

### 重置管理员密码 (reset_admin_password.py)

用于重置管理员账号的密码。默认将密码重置为"admin123456"。

```bash
# 使用默认密码
python tools/reset_admin_password.py

# 指定新密码
python tools/reset_admin_password.py 新密码
```

输出包括：

- 数据库路径
- 新密码
- 新密码的哈希值

## 测试工具

### 密码验证测试 (test_password.py)

用于测试密码哈希和验证功能是否正常工作。

```bash
python tools/test_password.py
```

输出包括：

- 存储的密码哈希值
- 测试密码
- 密码验证结果
- 新生成的哈希值
- 新哈希值验证结果

### 管理员密码修改测试 (test_admin_password_change.py)

用于测试管理员密码修改功能是否正常工作。当管理员成功修改密码后，前端应用会自动退出登录并重定向到登录页面，这是一种安全实践。

```bash
# 使用默认参数（用户名：admin，当前密码：admin123456，新密码：admin123456）
python tools/test_admin_password_change.py

# 指定当前密码
python tools/test_admin_password_change.py 当前密码

# 指定用户名、当前密码和新密码
python tools/test_admin_password_change.py 用户名 当前密码 新密码
```

输出包括：

- 登录请求和响应信息
- 密码修改请求和响应信息
- 操作结果
- 使用新密码登录的测试结果（如果新密码与旧密码不同）

### 通知计数测试 (test_notification_count.py)

用于测试通知计数 API 是否正常工作。

```bash
# 使用默认参数（用户名：admin，密码：admin123456）
python tools/test_notification_count.py

# 指定密码
python tools/test_notification_count.py 密码

# 指定用户名和密码
python tools/test_notification_count.py 用户名 密码
```

输出包括：

- 登录请求和响应信息
- 通知计数请求和响应信息
- 操作结果

### 通知 API 完整测试 (test_notifications_api.py)

用于测试所有通知相关的 API 是否正常工作，包括获取通知列表、获取通知详情、标记为已读、标记所有为已读和删除通知等功能。

```bash
# 使用默认参数（用户名：admin，密码：admin123456）
python tools/test_notifications_api.py

# 指定密码
python tools/test_notifications_api.py 密码

# 指定用户名和密码
python tools/test_notifications_api.py 用户名 密码
```

输出包括：

- 登录请求和响应信息
- 各个通知 API 的请求和响应信息
- 操作结果

## 系统维护工具

### 检查 SQLAlchemy (check_sqlalchemy.py)

用于检查 SQLAlchemy 版本和可用的类，帮助诊断 SQLAlchemy 相关的问题。

```bash
python tools/check_sqlalchemy.py
```

输出包括：

- SQLAlchemy 版本
- AsyncSession 类的可用性
- sqlalchemy.ext.asyncio 模块中的类
- 异步数据库驱动的安装状态
- requirements.txt 中的 SQLAlchemy 相关依赖

### 修复 SQLAlchemy (fix_sqlalchemy.py)

用于安装正确版本的 SQLAlchemy，解决 AsyncSession 导入错误的问题。

```bash
python tools/fix_sqlalchemy.py
```

输出包括：

- 安装过程信息
- 安装后的 SQLAlchemy 版本
- AsyncSession 类的可用性

## 使用注意事项

1. 这些工具应该只在开发和维护环境中使用，不应该在生产环境中使用。
2. 重置密码工具会直接修改数据库，请谨慎使用。
3. 在使用这些工具之前，请确保已经备份了数据库。
4. 管理员修改密码后，需要重新登录系统。
5. 修复 SQLAlchemy 后，需要重新启动应用程序。
