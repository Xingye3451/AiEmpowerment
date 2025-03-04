import { Navigate, useLocation } from 'react-router-dom';

interface ProtectedRouteProps {
  children: JSX.Element;
}

const ProtectedRoute = ({ children }: ProtectedRouteProps) => {
  const location = useLocation();
  const isAdminRoute = location.pathname.startsWith('/admin');
  const token = isAdminRoute ? localStorage.getItem('adminToken') : localStorage.getItem('token');
  
  if (!token) {
    return <Navigate to={isAdminRoute ? '/admin/login' : '/login'} />;
  }

  return children;
};

export default ProtectedRoute;