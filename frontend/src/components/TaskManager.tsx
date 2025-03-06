import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress,
  Button,
  Chip,
  IconButton,
  Card,
  CardContent,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  CircularProgress,
  useTheme,
  Divider,
  Grid,
  Fade,
  Zoom,
  Tabs,
  Tab
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Info as InfoIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Pending as PendingIcon,
  PlayArrow as RunningIcon,
  Schedule as ScheduleIcon,
  Replay as RetryingIcon,
  History as HistoryIcon,
  ErrorOutline as ErrorOutlineIcon,
  Movie as MovieIcon,
  CloudUpload as CloudUploadIcon,
  Send as SendIcon
} from '@mui/icons-material';
import axios from 'axios';
import { DOUYIN_API } from '../config/api';

// 定义任务结果类型
interface TaskResult {
  video_url?: string;
  filename?: string;
  thumbnail_url?: string;
  processing_info?: any;
  processed_path?: string;
  success_count?: number;
  failed_accounts?: string[];
  [key: string]: any;
}

interface Task {
  task_id: string;
  type: string;
  task_type?: string;
  status: string;
  result: string | TaskResult;  // 任务结果
  progress: number;
  error?: string;
  created_at: string;
  updated_at: string;
  download_url?: string;
  video_url?: string;
  filename?: string;
  thumbnail_url?: string;
  processing_info?: any;
  // 其他可能的字段
  [key: string]: any;
}

