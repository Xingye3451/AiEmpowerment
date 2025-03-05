# 从core/deps.py导入所有依赖函数
from app.core.deps import (
    get_current_user,
    get_current_admin,
    get_current_active_superuser,
    get_db,
    oauth2_scheme,
    admin_oauth2_scheme,
)

# 重新导出这些函数，使其可以从app.api.deps导入
__all__ = [
    "get_current_user",
    "get_current_admin",
    "get_current_active_superuser",
    "get_db",
    "oauth2_scheme",
    "admin_oauth2_scheme",
]
