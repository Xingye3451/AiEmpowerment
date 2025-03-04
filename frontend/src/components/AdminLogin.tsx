import React, { useState } from 'react';
import { 
  Box, 
  Button, 
  TextField, 
  Typography, 
  Container,
  Paper,
  Alert,
  Zoom,
} from '@mui/material';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { AUTH_API } from '../config/api';

const AdminLogin = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);
      
      const response = await axios.post(
        AUTH_API.ADMIN_LOGIN,
        formData,
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        }
      );
      
      const token = response.data.access_token;
      localStorage.setItem('adminToken', token);
      
      // 为后续请求配置全局默认headers
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      
      navigate('/admin/dashboard');
    } catch (error: any) {
      setError(error.response?.data?.detail || '管理员登录失败');
      console.error('Login failed:', error);
    }
  };

  return (
    <Container component="main" maxWidth="xs">
      <Box
        sx={{
          mt: 8,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <Paper
          elevation={3}
          sx={{
            p: 4,
            width: '100%',
            background: 'linear-gradient(45deg, #f5f5f5 30%, #ffffff 90%)',
            borderRadius: 3,
            boxShadow: '0 3px 5px 2px rgba(63, 81, 181, .3)',
            transition: 'transform 0.3s ease-in-out',
            '&:hover': {
              transform: 'translateY(-4px)',
            },
          }}
        >
          <Typography
            component="h1"
            variant="h5"
            align="center"
            sx={{
              mb: 3,
              fontWeight: 'bold',
              color: theme => theme.palette.primary.main,
            }}
          >
            管理员登录
          </Typography>

          {error && (
            <Zoom in={!!error}>
              <Alert 
                severity="error" 
                sx={{ 
                  mb: 2,
                  borderRadius: 2,
                  boxShadow: '0 2px 8px rgba(244, 67, 54, 0.2)',
                }}
              >
                {error}
              </Alert>
            </Zoom>
          )}

          <Box 
            component="form" 
            onSubmit={handleSubmit} 
            sx={{ mt: 1 }}
          >
            <TextField
              margin="normal"
              required
              fullWidth
              label="管理员用户名"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              sx={{
                '& .MuiOutlinedInput-root': {
                  backgroundColor: '#ffffff',
                  borderRadius: 2,
                  boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
                },
              }}
            />
            <TextField
              margin="normal"
              required
              fullWidth
              label="密码"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              sx={{
                '& .MuiOutlinedInput-root': {
                  backgroundColor: '#ffffff',
                  borderRadius: 2,
                  boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
                },
              }}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{
                mt: 3,
                mb: 2,
                height: 48,
                background: 'linear-gradient(45deg, #3f51b5 30%, #757de8 90%)',
                borderRadius: 2,
                boxShadow: '0 3px 5px 2px rgba(63, 81, 181, .3)',
                transition: 'transform 0.3s',
                '&:hover': {
                  transform: 'translateY(-2px)',
                },
              }}
            >
              登录
            </Button>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
};

export default AdminLogin;