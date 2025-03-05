import React, { useEffect, useState } from 'react';
import { 
  Container, Typography, Paper, Box, Alert, Button, Grid, 
  Drawer, List, ListItem, ListItemIcon, ListItemText, AppBar,
  Toolbar, IconButton, Avatar, Divider, useTheme, Slide, Zoom,
  Card, CardContent, useMediaQuery, Badge, CssBaseline, Menu, MenuItem,
  ListSubheader, Collapse, Tooltip
} from '@mui/material';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import ContentDistributor from './ContentDistributor';
import AIVideoProcessor from './AIVideoProcessor';
import TaskManager from './TaskManager';
import SocialAccountManager from './SocialAccountManager';
import Logo from './Logo';
import { USER_API } from '../config/api';
import {
  Menu as MenuIcon,
  VideoLibrary as VideoLibraryIcon,
  Schedule as ScheduleIcon,
  CloudDownload as CloudDownloadIcon,
  Assignment as AssignmentIcon,
  Send as SendIcon,
  Notifications as NotificationsIcon,
  Group as GroupIcon,
  Logout as LogoutIcon,
  Settings as SettingsIcon,
  Person as PersonIcon,
  ExpandLess as ExpandLessIcon,
  ExpandMore as ExpandMoreIcon,
  WorkOutline as WorkOutlineIcon,
  Storage as StorageIcon,
  Dashboard as DashboardIcon,
  KeyboardArrowDown as KeyboardArrowDownIcon,
  PlaylistAddCheck as PlaylistAddCheckIcon,
  Image as ImageIcon
} from '@mui/icons-material';
import ScheduledTaskManager from './ScheduledTaskManager';
import ContentCollector from './ContentCollector';
import NotificationCenter from './NotificationCenter';
import NotificationsPage from './NotificationsPage';
import UserProfileDialog from './UserProfileDialog';
import ComfyUIIntegration from './ComfyUIIntegration';

const drawerWidth = 240;

// 菜单项接口
interface MenuItem {
  id: string;
  text: string;
  icon: JSX.Element;
  category?: string;
}

// 菜单分类接口
interface MenuCategory {
  id: string;
  text: string;
  icon: JSX.Element;
  items: MenuItem[];
}

