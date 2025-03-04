import axios from 'axios';
import { DOUYIN_API } from '../config/api';

export const douyinService = {
  getTasks: async () => {
    const token = localStorage.getItem('token');
    const response = await axios.get(DOUYIN_API.TASKS, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    return response.data;
  },

  // 其他抖音相关的 API 方法可以在这里添加
}; 