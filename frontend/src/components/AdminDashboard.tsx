import React, { useEffect, useState } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Tabs,
  Tab,
  useTheme,
  alpha,
  Grid,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  AppBar,
  Toolbar,
  IconButton,
  Avatar,
  Divider,
  useMediaQuery,
  Badge,
  CssBaseline,
  Menu,
  MenuItem,
  ListSubheader,
  Collapse,
  Tooltip,
  Switch,
  FormControlLabel,
} from '@mui/material';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { ADMIN_API } from '../config/api';
import DashboardIcon from '@mui/icons-material/Dashboard';
import PeopleIcon from '@mui/icons-material/People';
import SettingsIcon from '@mui/icons-material/Settings';
import Logo from './Logo';

interface User {
  id: string;
  username: string;
  email: string;
  is_active: boolean;
  role: string;
  last_login: string;
}

interface UserFormData {
  username: string;
  email: string;
  password?: string;
}

const AdminDashboard = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [resetDialog, setResetDialog] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [newPassword, setNewPassword] = useState('');
  const [createDialog, setCreateDialog] = useState(false);
  const [editDialog, setEditDialog] = useState(false);
  const [userFormData, setUserFormData] = useState<UserFormData>({
    username: '',
    email: '',
    password: '',
  });
  const [currentTab, setCurrentTab] = useState(0);
  const [changePasswordDialog, setChangePasswordDialog] = useState(false);
  const [passwordData, setPasswordData] = useState({
    old_password: '',
    new_password: '',
  });
  const navigate = useNavigate();

  useEffect(() => {
    // 在组件加载时设置全局默认headers
    const token = localStorage.getItem('adminToken');
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await axios.get(ADMIN_API.USERS);
      setUsers(response.data);
    } catch (error: any) {
      setError(error.response?.data?.detail || '获取用户列表失败');
      if (error.response?.status === 401) {
        localStorage.removeItem('adminToken');
        delete axios.defaults.headers.common['Authorization'];
        navigate('/admin/login');
      }
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('adminToken');
    delete axios.defaults.headers.common['Authorization'];
    navigate('/admin/login');
  };

  // 其他方法中不再需要手动设置header，因为已经设置了全局默认值
  const handleCreateUser = async () => {
    try {
      await axios.post(ADMIN_API.USERS, userFormData);
      setSuccess('用户创建成功');
      setCreateDialog(false);
      setUserFormData({ username: '', email: '', password: '' });
      fetchUsers();
    } catch (error: any) {
      setError(error.response?.data?.detail || '创建用户失败');
    }
  };

  const handleEditUser = async () => {
    if (!selectedUser) return;

    try {
      const updateData = {
        username: userFormData.username,
        email: userFormData.email,
      };

      const response = await axios.put(
        ADMIN_API.UPDATE_USER(selectedUser.id),
        updateData
      );
      
      // 更新本地用户列表，避免重新获取
      const updatedUser = response.data;
      setUsers(users.map(user => 
        user.id === selectedUser.id ? updatedUser : user
      ));
      
      setSuccess('用户信息更新成功');
      setEditDialog(false);
      setSelectedUser(null);
      setUserFormData({ username: '', email: '', password: '' });
      
      // 确保获取最新数据
      await fetchUsers();
    } catch (error: any) {
      setError(error.response?.data?.detail || '更新用户信息失败');
    }
  };

  const handleToggleStatus = async (user: User) => {
    try {
      await axios.put(ADMIN_API.USER_STATUS(user.id));
      setSuccess(`已${user.is_active ? '禁用' : '启用'}用户 ${user.username}`);
      fetchUsers();
    } catch (error: any) {
      setError(error.response?.data?.detail || '更改用户状态失败');
    }
  };

  const handleDeleteUser = async (user: User) => {
    if (!window.confirm(`确定要删除用户 ${user.username} 吗？`)) {
      return;
    }

    try {
      await axios.delete(ADMIN_API.DELETE_USER(user.id));
      setSuccess(`已删除用户 ${user.username}`);
      fetchUsers();
    } catch (error: any) {
      setError(error.response?.data?.detail || '删除用户失败');
    }
  };

  const handleOpenResetDialog = (user: User) => {
    setSelectedUser(user);
    setResetDialog(true);
    setNewPassword('');
  };

  const handleResetPassword = async () => {
    if (!selectedUser || !newPassword) return;

    try {
      await axios.put(
        ADMIN_API.USER_PASSWORD_RESET(selectedUser.id),
        { new_password: newPassword }
      );
      setSuccess(`已重置用户 ${selectedUser.username} 的密码`);
      setResetDialog(false);
      setSelectedUser(null);
      setNewPassword('');
    } catch (error: any) {
      setError(error.response?.data?.detail || '重置密码失败');
    }
  };

  const handleOpenEditDialog = (user: User) => {
    setSelectedUser(user);
    setUserFormData({
      username: user.username,
      email: user.email,
    });
    setEditDialog(true);
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  const handleChangePassword = async () => {
    try {
      await axios.put(
        ADMIN_API.CHANGE_PASSWORD,
        passwordData
      );
      setSuccess('密码修改成功');
      setChangePasswordDialog(false);
      setPasswordData({ old_password: '', new_password: '' });
    } catch (error: any) {
      setError(error.response?.data?.detail || '修改密码失败');
    }
  };

  // 系统设置组件
  const SystemSettings = () => {
    const [settings, setSettings] = useState<any>({
      uploadDir: '',
      maxUploadSize: 0,
      databaseUrl: '',
      comfyuiUrl: '',
      // 其他设置...
    });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    useEffect(() => {
      // 获取系统设置
      fetchSettings();
    }, []);

    const fetchSettings = async () => {
      try {
        setLoading(true);
        const response = await axios.get('/api/admin/settings');
        setSettings(response.data);
      } catch (error) {
        console.error('获取系统设置失败:', error);
        setError('获取系统设置失败');
      } finally {
        setLoading(false);
      }
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const { name, value } = e.target;
      setSettings({
        ...settings,
        [name]: value
      });
    };

    const handleSave = async () => {
      try {
        setLoading(true);
        setError('');
        setSuccess('');
        
        await axios.post('/api/admin/settings', settings);
        setSuccess('设置保存成功');
      } catch (error) {
        console.error('保存设置失败:', error);
        setError('保存设置失败');
      } finally {
        setLoading(false);
      }
    };

    return (
      <Paper elevation={3} sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          系统设置
        </Typography>
        <Divider sx={{ mb: 3 }} />
        
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}
        
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="上传目录"
              name="uploadDir"
              value={settings.uploadDir}
              onChange={handleChange}
              margin="normal"
              helperText="文件上传的存储目录"
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="最大上传大小 (MB)"
              name="maxUploadSize"
              type="number"
              value={settings.maxUploadSize}
              onChange={handleChange}
              margin="normal"
              helperText="允许上传的最大文件大小 (MB)"
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="数据库URL"
              name="databaseUrl"
              value={settings.databaseUrl}
              onChange={handleChange}
              margin="normal"
              helperText="数据库连接URL"
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="ComfyUI URL"
              name="comfyuiUrl"
              value={settings.comfyuiUrl}
              onChange={handleChange}
              margin="normal"
              helperText="ComfyUI服务的URL，例如: http://127.0.0.1:8188"
            />
          </Grid>
          {/* 其他设置字段 */}
        </Grid>
        
        <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
          <Button 
            variant="contained" 
            onClick={handleSave}
            disabled={loading}
          >
            保存设置
          </Button>
        </Box>
      </Paper>
    );
  };

  return (
    <Container component="main" maxWidth={false} sx={{ p: 0 }}>
      <Paper 
        elevation={3} 
        sx={{ 
          p: 4, 
          mt: 8, 
          mx: 0,
          minHeight: 'calc(100vh - 100px)',
          backgroundColor: '#f8f9fa'
        }}
      >
        <Box sx={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          mb: 4,
          borderBottom: '2px solid',
          borderColor: '#3f51b5',
          pb: 2
        }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Logo 
              sx={{ 
                width: 48, 
                height: 48, 
                mr: 2,
                color: '#3f51b5',
                background: 'linear-gradient(135deg, #3f51b5 0%, #757de8 100%)',
                padding: '8px',
                borderRadius: '12px',
                boxShadow: '0 4px 8px rgba(63, 81, 181, 0.2)',
                animation: 'float 3s ease-in-out infinite',
                '@keyframes float': {
                  '0%': {
                    transform: 'translateY(0px)',
                  },
                  '50%': {
                    transform: 'translateY(-6px)',
                  },
                  '100%': {
                    transform: 'translateY(0px)',
                  },
                },
              }} 
            />
            <Typography 
              variant="h4" 
              component="h1"
              sx={{
                fontWeight: 700,
                background: 'linear-gradient(45deg, #3f51b5 30%, #757de8 90%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent'
              }}
            >
              管理员控制面板
            </Typography>
          </Box>
          <Box>
            <Button 
              variant="contained" 
              onClick={() => setChangePasswordDialog(true)}
              sx={{ 
                mr: 2,
                background: 'linear-gradient(45deg, #3f51b5 30%, #757de8 90%)',
                boxShadow: '0 3px 5px 2px rgba(63, 81, 181, 0.3)',
                '&:hover': {
                  background: 'linear-gradient(45deg, #303f9f 30%, #5c6bc0 90%)',
                }
              }}
            >
              修改密码
            </Button>
            <Button 
              variant="outlined"
              onClick={handleLogout}
              sx={{
                borderColor: '#3f51b5',
                color: '#3f51b5',
                '&:hover': {
                  borderColor: '#303f9f',
                  backgroundColor: alpha('#3f51b5', 0.1)
                }
              }}
            >
              退出登录
            </Button>
          </Box>
        </Box>

        <Box sx={{ display: 'flex' }}>
          {/* 左侧导航栏优化 */}
          <Box sx={{ 
            width: '240px', 
            borderRight: '1px solid',
            borderColor: 'divider',
            pr: 2,
            position: 'sticky',
            left: 0,
            bgcolor: '#fff',
            zIndex: 1,
            height: 'calc(100vh - 200px)',
            boxShadow: '2px 0 5px rgba(0,0,0,0.05)',
            borderRadius: '10px 0 0 10px'
          }}>
            <Tabs
              orientation="vertical"
              variant="scrollable"
              value={currentTab}
              onChange={handleTabChange}
              sx={{
                '& .MuiTab-root': {
                  minHeight: 60,
                  justifyContent: 'flex-start',
                  textAlign: 'left',
                  pl: 3,
                  fontSize: '1rem',
                  fontWeight: 500,
                  color: 'text.secondary',
                  '&.Mui-selected': {
                    color: '#3498db',
                    backgroundColor: alpha('#3498db', 0.08),
                    borderRight: '3px solid',
                    borderColor: '#3498db'
                  },
                  '&:hover': {
                    backgroundColor: alpha('#3498db', 0.04),
                    color: '#3498db'
                  }
                }
              }}
            >
              <Tab 
                icon={<DashboardIcon />} 
                iconPosition="start" 
                label="仪表盘" 
                sx={{ mb: 1 }}
              />
              <Tab 
                icon={<PeopleIcon />} 
                iconPosition="start" 
                label="用户管理" 
                sx={{ mb: 1 }}
              />
              <Tab 
                icon={<SettingsIcon />} 
                iconPosition="start" 
                label="系统设置" 
                sx={{ mb: 1 }}
              />
            </Tabs>
          </Box>

          {/* 右侧内容区域优化 */}
          <Box sx={{ flex: 1, pl: 4 }}>
            {error && (
              <Alert 
                severity="error" 
                sx={{ 
                  mb: 2,
                  borderRadius: 2,
                  boxShadow: '0 2px 8px rgba(244, 67, 54, 0.2)'
                }} 
                onClose={() => setError('')}
              >
                {error}
              </Alert>
            )}
            {success && (
              <Alert 
                severity="success" 
                sx={{ 
                  mb: 2,
                  borderRadius: 2,
                  boxShadow: '0 2px 8px rgba(76, 175, 80, 0.2)'
                }} 
                onClose={() => setSuccess('')}
              >
                {success}
              </Alert>
            )}

            <Box sx={{ mt: 2 }}>
              {currentTab === 1 && (
                <>
                  <Box sx={{ mb: 3 }}>
                    <Button
                      variant="contained"
                      onClick={() => setCreateDialog(true)}
                      sx={{
                        background: 'linear-gradient(45deg, #3f51b5 30%, #757de8 90%)',
                        boxShadow: '0 3px 5px 2px rgba(63, 81, 181, 0.3)',
                        borderRadius: '20px',
                        px: 4,
                        py: 1,
                        '&:hover': {
                          background: 'linear-gradient(45deg, #303f9f 30%, #5c6bc0 90%)',
                        }
                      }}
                    >
                      + 创建用户
                    </Button>
                  </Box>

                  <TableContainer 
                    component={Paper}
                    sx={{ 
                      borderRadius: 2,
                      boxShadow: '0 0 10px rgba(0,0,0,0.1)',
                      overflow: 'hidden'
                    }}
                  >
                    <Table>
                      <TableHead>
                        <TableRow sx={{ backgroundColor: alpha('#3498db', 0.05) }}>
                          <TableCell sx={{ fontWeight: 700, color: 'text.primary' }}>用户名</TableCell>
                          <TableCell sx={{ fontWeight: 700, color: 'text.primary' }}>邮箱</TableCell>
                          <TableCell sx={{ fontWeight: 700, color: 'text.primary' }}>角色</TableCell>
                          <TableCell sx={{ fontWeight: 700, color: 'text.primary' }}>状态</TableCell>
                          <TableCell sx={{ fontWeight: 700, color: 'text.primary' }}>最后登录</TableCell>
                          <TableCell sx={{ fontWeight: 700, color: 'text.primary' }}>操作</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {users.map((user) => (
                          <TableRow 
                            key={user.id}
                            sx={{ 
                              '&:hover': {
                                backgroundColor: alpha('#3498db', 0.02)
                              },
                              '& > td': { 
                                py: 2,
                                fontSize: '0.95rem'
                              }
                            }}
                          >
                            <TableCell sx={{ fontWeight: 500 }}>{user.username}</TableCell>
                            <TableCell>{user.email}</TableCell>
                            <TableCell>
                              <Typography
                                sx={{
                                  display: 'inline-block',
                                  px: 2,
                                  py: 0.5,
                                  borderRadius: '15px',
                                  backgroundColor: user.role === 'admin' ? '#3f51b5' : '#9fa8da',
                                  color: '#fff',
                                  fontSize: '0.85rem',
                                  fontWeight: 500
                                }}
                              >
                                {user.role === 'admin' ? '管理员' : '普通用户'}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Typography
                                sx={{
                                  display: 'inline-block',
                                  px: 2,
                                  py: 0.5,
                                  borderRadius: '15px',
                                  backgroundColor: user.is_active ? '#2ecc71' : '#e74c3c',
                                  color: '#fff',
                                  fontSize: '0.85rem',
                                  fontWeight: 500
                                }}
                              >
                                {user.is_active ? '活跃' : '禁用'}
                              </Typography>
                            </TableCell>
                            <TableCell>{user.last_login ? new Date(user.last_login).toLocaleString() : '从未登录'}</TableCell>
                            <TableCell>
                              <Box sx={{ display: 'flex', gap: 1 }}>
                                {user.role !== 'admin' && (
                                  <>
                                    <Button
                                      variant="outlined"
                                      size="small"
                                      color={user.is_active ? 'error' : 'primary'}
                                      onClick={() => handleToggleStatus(user)}
                                      sx={{
                                        borderRadius: '15px',
                                        textTransform: 'none',
                                        minWidth: '80px',
                                        borderColor: user.is_active ? '#e74c3c' : '#3498db',
                                        color: user.is_active ? '#e74c3c' : '#3498db',
                                        '&:hover': {
                                          borderColor: user.is_active ? '#c0392b' : '#2980b9',
                                          backgroundColor: user.is_active ? alpha('#e74c3c', 0.1) : alpha('#3498db', 0.1)
                                        }
                                      }}
                                    >
                                      {user.is_active ? '禁用' : '启用'}
                                    </Button>
                                    <Button
                                      variant="outlined"
                                      size="small"
                                      onClick={() => handleOpenResetDialog(user)}
                                      sx={{
                                        borderRadius: '15px',
                                        textTransform: 'none',
                                        minWidth: '80px',
                                        borderColor: '#3f51b5',
                                        color: '#3f51b5',
                                        '&:hover': {
                                          borderColor: '#303f9f',
                                          backgroundColor: alpha('#3f51b5', 0.1)
                                        }
                                      }}
                                    >
                                      重置密码
                                    </Button>
                                    <Button
                                      variant="outlined"
                                      size="small"
                                      onClick={() => handleOpenEditDialog(user)}
                                      sx={{
                                        borderRadius: '15px',
                                        textTransform: 'none',
                                        minWidth: '80px',
                                        borderColor: '#3f51b5',
                                        color: '#3f51b5',
                                        '&:hover': {
                                          borderColor: '#303f9f',
                                          backgroundColor: alpha('#3f51b5', 0.1)
                                        }
                                      }}
                                    >
                                      编辑
                                    </Button>
                                    <Button
                                      variant="outlined"
                                      size="small"
                                      color="error"
                                      onClick={() => handleDeleteUser(user)}
                                      sx={{
                                        borderRadius: '15px',
                                        textTransform: 'none',
                                        minWidth: '80px',
                                        borderColor: '#e74c3c',
                                        color: '#e74c3c',
                                        '&:hover': {
                                          borderColor: '#c0392b',
                                          backgroundColor: alpha('#e74c3c', 0.1)
                                        }
                                      }}
                                    >
                                      删除
                                    </Button>
                                  </>
                                )}
                              </Box>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </>
              )}
            </Box>
          </Box>
        </Box>
      </Paper>

      {/* Dialog styles optimization */}
      <Dialog 
        open={resetDialog} 
        onClose={() => setResetDialog(false)}
        PaperProps={{
          sx: {
            borderRadius: 2,
            boxShadow: '0 8px 32px rgba(0,0,0,0.1)'
          }
        }}
      >
        <DialogTitle sx={{ 
          borderBottom: '2px solid',
          borderColor: '#3f51b5',
          pb: 2,
          '& .MuiTypography-root': {
            fontWeight: 700
          }
        }}>
          重置用户密码
        </DialogTitle>
        <DialogContent sx={{ mt: 2 }}>
          <TextField
            autoFocus
            margin="dense"
            label="新密码"
            type="password"
            fullWidth
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: 2,
                '&.Mui-focused fieldset': {
                  borderColor: '#3f51b5'
                }
              }
            }}
          />
        </DialogContent>
        <DialogActions sx={{ p: 2, pt: 0 }}>
          <Button 
            onClick={() => setResetDialog(false)}
            sx={{
              borderRadius: '20px',
              px: 3,
              color: '#3f51b5'
            }}
          >
            取消
          </Button>
          <Button 
            onClick={handleResetPassword} 
            variant="contained"
            sx={{
              borderRadius: '20px',
              px: 3,
              background: 'linear-gradient(45deg, #3f51b5 30%, #757de8 90%)',
              '&:hover': {
                background: 'linear-gradient(45deg, #303f9f 30%, #5c6bc0 90%)',
              }
            }}
          >
            确认重置
          </Button>
        </DialogActions>
      </Dialog>

      {/* 创建用户对话框 */}
      <Dialog 
        open={createDialog} 
        onClose={() => setCreateDialog(false)}
        PaperProps={{
          sx: {
            borderRadius: 2,
            boxShadow: '0 8px 32px rgba(0,0,0,0.1)'
          }
        }}
      >
        <DialogTitle sx={{ 
          borderBottom: '2px solid',
          borderColor: '#3498db',
          pb: 2,
          '& .MuiTypography-root': {
            fontWeight: 700
          }
        }}>
          创建新用户
        </DialogTitle>
        <DialogContent sx={{ mt: 2 }}>
          <TextField
            margin="dense"
            label="用户名"
            fullWidth
            required
            value={userFormData.username}
            onChange={(e) => setUserFormData({ ...userFormData, username: e.target.value })}
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: 2,
                '&.Mui-focused fieldset': {
                  borderColor: '#3498db'
                }
              }
            }}
          />
          <TextField
            margin="dense"
            label="邮箱"
            type="email"
            fullWidth
            required
            value={userFormData.email}
            onChange={(e) => setUserFormData({ ...userFormData, email: e.target.value })}
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: 2,
                '&.Mui-focused fieldset': {
                  borderColor: '#3498db'
                }
              }
            }}
          />
          <TextField
            margin="dense"
            label="密码"
            type="password"
            fullWidth
            required
            value={userFormData.password}
            onChange={(e) => setUserFormData({ ...userFormData, password: e.target.value })}
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: 2,
                '&.Mui-focused fieldset': {
                  borderColor: '#3498db'
                }
              }
            }}
          />
        </DialogContent>
        <DialogActions sx={{ p: 2, pt: 0 }}>
          <Button 
            onClick={() => setCreateDialog(false)}
            sx={{
              borderRadius: '20px',
              px: 3,
              color: '#3498db'
            }}
          >
            取消
          </Button>
          <Button 
            onClick={handleCreateUser} 
            variant="contained"
            sx={{
              borderRadius: '20px',
              px: 3,
              background: 'linear-gradient(45deg, #3498db 30%, #2980b9 90%)',
              '&:hover': {
                background: 'linear-gradient(45deg, #2980b9 30%, #2573a7 90%)',
              }
            }}
          >
            创建
          </Button>
        </DialogActions>
      </Dialog>

      {/* 编辑用户对话框 */}
      <Dialog open={editDialog} onClose={() => setEditDialog(false)}>
        <DialogTitle>编辑用户信息</DialogTitle>
        <DialogContent>
          <TextField
            margin="dense"
            label="用户名"
            fullWidth
            required
            value={userFormData.username}
            onChange={(e) => setUserFormData({ ...userFormData, username: e.target.value })}
          />
          <TextField
            margin="dense"
            label="邮箱"
            type="email"
            fullWidth
            required
            value={userFormData.email}
            onChange={(e) => setUserFormData({ ...userFormData, email: e.target.value })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialog(false)}>取消</Button>
          <Button onClick={handleEditUser} variant="contained" color="primary">
            保存
          </Button>
        </DialogActions>
      </Dialog>

      {/* 管理员修改密码对话框 */}
      <Dialog open={changePasswordDialog} onClose={() => setChangePasswordDialog(false)}>
        <DialogTitle>修改密码</DialogTitle>
        <DialogContent>
          <TextField
            margin="dense"
            label="旧密码"
            type="password"
            fullWidth
            required
            value={passwordData.old_password}
            onChange={(e) => setPasswordData({ ...passwordData, old_password: e.target.value })}
          />
          <TextField
            margin="dense"
            label="新密码"
            type="password"
            fullWidth
            required
            value={passwordData.new_password}
            onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setChangePasswordDialog(false)}>取消</Button>
          <Button onClick={handleChangePassword} variant="contained" color="primary">
            确认修改
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default AdminDashboard;