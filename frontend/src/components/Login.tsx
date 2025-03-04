import React, { useState } from 'react';
import { 
  Box, 
  Button, 
  TextField, 
  Typography, 
  Container,
  Paper,
  Alert,
  Link,
  Grid,
  useTheme,
  InputAdornment,
  IconButton,
  Card,
  CardContent,
  Fade,
  Zoom
} from '@mui/material';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { AUTH_API } from '../config/api';
import PersonIcon from '@mui/icons-material/Person';
import LockIcon from '@mui/icons-material/Lock';
import Visibility from '@mui/icons-material/Visibility';
import VisibilityOff from '@mui/icons-material/VisibilityOff';
import RocketLaunchIcon from '@mui/icons-material/RocketLaunch';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const theme = useTheme();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (loading) return;
    
    try {
      setLoading(true);
      setError('');
      
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
    } finally {
      setLoading(false);
    }
  };

  const handleTogglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  return (
    <Box sx={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #e8eaf6 0%, #c5cae9 100%)',
      padding: 2
    }}>
      <Fade in={true} timeout={1000}>
        <Container maxWidth="md" sx={{ 
          width: '100%',
          height: '600px'
        }}>
          <Grid container sx={{ 
            height: '100%',
            boxShadow: '0 10px 30px rgba(0, 0, 0, 0.1)',
            borderRadius: 2
          }}>
            <Grid item xs={12} md={6} sx={{
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              background: 'linear-gradient(135deg, #3f51b5 0%, #5c6bc0 100%)',
              borderRadius: { xs: '16px 16px 0 0', md: '16px 0 0 16px' },
              p: 4,
              color: 'white',
              height: '100%'
            }}>
              <Zoom in={true} style={{ transitionDelay: '500ms' }}>
                <Box sx={{ textAlign: 'center', mb: 4 }}>
                  <Box sx={{ 
                    borderRadius: '50%', 
                    bgcolor: 'rgba(255,255,255,0.1)',
                    width: 100, 
                    height: 100, 
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    margin: '0 auto 16px',
                    boxShadow: '0 10px 20px rgba(0, 0, 0, 0.1)',
                    animation: 'pulse 2s infinite'
                  }}>
                    <RocketLaunchIcon sx={{ fontSize: 50 }} />
                  </Box>
                  <Typography variant="h4" component="h1" gutterBottom fontWeight="bold">
                    AI赋能平台
                  </Typography>
                  <Typography variant="body1" sx={{ opacity: 0.9, mb: 2 }}>
                    用AI技术为您的内容创作赋能，释放创造力
                  </Typography>
                </Box>
              </Zoom>
              
              <Box sx={{ 
                mt: 'auto', 
                width: '100%', 
                textAlign: 'center', 
                p: 2,
                borderRadius: 2,
                bgcolor: 'rgba(255,255,255,0.1)'
              }}>
                <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <AutoAwesomeIcon sx={{ fontSize: 16, mr: 1 }} /> 智能创作，一键生成
                </Typography>
              </Box>
            </Grid>
            
            <Grid item xs={12} md={6} sx={{
              height: '100%',
              bgcolor: '#ffffff',
              borderRadius: { xs: '0 0 16px 16px', md: '0 16px 16px 0' }
            }}>
              <Box sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
                p: 4
              }}>
                <Typography variant="h5" component="h2" sx={{ mb: 3, fontWeight: 'bold', color: theme.palette.primary.main, textAlign: 'center' }}>
                  欢迎回来
                </Typography>
                
                {error && (
                  <Zoom in={!!error}>
                    <Alert 
                      severity="error" 
                      sx={{ 
                        mb: 3,
                        borderRadius: 2,
                        boxShadow: '0 2px 8px rgba(244, 67, 54, 0.2)'
                      }}
                    >
                      {error}
                    </Alert>
                  </Zoom>
                )}
                
                <Box component="form" onSubmit={handleSubmit}>
                  <TextField
                    margin="normal"
                    required
                    fullWidth
                    label="用户名"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <PersonIcon color="primary" />
                        </InputAdornment>
                      ),
                    }}
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        borderRadius: 2,
                      }
                    }}
                  />
                  
                  <TextField
                    margin="normal"
                    required
                    fullWidth
                    label="密码"
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <LockIcon color="primary" />
                        </InputAdornment>
                      ),
                      endAdornment: (
                        <InputAdornment position="end">
                          <IconButton
                            aria-label="toggle password visibility"
                            onClick={handleTogglePasswordVisibility}
                            edge="end"
                          >
                            {showPassword ? <VisibilityOff /> : <Visibility />}
                          </IconButton>
                        </InputAdornment>
                      )
                    }}
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        borderRadius: 2,
                      }
                    }}
                  />
                  
                  <Button
                    type="submit"
                    fullWidth
                    variant="contained"
                    disabled={loading}
                    sx={{ 
                      mt: 4, 
                      mb: 2,
                      py: 1.5,
                      borderRadius: 2,
                      fontWeight: 'bold',
                      position: 'relative',
                      overflow: 'hidden',
                      background: 'linear-gradient(45deg, #3f51b5 30%, #757de8 90%)',
                      '&::after': {
                        content: '""',
                        position: 'absolute',
                        top: 0,
                        left: '-100%',
                        width: '100%',
                        height: '100%',
                        background: 'linear-gradient(45deg, transparent 0%, rgba(255,255,255,0.3) 50%, transparent 100%)',
                        transition: 'all 0.6s',
                      },
                      '&:hover::after': {
                        left: '100%',
                      }
                    }}
                  >
                    {loading ? '登录中...' : '登录'}
                  </Button>
                  
                  <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap' }}>
                    <Link
                      component="button"
                      type="button"
                      variant="body2"
                      onClick={() => navigate('/register')}
                      sx={{ 
                        color: theme.palette.primary.main,
                        textDecoration: 'none',
                        '&:hover': {
                          textDecoration: 'underline'
                        }
                      }}
                    >
                      没有账号？立即注册
                    </Link>
                    
                    <Link
                      component="button"
                      type="button"
                      variant="body2"
                      onClick={() => navigate('/forgot-password')}
                      sx={{ 
                        color: theme.palette.text.secondary,
                        textDecoration: 'none',
                        '&:hover': {
                          textDecoration: 'underline'
                        }
                      }}
                    >
                      忘记密码？
                    </Link>
                  </Box>
                </Box>
              </Box>
            </Grid>
          </Grid>
        </Container>
      </Fade>
      
      {/* 添加CSS动画 */}
      <style>{`
        @keyframes pulse {
          0% {
            box-shadow: 0 0 0 0 rgba(255, 255, 255, 0.4);
          }
          70% {
            box-shadow: 0 0 0 15px rgba(255, 255, 255, 0);
          }
          100% {
            box-shadow: 0 0 0 0 rgba(255, 255, 255, 0);
          }
        }
      `}</style>
    </Box>
  );
};

export default Login;