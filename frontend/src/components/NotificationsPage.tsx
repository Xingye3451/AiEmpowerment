import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  Divider,
  IconButton,
  Button,
  Tabs,
  Tab,
  CircularProgress,
  Pagination,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  Tooltip,
  Alert,
  Snackbar,
} from '@mui/material';
import {
  Delete as DeleteIcon,
  CheckCircle as CheckCircleIcon,
  Info as InfoIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Notifications as NotificationsIcon,
  DeleteSweep as DeleteSweepIcon,
} from '@mui/icons-material';
import axios from 'axios';
import { format } from 'date-fns';
import { zhCN } from 'date-fns/locale';

interface Notification {
  id: string;
  title: string;
  content: string;
  type: string;
  status: string;
  created_at: string;
  read_at: string | null;
  related_id: string | null;
  related_type: string | null;
}

interface NotificationsPageProps {
  onNavigate?: (path: string, params?: any) => void;
}

const NotificationsPage: React.FC<NotificationsPageProps> = ({ onNavigate }) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(false);
  const [tabValue, setTabValue] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [selectedNotification, setSelectedNotification] = useState<Notification | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [confirmDeleteOpen, setConfirmDeleteOpen] = useState(false);
  const [confirmDeleteAllOpen, setConfirmDeleteAllOpen] = useState(false);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState<'success' | 'error'>('success');

  const ITEMS_PER_PAGE = 20;

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const status = tabValue === 1 ? 'unread' : tabValue === 2 ? 'read' : undefined;
      
      const response = await axios.get('/api/v1/notifications', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
        params: {
          page,
          limit: ITEMS_PER_PAGE,
          status,
        },
      });
      
      setNotifications(response.data.items);
      setTotalPages(Math.ceil(response.data.total / ITEMS_PER_PAGE));
    } catch (error) {
      console.error('获取通知失败:', error);
      showSnackbar('获取通知失败', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, [page, tabValue]);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
    setPage(1); // 切换标签时重置页码
  };

  const handlePageChange = (event: React.ChangeEvent<unknown>, value: number) => {
    setPage(value);
  };

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
      
      showSnackbar('通知已标记为已读', 'success');
    } catch (error) {
      console.error('标记通知为已读失败:', error);
      showSnackbar('标记通知为已读失败', 'error');
    }
  };

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
      
      showSnackbar('所有通知已标记为已读', 'success');
    } catch (error) {
      console.error('标记所有通知为已读失败:', error);
      showSnackbar('标记所有通知为已读失败', 'error');
    }
  };

  const handleDeleteNotification = async () => {
    if (!selectedNotification) return;
    
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`/api/v1/notifications/${selectedNotification.id}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      
      // 从列表中移除通知
      setNotifications(notifications.filter(notification => notification.id !== selectedNotification.id));
      setConfirmDeleteOpen(false);
      setSelectedNotification(null);
      
      showSnackbar('通知已删除', 'success');
    } catch (error) {
      console.error('删除通知失败:', error);
      showSnackbar('删除通知失败', 'error');
    }
  };

  const handleDeleteAllNotifications = async () => {
    try {
      const token = localStorage.getItem('token');
      const status = tabValue === 1 ? 'unread' : tabValue === 2 ? 'read' : undefined;
      
      await axios.delete('/api/v1/notifications', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
        params: {
          status,
        },
      });
      
      // 清空通知列表
      setNotifications([]);
      setConfirmDeleteAllOpen(false);
      
      showSnackbar('通知已全部删除', 'success');
    } catch (error) {
      console.error('删除所有通知失败:', error);
      showSnackbar('删除所有通知失败', 'error');
    }
  };

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

  const handleCloseDetail = () => {
    setDetailOpen(false);
  };

  const openDeleteConfirm = (notification: Notification) => {
    setSelectedNotification(notification);
    setConfirmDeleteOpen(true);
  };

  const closeDeleteConfirm = () => {
    setConfirmDeleteOpen(false);
    setSelectedNotification(null);
  };

  const openDeleteAllConfirm = () => {
    setConfirmDeleteAllOpen(true);
  };

  const closeDeleteAllConfirm = () => {
    setConfirmDeleteAllOpen(false);
  };

  const showSnackbar = (message: string, severity: 'success' | 'error') => {
    setSnackbarMessage(message);
    setSnackbarSeverity(severity);
    setSnackbarOpen(true);
  };

  const handleCloseSnackbar = () => {
    setSnackbarOpen(false);
  };

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

  const getNotificationTypeText = (type: string) => {
    switch (type) {
      case 'system':
        return '系统';
      case 'task':
        return '任务';
      case 'scheduled_task':
        return '定时任务';
      default:
        return '通知';
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), 'yyyy-MM-dd HH:mm:ss', { locale: zhCN });
    } catch (error) {
      return dateString;
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          通知中心
        </Typography>
        <Box>
          {notifications.length > 0 && (
            <>
              {tabValue === 1 && (
                <Button 
                  variant="outlined" 
                  startIcon={<CheckCircleIcon />} 
                  onClick={handleMarkAllAsRead}
                  sx={{ mr: 1 }}
                >
                  全部标记为已读
                </Button>
              )}
              <Button 
                variant="outlined" 
                color="error" 
                startIcon={<DeleteSweepIcon />} 
                onClick={openDeleteAllConfirm}
              >
                清空{tabValue === 1 ? '未读' : tabValue === 2 ? '已读' : '所有'}通知
              </Button>
            </>
          )}
        </Box>
      </Box>

      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          indicatorColor="primary"
          textColor="primary"
          variant="fullWidth"
        >
          <Tab label="全部通知" />
          <Tab label="未读通知" />
          <Tab label="已读通知" />
        </Tabs>
      </Paper>

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 5 }}>
          <CircularProgress />
        </Box>
      ) : notifications.length === 0 ? (
        <Paper sx={{ p: 5, textAlign: 'center' }}>
          <NotificationsIcon sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">
            暂无{tabValue === 1 ? '未读' : tabValue === 2 ? '已读' : ''}通知
          </Typography>
        </Paper>
      ) : (
        <Paper>
          <List sx={{ p: 0 }}>
            {notifications.map((notification) => (
              <React.Fragment key={notification.id}>
                <ListItem
                  alignItems="flex-start"
                  sx={{
                    bgcolor: notification.status === 'unread' ? 'rgba(25, 118, 210, 0.08)' : 'transparent',
                    '&:hover': { bgcolor: 'rgba(0, 0, 0, 0.04)' },
                    cursor: 'pointer',
                    p: 2,
                  }}
                  secondaryAction={
                    <IconButton 
                      edge="end" 
                      onClick={(e) => {
                        e.stopPropagation();
                        openDeleteConfirm(notification);
                      }}
                    >
                      <DeleteIcon />
                    </IconButton>
                  }
                  onClick={() => handleNotificationClick(notification)}
                >
                  <Box sx={{ mr: 2, display: 'flex', alignItems: 'flex-start' }}>
                    {getNotificationIcon(notification.type)}
                  </Box>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Typography variant="subtitle1" component="span">
                          {notification.title}
                        </Typography>
                        <Chip 
                          size="small" 
                          label={getNotificationTypeText(notification.type)} 
                          color={notification.type === 'system' ? 'primary' : notification.type === 'task' ? 'success' : 'warning'}
                          sx={{ ml: 1 }}
                        />
                        {notification.status === 'unread' && (
                          <Chip size="small" label="未读" color="error" sx={{ ml: 1 }} />
                        )}
                      </Box>
                    }
                    secondary={
                      <React.Fragment>
                        <Typography
                          sx={{ display: 'block', mt: 1 }}
                          component="span"
                          variant="body2"
                          color="text.primary"
                        >
                          {notification.content}
                        </Typography>
                        <Typography
                          component="span"
                          variant="caption"
                          color="text.secondary"
                          sx={{ mt: 1, display: 'block' }}
                        >
                          创建时间: {formatDate(notification.created_at)}
                          {notification.read_at && ` | 阅读时间: ${formatDate(notification.read_at)}`}
                        </Typography>
                      </React.Fragment>
                    }
                  />
                </ListItem>
                <Divider component="li" />
              </React.Fragment>
            ))}
          </List>

          {totalPages > 1 && (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
              <Pagination 
                count={totalPages} 
                page={page} 
                onChange={handlePageChange} 
                color="primary" 
              />
            </Box>
          )}
        </Paper>
      )}

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
              <Box sx={{ mb: 2 }}>
                <Chip 
                  size="small" 
                  label={getNotificationTypeText(selectedNotification.type)} 
                  color={selectedNotification.type === 'system' ? 'primary' : selectedNotification.type === 'task' ? 'success' : 'warning'}
                  sx={{ mr: 1 }}
                />
                {selectedNotification.status === 'unread' ? (
                  <Chip size="small" label="未读" color="error" />
                ) : (
                  <Chip size="small" label="已读" color="default" />
                )}
              </Box>
              
              <Typography variant="body1" gutterBottom>
                {selectedNotification.content}
              </Typography>
              
              <Box sx={{ mt: 3 }}>
                <Typography variant="caption" color="text.secondary" display="block">
                  创建时间: {formatDate(selectedNotification.created_at)}
                </Typography>
                {selectedNotification.read_at && (
                  <Typography variant="caption" color="text.secondary" display="block">
                    阅读时间: {formatDate(selectedNotification.read_at)}
                  </Typography>
                )}
                {selectedNotification.related_id && selectedNotification.related_type && (
                  <Typography variant="caption" color="text.secondary" display="block">
                    关联: {selectedNotification.related_type} (ID: {selectedNotification.related_id})
                  </Typography>
                )}
              </Box>
            </DialogContent>
            <DialogActions>
              <Button onClick={handleCloseDetail}>关闭</Button>
              {selectedNotification.status === 'unread' && (
                <Button 
                  onClick={() => handleMarkAsRead(selectedNotification.id)}
                  color="primary"
                >
                  标记为已读
                </Button>
              )}
              <Button 
                onClick={() => {
                  handleCloseDetail();
                  openDeleteConfirm(selectedNotification);
                }}
                color="error"
              >
                删除
              </Button>
            </DialogActions>
          </>
        )}
      </Dialog>

      {/* 删除确认对话框 */}
      <Dialog open={confirmDeleteOpen} onClose={closeDeleteConfirm}>
        <DialogTitle>确认删除</DialogTitle>
        <DialogContent>
          <Typography>
            确定要删除这条通知吗？此操作无法撤销。
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={closeDeleteConfirm}>取消</Button>
          <Button onClick={handleDeleteNotification} color="error">
            删除
          </Button>
        </DialogActions>
      </Dialog>

      {/* 删除所有确认对话框 */}
      <Dialog open={confirmDeleteAllOpen} onClose={closeDeleteAllConfirm}>
        <DialogTitle>确认删除所有通知</DialogTitle>
        <DialogContent>
          <Typography>
            确定要删除{tabValue === 1 ? '所有未读' : tabValue === 2 ? '所有已读' : '所有'}通知吗？此操作无法撤销。
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={closeDeleteAllConfirm}>取消</Button>
          <Button onClick={handleDeleteAllNotifications} color="error">
            删除
          </Button>
        </DialogActions>
      </Dialog>

      {/* 提示消息 */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={3000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbarSeverity} sx={{ width: '100%' }}>
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default NotificationsPage;