import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, CircularProgress, Alert } from '@mui/material';
import ServiceConfigPanel from './ServiceConfigPanel';
import { fetchAIServices } from '../services/ai_config';

const AIConfigTab: React.FC = () => {
  const [services, setServices] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setError(null);
      try {
        // 加载服务配置
        const servicesData = await fetchAIServices();
        setServices(servicesData);
      } catch (err) {
        console.error('加载配置失败:', err);
        setError('加载配置失败，请检查网络连接或权限设置');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  const handleServicesUpdate = (updatedServices: any[]) => {
    setServices(updatedServices);
  };

  return (
    <Paper elevation={3} sx={{ p: 2, height: '100%' }}>
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      ) : error ? (
        <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>
      ) : (
        <Box sx={{ width: '100%' }}>
          <ServiceConfigPanel 
            services={services} 
            onServicesUpdate={handleServicesUpdate} 
          />
        </Box>
      )}
    </Paper>
  );
};

export default AIConfigTab; 