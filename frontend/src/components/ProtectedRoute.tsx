import { Navigate, useLocation } from 'react-router-dom';
import { useEffect, useState } from 'react';
import axios from 'axios';
import { ADMIN_API } from '../config/api';

interface ProtectedRouteProps {
  children: JSX.Element;
  requiredRole?: string;
}

const ProtectedRoute = ({ children, requiredRole }: ProtectedRouteProps) => {
  const location = useLocation();
  const isAdminRoute = location.pathname.startsWith('/admin');
  const token = isAdminRoute ? localStorage.getItem('adminToken') : localStorage.getItem('token');
  const [isAuthorized, setIsAuthorized] = useState<boolean | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  
  useEffect(() => {
    const checkUserRole = async () => {
      if (!token) {
        setIsAuthorized(false);
        setIsLoading(false);
        return;
      }
      
      try {
        // 如果是管理员路由或需要管理员角色，验证用户是否为管理员
        if (isAdminRoute || requiredRole === 'admin') {
          const response = await axios.get(ADMIN_API.CHECK_ROLE, {
            headers: {
              Authorization: `Bearer ${token}`
            }
          });
          
          // 检查用户角色是否符合要求
          if (requiredRole) {
            setIsAuthorized(response.data.role === requiredRole);
          } else {
            setIsAuthorized(true);
          }
        } else {
          // 普通路由，只需要验证token有效性
          setIsAuthorized(true);
        }
      } catch (error) {
        console.error('权限验证失败:', error);
        setIsAuthorized(false);
        // 如果是401错误，清除token
        if (axios.isAxiosError(error) && error.response?.status === 401) {
          if (isAdminRoute) {
            localStorage.removeItem('adminToken');
          } else {
            localStorage.removeItem('token');
          }
        }
      } finally {
        setIsLoading(false);
      }
    };
    
    checkUserRole();
  }, [token, isAdminRoute, requiredRole]);
  
  if (isLoading) {
    // 可以在这里添加加载指示器
    return <div>加载中...</div>;
  }
  
  if (!isAuthorized) {
    return <Navigate to={isAdminRoute ? '/admin/login' : '/login'} />;
  }

  return children;
};

export default ProtectedRoute;