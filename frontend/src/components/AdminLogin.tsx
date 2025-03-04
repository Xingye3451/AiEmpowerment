import React, { useState } from 'react';
import { 
  Box, 
  Button, 
  TextField, 
  Typography, 
  Container,
  Paper,
  Alert,
  Grid,
  useTheme,
  InputAdornment,
  IconButton,
  Fade,
  Zoom
} from '@mui/material';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { AUTH_API } from '../config/api';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';
import SecurityIcon from '@mui/icons-material/Security';
import LockIcon from '@mui/icons-material/Lock';
import Visibility from '@mui/icons-material/Visibility';
import VisibilityOff from '@mui/icons-material/VisibilityOff';
import DashboardIcon from '@mui/icons-material/Dashboard';
import SettingsIcon from '@mui/icons-material/Settings';
import GroupIcon from '@mui/icons-material/Group';
import StorageIcon from '@mui/icons-material/Storage';

const AdminLogin = () => {
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
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      navigate('/admin/dashboard');
    } catch (error: any) {
      setError(error.response?.data?.detail || '管理员登录失败');
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
      background: 'linear-gradient(135deg, #1a237e 0%, #283593 100%)',
      padding: 2
    }}>
      <Fade in={true} timeout={1000}>
        <Container maxWidth="md" sx={{ 
          width: '100%',
          height: '600px'
        }}>
          <Grid container sx={{ 
            height: '100%',
            boxShadow: '0 10px 30px rgba(0, 0, 0, 0.2)',
            borderRadius: 2
          }}>
            <Grid item xs={12} md={6} sx={{
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              background: 'linear-gradient(135deg, #0d47a1 0%, #1565c0 100%)',
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
                    <AdminPanelSettingsIcon sx={{ fontSize: 50 }} />
                  </Box>
                  <Typography variant="h4" component="h1" gutterBottom fontWeight="bold">
                    后台管理系统
                  </Typography>
                  <Typography variant="body1" sx={{ opacity: 0.9, mb: 2 }}>
                    全方位的系统管理与数据分析平台
                  </Typography>
                </Box>
              </Zoom>
              
              <Grid container spacing={2} sx={{ mt: 4 }}>
                <Grid item xs={6}>
                  <Box sx={{ 
                    p: 2, 
                    bgcolor: 'rgba(255,255,255,0.1)', 
                    borderRadius: 2,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1
                  }}>
                    <DashboardIcon />
                    <Typography variant="body2">数据看板</Typography>
                  </Box>
                </Grid>
                <Grid item xs={6}>
                  <Box sx={{ 
                    p: 2, 
                    bgcolor: 'rgba(255,255,255,0.1)', 
                    borderRadius: 2,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1
                  }}>
                    <GroupIcon />
                    <Typography variant="body2">用户管理</Typography>
                  </Box>
                </Grid>
                <Grid item xs={6}>
                  <Box sx={{ 
                    p: 2, 
                    bgcolor: 'rgba(255,255,255,0.1)', 
                    borderRadius: 2,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1
                  }}>
                    <StorageIcon />
                    <Typography variant="body2">系统配置</Typography>
                  </Box>
                </Grid>
                <Grid item xs={6}>
                  <Box sx={{ 
                    p: 2, 
                    bgcolor: 'rgba(255,255,255,0.1)', 
                    borderRadius: 2,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1
                  }}>
                    <SettingsIcon />
                    <Typography variant="body2">权限控制</Typography>
                  </Box>
                </Grid>
              </Grid>
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
                <Typography variant="h5" component="h2" sx={{ 
                  mb: 3, 
                  fontWeight: 'bold', 
                  color: theme.palette.primary.main, 
                  textAlign: 'center',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 1
                }}>
                  <SecurityIcon />
                  管理员登录
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
                    label="管理员账号"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <AdminPanelSettingsIcon color="primary" />
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
                    label="管理员密码"
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
                      background: 'linear-gradient(45deg, #0d47a1 30%, #1565c0 90%)',
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
                    {loading ? '登录中...' : '安全登录'}
                  </Button>
                </Box>
              </Box>
            </Grid>
          </Grid>
        </Container>
      </Fade>
      
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

export default AdminLogin;