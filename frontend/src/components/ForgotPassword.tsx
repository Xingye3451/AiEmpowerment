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
  useTheme,
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
  const theme = useTheme();

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
            忘记密码
          </Typography>

          {message && (
            <Zoom in={!!message}>
              <Alert 
                severity="success" 
                sx={{ 
                  mb: 2,
                  borderRadius: 2,
                  boxShadow: '0 2px 8px rgba(76, 175, 80, 0.2)',
                }}
              >
                {message}
              </Alert>
            </Zoom>
          )}

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

          {step === 1 ? (
            <Box 
              component="form" 
              onSubmit={handleRequestReset}
              sx={{ mt: 1 }}
            >
              <TextField
                margin="normal"
                required
                fullWidth
                label="邮箱地址"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
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
                发送重置链接
              </Button>
            </Box>
          ) : (
            <Box 
              component="form" 
              onSubmit={handleResetPassword}
              sx={{ mt: 1 }}
            >
              <TextField
                margin="normal"
                required
                fullWidth
                label="重置码"
                value={resetToken}
                onChange={(e) => setResetToken(e.target.value)}
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
                label="新密码"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
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
                重置密码
              </Button>
            </Box>
          )}

          <Button
            fullWidth
            variant="text"
            onClick={() => navigate('/login')}
            sx={{
              mt: 1,
              color: theme => theme.palette.primary.main,
              transition: 'all 0.3s',
              '&:hover': {
                backgroundColor: 'rgba(63, 81, 181, 0.08)',
              },
            }}
          >
            返回登录
          </Button>
        </Paper>
      </Box>
    </Container>
  );
};

export default ForgotPassword;