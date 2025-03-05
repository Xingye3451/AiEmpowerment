import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  List,
  ListItem,
  ListItemText,
  Divider,
  IconButton,
  Badge,
  Menu,
  MenuItem,
  Button,
  Tooltip,
  CircularProgress,
  Tabs,
  Tab,
  Paper,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Notifications as NotificationsIcon,
  Delete as DeleteIcon,
  CheckCircle as CheckCircleIcon,
  Info as InfoIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import axios from 'axios';
import { format } from 'date-fns';
import { zhCN } from 'date-fns/locale';
import { BASE_URL } from '../config/api';

// 通知数据接口
interface Notification {
  id: string;
  title: string;
  content: string;
  type: string;      // 通知类型：system, task, scheduled_task 等
  status: string;    // 通知状态：read, unread
  created_at: string;
  read_at: string | null;
  related_id: string | null;    // 关联对象ID
  related_type: string | null;  // 关联对象类型
}

interface NotificationCenterProps {
  onNavigate?: (path: string, params?: any) => void;  // 导航回调函数
}

/**
 * 通知中心组件
 * 显示为顶部导航栏中的通知图标，点击后显示通知下拉菜单
 */
const NotificationCenter: React.FC<NotificationCenterProps> = ({ onNavigate }) => {
  // 菜单锚点元素
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  // 通知列表
  const [notifications, setNotifications] = useState<Notification[]>([]);
  // 未读通知数量
  const [unreadCount, setUnreadCount] = useState(0);
  // 加载状态
  const [loading, setLoading] = useState(false);
  // 当前选中的标签页（全部/未读/已读）
  const [tabValue, setTabValue] = useState(0);
  // 当前选中的通知
  const [selectedNotification, setSelectedNotification] = useState<Notification | null>(null);
  // 通知详情对话框开关
  const [detailOpen, setDetailOpen] = useState(false);

  /**
   * 获取通知列表
   */
  const fetchNotifications = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.get('/api/v1/notifications', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
        params: {
          limit: 10,  // 只获取最近10条通知
        },
      });
      setNotifications(response.data.items);
      setUnreadCount(response.data.unread_count);
    } catch (error) {
      console.error('获取通知失败:', error);
    } finally {
      setLoading(false);
    }
  };

  /**
   * 获取未读通知数量
   */
  const fetchNotificationCount = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${BASE_URL}/notifications/count`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setUnreadCount(response.data.unread);
    } catch (error) {
      console.error('获取通知计数失败:', error);
    }
  };

  // 组件挂载时获取未读通知数量，并设置定时更新
  useEffect(() => {
    // 初始加载通知计数
    fetchNotificationCount();

    // 每分钟更新一次通知计数
    const interval = setInterval(fetchNotificationCount, 60000);

    // 组件卸载时清除定时器
    return () => clearInterval(interval);
  }, []);

  /**
   * 打开通知菜单
   */
  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
    fetchNotifications();  // 打开菜单时获取最新通知
  };

  /**
   * 关闭通知菜单
   */
  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  /**
   * 切换标签页
   */
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  /**
   * 标记通知为已读
   */
  const handleMarkAsRead = async (notificationId: string) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(`/api/v1/notifications/${notificationId}/read`, {}, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      
      // 更新本地通知状态
      setNotifications(notifications.map(notification => 
        notification.id === notificationId 
          ? { ...notification, status: 'read', read_at: new Date().toISOString() } 
          : notification
      ));
      
      // 更新未读计数
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      console.error('标记通知为已读失败:', error);
    }
  };

  /**
   * 标记所有通知为已读
   */
  const handleMarkAllAsRead = async () => {
    try {
      const token = localStorage.getItem('token');
      await axios.post('/api/v1/notifications/read-all', {}, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      
      // 更新本地通知状态
      setNotifications(notifications.map(notification => ({ 
        ...notification, 
        status: 'read', 
        read_at: new Date().toISOString() 
      })));
      
      // 更新未读计数
      setUnreadCount(0);
    } catch (error) {
      console.error('标记所有通知为已读失败:', error);
    }
  };

  /**
   * 删除通知
   */
  const handleDeleteNotification = async (notificationId: string) => {
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`/api/v1/notifications/${notificationId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      
      // 从列表中移除通知
      setNotifications(notifications.filter(notification => notification.id !== notificationId));
      
      // 如果删除的是未读通知，更新未读计数
      const deletedNotification = notifications.find(n => n.id === notificationId);
      if (deletedNotification && deletedNotification.status === 'unread') {
        setUnreadCount(prev => Math.max(0, prev - 1));
      }
    } catch (error) {
      console.error('删除通知失败:', error);
    }
  };

  /**
   * 点击通知项
   */
  const handleNotificationClick = (notification: Notification) => {
    // 如果通知未读，标记为已读
    if (notification.status === 'unread') {
      handleMarkAsRead(notification.id);
    }
    
    // 显示通知详情
    setSelectedNotification(notification);
    setDetailOpen(true);
    
    // 如果有关联的任务，可以导航到相应页面
    if (notification.related_id && notification.related_type && onNavigate) {
      // 关闭菜单
      handleMenuClose();
      
      // 根据通知类型导航到不同页面
      switch (notification.related_type) {
        case 'collection_task':
          onNavigate('/collection', { taskId: notification.related_id });
          break;
        case 'scheduled_task':
          onNavigate('/scheduled-tasks', { taskId: notification.related_id });
          break;
        default:
          break;
      }
    }
  };

  /**
   * 关闭通知详情对话框
   */
  const handleCloseDetail = () => {
    setDetailOpen(false);
    setSelectedNotification(null);
  };

  /**
   * 根据通知类型获取对应图标
   */
  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'system':
        return <InfoIcon color="primary" />;
      case 'task':
        return <CheckCircleIcon color="success" />;
      case 'scheduled_task':
        return <WarningIcon color="warning" />;
      default:
        return <NotificationsIcon />;
    }
  };

  /**
   * 格式化日期
   */
  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), 'yyyy-MM-dd HH:mm', { locale: zhCN });
    } catch (error) {
      return dateString;
    }
  };

  // 根据当前标签页筛选通知
  const filteredNotifications = tabValue === 0 
    ? notifications 
    : tabValue === 1 
      ? notifications.filter(n => n.status === 'unread')
      : notifications.filter(n => n.status === 'read');

  return (
    <>
      {/* 通知图标按钮 */}
      <Tooltip title="通知">
        <IconButton color="inherit" onClick={handleMenuOpen}>
          <Badge badgeContent={unreadCount} color="error">
            <NotificationsIcon />
          </Badge>
        </IconButton>
      </Tooltip>
      
      {/* 通知下拉菜单 */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
        PaperProps={{
          sx: { width: 360, maxHeight: 500 }
        }}
      >
        {/* 菜单标题 */}
        <Box sx={{ p: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6">通知中心</Typography>
          {unreadCount > 0 && (
            <Button size="small" onClick={handleMarkAllAsRead}>
              全部已读
            </Button>
          )}
        </Box>
        
        <Divider />
        
        {/* 标签页切换 */}
        <Paper sx={{ width: '100%' }}>
          <Tabs
            value={tabValue}
            onChange={handleTabChange}
            indicatorColor="primary"
            textColor="primary"
            variant="fullWidth"
          >
            <Tab label="全部" />
            <Tab label={`未读 (${unreadCount})`} />
            <Tab label="已读" />
          </Tabs>
        </Paper>
        
        {/* 通知列表 */}
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <CircularProgress size={24} />
          </Box>
        ) : filteredNotifications.length === 0 ? (
          <Box sx={{ p: 3, textAlign: 'center' }}>
            <Typography color="text.secondary">暂无通知</Typography>
          </Box>
        ) : (
          <List sx={{ p: 0 }}>
            {filteredNotifications.map((notification) => (
              <React.Fragment key={notification.id}>
                <ListItem
                  alignItems="flex-start"
                  sx={{
                    bgcolor: notification.status === 'unread' ? 'rgba(25, 118, 210, 0.08)' : 'transparent',
                    '&:hover': { bgcolor: 'rgba(0, 0, 0, 0.04)' },
                    cursor: 'pointer'
                  }}
                  secondaryAction={
                    <IconButton 
                      edge="end" 
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteNotification(notification.id);
                      }}
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  }
                  onClick={() => handleNotificationClick(notification)}
                >
                  <Box sx={{ mr: 1, display: 'flex', alignItems: 'center' }}>
                    {getNotificationIcon(notification.type)}
                  </Box>
                  <ListItemText
                    primary={notification.title}
                    secondary={
                      <React.Fragment>
                        <Typography
                          sx={{ display: 'block' }}
                          component="span"
                          variant="body2"
                          color="text.secondary"
                        >
                          {notification.content.length > 50 
                            ? `${notification.content.substring(0, 50)}...` 
                            : notification.content}
                        </Typography>
                        <Typography
                          component="span"
                          variant="caption"
                          color="text.secondary"
                        >
                          {formatDate(notification.created_at)}
                        </Typography>
                      </React.Fragment>
                    }
                  />
                </ListItem>
                <Divider component="li" />
              </React.Fragment>
            ))}
          </List>
        )}
        
        {/* 查看全部通知按钮 */}
        {notifications.length > 0 && (
          <Box sx={{ p: 1, textAlign: 'center' }}>
            <Button size="small" onClick={() => {
              handleMenuClose();
              if (onNavigate) {
                onNavigate('/notifications');
              }
            }}>
              查看全部通知
            </Button>
          </Box>
        )}
      </Menu>
      
      {/* 通知详情对话框 */}
      <Dialog open={detailOpen} onClose={handleCloseDetail} maxWidth="sm" fullWidth>
        {selectedNotification && (
          <>
            <DialogTitle>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                {getNotificationIcon(selectedNotification.type)}
                <Typography variant="h6" sx={{ ml: 1 }}>
                  {selectedNotification.title}
                </Typography>
              </Box>
            </DialogTitle>
            <DialogContent>
              <Typography variant="body1" gutterBottom>
                {selectedNotification.content}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {formatDate(selectedNotification.created_at)}
              </Typography>
            </DialogContent>
            <DialogActions>
              <Button onClick={handleCloseDetail}>关闭</Button>
            </DialogActions>
          </>
        )}
      </Dialog>
    </>
  );
};

export default NotificationCenter; 