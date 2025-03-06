import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  TextField,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Alert,
  CircularProgress,
  LinearProgress,
  Collapse,
  Tabs,
  Tab,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
  Card,
  CardContent,
  useTheme,
  Fade,
  Zoom,
  Chip,
  Grid,
  Divider,
  Tooltip,
  Snackbar
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import FileUploadIcon from '@mui/icons-material/FileUpload';
import VideocamIcon from '@mui/icons-material/Videocam';
import ImageIcon from '@mui/icons-material/Image';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import PreviewIcon from '@mui/icons-material/Preview';
import EventNoteIcon from '@mui/icons-material/EventNote';
import SendIcon from '@mui/icons-material/Send';
import HistoryIcon from '@mui/icons-material/History';
import BarChartIcon from '@mui/icons-material/BarChart';
import RefreshIcon from '@mui/icons-material/Refresh';
import axios from 'axios';
import VideoPreview from './VideoPreview';
import SchedulePost from './SchedulePost';
import PublishStats from './PublishStats';
import { DISTRIBUTE_API, SOCIAL_ACCOUNT_API, TASK_API, DOUYIN_API } from '../config/api';
import { API_BASE_URL } from '../config';

interface VideoInfo {
  title: string;
  description: string;
  file: File | null;
  uploadPath: string;
}

interface Task {
  task_id: string;
  type: string;
  status: string;
  progress: number;
  created_at: string;
  updated_at: string;
  result?: any;
  title?: string;
  description?: string;
  platforms?: string[];
  accounts?: any[];
  media_path?: string;
}

interface SocialAccount {
  id: number;
  username: string;
  platform: string;
  status: string;
}

interface AccountGroup {
  id: number;
  name: string;
  accounts: SocialAccount[];
}

interface Platform {
  id: string;
  name: string;
  icon: string;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

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

const ContentDistributor: React.FC = () => {
  const theme = useTheme();
  const [tabValue, setTabValue] = useState(0);
  const [videoInfo, setVideoInfo] = useState<VideoInfo>({
    title: '',
    description: '',
    file: null,
    uploadPath: '',
  });
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedAccounts, setSelectedAccounts] = useState<number[]>([]);
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([]);
  const [accounts, setAccounts] = useState<SocialAccount[]>([]);
  const [groups, setGroups] = useState<AccountGroup[]>([]);
  const [platforms, setPlatforms] = useState<Platform[]>([]);
  const [selectedGroup, setSelectedGroup] = useState<string>('');
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [scheduledTime, setScheduledTime] = useState<Date | null>(null);
  const [showScheduler, setShowScheduler] = useState(false);

