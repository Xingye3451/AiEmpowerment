import axios from 'axios';
import { API_BASE_URL } from '../config';

// 创建axios实例
const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
});

// 请求拦截器
(api as any).interceptors.request.use(
  config => {
    // 从localStorage获取token
    const token = localStorage.getItem('token');
    
    // 如果token存在，则添加到请求头中
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// 响应拦截器
(api as any).interceptors.response.use(
  response => {
    return response;
  },
  error => {
    // 如果响应状态码是401，可能是token过期或无效
    if (error.response && error.response.status === 401) {
      console.log('认证失败，请重新登录');
      // 可以在这里添加重定向到登录页面的逻辑
      // window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api; 