// API基础URL
export const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

// 其他配置
export const APP_NAME = '智能视频处理平台';
export const APP_VERSION = '1.0.0';

// 上传配置
export const MAX_UPLOAD_SIZE = 500 * 1024 * 1024; // 500MB
export const ALLOWED_VIDEO_FORMATS = ['.mp4', '.avi', '.mov', '.mkv', '.wmv'];

// 通知配置
export const NOTIFICATION_DURATION = 5000; // 5秒 