  // 初始化数据
  useEffect(() => {
    fetchTasks();
    fetchAccounts();
    fetchGroups();
    fetchPlatforms();
    fetchHistory();

    // 定期检查任务状态
    const interval = setInterval(checkTaskStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  // 获取任务列表
  const fetchTasks = async () => {
    try {
      const response = await axios.get(DISTRIBUTE_API.LIST, {
        withCredentials: true
      });
      setTasks(response.data);
    } catch (err) {
      console.error('获取任务列表失败:', err);
      setError('获取任务列表失败');
    }
  };

  // 检查任务状态
  const checkTaskStatus = async () => {
    if (tasks.length === 0) return;
    
    try {
      const pendingTasks = tasks.filter(task => 
        task.status === 'pending' || task.status === 'processing'
      );
      
      if (pendingTasks.length === 0) return;
      
      const response = await axios.get(DISTRIBUTE_API.LIST, {
        withCredentials: true
      });
      
      setTasks(response.data);
      
      // 如果有任务完成，刷新历史记录
      const completedTasks = response.data.filter((task: Task) => 
        task.status === 'completed' && 
        pendingTasks.some(pt => pt.task_id === task.task_id && pt.status !== 'completed')
      );
      
      if (completedTasks.length > 0) {
        fetchHistory();
      }
    } catch (err) {
      console.error('检查任务状态失败:', err);
    }
  };

  // 获取社交账号列表
  const fetchAccounts = async () => {
    try {
      const response = await axios.get(SOCIAL_ACCOUNT_API.LIST, {
        withCredentials: true
      });
      setAccounts(response.data);
    } catch (err) {
      console.error('获取社交账号列表失败:', err);
      setError('获取社交账号列表失败');
    }
  };

  // 获取账号分组列表
  const fetchGroups = async () => {
    try {
      const response = await axios.get(SOCIAL_ACCOUNT_API.GROUPS, {
        withCredentials: true
      });
      setGroups(response.data);
    } catch (err) {
      console.error('获取账号分组列表失败:', err);
      setError('获取账号分组列表失败');
    }
  };

  // 获取支持的平台列表
  const fetchPlatforms = async () => {
    try {
      const response = await axios.get(SOCIAL_ACCOUNT_API.PLATFORMS, {
        withCredentials: true
      });
      setPlatforms(response.data.platforms);
    } catch (err) {
      console.error('获取平台列表失败:', err);
      setError('获取平台列表失败');
    }
  };

  // 获取历史记录
  const fetchHistory = async () => {
    try {
      const response = await axios.get(`${DISTRIBUTE_API.LIST}?status=completed`, {
        withCredentials: true
      });
      setHistory(response.data);
    } catch (err) {
      console.error('获取历史记录失败:', err);
      setError('获取历史记录失败');
    }
  };

  // 处理选项卡切换
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  // 处理分组选择
  const handleGroupSelect = (event: SelectChangeEvent) => {
    const groupId = event.target.value;
    setSelectedGroup(groupId);
    
    if (groupId) {
      const group = groups.find(g => g.id.toString() === groupId);
      if (group) {
        setSelectedAccounts(group.accounts.map(account => account.id));
      }
    } else {
      setSelectedAccounts([]);
    }
  };

  // 处理平台选择
  const handlePlatformSelect = (event: SelectChangeEvent<string[]>) => {
    const value = event.target.value;
    setSelectedPlatforms(typeof value === 'string' ? value.split(',') : value);
  };

  // 处理账号选择
  const handleAccountSelect = (event: SelectChangeEvent<number[]>) => {
    const value = event.target.value;
    setSelectedAccounts(typeof value === 'string' ? value.split(',').map(Number) : value);
  };

  // 处理文件选择
  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      const file = event.target.files[0];
      setVideoInfo({
        ...videoInfo,
        file,
      });
      
      // 创建预览URL
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
    }
  };

  // 处理视频上传
  const handleVideoUpload = async () => {
    if (!videoInfo.file) {
      setError('请选择要上传的文件');
      return;
    }

    if (!videoInfo.title) {
      setError('请输入标题');
      return;
    }

    setUploading(true);
    setUploadProgress(0);
    setError(null);

    const formData = new FormData();
    formData.append('file', videoInfo.file);
    formData.append('title', videoInfo.title);
    if (videoInfo.description) {
      formData.append('description', videoInfo.description);
    }

    try {
      const response = await axios.post(DOUYIN_API.UPLOAD_VIDEO, formData, {
        withCredentials: true,
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / (progressEvent.total || 100)
          );
          setUploadProgress(percentCompleted);
        },
      });

      setVideoInfo({
        ...videoInfo,
        uploadPath: response.data.file_path,
      });
      
      setSuccess('文件上传成功');
    } catch (err) {
      console.error('上传失败:', err);
      setError('文件上传失败');
    } finally {
      setUploading(false);
    }
  };

  // 处理内容分发
  const handleDistribute = async () => {
    if (!videoInfo.uploadPath && !videoInfo.file) {
      setError('请先上传文件');
      return;
    }

    if (selectedAccounts.length === 0) {
      setError('请选择至少一个账号');
      return;
    }

    if (selectedPlatforms.length === 0) {
      setError('请选择至少一个平台');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // 如果还没上传，先上传文件
      let filePath = videoInfo.uploadPath;
      if (!filePath && videoInfo.file) {
        await handleVideoUpload();
        filePath = videoInfo.uploadPath;
      }

      // 创建分发任务
      const taskData = {
        title: videoInfo.title,
        description: videoInfo.description,
        media_path: filePath,
        account_ids: selectedAccounts,
        platforms: selectedPlatforms,
        scheduled_time: scheduledTime
      };

      const response = await axios.post(DISTRIBUTE_API.CREATE, taskData, {
        withCredentials: true
      });

      setSuccess('内容分发任务已创建');
      fetchTasks();
      
      // 重置表单
      setVideoInfo({
        title: '',
        description: '',
        file: null,
        uploadPath: '',
      });
      setPreviewUrl(null);
      setScheduledTime(null);
      setShowScheduler(false);
    } catch (err) {
      console.error('分发失败:', err);
      setError('内容分发失败');
    } finally {
      setLoading(false);
    }
  };

  // 处理预览
  const handlePreview = () => {
    if (previewUrl) {
      setPreviewOpen(true);
    }
  };

  // 关闭预览
  const handleClosePreview = () => {
    setPreviewOpen(false);
  };

  // 处理定时发布
  const handleScheduled = (date: Date | null) => {
    setScheduledTime(date);
    setShowScheduler(false);
  };

  // 渲染任务列表
  const renderTaskList = () => {
    return (
      <TableContainer component={Paper} sx={{ mt: 2 }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>任务ID</TableCell>
              <TableCell>标题</TableCell>
              <TableCell>平台</TableCell>
              <TableCell>账号数</TableCell>
              <TableCell>状态</TableCell>
              <TableCell>进度</TableCell>
              <TableCell>创建时间</TableCell>
              <TableCell>操作</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {tasks.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  暂无任务
                </TableCell>
              </TableRow>
            ) : (
              tasks.map((task) => (
                <TableRow key={task.task_id}>
                  <TableCell>{task.task_id.substring(0, 8)}...</TableCell>
                  <TableCell>{task.title || '未知'}</TableCell>
                  <TableCell>
                    {task.platforms && Array.isArray(task.platforms) ? 
                      task.platforms.map((platform: string) => (
                        <Chip 
                          key={platform} 
                          label={getPlatformName(platform)} 
                          size="small" 
                          sx={{ mr: 0.5, mb: 0.5 }} 
                        />
                      )) : '未知'
                    }
                  </TableCell>
                  <TableCell>
                    {task.accounts && Array.isArray(task.accounts) ? task.accounts.length : 0}
                  </TableCell>
                  <TableCell>
                    <Chip 
                      label={getStatusText(task.status)} 
                      color={getStatusColor(task.status)} 
                      size="small" 
                    />
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Box sx={{ width: '100%', mr: 1 }}>
                        <LinearProgress variant="determinate" value={task.progress} />
                      </Box>
                      <Box sx={{ minWidth: 35 }}>
                        <Typography variant="body2" color="text.secondary">
                          {`${Math.round(task.progress)}%`}
                        </Typography>
                      </Box>
                    </Box>
                  </TableCell>
                  <TableCell>{new Date(task.created_at).toLocaleString()}</TableCell>
                  <TableCell>
                    <IconButton 
                      size="small" 
                      onClick={() => handleViewTaskDetail(task.task_id)}
                      disabled={task.status === 'pending'}
                    >
                      <PreviewIcon fontSize="small" />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
    );
  };

  // 查看任务详情
  const handleViewTaskDetail = (taskId: string) => {
    // 实现查看任务详情的逻辑
    console.log('查看任务详情:', taskId);
  };

  // 渲染历史记录
  const renderHistory = () => {
    return (
      <TableContainer component={Paper} sx={{ mt: 2 }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>任务ID</TableCell>
              <TableCell>标题</TableCell>
              <TableCell>平台</TableCell>
              <TableCell>账号数</TableCell>
              <TableCell>状态</TableCell>
              <TableCell>完成时间</TableCell>
              <TableCell>操作</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {history.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  暂无历史记录
                </TableCell>
              </TableRow>
            ) : (
              history.map((item) => (
                <TableRow key={item.task_id}>
                  <TableCell>{item.task_id.substring(0, 8)}...</TableCell>
                  <TableCell>{item.title || '未知'}</TableCell>
                  <TableCell>
                    {item.platforms && Array.isArray(item.platforms) ? 
                      item.platforms.map((platform: string) => (
                        <Chip 
                          key={platform} 
                          label={getPlatformName(platform)} 
                          size="small" 
                          sx={{ mr: 0.5, mb: 0.5 }} 
                        />
                      )) : '未知'
                    }
                  </TableCell>
                  <TableCell>
                    {item.accounts && Array.isArray(item.accounts) ? item.accounts.length : 0}
                  </TableCell>
                  <TableCell>
                    <Chip 
                      label={getStatusText(item.status)} 
                      color={getStatusColor(item.status)} 
                      size="small" 
                    />
                  </TableCell>
                  <TableCell>{new Date(item.updated_at).toLocaleString()}</TableCell>
                  <TableCell>
                    <IconButton 
                      size="small" 
                      onClick={() => handleViewTaskDetail(item.task_id)}
                    >
                      <PreviewIcon fontSize="small" />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
    );
  };

  // 获取平台名称
  const getPlatformName = (platformId: string) => {
    const platform = platforms.find(p => p.id === platformId);
    return platform ? platform.name : platformId;
  };

  // 获取状态文本
  const getStatusText = (status: string) => {
    switch (status) {
      case 'pending': return '等待中';
      case 'processing': return '处理中';
      case 'completed': return '已完成';
      case 'failed': return '失败';
      default: return status;
    }
  };

  // 获取状态颜色
  const getStatusColor = (status: string): 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' => {
    switch (status) {
      case 'pending': return 'warning';
      case 'processing': return 'info';
      case 'completed': return 'success';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Typography variant="h5" gutterBottom>
        内容分发中心
      </Typography>
      
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="内容分发选项卡">
          <Tab icon={<SendIcon />} label="发布内容" />
          <Tab icon={<HistoryIcon />} label="任务列表" />
          <Tab icon={<BarChartIcon />} label="发布统计" />
        </Tabs>
      </Box>
      
      {/* 发布内容选项卡 */}
      <TabPanel value={tabValue} index={0}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                上传内容
              </Typography>
              <TextField
                label="标题"
                fullWidth
                margin="normal"
                value={videoInfo.title}
                onChange={(e) => setVideoInfo({ ...videoInfo, title: e.target.value })}
              />
              <TextField
                label="描述"
                fullWidth
                margin="normal"
                multiline
                rows={3}
                value={videoInfo.description}
                onChange={(e) => setVideoInfo({ ...videoInfo, description: e.target.value })}
              />
              <Box sx={{ mt: 2, mb: 2 }}>
                <Button
                  variant="contained"
                  component="label"
                  startIcon={<FileUploadIcon />}
                  sx={{ mr: 1 }}
                >
                  选择文件
                  <input
                    type="file"
                    hidden
                    accept="video/*,image/*"
                    onChange={handleFileChange}
                  />
                </Button>
                {videoInfo.file && (
                  <Button
                    variant="outlined"
                    onClick={handlePreview}
                    startIcon={<PreviewIcon />}
                  >
                    预览
                  </Button>
                )}
              </Box>
              {videoInfo.file && (
                <Typography variant="body2" sx={{ mb: 2 }}>
                  已选择: {videoInfo.file.name} ({(videoInfo.file.size / 1024 / 1024).toFixed(2)} MB)
                </Typography>
              )}
              {uploading && (
                <Box sx={{ width: '100%', mt: 2 }}>
                  <LinearProgress variant="determinate" value={uploadProgress} />
                  <Typography variant="body2" align="center" sx={{ mt: 1 }}>
                    上传中... {uploadProgress}%
                  </Typography>
                </Box>
              )}
            </Paper>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                分发设置
              </Typography>
              
              <FormControl fullWidth margin="normal">
                <InputLabel>选择平台</InputLabel>
                <Select
                  multiple
                  value={selectedPlatforms}
                  onChange={handlePlatformSelect}
                  label="选择平台"
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {selected.map((value) => (
                        <Chip key={value} label={getPlatformName(value)} />
                      ))}
                    </Box>
                  )}
                >
                  {platforms.map((platform) => (
                    <MenuItem key={platform.id} value={platform.id}>
                      {platform.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              
              <FormControl fullWidth margin="normal">
                <InputLabel>选择分组</InputLabel>
                <Select
                  value={selectedGroup}
                  onChange={handleGroupSelect}
                  label="选择分组"
                >
                  <MenuItem value="">
                    <em>不使用分组</em>
                  </MenuItem>
                  {groups.map((group) => (
                    <MenuItem key={group.id} value={group.id.toString()}>
                      {group.name} ({group.accounts.length}个账号)
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              
              <FormControl fullWidth margin="normal">
                <InputLabel>选择账号</InputLabel>
                <Select
                  multiple
                  value={selectedAccounts}
                  onChange={handleAccountSelect}
                  label="选择账号"
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {selected.map((value) => {
                        const account = accounts.find(a => a.id === value);
                        return account ? (
                          <Chip 
                            key={value} 
                            label={`${account.username} (${getPlatformName(account.platform)})`} 
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
              
              <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between' }}>
                <Button
                  variant="outlined"
                  onClick={() => setShowScheduler(true)}
                  startIcon={<EventNoteIcon />}
                >
                  {scheduledTime ? `定时: ${scheduledTime.toLocaleString()}` : '定时发布'}
                </Button>
                
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleDistribute}
                  disabled={loading || (!videoInfo.file && !videoInfo.uploadPath) || selectedAccounts.length === 0 || selectedPlatforms.length === 0}
                  startIcon={<SendIcon />}
                >
                  {loading ? <CircularProgress size={24} /> : '开始分发'}
                </Button>
              </Box>
            </Paper>
          </Grid>
        </Grid>
        
        {showScheduler && (
          <SchedulePost
            open={showScheduler}
            onClose={() => setShowScheduler(false)}
            onScheduled={() => handleScheduled(scheduledTime)}
            videoPath=""
            videoTitle={videoInfo.title}
            videoDescription={videoInfo.description}
            accounts={[]}
            groups={[]}
          />
        )}
        
        {previewOpen && previewUrl && (
          <VideoPreview
            open={previewOpen}
            onClose={handleClosePreview}
            videoPath={previewUrl}
          />
        )}
      </TabPanel>
      
      {/* 任务列表选项卡 */}
      <TabPanel value={tabValue} index={1}>
        <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between' }}>
          <Typography variant="h6">
            任务列表
          </Typography>
          <Button
            variant="outlined"
            onClick={fetchTasks}
            startIcon={<RefreshIcon />}
          >
            刷新
          </Button>
        </Box>
        {renderTaskList()}
        
        <Box sx={{ mt: 4, mb: 2, display: 'flex', justifyContent: 'space-between' }}>
          <Typography variant="h6">
            历史记录
          </Typography>
          <Button
            variant="outlined"
            onClick={fetchHistory}
            startIcon={<RefreshIcon />}
          >
            刷新
          </Button>
        </Box>
        {renderHistory()}
      </TabPanel>
      
      {/* 发布统计选项卡 */}
      <TabPanel value={tabValue} index={2}>
        <PublishStats />
      </TabPanel>
      
      {/* 错误提示 */}
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
      
      {/* 成功提示 */}
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

export default ContentDistributor; 