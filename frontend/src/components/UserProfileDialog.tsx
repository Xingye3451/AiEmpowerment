import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Grid,
  Avatar,
  Typography,
  Box,
  Divider,
  IconButton,
  Alert,
  CircularProgress,
  Snackbar
} from '@mui/material';
import {
  Edit as EditIcon,
  Save as SaveIcon,
  Close as CloseIcon,
  Person as PersonIcon,
  Email as EmailIcon,
  Phone as PhoneIcon,
  LocationOn as LocationIcon,
  Work as WorkIcon,
  CalendarToday as CalendarIcon
} from '@mui/icons-material';
import axios from 'axios';
import { USER_API } from '../config/api';

interface UserData {
  id: string;
  username: string;
  email: string;
  role: string;
  last_login?: string;
  last_active?: string;
  created_at: string;
  updated_at: string;
  preferences?: any;
  phone?: string;
  location?: string;
  job_title?: string;
}

interface UserProfileDialogProps {
  open: boolean;
  onClose: () => void;
  userData: UserData | null;
  onUserDataUpdate?: (userData: UserData) => void;
}

const UserProfileDialog: React.FC<UserProfileDialogProps> = ({
  open,
  onClose,
  userData,
  onUserDataUpdate
}) => {
  const [editMode, setEditMode] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [formData, setFormData] = useState<Partial<UserData>>({});

  // 当对话框打开或用户数据变化时，重置表单数据
  React.useEffect(() => {
    if (userData) {
      setFormData({
        username: userData.username,
        email: userData.email,
        phone: userData.phone || '',
        location: userData.location || '',
        job_title: userData.job_title || ''
      });
    }
  }, [userData, open]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
  };

  const handleSave = async () => {
    if (!userData) return;
    
    try {
      setLoading(true);
      setError('');
      
      const token = localStorage.getItem('token');
      const response = await axios.put(
        `${USER_API.PROFILE}`,
        formData,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          }
        }
      );
      
      // 确保响应数据是对象
      if (response.data && typeof response.data === 'object') {
        setSuccess('个人资料更新成功');
        setEditMode(false);
        
        // 如果提供了更新回调，则调用它
        if (onUserDataUpdate) {
          onUserDataUpdate(response.data);
        }
      } else {
        console.error('用户资料数据格式不正确:', response.data);
        setError('更新个人资料失败：服务器返回的数据格式不正确');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || '更新个人资料失败');
      console.error('更新个人资料失败:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCloseSnackbar = () => {
    setSuccess('');
    setError('');
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return '未知';
    try {
      const date = new Date(dateString);
      return date.toLocaleString('zh-CN');
    } catch (e) {
      return dateString;
    }
  };

  return (
    <>
      <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="h6">个人资料</Typography>
            <Box>
              {!editMode ? (
                <IconButton onClick={() => setEditMode(true)} color="primary">
                  <EditIcon />
                </IconButton>
              ) : (
                <IconButton onClick={() => setEditMode(false)} color="default">
                  <CloseIcon />
                </IconButton>
              )}
              <IconButton onClick={onClose}>
                <CloseIcon />
              </IconButton>
            </Box>
          </Box>
        </DialogTitle>
        
        <DialogContent dividers>
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
            </Box>
          ) : (
            <Grid container spacing={3}>
              {/* 头像和基本信息 */}
              <Grid item xs={12} sx={{ textAlign: 'center', mb: 2 }}>
                <Avatar
                  sx={{ width: 100, height: 100, mx: 'auto', mb: 2, fontSize: '2.5rem' }}
                >
                  {userData?.username?.charAt(0)?.toUpperCase() || 'U'}
                </Avatar>
                <Typography variant="h5">{userData?.username}</Typography>
                <Typography variant="body2" color="text.secondary">
                  {userData?.role === 'admin' ? '管理员' : userData?.role === 'editor' ? '编辑' : '普通用户'}
                </Typography>
              </Grid>
              
              <Grid item xs={12}>
                <Divider sx={{ my: 1 }}>
                  <Typography variant="subtitle2" color="text.secondary">基本信息</Typography>
                </Divider>
              </Grid>
              
              {/* 可编辑字段 */}
              <Grid item xs={12} md={6}>
                <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
                  <PersonIcon sx={{ mr: 1, color: 'primary.main' }} />
                  {editMode ? (
                    <TextField
                      fullWidth
                      label="用户名"
                      name="username"
                      value={formData.username || ''}
                      onChange={handleInputChange}
                      size="small"
                      variant="outlined"
                    />
                  ) : (
                    <Box>
                      <Typography variant="body2" color="text.secondary">用户名</Typography>
                      <Typography variant="body1">{userData?.username}</Typography>
                    </Box>
                  )}
                </Box>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
                  <EmailIcon sx={{ mr: 1, color: 'primary.main' }} />
                  {editMode ? (
                    <TextField
                      fullWidth
                      label="邮箱"
                      name="email"
                      value={formData.email || ''}
                      onChange={handleInputChange}
                      size="small"
                      variant="outlined"
                    />
                  ) : (
                    <Box>
                      <Typography variant="body2" color="text.secondary">邮箱</Typography>
                      <Typography variant="body1">{userData?.email}</Typography>
                    </Box>
                  )}
                </Box>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
                  <PhoneIcon sx={{ mr: 1, color: 'primary.main' }} />
                  {editMode ? (
                    <TextField
                      fullWidth
                      label="电话"
                      name="phone"
                      value={formData.phone || ''}
                      onChange={handleInputChange}
                      size="small"
                      variant="outlined"
                    />
                  ) : (
                    <Box>
                      <Typography variant="body2" color="text.secondary">电话</Typography>
                      <Typography variant="body1">{userData?.phone || '未设置'}</Typography>
                    </Box>
                  )}
                </Box>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
                  <LocationIcon sx={{ mr: 1, color: 'primary.main' }} />
                  {editMode ? (
                    <TextField
                      fullWidth
                      label="地区"
                      name="location"
                      value={formData.location || ''}
                      onChange={handleInputChange}
                      size="small"
                      variant="outlined"
                    />
                  ) : (
                    <Box>
                      <Typography variant="body2" color="text.secondary">地区</Typography>
                      <Typography variant="body1">{userData?.location || '未设置'}</Typography>
                    </Box>
                  )}
                </Box>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
                  <WorkIcon sx={{ mr: 1, color: 'primary.main' }} />
                  {editMode ? (
                    <TextField
                      fullWidth
                      label="职位"
                      name="job_title"
                      value={formData.job_title || ''}
                      onChange={handleInputChange}
                      size="small"
                      variant="outlined"
                    />
                  ) : (
                    <Box>
                      <Typography variant="body2" color="text.secondary">职位</Typography>
                      <Typography variant="body1">{userData?.job_title || '未设置'}</Typography>
                    </Box>
                  )}
                </Box>
              </Grid>
              
              <Grid item xs={12}>
                <Divider sx={{ my: 1 }}>
                  <Typography variant="subtitle2" color="text.secondary">账户信息</Typography>
                </Divider>
              </Grid>
              
              {/* 只读字段 */}
              <Grid item xs={12} md={6}>
                <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
                  <CalendarIcon sx={{ mr: 1, color: 'primary.main' }} />
                  <Box>
                    <Typography variant="body2" color="text.secondary">上次登录</Typography>
                    <Typography variant="body1">{formatDate(userData?.last_login)}</Typography>
                  </Box>
                </Box>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 2 }}>
                  <CalendarIcon sx={{ mr: 1, color: 'primary.main' }} />
                  <Box>
                    <Typography variant="body2" color="text.secondary">注册时间</Typography>
                    <Typography variant="body1">{formatDate(userData?.created_at)}</Typography>
                  </Box>
                </Box>
              </Grid>
              
              {error && (
                <Grid item xs={12}>
                  <Alert severity="error">{error}</Alert>
                </Grid>
              )}
            </Grid>
          )}
        </DialogContent>
        
        <DialogActions>
          {editMode ? (
            <>
              <Button onClick={() => setEditMode(false)}>取消</Button>
              <Button 
                onClick={handleSave} 
                variant="contained" 
                startIcon={<SaveIcon />}
                disabled={loading}
              >
                保存
              </Button>
            </>
          ) : (
            <Button onClick={onClose}>关闭</Button>
          )}
        </DialogActions>
      </Dialog>
      
      <Snackbar
        open={!!success}
        autoHideDuration={3000}
        onClose={handleCloseSnackbar}
        message={success}
      />
    </>
  );
};

export default UserProfileDialog; 