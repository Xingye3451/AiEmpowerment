import axios from 'axios';

export interface User {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  role: string;
  last_login: string | null;
}

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

export const userService = {
  getCurrentUser: async (): Promise<User> => {
    const response = await axios.get(`${API_URL}/users/me`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });
    return response.data;
  },

  createUser: async (userData: { username: string; email: string; password: string }): Promise<User> => {
    const response = await axios.post(`${API_URL}/users/`, userData);
    return response.data;
  },

  resetPasswordRequest: async (email: string) => {
    const response = await axios.post(`${API_URL}/users/reset-password-request`, { email });
    return response.data;
  },

  resetPasswordVerify: async (token: string, new_password: string) => {
    const response = await axios.post(`${API_URL}/users/reset-password-verify`, {
      token,
      new_password
    });
    return response.data;
  }
}; 