// 任务行组件，使用memo优化渲染
const TaskRow = React.memo(({ 
  task, 
  formatDate, 
  getTaskTypeLabel, 
  getStatusChip, 
  fetchTaskDetails, 
  downloadVideo,
  isTaskResult
}: { 
  task: Task, 
  formatDate: (date: string) => string,
  getTaskTypeLabel: (type: string) => JSX.Element,
  getStatusChip: (status: string, result?: string) => JSX.Element,
  fetchTaskDetails: (taskId: string) => Promise<void>,
  downloadVideo: (url: string, filename: string) => void,
  isTaskResult: (result: any) => result is TaskResult
}) => {
  return (
    <Fade in={true}>
      <TableRow 
        hover
        sx={{
          '&:hover': {
            bgcolor: 'rgba(63, 81, 181, 0.04)',
          }
        }}
      >
        <TableCell>{task.task_id.slice(0, 8)}...</TableCell>
        <TableCell>{getTaskTypeLabel(task.type || task.task_type || '')}</TableCell>
        <TableCell>{getStatusChip(task.status, task.result as string)}</TableCell>
        <TableCell>
          <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
            <Box sx={{ width: '100%', mr: 1 }}>
              <LinearProgress 
                variant="determinate" 
                value={task.progress} 
                sx={{
                  height: 8,
                  borderRadius: 4,
                  bgcolor: 'rgba(0, 0, 0, 0.05)',
                  '& .MuiLinearProgress-bar': {
                    borderRadius: 4,
                  }
                }}
              />
            </Box>
            <Box sx={{ minWidth: 35 }}>
              <Typography variant="body2" color="text.secondary">
                {task.progress}%
              </Typography>
            </Box>
          </Box>
        </TableCell>
        <TableCell>
          {task.error && (
            <Tooltip title={task.error}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <ErrorOutlineIcon fontSize="small" color="error" />
                <Typography variant="body2" color="error" sx={{ ml: 1, maxWidth: 150, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {task.error}
                </Typography>
              </Box>
            </Tooltip>
          )}
        </TableCell>
        <TableCell>{formatDate(task.created_at)}</TableCell>
        <TableCell>{formatDate(task.updated_at)}</TableCell>
        <TableCell>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="查看详情">
              <IconButton 
                size="small" 
                onClick={() => fetchTaskDetails(task.task_id)}
                sx={{ color: 'info.main' }}
              >
                <InfoIcon />
              </IconButton>
            </Tooltip>
            {task.status === 'completed' && isTaskResult(task.result) && task.result.video_url && (
              <Tooltip title="下载视频">
                <IconButton 
                  size="small" 
                  onClick={() => {
                    if (isTaskResult(task.result)) {
                      const url = task.result.video_url || '';
                      const name = task.result.filename || `processed_video_${task.task_id}.mp4`;
                      downloadVideo(url, name);
                    }
                  }}
                  sx={{ color: 'success.main' }}
                >
                  <DownloadIcon />
                </IconButton>
              </Tooltip>
            )}
          </Box>
        </TableCell>
      </TableRow>
    </Fade>
  );
});

// 历史任务行组件，使用memo优化渲染
const HistoryTaskRow = React.memo(({ 
  task, 
  formatDate, 
  getTaskTypeLabel, 
  getStatusChip, 
  fetchTaskDetails, 
  downloadVideo 
}: { 
  task: Task, 
  formatDate: (date: string) => string,
  getTaskTypeLabel: (type: string) => JSX.Element,
  getStatusChip: (status: string, result?: string) => JSX.Element,
  fetchTaskDetails: (taskId: string) => Promise<void>,
  downloadVideo: (url: string, filename: string) => void
}) => {
  return (
    <Fade in={true}>
      <TableRow 
        hover
        sx={{
          '&:hover': {
            bgcolor: 'rgba(63, 81, 181, 0.04)',
          }
        }}
      >
        <TableCell>{task.task_id.slice(0, 8)}...</TableCell>
        <TableCell>{getTaskTypeLabel(task.type || task.task_type || '')}</TableCell>
        <TableCell>{getStatusChip(task.status, task.result as string)}</TableCell>
        <TableCell>
          {task.error && (
            <Tooltip title={task.error}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <ErrorOutlineIcon fontSize="small" color="error" />
                <Typography variant="body2" color="error" sx={{ ml: 1, maxWidth: 150, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {task.error}
                </Typography>
              </Box>
            </Tooltip>
          )}
        </TableCell>
        <TableCell>{formatDate(task.created_at)}</TableCell>
        <TableCell>{formatDate(task.updated_at)}</TableCell>
        <TableCell>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="查看详情">
              <IconButton 
                size="small" 
                onClick={() => fetchTaskDetails(task.task_id)}
                sx={{ color: 'info.main' }}
              >
                <InfoIcon />
              </IconButton>
            </Tooltip>
            {task.status === 'completed' && (task.download_url || task.video_url) && (
              <Tooltip title="下载视频">
                <IconButton 
                  size="small" 
                  onClick={() => {
                    const url = task.download_url || task.video_url || '';
                    const name = task.filename || `processed_video_${task.task_id}.mp4`;
                    downloadVideo(url, name);
                  }}
                  sx={{ color: 'success.main' }}
                >
                  <DownloadIcon />
                </IconButton>
              </Tooltip>
            )}
          </Box>
        </TableCell>
      </TableRow>
    </Fade>
  );
});

const TaskManager: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [taskHistory, setTaskHistory] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState<NodeJS.Timeout | null>(null);
  const [pollingInterval, setPollingInterval] = useState(10000); // 默认10秒
  const [activeTab, setActiveTab] = useState(0);
  const theme = useTheme();

  // 通用的Chip样式
  const getChipSx = () => ({
    fontWeight: 'medium',
    borderRadius: '12px',
    '& .MuiChip-icon': {
      fontSize: '0.875rem',
    },
    '&.MuiChip-colorPrimary': {
      borderColor: theme.palette.primary.main,
      backgroundColor: `${theme.palette.primary.main}10`,
    },
    '&.MuiChip-colorSecondary': {
      borderColor: theme.palette.secondary.main,
      backgroundColor: `${theme.palette.secondary.main}10`,
    },
    '&.MuiChip-colorSuccess': {
      borderColor: theme.palette.success.main,
      backgroundColor: `${theme.palette.success.main}10`,
    },
    '&.MuiChip-colorError': {
      borderColor: theme.palette.error.main,
      backgroundColor: `${theme.palette.error.main}10`,
    },
    '&.MuiChip-colorInfo': {
      borderColor: theme.palette.info.main,
      backgroundColor: `${theme.palette.info.main}10`,
    },
    '&.MuiChip-colorWarning': {
      borderColor: theme.palette.warning.main,
      backgroundColor: `${theme.palette.warning.main}10`,
    }
  });

  // 类型守卫函数，检查 result 是否为 TaskResult 类型
  const isTaskResult = (result: any): result is TaskResult => {
    return typeof result === 'object' && result !== null;
  };

  const fetchTasks = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('未登录或登录已过期');
      }

      // 获取正在执行的任务（状态为 pending、scheduled 或 running）
      const response = await axios.get(DOUYIN_API.TASKS, {
        params: {
          status: 'pending,scheduled,running'  // 获取等待中、已调度和正在运行的任务
        },
        headers: {
          Authorization: `Bearer ${token}`
        }
      });

      console.log('获取到的当前任务列表:', response.data);
      
      // 比较新旧数据，只在数据发生变化时才更新状态
      const newTasks = response.data;
      const hasChanged = JSON.stringify(newTasks) !== JSON.stringify(tasks);
      
      if (hasChanged) {
        setTasks(newTasks);
      }
      
      setError('');
    } catch (err: any) {
      console.error('获取任务列表失败:', err);
      setError(err.response?.data?.detail || err.message || '获取任务列表失败');
      
      if (err.response?.status === 401) {
        localStorage.removeItem('token');
        window.location.href = '/login';
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchTaskHistory = async () => {
    try {
      setHistoryLoading(true);
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('未登录或登录已过期');
      }

      // 获取所有已完成的任务
      const response = await axios.get(DOUYIN_API.TASKS, {
        params: {
          status: 'completed'  // 获取已完成的任务
        },
        headers: {
          Authorization: `Bearer ${token}`
        }
      });

      console.log('获取到的历史任务列表:', response.data);
      
      // 比较新旧数据，只在数据发生变化时才更新状态
      const newTaskHistory = response.data;
      const hasChanged = JSON.stringify(newTaskHistory) !== JSON.stringify(taskHistory);
      
      if (hasChanged) {
        setTaskHistory(newTaskHistory);
      }
      
      setError('');
    } catch (err: any) {
      console.error('获取任务历史失败:', err);
      setError(err.response?.data?.detail || err.message || '获取任务历史失败');
      
      if (err.response?.status === 401) {
        localStorage.removeItem('token');
        window.location.href = '/login';
      }
    } finally {
      setHistoryLoading(false);
    }
  };

  const refreshTasks = () => {
    fetchTasks();
    if (activeTab === 1) {
      fetchTaskHistory();
    }
  };

  const fetchTaskDetails = async (taskId: string) => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('未登录或登录已过期');
      }

      const response = await axios.get(DOUYIN_API.TASK(taskId), {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });

      setSelectedTask(response.data);
      setDetailsOpen(true);
    } catch (err: any) {
      console.error('获取任务详情失败:', err);
      setError(err.response?.data?.detail || err.message || '获取任务详情失败');
      
      if (err.response?.status === 401) {
        localStorage.removeItem('token');
        window.location.href = '/login';
      }
    }
  };

  const downloadVideo = (videoUrl: string, filename: string) => {
    const token = localStorage.getItem('token');
    if (!token) {
      setError('未登录或登录已过期，请重新登录');
      window.location.href = '/login';
      return;
    }

    // 添加token到请求头
    const headers = new Headers();
    headers.append('Authorization', `Bearer ${token}`);
    
    // 使用fetch API发起请求
    fetch(videoUrl, { headers })
      .then(response => response.blob())
      .then(blob => {
        const url = window.URL.createObjectURL(blob);
        // 创建一个隐藏的a标签
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      })
      .catch(err => {
        console.error('下载视频失败:', err);
        setError('下载视频失败');
      });
  };

  // 使用useCallback优化函数引用
  const formatDateCallback = useCallback((dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  }, []);

  const getTaskTypeLabelCallback = useCallback((type: string) => {
    let label = '';
    let color: 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' = 'default';
    let icon = <InfoIcon fontSize="small" />;

    switch (type) {
      case 'video_processing':
        label = '视频处理';
        color = 'secondary';
        icon = <MovieIcon fontSize="small" />;
        break;
      case 'video_upload':
        label = '视频上传';
        color = 'info';
        icon = <CloudUploadIcon fontSize="small" />;
        break;
      case 'post_scheduling':
        label = '发布调度';
        color = 'warning';
        icon = <ScheduleIcon fontSize="small" />;
        break;
      case 'douyin_post':
        label = '抖音发布';
        color = 'success';
        icon = <SendIcon fontSize="small" />;
        break;
      default:
        label = type;
        color = 'default';
        icon = <InfoIcon fontSize="small" />;
    }

    return (
      <Chip
        icon={icon}
        label={label}
        color={color}
        size="small"
        variant="outlined"
        sx={getChipSx()}
      />
    );
  }, [getChipSx]);

  const getStatusChipCallback = useCallback((status: string, result?: string) => {
    let color: 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' = 'default';
    let icon = <PendingIcon />;
    let label = '未知';

    switch (status) {
      case 'pending':
        color = 'default';
        icon = <PendingIcon />;
        label = '等待中';
        break;
      case 'scheduled':
        color = 'info';
        icon = <ScheduleIcon />;
        label = '已调度';
        break;
      case 'running':
        color = 'primary';
        icon = <RunningIcon />;
        label = '运行中';
        break;
      case 'completed':
        // 如果是已完成状态，根据 result 判断是成功还是失败
        if (result === 'failed' || result === 'error') {
          color = 'error';
          icon = <ErrorIcon />;
          label = '失败';
        } else {
          color = 'success';
          icon = <CheckCircleIcon />;
          label = '已完成';
        }
        break;
      case 'retrying':
        color = 'warning';
        icon = <RetryingIcon />;
        label = '重试中';
        break;
    }

    return (
      <Chip
        icon={icon}
        label={label}
        color={color}
        size="small"
        variant="outlined"
        sx={getChipSx()}
      />
    );
  }, [getChipSx]);

  useEffect(() => {
    fetchTasks();
    fetchTaskHistory();

    // 根据任务状态动态调整轮询间隔
    const adjustPollingInterval = () => {
      // 检查是否有正在运行的任务
      const hasRunningTasks = tasks.some(task => 
        task.status === 'running' || task.status === 'scheduled' || task.status === 'pending'
      );
      
      // 如果有运行中的任务，使用较短的轮询间隔（5秒）
      // 如果没有运行中的任务，使用较长的轮询间隔（30秒）
      setPollingInterval(hasRunningTasks ? 5000 : 30000);
    };

    // 初始调整轮询间隔
    adjustPollingInterval();

    // 设置定时刷新
    const interval = setInterval(() => {
      fetchTasks();
      if (activeTab === 1) {
        fetchTaskHistory();
      }
      
      // 每次轮询后重新调整间隔
      adjustPollingInterval();
    }, pollingInterval);

    setRefreshInterval(interval);

    return () => {
      if (refreshInterval) {
        clearInterval(refreshInterval);
      }
    };
  }, [activeTab, pollingInterval, tasks]);

  // 使用useMemo优化任务列表渲染
  const taskListContent = useMemo(() => {
    if (loading) {
      return (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      );
    }
    
    if (tasks.length === 0) {
      return (
        <Paper 
          elevation={0} 
          sx={{ 
            p: 4, 
            textAlign: 'center',
            bgcolor: 'rgba(0, 0, 0, 0.02)',
            borderRadius: 2
          }}
        >
          <Typography variant="body1" color="text.secondary">
            暂无任务记录
          </Typography>
        </Paper>
      );
    }
    
    return (
      <TableContainer component={Paper} sx={{ borderRadius: 2, boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
        <Table>
          <TableHead sx={{ bgcolor: theme.palette.primary.light }}>
            <TableRow>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>任务ID</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>类型</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>状态</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>进度</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>错误信息</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>创建时间</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>更新时间</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>操作</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {tasks.map((task) => (
              <TaskRow
                key={task.task_id}
                task={task}
                formatDate={formatDateCallback}
                getTaskTypeLabel={getTaskTypeLabelCallback}
                getStatusChip={getStatusChipCallback}
                fetchTaskDetails={fetchTaskDetails}
                downloadVideo={downloadVideo}
                isTaskResult={isTaskResult}
              />
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    );
  }, [tasks, loading, theme, formatDateCallback, getTaskTypeLabelCallback, getStatusChipCallback, fetchTaskDetails, downloadVideo]);

  // 使用useMemo优化历史任务列表渲染
  const historyTaskListContent = useMemo(() => {
    if (historyLoading) {
      return (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      );
    }
    
    if (taskHistory.length === 0) {
      return (
        <Paper 
          elevation={0} 
          sx={{ 
            p: 4, 
            textAlign: 'center',
            bgcolor: 'rgba(0, 0, 0, 0.02)',
            borderRadius: 2
          }}
        >
          <Typography variant="body1" color="text.secondary">
            暂无历史任务记录
          </Typography>
        </Paper>
      );
    }
    
    return (
      <TableContainer component={Paper} sx={{ borderRadius: 2, boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
        <Table>
          <TableHead sx={{ bgcolor: theme.palette.primary.light }}>
            <TableRow>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>任务ID</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>类型</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>状态</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>错误信息</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>创建时间</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>更新时间</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>操作</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {taskHistory.map((task) => (
              <HistoryTaskRow
                key={task.task_id}
                task={task}
                formatDate={formatDateCallback}
                getTaskTypeLabel={getTaskTypeLabelCallback}
                getStatusChip={getStatusChipCallback}
                fetchTaskDetails={fetchTaskDetails}
                downloadVideo={downloadVideo}
              />
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    );
  }, [taskHistory, historyLoading, theme, formatDateCallback, getTaskTypeLabelCallback, getStatusChipCallback, fetchTaskDetails, downloadVideo]);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <Card 
        elevation={3} 
        sx={{ 
          borderRadius: 3,
          background: 'linear-gradient(45deg, #e8eaf6 30%, #ffffff 90%)',
        }}
      >
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography 
              variant="h5" 
              sx={{ 
                fontWeight: 'bold',
                color: theme.palette.primary.main
              }}
            >
              任务管理中心
            </Typography>
            <Tooltip title="刷新任务列表">
              <IconButton 
                onClick={refreshTasks}
                sx={{
                  bgcolor: theme.palette.primary.light,
                  color: 'white',
                  '&:hover': {
                    bgcolor: theme.palette.primary.main,
                  }
                }}
              >
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Box>

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

          <Tabs
            value={activeTab}
            onChange={(e, newValue) => setActiveTab(newValue)}
            sx={{ 
              mb: 3,
              '& .MuiTabs-indicator': {
                backgroundColor: theme.palette.primary.main,
              }
            }}
          >
            <Tab 
              label="当前任务" 
              icon={<RunningIcon />} 
              iconPosition="start"
              sx={{ 
                fontWeight: 'bold',
                '&.Mui-selected': {
                  color: theme.palette.primary.main,
                }
              }}
            />
            <Tab 
              label="历史记录" 
              icon={<HistoryIcon />} 
              iconPosition="start"
              sx={{ 
                fontWeight: 'bold',
                '&.Mui-selected': {
                  color: theme.palette.primary.main,
                }
              }}
            />
          </Tabs>

          {activeTab === 0 ? taskListContent : historyTaskListContent}
        </CardContent>
      </Card>

      <Dialog 
        open={detailsOpen} 
        onClose={() => setDetailsOpen(false)}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 2,
            boxShadow: '0 8px 32px rgba(0,0,0,0.2)',
          }
        }}
      >
        <DialogTitle sx={{ 
          bgcolor: theme.palette.primary.main, 
          color: 'white',
          fontWeight: 'bold'
        }}>
          任务详情
        </DialogTitle>
        <DialogContent dividers>
          {selectedTask && (
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                  基本信息
                </Typography>
                <Paper sx={{ p: 2, bgcolor: 'rgba(0, 0, 0, 0.02)', borderRadius: 2 }}>
                  <Box sx={{ mb: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      任务ID:
                    </Typography>
                    <Typography variant="body1">
                      {selectedTask.task_id}
                    </Typography>
                  </Box>
                  <Box sx={{ mb: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      类型:
                    </Typography>
                    <Typography variant="body1">
                      {getTaskTypeLabelCallback(selectedTask.type || '')}
                    </Typography>
                  </Box>
                  <Box sx={{ mb: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      状态:
                    </Typography>
                    <Box sx={{ mt: 0.5 }}>
                      {getStatusChipCallback(selectedTask.status, selectedTask.result as string)}
                    </Box>
                  </Box>
                  <Box sx={{ mb: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      进度:
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', mt: 0.5 }}>
                      <Box sx={{ width: '100%', mr: 1 }}>
                        <LinearProgress 
                          variant="determinate" 
                          value={selectedTask.progress} 
                          sx={{
                            height: 10,
                            borderRadius: 5,
                            bgcolor: 'rgba(0, 0, 0, 0.05)',
                            '& .MuiLinearProgress-bar': {
                              borderRadius: 5,
                            }
                          }}
                        />
                      </Box>
                      <Box sx={{ minWidth: 35 }}>
                        <Typography variant="body2" color="text.secondary">
                          {selectedTask.progress}%
                        </Typography>
                      </Box>
                    </Box>
                  </Box>
                  
                  {/* 显示错误信息 */}
                  {selectedTask.error && (
                    <Box sx={{ mb: 1 }}>
                      <Typography variant="body2" color="error" fontWeight="bold">
                        错误信息:
                      </Typography>
                      <Paper 
                        elevation={0} 
                        sx={{ 
                          p: 1.5, 
                          bgcolor: 'rgba(244, 67, 54, 0.05)', 
                          borderRadius: 2,
                          border: '1px solid rgba(244, 67, 54, 0.2)',
                          mt: 0.5
                        }}
                      >
                        <Typography variant="body2" color="error.main" sx={{ wordBreak: 'break-word' }}>
                          {selectedTask.error}
                        </Typography>
                      </Paper>
                    </Box>
                  )}
                  
                  {/* 显示重试次数 */}
                  {selectedTask.retry_count > 0 && (
                    <Box sx={{ mb: 1 }}>
                      <Typography variant="body2" color="text.secondary">
                        重试次数:
                      </Typography>
                      <Typography variant="body1">
                        {selectedTask.retry_count}
                      </Typography>
                    </Box>
                  )}
                </Paper>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                  时间信息
                </Typography>
                <Paper sx={{ p: 2, bgcolor: 'rgba(0, 0, 0, 0.02)', borderRadius: 2 }}>
                  <Box sx={{ mb: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      创建时间:
                    </Typography>
                    <Typography variant="body1">
                      {formatDateCallback(selectedTask.created_at)}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      更新时间:
                    </Typography>
                    <Typography variant="body1">
                      {formatDateCallback(selectedTask.updated_at)}
                    </Typography>
                  </Box>
                </Paper>
              </Grid>
              
              {/* 显示任务数据 */}
              {selectedTask.data && (
                <Grid item xs={12}>
                  <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                    任务数据
                  </Typography>
                  <Paper sx={{ p: 2, bgcolor: 'rgba(0, 0, 0, 0.02)', borderRadius: 2 }}>
                    <Box sx={{ maxHeight: '200px', overflow: 'auto' }}>
                      <pre style={{ margin: 0, fontSize: '0.875rem' }}>
                        {JSON.stringify(selectedTask.data, null, 2)}
                      </pre>
                    </Box>
                  </Paper>
                </Grid>
              )}
              
              {/* 显示处理结果 */}
              {selectedTask.result_data && (
                <Grid item xs={12}>
                  <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                    处理结果
                  </Typography>
                  <Paper sx={{ p: 2, bgcolor: 'rgba(0, 0, 0, 0.02)', borderRadius: 2 }}>
                    {isTaskResult(selectedTask.result) && selectedTask.result.video_url ? (
                      <Box>
                        <Box sx={{ mb: 2 }}>
                          <Typography variant="body2" color="text.secondary" gutterBottom>
                            处理后的视频:
                          </Typography>
                          {isTaskResult(selectedTask.result) && selectedTask.result.thumbnail_url && (
                            <Box 
                              component="img" 
                              src={selectedTask.result.thumbnail_url} 
                              alt="视频缩略图"
                              sx={{ 
                                width: '100%', 
                                maxHeight: '200px',
                                objectFit: 'contain',
                                borderRadius: 1,
                                mb: 2
                              }}
                            />
                          )}
                          <Button 
                            fullWidth
                            variant="contained"
                            startIcon={<DownloadIcon />}
                            onClick={() => {
                              if (selectedTask && isTaskResult(selectedTask.result)) {
                                downloadVideo(
                                  selectedTask.result.video_url || '', 
                                  selectedTask.result.filename || `processed_video_${selectedTask.task_id}.mp4`
                                );
                              }
                            }}
                            sx={{
                              background: 'linear-gradient(45deg, #4caf50 30%, #81c784 90%)',
                              boxShadow: '0 3px 5px 2px rgba(76, 175, 80, .3)',
                            }}
                          >
                            下载处理后的视频
                          </Button>
                        </Box>
                        {isTaskResult(selectedTask.result) && selectedTask.result.processing_info && (
                          <Box>
                            <Typography variant="body2" color="text.secondary" gutterBottom>
                              处理信息:
                            </Typography>
                            <Typography variant="body2">
                              {selectedTask.result.processing_info}
                            </Typography>
                          </Box>
                        )}
                      </Box>
                    ) : (
                      <Box sx={{ maxHeight: '200px', overflow: 'auto' }}>
                        <pre style={{ margin: 0, fontSize: '0.875rem' }}>
                          {JSON.stringify(selectedTask.result_data, null, 2)}
                        </pre>
                      </Box>
                    )}
                  </Paper>
                </Grid>
              )}
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsOpen(false)}>关闭</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TaskManager; 