import React, { useState } from 'react';
import {
  Box,
  Button,
  TextField,
  Typography,
  Container,
  Paper,
  Alert,
} from '@mui/material';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { USER_API } from '../config/api';

const ForgotPassword = () => {
  const [email, setEmail] = useState('');
  const [resetToken, setResetToken] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [step, setStep] = useState(1); // 1: 输入邮箱, 2: 输入重置码和新密码
  const navigate = useNavigate();

  const handleRequestReset = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await axios.post(USER_API.RESET_PASSWORD_REQUEST, {
        email,
      });
      setMessage(response.data.message);
      setStep(2);
      setError('');
    } catch (error: any) {
      setError(error.response?.data?.detail || '发送重置请求失败');
    }
  };

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const response = await axios.post(USER_API.RESET_PASSWORD_VERIFY, {
        token: resetToken,
        new_password: newPassword,
      });
      setMessage('密码重置成功，请使用新密码登录');
      setTimeout(() => {
        navigate('/login');
      }, 2000);
    } catch (error: any) {
      setError(error.response?.data?.detail || '重置密码失败');
    }
  };

  return (
    <Container component="main" maxWidth="xs">
      <Paper elevation={3} sx={{ p: 4, mt: 8 }}>
        <Typography component="h1" variant="h5" align="center">
          忘记密码
        </Typography>
        {message && (
          <Alert severity="success" sx={{ mt: 2 }}>
            {message}
          </Alert>
        )}
        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}
        {step === 1 ? (
          <Box component="form" onSubmit={handleRequestReset} sx={{ mt: 1 }}>
            <TextField
              margin="normal"
              required
              fullWidth
              label="邮箱地址"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
            >
              发送重置链接
            </Button>
          </Box>
        ) : (
          <Box component="form" onSubmit={handleResetPassword} sx={{ mt: 1 }}>
            <TextField
              margin="normal"
              required
              fullWidth
              label="重置码"
              value={resetToken}
              onChange={(e) => setResetToken(e.target.value)}
            />
            <TextField
              margin="normal"
              required
              fullWidth
              label="新密码"
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
            >
              重置密码
            </Button>
          </Box>
        )}
        <Button
          fullWidth
          variant="text"
          onClick={() => navigate('/login')}
          sx={{ mt: 1 }}
        >
          返回登录
        </Button>
      </Paper>
    </Container>
  );
};

export default ForgotPassword;