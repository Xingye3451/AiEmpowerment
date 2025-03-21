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
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import FileUploadIcon from '@mui/icons-material/FileUpload';
import VideocamIcon from '@mui/icons-material/Videocam';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import PreviewIcon from '@mui/icons-material/Preview';
import EventNoteIcon from '@mui/icons-material/EventNote';
import axios from 'axios';
import VideoPreview from './VideoPreview';
import AccountGroups from './AccountGroups';
import SchedulePost from './SchedulePost';
import PublishStats from './PublishStats';

interface DouyinAccount {
  username: string;
  password: string;
}

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
}

interface Group {
  id: string;
  name: string;
  accounts: string[];
}

const DOUYIN_API = {
  UPLOAD_VIDEO: '/api/v1/douyin/upload-video',
  BATCH_LOGIN: '/api/v1/douyin/batch-login',
  BATCH_POST: '/api/v1/douyin/batch-post',
  TASK: (taskId: string) => `/api/v1/douyin/task/${taskId}`,
  TASKS: '/api/v1/douyin/tasks',
  GROUPS: '/api/v1/douyin/groups',
  HISTORY: '/api/v1/douyin/history',
};

const DouyinManager: React.FC = () => {
  const [accounts, setAccounts] = useState<DouyinAccount[]>([]);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [video, setVideo] = useState<VideoInfo>({
    title: '',
    description: '',
    file: null,
    uploadPath: '',
  });
  const [message, setMessage] = useState({ type: '', content: '' });
  const [isUploading, setIsUploading] = useState(false);
  const [isPosting, setIsPosting] = useState(false);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [currentTaskId, setCurrentTaskId] = useState<string>('');
  const [showTasks, setShowTasks] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [currentTab, setCurrentTab] = useState(0);
  const [groups, setGroups] = useState<Group[]>([]);
  const [selectedGroup, setSelectedGroup] = useState<string>('');
  const [history, setHistory] = useState<any[]>([]);
  const [showScheduleDialog, setShowScheduleDialog] = useState(false);

  // 定期刷新任务状态
  useEffect(() => {
    const fetchTasks = async () => {
      try {
        const response = await axios.get(DOUYIN_API.TASKS);
        setTasks(response.data);
      } catch (error) {
        console.error('Failed to fetch tasks:', error);
      }
    };

    // 初始加载
    fetchTasks();

    // 每5秒更新一次任务状态
    const interval = setInterval(fetchTasks, 5000);
    return () => clearInterval(interval);
  }, []);

  // 监控当前任务状态
  useEffect(() => {
    if (!currentTaskId) return;

    const checkTaskStatus = async () => {
      try {
        const response = await axios.get(DOUYIN_API.TASK(currentTaskId));
        const task = response.data;
        
        if (task.status === 'completed' || task.status === 'failed') {
          setCurrentTaskId('');
          // 刷新任务列表
          const tasksResponse = await axios.get(DOUYIN_API.TASKS);
          setTasks(tasksResponse.data);
          
          setMessage({
            type: task.status === 'completed' ? 'success' : 'error',
            content: task.status === 'completed' ? '发布任务完成' : `发布失败: ${task.error}`
          });
        }
      } catch (error) {
        console.error('Failed to check task status:', error);
      }
    };

    const interval = setInterval(checkTaskStatus, 2000);
    return () => clearInterval(interval);
  }, [currentTaskId]);

  useEffect(() => {
    fetchGroups();
    fetchHistory();
  }, []);

  const fetchGroups = async () => {
    try {
      const response = await axios.get(DOUYIN_API.GROUPS);
      const groupsData = Object.entries(response.data).map(([id, data]: [string, any]) => ({
        id,
        ...data,
      }));
      setGroups(groupsData);
    } catch (error) {
      console.error('Failed to fetch groups:', error);
    }
  };

  const fetchHistory = async () => {
    try {
      const response = await axios.get(DOUYIN_API.HISTORY);
      setHistory(response.data);
    } catch (error) {
      console.error('Failed to fetch history:', error);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  const handleGroupSelect = (event: SelectChangeEvent) => {
    const groupId = event.target.value;
    setSelectedGroup(groupId);
    if (groupId) {
      const group = groups.find(g => g.id === groupId);
      if (group) {
        const groupAccounts = accounts.filter(acc => 
          group.accounts.includes(acc.username)
        );
        setAccounts(groupAccounts);
      }
    }
  };

  const addAccount = () => {
    if (username && password) {
      setAccounts([...accounts, { username, password }]);
      setUsername('');
      setPassword('');
    }
  };

  const removeAccount = (index: number) => {
    const newAccounts = accounts.filter((_, i) => i !== index);
    setAccounts(newAccounts);
  };

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      const file = event.target.files[0];
      setVideo(prev => ({ ...prev, file }));
      
      if (!video.title) {
        // 使用文件名作为默认标题
        const defaultTitle = file.name.split('.')[0];
        setVideo(prev => ({ ...prev, title: defaultTitle }));
      }
    }
  };

  const handleVideoUpload = async () => {
    if (!video.file || !video.title) {
      setMessage({ type: 'error', content: '请选择视频并填写标题' });
      return;
    }

    setIsUploading(true);
    const formData = new FormData();
    formData.append('video', video.file);
    formData.append('title', video.title);
    if (video.description) {
      formData.append('description', video.description);
    }

    try {
      const response = await axios.post(DOUYIN_API.UPLOAD_VIDEO, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data.success) {
        setVideo(prev => ({ ...prev, uploadPath: response.data.file_path }));
        setMessage({ type: 'success', content: '视频上传成功' });
      }
    } catch (error: any) {
      setMessage({ 
        type: 'error', 
        content: error.response?.data?.detail || '视频上传失败' 
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handleBatchLogin = async () => {
    if (accounts.length === 0) {
      setMessage({ type: 'error', content: '请先添加抖音账号' });
      return;
    }

    try {
      const response = await axios.post(DOUYIN_API.BATCH_LOGIN, {
        accounts: accounts,
      });
      
      const results = response.data.results;
      const successCount = results.filter((r: any) => r.success).length;
      setMessage({ 
        type: 'success', 
        content: `批量登录完成：${successCount}/${accounts.length} 个账号登录成功` 
      });
    } catch (error: any) {
      setMessage({ 
        type: 'error', 
        content: error.response?.data?.detail || '批量登录失败' 
      });
    }
  };

  const handleBatchPost = async () => {
    if (!video.uploadPath || !video.title) {
      setMessage({ type: 'error', content: '请先上传视频并填写标题' });
      return;
    }

    if (accounts.length === 0) {
      setMessage({ type: 'error', content: '请先添加并登录抖音账号' });
      return;
    }

    setIsPosting(true);
    const formData = new FormData();
    formData.append('accounts', JSON.stringify(accounts.map(acc => acc.username)));
    formData.append('video_path', video.uploadPath);
    formData.append('title', video.title);
    if (video.description) {
      formData.append('description', video.description);
    }

    try {
      const response = await axios.post(DOUYIN_API.BATCH_POST, formData);
      setCurrentTaskId(response.data.task_id);
      setMessage({ type: 'success', content: '任务已添加到队列' });
    } catch (error: any) {
      setMessage({ 
        type: 'error', 
        content: error.response?.data?.detail || '创建发布任务失败' 
      });
    } finally {
      setIsPosting(false);
    }
  };

  const handleScheduled = async () => {
    setMessage({ type: 'success', content: '定时任务创建成功' });
    // 刷新任务列表
    const tasksResponse = await axios.get(DOUYIN_API.TASKS);
  };

  const renderTaskList = () => {
    if (tasks.length === 0) {
      return (
        <Typography variant="body2" sx={{ p: 2, textAlign: 'center' }}>
          暂无任务
        </Typography>
      );
    }

    return (
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>任务ID</TableCell>
              <TableCell>类型</TableCell>
              <TableCell>状态</TableCell>
              <TableCell>进度</TableCell>
              <TableCell>创建时间</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {tasks.map((task) => (
              <TableRow key={task.task_id}>
                <TableCell>{task.task_id.slice(0, 8)}</TableCell>
                <TableCell>{task.type}</TableCell>
                <TableCell>{task.status}</TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Box sx={{ width: '100%', mr: 1 }}>
                      <LinearProgress variant="determinate" value={task.progress} />
                    </Box>
                    <Box sx={{ minWidth: 35 }}>
                      <Typography variant="body2" color="text.secondary">
                        {task.progress}%
                      </Typography>
                    </Box>
                  </Box>
                </TableCell>
                <TableCell>
                  {new Date(task.created_at).toLocaleString()}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    );
  };

  const renderHistory = () => {
    if (history.length === 0) {
      return (
        <Typography variant="body2" sx={{ p: 2, textAlign: 'center' }}>
          暂无发布历史
        </Typography>
      );
    }

    return (
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>标题</TableCell>
              <TableCell>发布时间</TableCell>
              <TableCell>账号数</TableCell>
              <TableCell>成功/失败</TableCell>
              <TableCell>状态</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {history.map((record) => (
              <TableRow key={record.task_id}>
                <TableCell>{record.title}</TableCell>
                <TableCell>
                  {new Date(record.created_at).toLocaleString()}
                </TableCell>
                <TableCell>{record.accounts.length}</TableCell>
                <TableCell>
                  {record.success_count}/{record.failed_count}
                </TableCell>
                <TableCell>{record.status}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    );
  };

  return (
    <Box sx={{ p: 3, display: 'flex' }}>
      {/* 左侧Tab导航 */}
      <Box sx={{ width: '200px', borderRight: 1, borderColor: 'divider', pr: 2 }}>
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
          <Tab label="发布管理" />
          <Tab label="账号分组" />
          <Tab label="发布历史" />
          <Tab label="统计分析" />
        </Tabs>
      </Box>

      {/* 右侧内容区域 */}
      <Box sx={{ flex: 1, pl: 3 }}>
        {message.content && (
          <Alert severity={message.type as 'success' | 'error'} sx={{ mb: 2 }}>
            {message.content}
          </Alert>
        )}

        {/* Tab内容区域 */}
        <Box sx={{ mt: 2 }}>
          {currentTab === 0 && (
            <>
              <Paper sx={{ p: 2, mb: 2 }}>
                <Typography variant="h6" gutterBottom>
                  添加账号
                </Typography>
                <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                  <TextField
                    label="抖音用户名"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                  />
                  <TextField
                    label="密码"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                  <Button variant="contained" onClick={addAccount}>
                    添加
                  </Button>
                </Box>

                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>选择账号分组</InputLabel>
                  <Select
                    value={selectedGroup}
                    onChange={handleGroupSelect}
                    label="选择账号分组"
                  >
                    <MenuItem value="">
                      <em>不使用分组</em>
                    </MenuItem>
                    {groups.map((group) => (
                      <MenuItem key={group.id} value={group.id}>
                        {group.name} ({group.accounts.length}个账号)
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>

                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>用户名</TableCell>
                        <TableCell>密码</TableCell>
                        <TableCell>操作</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {accounts.map((account, index) => (
                        <TableRow key={index}>
                          <TableCell>{account.username}</TableCell>
                          <TableCell>******</TableCell>
                          <TableCell>
                            <IconButton onClick={() => removeAccount(index)}>
                              <DeleteIcon />
                            </IconButton>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>

                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleBatchLogin}
                  sx={{ mt: 2 }}
                  disabled={accounts.length === 0}
                >
                  批量登录
                </Button>
              </Paper>

              <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  批量发布视频
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <TextField
                    label="视频标题"
                    value={video.title}
                    onChange={(e) => setVideo(prev => ({ ...prev, title: e.target.value }))}
                  />
                  <TextField
                    label="视频描述"
                    multiline
                    rows={3}
                    value={video.description}
                    onChange={(e) => setVideo(prev => ({ ...prev, description: e.target.value }))}
                  />
                  <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                    <Button
                      variant="contained"
                      component="label"
                      startIcon={<FileUploadIcon />}
                      disabled={isUploading}
                    >
                      选择视频
                      <input
                        type="file"
                        hidden
                        accept="video/*"
                        onChange={handleFileChange}
                      />
                    </Button>
                    {video.file && (
                      <>
                        <Typography variant="body2" sx={{ flex: 1 }}>
                          已选择视频: {video.file.name}
                        </Typography>
                        <Button
                          variant="contained"
                          color="secondary"
                          onClick={handleVideoUpload}
                          disabled={isUploading}
                          startIcon={isUploading ? <CircularProgress size={20} /> : <VideocamIcon />}
                        >
                          {isUploading ? '上传中...' : '上传视频'}
                        </Button>
                        <IconButton
                          color="primary"
                          onClick={() => setShowPreview(true)}
                          disabled={!video.uploadPath}
                        >
                          <PreviewIcon />
                        </IconButton>
                      </>
                    )}
                  </Box>
                  
                  {video.uploadPath && (
                    <Box sx={{ display: 'flex', gap: 2 }}>
                      <Button
                        variant="contained"
                        color="primary"
                        onClick={handleBatchPost}
                        disabled={isPosting || accounts.length === 0}
                        startIcon={isPosting ? <CircularProgress size={20} /> : null}
                      >
                        {isPosting ? '发布中...' : '立即发布'}
                      </Button>
                      <Button
                        variant="outlined"
                        color="primary"
                        onClick={() => setShowScheduleDialog(true)}
                        disabled={accounts.length === 0}
                        startIcon={<EventNoteIcon />}
                      >
                        定时发布
                      </Button>
                    </Box>
                  )}
                </Box>
              </Paper>

              <Paper sx={{ p: 2, mt: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}
                    onClick={() => setShowTasks(!showTasks)}>
                  <Typography variant="h6" sx={{ flex: 1 }}>
                    任务列表
                  </Typography>
                  <IconButton>
                    {showTasks ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                  </IconButton>
                </Box>
                <Collapse in={showTasks}>
                  {renderTaskList()}
                </Collapse>
              </Paper>

              {video.uploadPath && (
                <>
                  <VideoPreview
                    videoPath={video.uploadPath}
                    open={showPreview}
                    onClose={() => setShowPreview(false)}
                  />
                  <SchedulePost
                    open={showScheduleDialog}
                    onClose={() => setShowScheduleDialog(false)}
                    videoPath={video.uploadPath}
                    videoTitle={video.title}
                    videoDescription={video.description}
                    accounts={accounts.map(acc => acc.username)}
                    groups={groups}
                    onScheduled={handleScheduled}
                  />
                </>
              )}
            </>
          )}

          {currentTab === 1 && <AccountGroups />}

          {currentTab === 2 && (
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                发布历史
              </Typography>
              {renderHistory()}
            </Paper>
          )}

          {currentTab === 3 && <PublishStats />}
        </Box>
      </Box>
    </Box>
  );
};

export default DouyinManager;
