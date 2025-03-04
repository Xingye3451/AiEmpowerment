import React, { useEffect, useState } from 'react';
import { 
  Container, Typography, Paper, Box, Alert, Button, Grid, 
  Drawer, List, ListItem, ListItemIcon, ListItemText, AppBar,
  Toolbar, IconButton, Avatar, Divider, useTheme, Slide, Zoom,
  Card, CardContent, useMediaQuery, Badge
} from '@mui/material';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import DouyinManager from './DouyinManager';
import AIVideoProcessor from './AIVideoProcessor';
import { USER_API } from '../config/api';
import MenuIcon from '@mui/icons-material/Menu';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import HomeIcon from '@mui/icons-material/Home';
import VideocamIcon from '@mui/icons-material/Videocam';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import LogoutIcon from '@mui/icons-material/Logout';
import NotificationsIcon from '@mui/icons-material/Notifications';

const Dashboard: React.FC = () => {
  const [userData, setUserData] = useState<any>(null);
  const [error, setError] = useState('');
  const [activeComponent, setActiveComponent] = useState<'douyin' | 'ai'>('douyin');
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        setLoading(true);
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
      } finally {
        setLoading(false);
      }
    };

    fetchUserData();
  }, [navigate]);

  const handleComponentChange = (component: 'douyin' | 'ai') => {
    setActiveComponent(component);
    if (isMobile) {
      setDrawerOpen(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  const drawerWidth = 240;

  const drawer = (
    <>
      {isMobile && (
        <>
          <Box sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'flex-end',
            padding: '8px'
          }}>
            <IconButton 
              onClick={() => setDrawerOpen(false)}
              sx={{
                '&:hover': {
                  backgroundColor: 'rgba(0, 0, 0, 0.04)',
                },
              }}
            >
              <ChevronLeftIcon />
            </IconButton>
          </Box>
          <Divider />
        </>
      )}
      {userData && (
        <Box sx={{ 
          display: 'flex', 
          flexDirection: 'column', 
          alignItems: 'center',
          padding: '20px 0'
        }}>
          <Avatar 
            sx={{ 
              width: 80, 
              height: 80, 
              bgcolor: theme.palette.primary.main,
              mb: 2,
              boxShadow: '0 4px 8px rgba(0, 0, 0, 0.1)',
              transition: 'transform 0.3s',
              '&:hover': {
                transform: 'scale(1.05)',
              }
            }}
          >
            {userData.username[0].toUpperCase()}
          </Avatar>
          <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
            {userData.username}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {userData.email}
          </Typography>
        </Box>
      )}
      <Divider />
      <List component="nav" sx={{ pt: 2 }}>
        <ListItem 
          button 
          selected={activeComponent === 'douyin'}
          onClick={() => handleComponentChange('douyin')}
          sx={{
            borderRadius: '0 20px 20px 0',
            mr: 2,
            mb: 1,
            '&.Mui-selected': {
              backgroundColor: theme.palette.primary.light,
              color: theme.palette.primary.contrastText,
              '& .MuiListItemIcon-root': {
                color: theme.palette.primary.contrastText,
              },
            },
          }}
        >
          <ListItemIcon>
            <VideocamIcon />
          </ListItemIcon>
          <ListItemText primary="抖音管理" />
        </ListItem>
        <ListItem 
          button 
          selected={activeComponent === 'ai'}
          onClick={() => handleComponentChange('ai')}
          sx={{
            borderRadius: '0 20px 20px 0',
            mr: 2,
            mb: 1,
            '&.Mui-selected': {
              backgroundColor: theme.palette.primary.light,
              color: theme.palette.primary.contrastText,
              '& .MuiListItemIcon-root': {
                color: theme.palette.primary.contrastText,
              },
            },
          }}
        >
          <ListItemIcon>
            <SmartToyIcon />
          </ListItemIcon>
          <ListItemText primary="AI视频处理" />
        </ListItem>
        <Divider sx={{ my: 2 }} />
        <ListItem 
          button 
          onClick={handleLogout}
          sx={{
            borderRadius: '0 20px 20px 0',
            mr: 2,
            color: theme.palette.error.main,
            '& .MuiListItemIcon-root': {
              color: theme.palette.error.main,
            },
          }}
        >
          <ListItemIcon>
            <LogoutIcon />
          </ListItemIcon>
          <ListItemText primary="退出登录" />
        </ListItem>
      </List>
    </>
  );

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <AppBar 
        position="fixed" 
        sx={{ 
          zIndex: theme.zIndex.drawer + 1,
          background: 'linear-gradient(45deg, #3f51b5 30%, #757de8 90%)',
          boxShadow: '0 3px 5px 2px rgba(63, 81, 181, .3)',
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={() => setDrawerOpen(!drawerOpen)}
            sx={{ 
              mr: 2,
              display: { sm: 'none' }
            }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 'bold' }}>
            AI赋能平台
          </Typography>
          <IconButton color="inherit">
            <Badge badgeContent={4} color="error">
              <NotificationsIcon />
            </Badge>
          </IconButton>
          {!isMobile && userData && (
            <Box sx={{ display: 'flex', alignItems: 'center', ml: 2 }}>
              <Avatar sx={{ bgcolor: theme.palette.secondary.main, mr: 1 }}>
                {userData.username[0].toUpperCase()}
              </Avatar>
              <Typography variant="subtitle1">{userData.username}</Typography>
            </Box>
          )}
        </Toolbar>
      </AppBar>

      <Drawer
        variant={isMobile ? "temporary" : "permanent"}
        open={isMobile ? drawerOpen : true}
        onClose={() => setDrawerOpen(false)}
        ModalProps={{
          keepMounted: true,
        }}
        sx={{
          display: { xs: 'block' },
          '& .MuiDrawer-paper': {
            boxSizing: 'border-box',
            width: drawerWidth,
            backgroundImage: 'linear-gradient(to bottom, #f5f5f5, #ffffff)',
            ...(isMobile ? {
              height: '100%',
            } : {
              position: 'relative',
              marginTop: '64px',
              height: 'calc(100% - 64px)',
            }),
          },
        }}
      >
        {isMobile && <Toolbar />}
        {drawer}
      </Drawer>

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          backgroundColor: theme.palette.background.default,
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: { sm: `${drawerWidth}px` },
        }}
      >
        <Toolbar />
        
        {error && (
          <Zoom in={!!error}>
            <Alert 
              severity="error" 
              sx={{ 
                mb: 2,
                boxShadow: '0 2px 10px rgba(244, 67, 54, 0.2)',
                borderRadius: 2
              }}
            >
              {error}
            </Alert>
          </Zoom>
        )}

        <Slide direction="down" in={!loading} mountOnEnter unmountOnExit>
          <Box sx={{ mt: 2 }}>
            <Card 
              elevation={3} 
              sx={{ 
                mb: 4,
                borderRadius: 3,
                background: 'linear-gradient(45deg, #e8eaf6 30%, #ffffff 90%)'
              }}
            >
              <CardContent>
                <Typography 
                  component="h1" 
                  variant="h4" 
                  gutterBottom 
                  sx={{ 
                    fontWeight: 'bold',
                    color: theme.palette.primary.main 
                  }}
                >
                  {activeComponent === 'douyin' ? '抖音管理中心' : 'AI视频处理中心'}
                </Typography>
                <Typography variant="body1" color="text.secondary" paragraph>
                  {activeComponent === 'douyin' 
                    ? '在这里管理您的抖音账号、视频和发布计划。' 
                    : '使用人工智能技术处理和优化您的视频内容。'}
                </Typography>
              </CardContent>
            </Card>

            <Box sx={{ mt: 4 }}>
              {activeComponent === 'douyin' ? (
                <DouyinManager />
              ) : (
                <AIVideoProcessor />
              )}
            </Box>
          </Box>
        </Slide>
      </Box>
    </Box>
  );
};

export default Dashboard;