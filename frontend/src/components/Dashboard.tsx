import React, { useEffect, useState } from 'react';
import { Container, Typography, Paper, Box, Alert, Button, Grid } from '@mui/material';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import DouyinManager from './DouyinManager';
import AIVideoProcessor from './AIVideoProcessor';
import { USER_API } from '../config/api';

const Dashboard: React.FC = () => {
  const [userData, setUserData] = useState<any>(null);
  const [error, setError] = useState('');
  const [activeComponent, setActiveComponent] = useState<'douyin' | 'ai'>('douyin');
  const navigate = useNavigate();

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await axios.get(USER_API.PROFILE, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
          withCredentials: true,
        });
        setUserData(response.data);
      } catch (error: any) {
        setError(error.response?.data?.detail || '获取用户信息失败');
        console.error('Error fetching user data:', error);
        if (error.response?.status === 401) {
          localStorage.removeItem('token');
          navigate('/login');
        }
      }
    };

    fetchUserData();
  }, [navigate]);

  return (
    <Container component="main" maxWidth="lg">
      <Paper elevation={3} sx={{ p: 4, mt: 8 }}>
        <Typography component="h1" variant="h4" align="center" gutterBottom>
          仪表板
        </Typography>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {userData && (
          <Box sx={{ mt: 4 }}>
            <Typography variant="h6">欢迎回来, {userData.username}!</Typography>
            <Typography variant="body1" sx={{ mt: 2 }}>
              邮箱: {userData.email}
            </Typography>
          </Box>
        )}
        
        <Box sx={{ mt: 4 }}>
          <Grid container spacing={2} sx={{ mb: 4 }}>
            <Grid item>
              <Button
                variant={activeComponent === 'douyin' ? 'contained' : 'outlined'}
                onClick={() => setActiveComponent('douyin')}
              >
                抖音管理
              </Button>
            </Grid>
            <Grid item>
              <Button
                variant={activeComponent === 'ai' ? 'contained' : 'outlined'}
                onClick={() => setActiveComponent('ai')}
              >
                AI视频处理
              </Button>
            </Grid>
          </Grid>

          {activeComponent === 'douyin' ? (
            <DouyinManager />
          ) : (
            <AIVideoProcessor />
          )}
        </Box>
      </Paper>
    </Container>
  );
};

export default Dashboard;