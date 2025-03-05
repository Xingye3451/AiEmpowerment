// API 基础配置
const isDevelopment = process.env.NODE_ENV === 'development';

// 从环境变量获取API基础URL，如果不存在则使用相对路径或本地开发地址
const API_BASE = process.env.REACT_APP_API_BASE_URL || 
                (isDevelopment ? 'http://localhost:8000' : '');

// 构建最终的API基础URL
// 如果API_BASE为空，则使用相对路径，这样可以适应任何部署环境
export const BASE_URL = API_BASE ? 
                        `${API_BASE}/api/v1` : 
                        '/api/v1';

// Auth API 路径配置
export const AUTH_API = {
    LOGIN: `${BASE_URL}/login`,
    ADMIN_LOGIN: `${BASE_URL}/login/admin`,
};

// User API 路径配置
export const USER_API = {
    REGISTER: `${BASE_URL}/users`,
    PROFILE: `${BASE_URL}/users/me`,
    RESET_PASSWORD_REQUEST: `${BASE_URL}/users/reset-password-request`,
    RESET_PASSWORD_VERIFY: `${BASE_URL}/users/reset-password-verify`,
};

// Admin API 路径配置
export const ADMIN_API = {
    USERS: `${BASE_URL}/admin/users`,
    CHANGE_PASSWORD: `${BASE_URL}/admin/change-password`,
    USER_STATUS: (userId: number) => `${BASE_URL}/admin/users/${userId}/toggle-status`,
    USER_PASSWORD_RESET: (userId: number) => `${BASE_URL}/admin/users/${userId}/reset-password`,
    DELETE_USER: (userId: number) => `${BASE_URL}/admin/users/${userId}`,
    UPDATE_USER: (userId: number) => `${BASE_URL}/admin/users/${userId}`,
};

// Douyin API 路径配置
export const DOUYIN_API = {
    UPLOAD_VIDEO: `${BASE_URL}/douyin/upload-video`,
    PREVIEW: (filename: string) => `${BASE_URL}/douyin/preview/${filename}`,
    VIDEO: (filename: string) => `${BASE_URL}/douyin/video/${filename}`,
    BATCH_LOGIN: `${BASE_URL}/douyin/batch-login`,
    BATCH_POST: `${BASE_URL}/douyin/batch-post`,
    SCHEDULE: `${BASE_URL}/douyin/schedule`,
    TASKS: `${BASE_URL}/douyin/tasks`,
    TASK: (taskId: string) => `${BASE_URL}/douyin/task/${taskId}`,
    GROUPS: `${BASE_URL}/douyin/groups`,
    GROUP: (groupId: string) => `${BASE_URL}/douyin/groups/${groupId}`,
    ACCOUNTS: `${BASE_URL}/douyin/accounts`,
    HISTORY: `${BASE_URL}/douyin/history`,
    STATS: `${BASE_URL}/douyin/stats`,
    // 新增的视频处理相关API
    BATCH_PROCESS_VIDEOS: `${BASE_URL}/douyin/batch-process-videos`,
    PROCESS_STATUS: (taskId: string) => `${BASE_URL}/douyin/process-status/${taskId}`,
};