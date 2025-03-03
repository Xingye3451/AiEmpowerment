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
} from '@mui/material';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { ADMIN_API } from '../config/api';

interface User {
  id: number;
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

      await axios.put(
        ADMIN_API.UPDATE_USER(selectedUser.id),
        updateData
      );
      setSuccess('用户信息更新成功');
      setEditDialog(false);
      setSelectedUser(null);
      setUserFormData({ username: '', email: '', password: '' });
      fetchUsers();
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

  return (
    <Container component="main" maxWidth={false} sx={{ p: 0 }}>
      <Paper elevation={3} sx={{ p: 4, mt: 8, mx: 0 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 4 }}>
          <Typography variant="h4" component="h1">
            管理员控制面板
          </Typography>
          <Box>
            <Button 
              variant="outlined" 
              color="primary" 
              onClick={() => setChangePasswordDialog(true)}
              sx={{ mr: 2 }}
            >
              修改密码
            </Button>
            <Button variant="outlined" color="primary" onClick={handleLogout}>
              退出登录
            </Button>
          </Box>
        </Box>

        <Box sx={{ display: 'flex' }}>
          {/* 左侧Tab导航 - 调整到最左侧 */}
          <Box sx={{ 
            width: '200px', 
            borderRight: 1, 
            borderColor: 'divider', 
            pr: 2,
            position: 'sticky',
            left: 0,
            bgcolor: 'background.paper',
            zIndex: 1,
          }}>
            <Tabs
              orientation="vertical"
              variant="scrollable"
              value={currentTab}
              onChange={handleTabChange}
              sx={{
                '& .MuiTab-root': {
                  minHeight: 48,
                  justifyContent: 'flex-start',
                  textAlign: 'left',
                  pl: 2,
                },
              }}
            >
              <Tab label="用户管理" />
              {/* 后续可以在这里添加更多的tab */}
            </Tabs>
          </Box>

          {/* 右侧内容区域 - 增加左侧间距 */}
          <Box sx={{ flex: 1, pl: 4 }}>
            {error && (
              <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
                {error}
              </Alert>
            )}
            {success && (
              <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>
                {success}
              </Alert>
            )}

            {/* Tab内容区域 */}
            <Box sx={{ mt: 2 }}>
              {currentTab === 0 && (
                <>
                  <Box sx={{ mb: 2 }}>
                    <Button
                      variant="contained"
                      color="primary"
                      onClick={() => setCreateDialog(true)}
                    >
                      创建用户
                    </Button>
                  </Box>

                  <TableContainer>
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell>ID</TableCell>
                          <TableCell>用户名</TableCell>
                          <TableCell>邮箱</TableCell>
                          <TableCell>角色</TableCell>
                          <TableCell>状态</TableCell>
                          <TableCell>最后登录</TableCell>
                          <TableCell>操作</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {users.map((user) => (
                          <TableRow 
                            key={user.id}
                            sx={{ 
                              '& > td': { 
                                py: 2 // 增加行高
                              }
                            }}
                          >
                            <TableCell>{user.id}</TableCell>
                            <TableCell>{user.username}</TableCell>
                            <TableCell>{user.email}</TableCell>
                            <TableCell>
                              {user.role === 'admin' ? '管理员' : '普通用户'}
                            </TableCell>
                            <TableCell>
                              <Box
                                sx={{
                                  display: 'inline-block',
                                  px: 2,
                                  py: 0.5,
                                  borderRadius: 1,
                                  backgroundColor: user.is_active ? 'success.light' : 'error.light',
                                  color: '#fff'
                                }}
                              >
                                {user.is_active ? '活跃' : '禁用'}
                              </Box>
                            </TableCell>
                            <TableCell>
                              {user.last_login ? new Date(user.last_login).toLocaleString() : '从未登录'}
                            </TableCell>
                            <TableCell>
                              <Box sx={{ display: 'flex', gap: 1 }}>
                                {user.role !== 'admin' && (
                                  <>
                                    <Button
                                      variant="outlined"
                                      size="small"
                                      color={user.is_active ? 'error' : 'primary'}
                                      onClick={() => handleToggleStatus(user)}
                                    >
                                      {user.is_active ? '禁用' : '启用'}
                                    </Button>
                                    <Button
                                      variant="outlined"
                                      size="small"
                                      onClick={() => handleOpenResetDialog(user)}
                                    >
                                      重置密码
                                    </Button>
                                    <Button
                                      variant="outlined"
                                      size="small"
                                      onClick={() => handleOpenEditDialog(user)}
                                    >
                                      编辑
                                    </Button>
                                    <Button
                                      variant="outlined"
                                      size="small"
                                      color="error"
                                      onClick={() => handleDeleteUser(user)}
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

      {/* 重置密码对话框 */}
      <Dialog open={resetDialog} onClose={() => setResetDialog(false)}>
        <DialogTitle>重置用户密码</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="新密码"
            type="password"
            fullWidth
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setResetDialog(false)}>取消</Button>
          <Button onClick={handleResetPassword} variant="contained" color="primary">
            确认重置
          </Button>
        </DialogActions>
      </Dialog>

      {/* 创建用户对话框 */}
      <Dialog open={createDialog} onClose={() => setCreateDialog(false)}>
        <DialogTitle>创建新用户</DialogTitle>
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
          <TextField
            margin="dense"
            label="密码"
            type="password"
            fullWidth
            required
            value={userFormData.password}
            onChange={(e) => setUserFormData({ ...userFormData, password: e.target.value })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialog(false)}>取消</Button>
          <Button onClick={handleCreateUser} variant="contained" color="primary">
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