import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Button, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Dialog, DialogActions, DialogContent, DialogTitle, TextField, FormControl, InputLabel, Select, MenuItem,
  Tabs, Tab, IconButton, Chip, Grid, Snackbar, Alert, CircularProgress, Divider, Card, CardContent,
  CardActions, Tooltip, TablePagination, SelectChangeEvent
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Group as GroupIcon,
  Login as LoginIcon,
  Logout as LogoutIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon
} from '@mui/icons-material';
import axios from 'axios';
import { API_BASE_URL } from '../config';
import { SOCIAL_ACCOUNT_API } from '../config/api';

// 定义接口
interface SocialAccount {
  id: number;
  username: string;
  platform: string;
  status: string;
  last_login: string | null;
  created_at: string;
  updated_at: string;
}

interface AccountGroup {
  id: number;
  name: string;
  description: string;
  accounts: SocialAccount[];
  created_at: string;
  updated_at: string;
}

interface Platform {
  id: string;
  name: string;
  icon: string;
}

interface LoginAccount {
  username: string;
  password: string;
  platform: string;
  extra_data?: Record<string, any>;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

// 选项卡面板组件
function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const SocialAccountManager: React.FC = () => {
  // 状态管理
  const [tabValue, setTabValue] = useState(0);
  const [accounts, setAccounts] = useState<SocialAccount[]>([]);
  const [groups, setGroups] = useState<AccountGroup[]>([]);
  const [platforms, setPlatforms] = useState<Platform[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // 账号对话框状态
  const [accountDialogOpen, setAccountDialogOpen] = useState(false);
  const [accountFormData, setAccountFormData] = useState<LoginAccount>({
    username: '',
    password: '',
    platform: '',
    extra_data: {}
  });
  
  // 分组对话框状态
  const [groupDialogOpen, setGroupDialogOpen] = useState(false);
  const [groupFormData, setGroupFormData] = useState({
    name: '',
    description: '',
    account_ids: [] as number[]
  });
  const [editingGroupId, setEditingGroupId] = useState<number | null>(null);
  
  // 批量登录对话框状态
  const [batchLoginDialogOpen, setBatchLoginDialogOpen] = useState(false);
  const [batchLoginAccounts, setBatchLoginAccounts] = useState<LoginAccount[]>([]);
  const [loginInProgress, setLoginInProgress] = useState(false);
  
  // 分页状态
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  
  // 加载数据
  useEffect(() => {
    fetchAccounts();
    fetchGroups();
    fetchPlatforms();
  }, []);
  
  // 获取账号列表
  const fetchAccounts = async () => {
    setLoading(true);
    try {
      const response = await axios.get(SOCIAL_ACCOUNT_API.LIST, {
        withCredentials: true
      });
      setAccounts(response.data);
    } catch (error) {
      console.error('获取账号列表失败:', error);
      setError('获取账号列表失败');
    } finally {
      setLoading(false);
    }
  };
  
  // 获取分组列表
  const fetchGroups = async () => {
    try {
      const response = await axios.get(SOCIAL_ACCOUNT_API.GROUPS, {
        withCredentials: true
      });
      setGroups(response.data);
    } catch (error) {
      console.error('获取分组列表失败:', error);
      setError('获取分组列表失败');
    }
  };
  
  // 获取支持的平台列表
  const fetchPlatforms = async () => {
    try {
      const response = await axios.get(SOCIAL_ACCOUNT_API.PLATFORMS, {
        withCredentials: true
      });
      setPlatforms(response.data.platforms);
    } catch (error) {
      console.error('获取平台列表失败:', error);
      setError('获取平台列表失败');
    }
  };
  
  // 处理选项卡切换
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };
  
  // 处理账号表单变化
  const handleAccountFormChange = (e: React.ChangeEvent<HTMLInputElement | { name?: string; value: unknown }> | SelectChangeEvent<string>) => {
    const { name, value } = e.target;
    setAccountFormData({
      ...accountFormData,
      [name as string]: value
    });
  };
  
  // 处理分组表单变化
  const handleGroupFormChange = (e: React.ChangeEvent<HTMLInputElement | { name?: string; value: unknown }>) => {
    const { name, value } = e.target;
    setGroupFormData({
      ...groupFormData,
      [name as string]: value
    });
  };
  
  // 处理分组账号选择变化
  const handleGroupAccountsChange = (event: SelectChangeEvent<number[]>) => {
    setGroupFormData({
      ...groupFormData,
      account_ids: event.target.value as number[]
    });
  };
  
  // 打开添加账号对话框
  const openAddAccountDialog = () => {
    setAccountFormData({
      username: '',
      password: '',
      platform: '',
      extra_data: {}
    });
    setAccountDialogOpen(true);
  };
  
  // 打开添加分组对话框
  const openAddGroupDialog = () => {
    setGroupFormData({
      name: '',
      description: '',
      account_ids: []
    });
    setEditingGroupId(null);
    setGroupDialogOpen(true);
  };
  
  // 打开编辑分组对话框
  const openEditGroupDialog = (group: AccountGroup) => {
    setGroupFormData({
      name: group.name,
      description: group.description,
      account_ids: group.accounts.map(account => account.id)
    });
    setEditingGroupId(group.id);
    setGroupDialogOpen(true);
  };
  
  // 打开批量登录对话框
  const openBatchLoginDialog = () => {
    setBatchLoginAccounts([{
      username: '',
      password: '',
      platform: platforms.length > 0 ? platforms[0].id : ''
    }]);
    setBatchLoginDialogOpen(true);
  };
  
  // 添加批量登录账号
  const addBatchLoginAccount = () => {
    setBatchLoginAccounts([
      ...batchLoginAccounts,
      {
        username: '',
        password: '',
        platform: platforms.length > 0 ? platforms[0].id : ''
      }
    ]);
  };
  
  // 移除批量登录账号
  const removeBatchLoginAccount = (index: number) => {
    const newAccounts = [...batchLoginAccounts];
    newAccounts.splice(index, 1);
    setBatchLoginAccounts(newAccounts);
  };
  
  // 处理批量登录账号变化
  const handleBatchLoginAccountChange = (index: number, field: keyof LoginAccount, value: any) => {
    const newAccounts = [...batchLoginAccounts];
    newAccounts[index] = {
      ...newAccounts[index],
      [field]: value
    };
    setBatchLoginAccounts(newAccounts);
  };
  
  // 提交添加/编辑账号
  const submitAccountForm = async () => {
    setLoading(true);
    try {
      await axios.post(SOCIAL_ACCOUNT_API.LIST, accountFormData, {
        withCredentials: true
      });
      setSuccess('账号添加成功');
      setAccountDialogOpen(false);
      fetchAccounts();
    } catch (err) {
      setError('账号添加失败');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };
  
  // 提交添加/编辑分组
  const submitGroupForm = async () => {
    setLoading(true);
    try {
      if (editingGroupId) {
        // 编辑现有分组
        await axios.put(SOCIAL_ACCOUNT_API.GROUP_DETAIL(String(editingGroupId)), groupFormData, {
          withCredentials: true
        });
        setSuccess('分组更新成功');
      } else {
        // 添加新分组
        await axios.post(SOCIAL_ACCOUNT_API.GROUPS, groupFormData, {
          withCredentials: true
        });
        setSuccess('分组添加成功');
      }
      setGroupDialogOpen(false);
      fetchGroups();
    } catch (err) {
      setError('分组操作失败');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };
  
  // 删除账号
  const deleteAccount = async (accountId: number) => {
    if (!window.confirm('确定要删除此账号吗？')) return;
    
    setLoading(true);
    try {
      await axios.delete(SOCIAL_ACCOUNT_API.DELETE(String(accountId)), {
        withCredentials: true
      });
      setSuccess('账号删除成功');
      fetchAccounts();
    } catch (err) {
      setError('账号删除失败');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };
  
  // 删除分组
  const deleteGroup = async (groupId: number) => {
    if (!window.confirm('确定要删除此分组吗？')) return;
    
    setLoading(true);
    try {
      await axios.delete(SOCIAL_ACCOUNT_API.GROUP_DETAIL(String(groupId)), {
        withCredentials: true
      });
      setSuccess('分组删除成功');
      fetchGroups();
    } catch (err) {
      setError('分组删除失败');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };
  
  // 批量登录
  const submitBatchLogin = async () => {
    setLoginInProgress(true);
    try {
      const response = await axios.post(SOCIAL_ACCOUNT_API.BATCH_LOGIN, {
        accounts: batchLoginAccounts
      }, {
        withCredentials: true
      });
      
      setBatchLoginDialogOpen(false);
      setSuccess(`批量登录完成: ${response.data.results.filter((r: any) => r.success).length}个成功, ${response.data.results.filter((r: any) => !r.success).length}个失败`);
      fetchAccounts();
    } catch (err) {
      setError('批量登录失败');
      console.error(err);
    } finally {
      setLoginInProgress(false);
    }
  };
  
  // 处理分页变化
  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };
  
  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };
  
  // 获取平台名称
  const getPlatformName = (platformId: string) => {
    const platform = platforms.find(p => p.id === platformId);
    return platform ? platform.name : platformId;
  };
  
  // 获取状态标签
  const getStatusChip = (status: string) => {
    switch (status) {
      case 'active':
        return <Chip icon={<CheckCircleIcon />} label="活跃" color="success" size="small" />;
      case 'inactive':
        return <Chip icon={<ErrorIcon />} label="未登录" color="error" size="small" />;
      default:
        return <Chip label={status} size="small" />;
    }
  };
  
  // 格式化日期
  const formatDate = (dateString: string | null) => {
    if (!dateString) return '未知';
    return new Date(dateString).toLocaleString();
  };
  
  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="社交账号管理选项卡">
          <Tab label="账号管理" />
          <Tab label="分组管理" />
        </Tabs>
      </Box>
      
      {/* 账号管理选项卡 */}
      <TabPanel value={tabValue} index={0}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6">社交媒体账号</Typography>
          <Box>
            <Button 
              variant="outlined" 
              startIcon={<RefreshIcon />} 
              onClick={fetchAccounts}
              sx={{ mr: 1 }}
            >
              刷新
            </Button>
            <Button 
              variant="outlined" 
              startIcon={<LoginIcon />} 
              onClick={openBatchLoginDialog}
              sx={{ mr: 1 }}
            >
              批量登录
            </Button>
            <Button 
              variant="contained" 
              startIcon={<AddIcon />} 
              onClick={openAddAccountDialog}
            >
              添加账号
            </Button>
          </Box>
        </Box>
        
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>ID</TableCell>
                <TableCell>用户名</TableCell>
                <TableCell>平台</TableCell>
                <TableCell>状态</TableCell>
                <TableCell>最后登录</TableCell>
                <TableCell>创建时间</TableCell>
                <TableCell>操作</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading && accounts.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    <CircularProgress size={24} />
                  </TableCell>
                </TableRow>
              ) : accounts.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    暂无账号数据
                  </TableCell>
                </TableRow>
              ) : (
                accounts
                  .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                  .map((account) => (
                    <TableRow key={account.id}>
                      <TableCell>{account.id}</TableCell>
                      <TableCell>{account.username}</TableCell>
                      <TableCell>{getPlatformName(account.platform)}</TableCell>
                      <TableCell>{getStatusChip(account.status)}</TableCell>
                      <TableCell>{formatDate(account.last_login)}</TableCell>
                      <TableCell>{formatDate(account.created_at)}</TableCell>
                      <TableCell>
                        <IconButton size="small" onClick={() => deleteAccount(account.id)}>
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))
              )}
            </TableBody>
          </Table>
          <TablePagination
            rowsPerPageOptions={[5, 10, 25]}
            component="div"
            count={accounts.length}
            rowsPerPage={rowsPerPage}
            page={page}
            onPageChange={handleChangePage}
            onRowsPerPageChange={handleChangeRowsPerPage}
            labelRowsPerPage="每页行数:"
          />
        </TableContainer>
      </TabPanel>
      
