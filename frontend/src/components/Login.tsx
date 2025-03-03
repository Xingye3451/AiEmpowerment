import React, { useState } from 'react';
import { 
  Box, 
  Button, 
  TextField, 
  Typography, 
  Container,
  Paper,
  Alert,
  Link
} from '@mui/material';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { AUTH_API } from '../config/api';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await axios.post(AUTH_API.LOGIN, 
        new URLSearchParams({
          username,
          password,
        }),
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        }
      );
      localStorage.setItem('token', response.data.access_token);
      navigate('/dashboard');
    } catch (error: any) {
      setError(error.response?.data?.detail || '登录失败');
      console.error('Login failed:', error);
    }
  };

  return (
    <Container component="main" maxWidth="xs">
      <Paper elevation={3} sx={{ p: 4, mt: 8 }}>
        <Typography component="h1" variant="h5" align="center">
          登录
        </Typography>
        <Box component="form" onSubmit={handleSubmit} sx={{ mt: 1 }}>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          <TextField
            margin="normal"
            required
            fullWidth
            label="用户名"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          <TextField
            margin="normal"
            required
            fullWidth
            label="密码"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <Button
            type="submit"
            fullWidth
            variant="contained"
            sx={{ mt: 3, mb: 2 }}
          >
            登录
          </Button>
          <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between' }}>
            <Link
              component="button"
              variant="body2"
              onClick={() => navigate('/register')}
            >
              没有账号？立即注册
            </Link>
            <Link
              component="button"
              variant="body2"
              onClick={() => navigate('/forgot-password')}
            >
              忘记密码？
            </Link>
          </Box>
        </Box>
      </Paper>
    </Container>
  );
};

export default Login;