const Dashboard: React.FC = () => {
  const [userData, setUserData] = useState<any>(null);
  const [error, setError] = useState('');
  const [activeComponent, setActiveComponent] = useState('ai_video');
  const [mobileOpen, setMobileOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [profileDialogOpen, setProfileDialogOpen] = useState(false);
  const [expandedCategories, setExpandedCategories] = useState<Record<string, boolean>>({
    business: true,
    task: true,
    resource: true,
    system: true
  });
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
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          withCredentials: true
        });
        
        // 确保响应数据是对象
        if (response.data && typeof response.data === 'object') {
          setUserData(response.data);
        } else {
          console.error('用户资料数据格式不正确:', response.data);
          setError('获取用户信息失败：数据格式不正确');
        }
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

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleComponentChange = (componentId: string) => {
    setActiveComponent(componentId);
    if (isMobile) {
      setMobileOpen(false);
    }
  };

  const handleUserMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleUserMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
    handleUserMenuClose();
  };

  const handleProfile = () => {
    handleUserMenuClose();
    setProfileDialogOpen(true);
  };

  const handleNavigate = (path: string, params?: any) => {
    switch (path) {
      case '/notifications':
        setActiveComponent('notifications');
        break;
      case '/collection':
        setActiveComponent('content_collect');
        break;
      case '/scheduled-tasks':
        setActiveComponent('scheduled_tasks');
        break;
      default:
        break;
    }
  };

  const handleUserDataUpdate = (updatedUserData: any) => {
    setUserData(updatedUserData);
  };

  const handleCategoryToggle = (categoryId: string) => {
    setExpandedCategories({
      ...expandedCategories,
      [categoryId]: !expandedCategories[categoryId]
    });
  };

  // 菜单分类
  const menuCategories: MenuCategory[] = [
    {
      id: 'business',
      text: '内容工作台',
      icon: <WorkOutlineIcon color="primary" />,
      items: [
        { id: 'ai_video', text: 'AI视频处理', icon: <VideoLibraryIcon color="primary" /> },
        { id: 'content_distribute', text: '内容分发', icon: <SendIcon color="primary" /> },
        { id: 'content_collect', text: '内容采集', icon: <CloudDownloadIcon color="primary" /> },
        { id: 'comfyui', text: 'ComfyUI集成', icon: <ImageIcon color="primary" /> }
      ]
    },
    {
      id: 'task',
      text: '任务中心',
      icon: <PlaylistAddCheckIcon color="secondary" />,
      items: [
        { id: 'tasks', text: '任务管理', icon: <AssignmentIcon color="secondary" /> },
        { id: 'scheduled_tasks', text: '定时任务管理', icon: <ScheduleIcon color="secondary" /> }
      ]
    },
    {
      id: 'resource',
      text: '资源管理',
      icon: <StorageIcon color="success" />,
      items: [
        { id: 'social_accounts', text: '社交账号管理', icon: <GroupIcon color="success" /> }
      ]
    },
    {
      id: 'system',
      text: '系统设置',
      icon: <SettingsIcon color="info" />,
      items: [
        { id: 'notifications', text: '通知中心', icon: <NotificationsIcon color="info" /> }
      ]
    }
  ];

  // 获取所有菜单项的平面列表（用于查找当前活动项的文本）
  const allMenuItems = menuCategories.flatMap(category => category.items);

  const drawer = (
    <div>
      <Box sx={{ display: 'flex', alignItems: 'center', p: 2 }}>
        <Logo sx={{ width: 40, height: 40, color: 'primary.main' }} />
        <Typography variant="h6" noWrap component="div" sx={{ ml: 1, color: 'primary.main', fontWeight: 'bold' }}>
          AI赋能中心
        </Typography>
      </Box>
      <Divider />
      
      {menuCategories.map((category) => (
        <React.Fragment key={category.id}>
          <List
            subheader={
              <ListItem 
                button 
                onClick={() => handleCategoryToggle(category.id)}
                sx={{ 
                  bgcolor: 'rgba(0, 0, 0, 0.03)',
                  '&:hover': { bgcolor: 'rgba(0, 0, 0, 0.06)' }
                }}
              >
                <ListItemIcon>{category.icon}</ListItemIcon>
                <ListItemText 
                  primary={category.text} 
                  primaryTypographyProps={{ 
                    fontWeight: 'medium',
                    variant: 'subtitle1'
                  }}
                />
                {expandedCategories[category.id] ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              </ListItem>
            }
          >
            <Collapse in={expandedCategories[category.id]} timeout="auto" unmountOnExit>
              {category.items.map((item) => (
                <ListItem
                  button
                  key={item.id}
                  selected={activeComponent === item.id}
                  onClick={() => handleComponentChange(item.id)}
                  sx={{ 
                    pl: 4,
                    '&.Mui-selected': {
                      bgcolor: 'rgba(0, 0, 0, 0.08)',
                      '&:hover': {
                        bgcolor: 'rgba(0, 0, 0, 0.12)'
                      }
                    }
                  }}
                >
                  <ListItemIcon>{item.icon}</ListItemIcon>
                  <ListItemText primary={item.text} />
                </ListItem>
              ))}
            </Collapse>
          </List>
          <Divider />
        </React.Fragment>
      ))}
    </div>
  );

  const renderComponent = () => {
    switch (activeComponent) {
      case 'ai_video':
        return <AIVideoProcessor />;
      case 'tasks':
        return <TaskManager />;
      case 'content_distribute':
        return <ContentDistributor />;
      case 'social_accounts':
        return <SocialAccountManager />;
      case 'scheduled_tasks':
        return <ScheduledTaskManager />;
      case 'content_collect':
        return <ContentCollector />;
      case 'notifications':
        return <NotificationsPage onNavigate={handleNavigate} />;
      case 'comfyui':
        return <ComfyUIIntegration />;
      default:
        return <AIVideoProcessor />;
    }
  };

  const fetchUserProfile = async () => {
    try {
      setLoading(true);
      const response = await axios.get(USER_API.PROFILE, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });
      
      // 确保响应数据是对象
      if (response.data && typeof response.data === 'object') {
        setUserData(response.data);
      } else {
        console.error('用户资料数据格式不正确:', response.data);
        setError('获取用户资料失败：数据格式不正确');
      }
    } catch (error) {
      console.error('获取用户资料失败:', error);
      setError('获取用户资料失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      <AppBar
        position="fixed"
        sx={{
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: { sm: `${drawerWidth}px` },
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            {allMenuItems.find(item => item.id === activeComponent)?.text || 'AI赋能中心'}
          </Typography>
          
          {/* 通知中心 */}
          <NotificationCenter onNavigate={handleNavigate} />
          
          {/* 用户头像和菜单 */}
          <Box sx={{ display: 'flex', alignItems: 'center', ml: 2 }}>
            <Tooltip title="账户设置">
              <Button
                onClick={handleUserMenuOpen}
                color="inherit"
                endIcon={<KeyboardArrowDownIcon />}
                sx={{ 
                  textTransform: 'none',
                  display: 'flex',
                  alignItems: 'center'
                }}
              >
                <Avatar 
                  sx={{ 
                    width: 32, 
                    height: 32,
                    mr: 1,
                    bgcolor: 'primary.dark'
                  }}
                >
                  {userData?.username?.charAt(0)?.toUpperCase() || 'U'}
                </Avatar>
                {userData?.username || '用户'}
              </Button>
            </Tooltip>
            <Menu
              id="menu-appbar"
              anchorEl={anchorEl}
              anchorOrigin={{
                vertical: 'bottom',
                horizontal: 'right',
              }}
              keepMounted
              transformOrigin={{
                vertical: 'top',
                horizontal: 'right',
              }}
              open={Boolean(anchorEl)}
              onClose={handleUserMenuClose}
              PaperProps={{
                elevation: 3,
                sx: { 
                  minWidth: 180,
                  mt: 1
                }
              }}
            >
              <MenuItem onClick={handleProfile} sx={{ py: 1.5 }}>
                <ListItemIcon>
                  <PersonIcon fontSize="small" />
                </ListItemIcon>
                <ListItemText primary="个人资料" />
              </MenuItem>
              <MenuItem onClick={handleComponentChange.bind(null, 'notifications')} sx={{ py: 1.5 }}>
                <ListItemIcon>
                  <NotificationsIcon fontSize="small" />
                </ListItemIcon>
                <ListItemText primary="通知中心" />
              </MenuItem>
              <Divider />
              <MenuItem onClick={handleLogout} sx={{ py: 1.5 }}>
                <ListItemIcon>
                  <LogoutIcon fontSize="small" color="error" />
                </ListItemIcon>
                <ListItemText primary="退出登录" sx={{ color: 'error.main' }} />
              </MenuItem>
            </Menu>
          </Box>
        </Toolbar>
      </AppBar>
      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
      >
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true, // Better open performance on mobile.
          }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          minHeight: '100vh'
        }}
      >
        <Toolbar />
        <Container maxWidth="xl">
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '70vh' }}>
              <Typography>加载中...</Typography>
            </Box>
          ) : (
            renderComponent()
          )}
        </Container>
      </Box>

      {/* 用户资料对话框 */}
      <UserProfileDialog
        open={profileDialogOpen}
        onClose={() => setProfileDialogOpen(false)}
        userData={userData}
        onUserDataUpdate={handleUserDataUpdate}
      />
    </Box>
  );
};

export default Dashboard;