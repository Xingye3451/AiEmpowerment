from sqlalchemy import Column, Integer, String, Boolean, JSON, DateTime
from app.db.database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    role = Column(String, default="user")  # 新增角色字段：admin 或 user
    douyin_accounts = Column(JSON, nullable=True)  # 存储多个抖音账号信息
    douyin_cookies = Column(JSON, nullable=True)   # 存储抖音账号登录后的cookies
    douyin_groups = Column(JSON, nullable=True)    # 存储抖音账号分组
    douyin_history = Column(JSON, nullable=True)   # 存储发布历史记录
    last_login = Column(DateTime, nullable=True)   # 最后登录时间
    last_active = Column(DateTime, default=datetime.utcnow)  # 最后活跃时间
    reset_token = Column(String, nullable=True)    # 密码重置令牌
    reset_token_expires = Column(DateTime, nullable=True)  # 密码重置令牌过期时间