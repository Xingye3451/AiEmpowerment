/**
 * 认证工具函数
 */

/**
 * 获取认证头
 * @returns 包含Authorization头的对象，如果没有token则返回空对象
 */
export const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

/**
 * 检查用户是否已认证
 * @returns 布尔值，表示用户是否已认证
 */
export const isAuthenticated = () => {
  return !!localStorage.getItem('token');
};

/**
 * 保存认证令牌
 * @param token JWT令牌
 */
export const saveToken = (token: string) => {
  localStorage.setItem('token', token);
};

/**
 * 清除认证令牌
 */
export const clearToken = () => {
  localStorage.removeItem('token');
}; 