      {/* 分组管理选项卡 */}
      <TabPanel value={tabValue} index={1}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6">账号分组</Typography>
          <Box>
            <Button 
              variant="outlined" 
              startIcon={<RefreshIcon />} 
              onClick={fetchGroups}
              sx={{ mr: 1 }}
            >
              刷新
            </Button>
            <Button 
              variant="contained" 
              startIcon={<AddIcon />} 
              onClick={openAddGroupDialog}
            >
              添加分组
            </Button>
          </Box>
        </Box>
        
        <Grid container spacing={2}>
          {loading && groups.length === 0 ? (
            <Grid item xs={12}>
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                <CircularProgress />
              </Box>
            </Grid>
          ) : groups.length === 0 ? (
            <Grid item xs={12}>
              <Paper sx={{ p: 3, textAlign: 'center' }}>
                暂无分组数据
              </Paper>
            </Grid>
          ) : (
            groups.map((group) => (
              <Grid item xs={12} md={6} lg={4} key={group.id}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      {group.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      {group.description || '无描述'}
                    </Typography>
                    <Divider sx={{ my: 1 }} />
                    <Typography variant="body2">
                      账号数量: {group.accounts.length}
                    </Typography>
                    <Box sx={{ mt: 1 }}>
                      {group.accounts.slice(0, 3).map((account) => (
                        <Chip
                          key={account.id}
                          label={`${account.username} (${getPlatformName(account.platform)})`}
                          size="small"
                          sx={{ mr: 0.5, mb: 0.5 }}
                        />
                      ))}
                      {group.accounts.length > 3 && (
                        <Chip
                          label={`+${group.accounts.length - 3}个`}
                          size="small"
                          sx={{ mb: 0.5 }}
                        />
                      )}
                    </Box>
                  </CardContent>
                  <CardActions>
                    <Button 
                      size="small" 
                      startIcon={<EditIcon />}
                      onClick={() => openEditGroupDialog(group)}
                    >
                      编辑
                    </Button>
                    <Button 
                      size="small" 
                      color="error" 
                      startIcon={<DeleteIcon />}
                      onClick={() => deleteGroup(group.id)}
                    >
                      删除
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
            ))
          )}
        </Grid>
      </TabPanel>
      
      {/* 添加/编辑账号对话框 */}
      <Dialog open={accountDialogOpen} onClose={() => setAccountDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>添加社交媒体账号</DialogTitle>
        <DialogContent>
          <TextField
            margin="dense"
            name="username"
            label="用户名"
            type="text"
            fullWidth
            variant="outlined"
            value={accountFormData.username}
            onChange={handleAccountFormChange}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            name="password"
            label="密码"
            type="password"
            fullWidth
            variant="outlined"
            value={accountFormData.password}
            onChange={handleAccountFormChange}
            sx={{ mb: 2 }}
          />
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>平台</InputLabel>
            <Select
              name="platform"
              value={accountFormData.platform}
              label="平台"
              onChange={(event: SelectChangeEvent<string>) => {
                handleAccountFormChange({
                  target: {
                    name: 'platform',
                    value: event.target.value
                  }
                } as React.ChangeEvent<HTMLInputElement>);
              }}
            >
              {platforms.map((platform) => (
                <MenuItem key={platform.id} value={platform.id}>
                  {platform.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAccountDialogOpen(false)}>取消</Button>
          <Button onClick={submitAccountForm} variant="contained" disabled={loading}>
            {loading ? <CircularProgress size={24} /> : '保存'}
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* 添加/编辑分组对话框 */}
      <Dialog open={groupDialogOpen} onClose={() => setGroupDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editingGroupId ? '编辑分组' : '添加分组'}</DialogTitle>
        <DialogContent>
          <TextField
            margin="dense"
            name="name"
            label="分组名称"
            type="text"
            fullWidth
            variant="outlined"
            value={groupFormData.name}
            onChange={handleGroupFormChange}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            name="description"
            label="描述"
            type="text"
            fullWidth
            multiline
            rows={2}
            variant="outlined"
            value={groupFormData.description}
            onChange={handleGroupFormChange}
            sx={{ mb: 2 }}
          />
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>选择账号</InputLabel>
            <Select
              multiple
              name="account_ids"
              value={groupFormData.account_ids}
              label="选择账号"
              onChange={handleGroupAccountsChange}
              renderValue={(selected) => (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {(selected as number[]).map((accountId) => {
                    const account = accounts.find(a => a.id === accountId);
                    return account ? (
                      <Chip 
                        key={accountId} 
                        label={`${account.username} (${getPlatformName(account.platform)})`} 
                        size="small" 
                      />
                    ) : null;
                  })}
                </Box>
              )}
            >
              {accounts.map((account) => (
                <MenuItem key={account.id} value={account.id}>
                  {account.username} ({getPlatformName(account.platform)})
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setGroupDialogOpen(false)}>取消</Button>
          <Button onClick={submitGroupForm} variant="contained" disabled={loading}>
            {loading ? <CircularProgress size={24} /> : '保存'}
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* 批量登录对话框 */}
      <Dialog open={batchLoginDialogOpen} onClose={() => setBatchLoginDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>批量登录社交媒体账号</DialogTitle>
        <DialogContent>
          {batchLoginAccounts.map((account, index) => (
            <Box key={index} sx={{ mb: 2, p: 2, border: '1px solid #eee', borderRadius: 1 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="subtitle1">账号 #{index + 1}</Typography>
                {batchLoginAccounts.length > 1 && (
                  <IconButton size="small" onClick={() => removeBatchLoginAccount(index)}>
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                )}
              </Box>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={4}>
                  <TextField
                    fullWidth
                    label="用户名"
                    value={account.username}
                    onChange={(e) => handleBatchLoginAccountChange(index, 'username', e.target.value)}
                  />
                </Grid>
                <Grid item xs={12} sm={4}>
                  <TextField
                    fullWidth
                    label="密码"
                    type="password"
                    value={account.password}
                    onChange={(e) => handleBatchLoginAccountChange(index, 'password', e.target.value)}
                  />
                </Grid>
                <Grid item xs={12} sm={4}>
                  <FormControl fullWidth>
                    <InputLabel>平台</InputLabel>
                    <Select
                      value={account.platform}
                      label="平台"
                      onChange={(e) => handleBatchLoginAccountChange(index, 'platform', e.target.value)}
                    >
                      {platforms.map((platform) => (
                        <MenuItem key={platform.id} value={platform.id}>
                          {platform.name}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
              </Grid>
            </Box>
          ))}
          <Button
            startIcon={<AddIcon />}
            onClick={addBatchLoginAccount}
            sx={{ mt: 1 }}
          >
            添加更多账号
          </Button>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setBatchLoginDialogOpen(false)}>取消</Button>
          <Button 
            onClick={submitBatchLogin} 
            variant="contained" 
            disabled={loginInProgress || batchLoginAccounts.some(a => !a.username || !a.password || !a.platform)}
          >
            {loginInProgress ? <CircularProgress size={24} /> : '开始登录'}
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* 提示消息 */}
      <Snackbar 
        open={!!error} 
        autoHideDuration={6000} 
        onClose={() => setError(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={() => setError(null)} severity="error" sx={{ width: '100%' }}>
          {error}
        </Alert>
      </Snackbar>
      
      <Snackbar 
        open={!!success} 
        autoHideDuration={6000} 
        onClose={() => setSuccess(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={() => setSuccess(null)} severity="success" sx={{ width: '100%' }}>
          {success}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default SocialAccountManager; 