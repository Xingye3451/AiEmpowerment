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
    LOGIN: `${BASE_URL}/auth/login`,
    ADMIN_LOGIN: `${BASE_URL}/auth/login/admin`,
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
    CHECK_ROLE: `${BASE_URL}/admin/check-role`,
    USER_STATUS: (userId: string) => `${BASE_URL}/admin/users/${userId}/toggle-status`,
    USER_PASSWORD_RESET: (userId: string) => `${BASE_URL}/admin/users/${userId}/reset-password`,
    DELETE_USER: (userId: string) => `${BASE_URL}/admin/users/${userId}`,
    UPDATE_USER: (userId: string) => `${BASE_URL}/admin/users/${userId}`,
};

// 内容分发API路径配置
export const DISTRIBUTE_API = {
    LIST: `${BASE_URL}/social/distribute`,
    CREATE: `${BASE_URL}/social/distribute`,
    DETAIL: (taskId: string) => `${BASE_URL}/social/distribute/${taskId}`,
    STATUS: (taskId: string) => `${BASE_URL}/social/distribute/${taskId}/status`,
    CANCEL: (taskId: string) => `${BASE_URL}/social/distribute/${taskId}/cancel`,
};

// 社交平台账号API路径配置
export const SOCIAL_ACCOUNT_API = {
    LIST: `${BASE_URL}/social/accounts`,
    CREATE: `${BASE_URL}/social/accounts`,
    UPDATE: (accountId: string) => `${BASE_URL}/social/accounts/${accountId}`,
    DELETE: (accountId: string) => `${BASE_URL}/social/accounts/${accountId}`,
    STATUS: (accountId: string) => `${BASE_URL}/social/accounts/${accountId}/status`,
    GROUPS: `${BASE_URL}/social/account-groups`,
    GROUP_DETAIL: (groupId: string) => `${BASE_URL}/social/account-groups/${groupId}`,
};

// 任务管理API路径配置
export const TASK_API = {
    LIST: `${BASE_URL}/tasks`,
    CREATE: `${BASE_URL}/tasks`,
    DETAIL: (taskId: string) => `${BASE_URL}/tasks/${taskId}`,
    UPDATE: (taskId: string) => `${BASE_URL}/tasks/${taskId}`,
    DELETE: (taskId: string) => `${BASE_URL}/tasks/${taskId}`,
    STATUS: (taskId: string) => `${BASE_URL}/tasks/${taskId}/status`,
    CANCEL: (taskId: string) => `${BASE_URL}/tasks/${taskId}/cancel`,
    RETRY: (taskId: string) => `${BASE_URL}/tasks/${taskId}/retry`,
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
    BATCH_PROCESS_VIDEOS: `${BASE_URL}/douyin/batch-process-videos`,
    PROCESS_STATUS: (taskId: string) => `${BASE_URL}/douyin/process-status/${taskId}`,
    CHECK_LOCAL_PROCESSING: `${BASE_URL}/douyin/check-local-processing`,
    PROCESSED_VIDEO: (taskId: string) => `${BASE_URL}/douyin/processed-video/${taskId}`,
    PROCESSED_VIDEO_THUMBNAIL: (taskId: string) => `${BASE_URL}/douyin/processed-video-thumbnail/${taskId}`,
};

// 通知API路径配置
export const NOTIFICATION_API = {
    LIST: `${BASE_URL}/notifications`,
    COUNT: `${BASE_URL}/notifications/count`,
    READ: (notificationId: string) => `${BASE_URL}/notifications/${notificationId}/read`,
    READ_ALL: `${BASE_URL}/notifications/read-all`,
    DELETE: (notificationId: string) => `${BASE_URL}/notifications/${notificationId}`,
    DELETE_ALL: `${BASE_URL}/notifications`,
};