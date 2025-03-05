import React, { useState, useEffect } from 'react';
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
  Zoom
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Info as InfoIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Pending as PendingIcon,
  PlayArrow as RunningIcon,
  Schedule as ScheduledIcon,
  Replay as RetryingIcon
} from '@mui/icons-material';
import axios from 'axios';
import { DOUYIN_API } from '../config/api';

interface Task {
  task_id: string;
  type: string;
  status: string;
  progress: number;
  result?: any;
  error?: string;
  created_at: string;
  updated_at: string;
}

const TaskManager: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState<NodeJS.Timeout | null>(null);
  const theme = useTheme();

  const fetchTasks = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('未登录或登录已过期');
      }

      const response = await axios.get(DOUYIN_API.TASKS, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });

      setTasks(response.data);
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

  const refreshTasks = () => {
    fetchTasks();
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
    }
  };

  const downloadVideo = (videoUrl: string, filename: string) => {
    const token = localStorage.getItem('token');
    if (!token) {
      setError('未登录或登录已过期');
      return;
    }

    // 创建一个带有认证头的下载链接
    const a = document.createElement('a');
    a.href = `${videoUrl}?token=${token}`;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  const getStatusChip = (status: string) => {
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
        icon = <ScheduledIcon />;
        label = '已调度';
        break;
      case 'running':
        color = 'primary';
        icon = <RunningIcon />;
        label = '运行中';
        break;
      case 'completed':
        color = 'success';
        icon = <CheckCircleIcon />;
        label = '已完成';
        break;
      case 'failed':
        color = 'error';
        icon = <ErrorIcon />;
        label = '失败';
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
        sx={{ fontWeight: 'medium' }}
      />
    );
  };

  useEffect(() => {
    fetchTasks();

    // 设置定时刷新，每10秒刷新一次
    const interval = setInterval(() => {
      fetchTasks();
    }, 10000);
    setRefreshInterval(interval);

    return () => {
      if (refreshInterval) {
        clearInterval(refreshInterval);
      }
    };
  }, []);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const getTaskTypeLabel = (type: string) => {
    switch (type) {
      case 'video_processing':
        return '视频处理';
      case 'video_upload':
        return '视频上传';
      case 'post_scheduling':
        return '发布调度';
      default:
        return type;
    }
  };

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

          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
              <CircularProgress />
            </Box>
          ) : tasks.length === 0 ? (
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
          ) : (
            <TableContainer component={Paper} sx={{ borderRadius: 2, boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
              <Table>
                <TableHead sx={{ bgcolor: theme.palette.primary.light }}>
                  <TableRow>
                    <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>任务ID</TableCell>
                    <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>类型</TableCell>
                    <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>状态</TableCell>
                    <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>进度</TableCell>
                    <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>创建时间</TableCell>
                    <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>更新时间</TableCell>
                    <TableCell sx={{ color: 'white', fontWeight: 'bold' }}>操作</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {tasks.map((task) => (
                    <Fade in={true} key={task.task_id}>
                      <TableRow 
                        hover
                        sx={{
                          '&:hover': {
                            bgcolor: 'rgba(63, 81, 181, 0.04)',
                          }
                        }}
                      >
                        <TableCell>{task.task_id.slice(0, 8)}...</TableCell>
                        <TableCell>{getTaskTypeLabel(task.type)}</TableCell>
                        <TableCell>{getStatusChip(task.status)}</TableCell>
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
                        <TableCell>{formatDate(task.created_at)}</TableCell>
                        <TableCell>{formatDate(task.updated_at)}</TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', gap: 1 }}>
                            <Tooltip title="查看详情">
                              <IconButton 
                                size="small" 
                                onClick={() => fetchTaskDetails(task.task_id)}
                                sx={{ color: theme.palette.info.main }}
                              >
                                <InfoIcon />
                              </IconButton>
                            </Tooltip>
                            {task.status === 'completed' && task.result?.video_url && (
                              <Tooltip title="下载视频">
                                <IconButton 
                                  size="small" 
                                  onClick={() => downloadVideo(task.result.video_url, task.result.filename || `processed_video_${task.task_id}.mp4`)}
                                  sx={{ color: theme.palette.success.main }}
                                >
                                  <DownloadIcon />
                                </IconButton>
                              </Tooltip>
                            )}
                          </Box>
                        </TableCell>
                      </TableRow>
                    </Fade>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
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
                      {getTaskTypeLabel(selectedTask.type)}
                    </Typography>
                  </Box>
                  <Box sx={{ mb: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      状态:
                    </Typography>
                    <Box sx={{ mt: 0.5 }}>
                      {getStatusChip(selectedTask.status)}
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
                      {formatDate(selectedTask.created_at)}
                    </Typography>
                  </Box>
                  <Box sx={{ mb: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      更新时间:
                    </Typography>
                    <Typography variant="body1">
                      {formatDate(selectedTask.updated_at)}
                    </Typography>
                  </Box>
                  <Box sx={{ mb: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      运行时长:
                    </Typography>
                    <Typography variant="body1">
                      {(() => {
                        const created = new Date(selectedTask.created_at).getTime();
                        const updated = new Date(selectedTask.updated_at).getTime();
                        const diffSeconds = Math.floor((updated - created) / 1000);
                        const minutes = Math.floor(diffSeconds / 60);
                        const seconds = diffSeconds % 60;
                        return `${minutes}分${seconds}秒`;
                      })()}
                    </Typography>
                  </Box>
                </Paper>
              </Grid>

              {selectedTask.result && (
                <Grid item xs={12}>
                  <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                    处理结果
                  </Typography>
                  <Paper sx={{ p: 2, bgcolor: 'rgba(0, 0, 0, 0.02)', borderRadius: 2 }}>
                    {selectedTask.result.video_url ? (
                      <Box>
                        <Box sx={{ mb: 2 }}>
                          <Typography variant="body2" color="text.secondary" gutterBottom>
                            处理后的视频:
                          </Typography>
                          {selectedTask.result.thumbnail_url && (
                            <Box 
                              component="img" 
                              src={selectedTask.result.thumbnail_url} 
                              alt="视频缩略图"
                              sx={{ 
                                width: '100%', 
                                maxWidth: 320, 
                                borderRadius: 2,
                                boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                                mb: 2
                              }}
                            />
                          )}
                          <Button
                            variant="contained"
                            startIcon={<DownloadIcon />}
                            onClick={() => downloadVideo(selectedTask.result.video_url, selectedTask.result.filename || `processed_video_${selectedTask.task_id}.mp4`)}
                            sx={{
                              background: 'linear-gradient(45deg, #4caf50 30%, #81c784 90%)',
                              boxShadow: '0 3px 5px 2px rgba(76, 175, 80, .3)',
                            }}
                          >
                            下载视频
                          </Button>
                        </Box>
                        {selectedTask.result.processing_info && (
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
                      <Typography variant="body2">
                        无可用结果
                      </Typography>
                    )}
                  </Paper>
                </Grid>
              )}

              {selectedTask.error && (
                <Grid item xs={12}>
                  <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                    错误信息
                  </Typography>
                  <Alert severity="error" sx={{ borderRadius: 2 }}>
                    {selectedTask.error}
                  </Alert>
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