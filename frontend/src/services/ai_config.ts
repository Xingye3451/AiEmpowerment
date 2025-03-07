import axios from 'axios';
import { AI_CONFIG_API } from '../config/api';

// 获取所有AI服务配置
export const fetchAIServices = async (serviceType?: string) => {
  try {
    const token = localStorage.getItem('adminToken');
    const params = serviceType ? { service_type: serviceType } : {};
    
    const response = await axios.get(AI_CONFIG_API.SERVICES, {
      headers: {
        Authorization: `Bearer ${token}`
      },
      params
    });
    
    return response.data;
  } catch (error) {
    console.error('获取AI服务配置失败:', error);
    throw error;
  }
};

// 获取单个AI服务配置
export const fetchAIService = async (serviceId: number) => {
  try {
    const token = localStorage.getItem('adminToken');
    
    const response = await axios.get(AI_CONFIG_API.SERVICE_DETAIL(serviceId.toString()), {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error(`获取AI服务配置(ID: ${serviceId})失败:`, error);
    throw error;
  }
};

// 创建AI服务配置
export const createAIService = async (serviceData: any) => {
  try {
    const token = localStorage.getItem('adminToken');
    
    const response = await axios.post(AI_CONFIG_API.SERVICES, serviceData, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('创建AI服务配置失败:', error);
    throw error;
  }
};

// 更新AI服务配置
export const updateAIService = async (serviceId: number, serviceData: any) => {
  try {
    const token = localStorage.getItem('adminToken');
    
    const response = await axios.put(AI_CONFIG_API.SERVICE_DETAIL(serviceId.toString()), serviceData, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    return response.data;
  } catch (error) {
    console.error(`更新AI服务配置(ID: ${serviceId})失败:`, error);
    throw error;
  }
};

// 删除AI服务配置
export const deleteAIService = async (serviceId: number) => {
  try {
    const token = localStorage.getItem('adminToken');
    
    const response = await axios.delete(AI_CONFIG_API.SERVICE_DETAIL(serviceId.toString()), {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error(`删除AI服务配置(ID: ${serviceId})失败:`, error);
    throw error;
  }
};

// 获取系统配置
export const fetchSystemConfig = async () => {
  try {
    const token = localStorage.getItem('adminToken');
    
    const response = await axios.get(AI_CONFIG_API.SYSTEM, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('获取系统配置失败:', error);
    throw error;
  }
};

// 更新系统配置
export const updateSystemConfig = async (configData: any) => {
  try {
    const token = localStorage.getItem('adminToken');
    
    const response = await axios.put(AI_CONFIG_API.SYSTEM, configData, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('更新系统配置失败:', error);
    throw error;
  }
};

// 测试服务连接
export const testServiceConnection = async (testData: { service_type: string; service_url: string }) => {
  try {
    const token = localStorage.getItem('adminToken');
    
    const response = await axios.post(AI_CONFIG_API.TEST_CONNECTION, testData, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('测试服务连接失败:', error);
    throw error;
  }
}; 