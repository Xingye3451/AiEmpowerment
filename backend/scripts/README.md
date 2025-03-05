# 数据库迁移工具

本目录包含用于数据库迁移的工具脚本，特别是从 SQLite 迁移到 MySQL 的工具。

## 从 SQLite 迁移到 MySQL

### 准备工作

1. 确保已安装 Python 3.7+
2. 确保已安装 MySQL 服务器，并创建了相应的用户
3. 更新配置文件中的 MySQL 连接信息

### 配置文件

在执行迁移前，请先编辑`../config/default.yaml`文件，确保 MySQL 配置正确：

```yaml
database:
  type: "sqlite" # 迁移后会自动更新为"mysql"

  # SQLite配置
  sqlite:
    file: "app.db"

  # MySQL配置
  mysql:
    host: "localhost" # MySQL服务器地址
    port: 3306 # MySQL端口
    user: "root" # MySQL用户名
    password: "password" # MySQL密码
    db: "aiempowerment" # 数据库名称
    charset: "utf8mb4" # 字符集
```

### 执行迁移

#### Windows 系统

双击运行`migrate_to_mysql.bat`文件，或在命令行中执行：

```
cd backend/scripts
migrate_to_mysql.bat
```

#### Linux/Mac 系统

在终端中执行：

```bash
cd backend/scripts
chmod +x migrate_to_mysql.sh
./migrate_to_mysql.sh
```

### 手动执行

如果需要更多控制，可以直接运行 Python 脚本：

```bash
cd backend/scripts
python migrate_sqlite_to_mysql.py --config ../config/default.yaml
```

### 迁移过程

1. 脚本会读取配置文件中的数据库信息
2. 连接 SQLite 数据库，读取表结构和数据
3. 连接 MySQL 数据库，创建相应的表结构
4. 将数据从 SQLite 导入到 MySQL
5. 更新配置文件，将数据库类型改为"mysql"

### 注意事项

1. 迁移前请备份您的 SQLite 数据库文件
2. 确保 MySQL 服务器有足够的空间和权限
3. 迁移过程中请勿中断操作，以免数据不完整
4. 迁移完成后，请测试应用程序是否正常工作
5. 如果迁移失败，请查看`migration.log`日志文件了解详情

## 其他脚本

本目录下可能还包含其他实用脚本，请查看各脚本的注释了解其用途。
