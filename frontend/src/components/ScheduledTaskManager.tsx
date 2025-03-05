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
  Button,
  IconButton,
  Chip,
  LinearProgress,
  Tabs,
  Tab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
  Grid,
  Alert,
  Snackbar,
  CircularProgress
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Pause as PauseIcon,
  PlayArrow as PlayArrowIcon,
  Schedule as ScheduleIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import axios from 'axios';
import { API_BASE_URL } from '../config';

interface ScheduledTask {
  id: string;
  name: string;
  type: string;
  status: string;
  schedule: {
    type: string; // once, daily, weekly, monthly
    time: string;
    days?: string[]; // for weekly
    date?: number; // for monthly
  };
  data: any;
  last_run: string | null;
  next_run: string | null;
  created_at: string;
  updated_at: string;
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

const ScheduledTaskManager: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [tasks, setTasks] = useState<ScheduledTask[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedTask, setSelectedTask] = useState<ScheduledTask | null>(null);
  const [taskFormData, setTaskFormData] = useState({
    name: '',
    type: '',
    schedule_type: 'once',
    schedule_time: new Date(),
    schedule_days: [] as string[],
    schedule_date: 1
  });

  // 获取任务列表
  useEffect(() => {
    fetchTasks();
  }, []);

  const fetchTasks = async () => {
    setLoading(true);
    try {
      // 这里应该调用实际的API
      // const response = await axios.get(`${API_BASE_URL}/scheduled-tasks`);
      // setTasks(response.data);
      
      // 模拟数据
      setTasks([
        {
          id: '1',
          name: '每日抖音内容分发',
          type: 'content_distribution',
          status: 'active',
          schedule: {
            type: 'daily',
            time: '09:00:00',
          },
          data: {
            platforms: ['douyin'],
            accounts: [{ id: 1, username: 'account1' }],
            media_path: '/uploads/videos/sample.mp4',
            title: '每日精彩内容',
            description: '自动分发的内容'
          },
          last_run: '2023-06-01T09:00:00Z',
          next_run: '2023-06-02T09:00:00Z',
          created_at: '2023-05-01T10:00:00Z',
          updated_at: '2023-05-01T10:00:00Z'
        },
        {
          id: '2',
          name: '周末视频采集',
          type: 'content_collection',
          status: 'paused',
          schedule: {
            type: 'weekly',
            time: '10:00:00',
            days: ['saturday', 'sunday']
          },
          data: {
            keywords: ['旅游', '美食'],
            platforms: ['douyin', 'kuaishou'],
            limit: 50
          },
          last_run: '2023-05-28T10:00:00Z',
          next_run: '2023-06-03T10:00:00Z',
          created_at: '2023-05-15T14:30:00Z',
          updated_at: '2023-05-15T14:30:00Z'
        },
        {
          id: '3',
          name: '月度数据分析',
          type: 'data_analysis',
          status: 'active',
          schedule: {
            type: 'monthly',
            time: '00:00:00',
            date: 1
          },
          data: {
            report_type: 'performance',
            email_to: 'admin@example.com'
          },
          last_run: '2023-06-01T00:00:00Z',
          next_run: '2023-07-01T00:00:00Z',
          created_at: '2023-04-20T11:15:00Z',
          updated_at: '2023-04-20T11:15:00Z'
        }
      ]);
    } catch (err) {
      console.error('获取定时任务失败:', err);
      setError('获取定时任务列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 处理选项卡切换
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  // 打开编辑对话框
  const handleEditTask = (task: ScheduledTask) => {
    setSelectedTask(task);
    setTaskFormData({
      name: task.name,
      type: task.type,
      schedule_type: task.schedule.type,
      schedule_time: new Date(),
      schedule_days: task.schedule.days || [],
      schedule_date: task.schedule.date || 1
    });
    setEditDialogOpen(true);
  };

  // 打开删除对话框
  const handleDeleteTask = (task: ScheduledTask) => {
    setSelectedTask(task);
    setDeleteDialogOpen(true);
  };

  // 暂停/恢复任务
  const handleToggleTaskStatus = async (task: ScheduledTask) => {
    try {
      const newStatus = task.status === 'active' ? 'paused' : 'active';
      
      // 这里应该调用实际的API
      // await axios.patch(`${API_BASE_URL}/scheduled-tasks/${task.id}`, {
      //   status: newStatus
      // });
      
      // 更新本地状态
      setTasks(tasks.map(t => 
        t.id === task.id ? { ...t, status: newStatus } : t
      ));
      
      setSuccess(`任务已${newStatus === 'active' ? '激活' : '暂停'}`);
    } catch (err) {
      console.error('更新任务状态失败:', err);
      setError('更新任务状态失败');
    }
  };

  // 提交编辑表单
  const handleSubmitEdit = async () => {
    if (!selectedTask) return;
    
    try {
      // 这里应该调用实际的API
      // await axios.put(`${API_BASE_URL}/scheduled-tasks/${selectedTask.id}`, {
      //   name: taskFormData.name,
      //   schedule: {
      //     type: taskFormData.schedule_type,
      //     time: taskFormData.schedule_time.toTimeString().split(' ')[0],
      //     days: taskFormData.schedule_type === 'weekly' ? taskFormData.schedule_days : undefined,
      //     date: taskFormData.schedule_type === 'monthly' ? taskFormData.schedule_date : undefined
      //   }
      // });
      
      // 更新本地状态
      setTasks(tasks.map(t => 
        t.id === selectedTask.id ? { 
          ...t, 
          name: taskFormData.name,
          schedule: {
            type: taskFormData.schedule_type,
            time: taskFormData.schedule_time.toTimeString().split(' ')[0],
            days: taskFormData.schedule_type === 'weekly' ? taskFormData.schedule_days : undefined,
            date: taskFormData.schedule_type === 'monthly' ? taskFormData.schedule_date : undefined
          },
          updated_at: new Date().toISOString()
        } : t
      ));
      
      setSuccess('任务已更新');
      setEditDialogOpen(false);
    } catch (err) {
      console.error('更新任务失败:', err);
      setError('更新任务失败');
    }
  };

  // 确认删除任务
  const handleConfirmDelete = async () => {
    if (!selectedTask) return;
    
    try {
      // 这里应该调用实际的API
      // await axios.delete(`${API_BASE_URL}/scheduled-tasks/${selectedTask.id}`);
      
      // 更新本地状态
      setTasks(tasks.filter(t => t.id !== selectedTask.id));
      
      setSuccess('任务已删除');
      setDeleteDialogOpen(false);
    } catch (err) {
      console.error('删除任务失败:', err);
      setError('删除任务失败');
    }
  };

  // 处理表单变化
  const handleFormChange = (e: React.ChangeEvent<HTMLInputElement | { name?: string; value: unknown }>) => {
    const { name, value } = e.target;
    setTaskFormData({
      ...taskFormData,
      [name as string]: value
    });
  };

  // 处理Select变化
  const handleSelectChange = (event: SelectChangeEvent) => {
    const { name, value } = event.target;
    setTaskFormData({
      ...taskFormData,
      [name as string]: value
    });
  };

  // 处理日期时间变化
  const handleDateTimeChange = (date: Date | null) => {
    if (date) {
      setTaskFormData({
        ...taskFormData,
        schedule_time: date
      });
    }
  };

  // 处理周几选择变化
  const handleDaysChange = (event: SelectChangeEvent<string[]>) => {
    const { value } = event.target;
    setTaskFormData({
      ...taskFormData,
      schedule_days: typeof value === 'string' ? value.split(',') : value
    });
  };

  // 获取任务类型显示文本
  const getTaskTypeText = (type: string) => {
    switch (type) {
      case 'content_distribution': return '内容分发';
      case 'content_collection': return '内容采集';
      case 'data_analysis': return '数据分析';
      default: return type;
    }
  };

  // 获取任务状态显示文本
  const getTaskStatusText = (status: string) => {
    switch (status) {
      case 'active': return '运行中';
      case 'paused': return '已暂停';
      case 'completed': return '已完成';
      case 'failed': return '失败';
      default: return status;
    }
  };

  // 获取任务状态颜色
  const getTaskStatusColor = (status: string): 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' => {
    switch (status) {
      case 'active': return 'success';
      case 'paused': return 'warning';
      case 'completed': return 'info';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  // 获取计划类型显示文本
  const getScheduleTypeText = (type: string) => {
    switch (type) {
      case 'once': return '一次性';
      case 'daily': return '每日';
      case 'weekly': return '每周';
      case 'monthly': return '每月';
      default: return type;
    }
  };

  // 格式化日期时间
  const formatDateTime = (dateTimeStr: string | null) => {
    if (!dateTimeStr) return '未设置';
    return new Date(dateTimeStr).toLocaleString();
  };

  // 获取周几显示文本
  const getDayText = (day: string) => {
    const dayMap: Record<string, string> = {
      'monday': '周一',
      'tuesday': '周二',
      'wednesday': '周三',
      'thursday': '周四',
      'friday': '周五',
      'saturday': '周六',
      'sunday': '周日'
    };
    return dayMap[day] || day;
  };

  // 渲染计划详情
  const renderScheduleDetails = (task: ScheduledTask) => {
    const { schedule } = task;
    const time = schedule.time.split(':').slice(0, 2).join(':');
    
    switch (schedule.type) {
      case 'once':
        return `一次性 ${time}`;
      case 'daily':
        return `每天 ${time}`;
      case 'weekly':
        if (schedule.days && schedule.days.length > 0) {
          return `每周 ${schedule.days.map(getDayText).join('、')} ${time}`;
        }
        return `每周 ${time}`;
      case 'monthly':
        return `每月 ${schedule.date || 1}日 ${time}`;
      default:
        return '未知计划';
    }
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Typography variant="h5" gutterBottom>
        定时任务管理
      </Typography>
      
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={handleTabChange} aria-label="定时任务选项卡">
          <Tab label="所有任务" />
          <Tab label="内容分发" />
          <Tab label="内容采集" />
          <Tab label="数据分析" />
        </Tabs>
      </Box>
      
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2, mb: 2 }}>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={fetchTasks}
          sx={{ mr: 1 }}
        >
          刷新
        </Button>
        <Button
          variant="contained"
          startIcon={<ScheduleIcon />}
        >
          创建任务
        </Button>
      </Box>
      
      {/* 所有任务选项卡 */}
      <TabPanel value={tabValue} index={0}>
        {renderTaskTable(tasks)}
      </TabPanel>
      
      {/* 内容分发选项卡 */}
      <TabPanel value={tabValue} index={1}>
        {renderTaskTable(tasks.filter(task => task.type === 'content_distribution'))}
      </TabPanel>
      
      {/* 内容采集选项卡 */}
      <TabPanel value={tabValue} index={2}>
        {renderTaskTable(tasks.filter(task => task.type === 'content_collection'))}
      </TabPanel>
      
      {/* 数据分析选项卡 */}
      <TabPanel value={tabValue} index={3}>
        {renderTaskTable(tasks.filter(task => task.type === 'data_analysis'))}
      </TabPanel>
      
      {/* 编辑任务对话框 */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>编辑定时任务</DialogTitle>
        <DialogContent>
          <TextField
            margin="dense"
            name="name"
            label="任务名称"
            type="text"
            fullWidth
            value={taskFormData.name}
            onChange={handleFormChange}
            sx={{ mb: 2 }}
          />
          
          <FormControl fullWidth margin="dense" sx={{ mb: 2 }}>
            <InputLabel>计划类型</InputLabel>
            <Select
              name="schedule_type"
              value={taskFormData.schedule_type}
              label="计划类型"
              onChange={handleSelectChange}
            >
              <MenuItem value="once">一次性</MenuItem>
              <MenuItem value="daily">每日</MenuItem>
              <MenuItem value="weekly">每周</MenuItem>
              <MenuItem value="monthly">每月</MenuItem>
            </Select>
          </FormControl>
          
          <LocalizationProvider dateAdapter={AdapterDateFns}>
            <DateTimePicker
              label="执行时间"
              value={taskFormData.schedule_time}
              onChange={handleDateTimeChange}
              sx={{ width: '100%', mb: 2 }}
            />
          </LocalizationProvider>
          
          {taskFormData.schedule_type === 'weekly' && (
            <FormControl fullWidth margin="dense" sx={{ mb: 2 }}>
              <InputLabel>执行日</InputLabel>
              <Select
                multiple
                name="schedule_days"
                value={taskFormData.schedule_days}
                label="执行日"
                onChange={handleDaysChange}
                renderValue={(selected) => selected.map(getDayText).join(', ')}
              >
                <MenuItem value="monday">周一</MenuItem>
                <MenuItem value="tuesday">周二</MenuItem>
                <MenuItem value="wednesday">周三</MenuItem>
                <MenuItem value="thursday">周四</MenuItem>
                <MenuItem value="friday">周五</MenuItem>
                <MenuItem value="saturday">周六</MenuItem>
                <MenuItem value="sunday">周日</MenuItem>
              </Select>
            </FormControl>
          )}
          
          {taskFormData.schedule_type === 'monthly' && (
            <TextField
              margin="dense"
              name="schedule_date"
              label="执行日期"
              type="number"
              fullWidth
              value={taskFormData.schedule_date}
              onChange={handleFormChange}
              inputProps={{ min: 1, max: 31 }}
              sx={{ mb: 2 }}
            />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>取消</Button>
          <Button onClick={handleSubmitEdit} variant="contained">保存</Button>
        </DialogActions>
      </Dialog>
      
      {/* 删除任务确认对话框 */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>确认删除</DialogTitle>
        <DialogContent>
          <Typography>
            确定要删除任务 "{selectedTask?.name}" 吗？此操作不可撤销。
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>取消</Button>
          <Button onClick={handleConfirmDelete} color="error">删除</Button>
        </DialogActions>
      </Dialog>
      
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

  // 渲染任务表格
  function renderTaskTable(taskList: ScheduledTask[]) {
    return (
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>任务名称</TableCell>
              <TableCell>类型</TableCell>
              <TableCell>状态</TableCell>
              <TableCell>计划</TableCell>
              <TableCell>上次执行</TableCell>
              <TableCell>下次执行</TableCell>
              <TableCell>创建时间</TableCell>
              <TableCell>操作</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  <CircularProgress size={24} />
                </TableCell>
              </TableRow>
            ) : taskList.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  暂无任务
                </TableCell>
              </TableRow>
            ) : (
              taskList.map((task) => (
                <TableRow key={task.id}>
                  <TableCell>{task.name}</TableCell>
                  <TableCell>{getTaskTypeText(task.type)}</TableCell>
                  <TableCell>
                    <Chip 
                      label={getTaskStatusText(task.status)} 
                      color={getTaskStatusColor(task.status)} 
                      size="small" 
                    />
                  </TableCell>
                  <TableCell>{renderScheduleDetails(task)}</TableCell>
                  <TableCell>{formatDateTime(task.last_run)}</TableCell>
                  <TableCell>{formatDateTime(task.next_run)}</TableCell>
                  <TableCell>{new Date(task.created_at).toLocaleDateString()}</TableCell>
                  <TableCell>
                    <IconButton 
                      size="small" 
                      onClick={() => handleToggleTaskStatus(task)}
                      title={task.status === 'active' ? '暂停' : '激活'}
                      sx={{ mr: 1 }}
                    >
                      {task.status === 'active' ? <PauseIcon fontSize="small" /> : <PlayArrowIcon fontSize="small" />}
                    </IconButton>
                    <IconButton 
                      size="small" 
                      onClick={() => handleEditTask(task)}
                      title="编辑"
                      sx={{ mr: 1 }}
                    >
                      <EditIcon fontSize="small" />
                    </IconButton>
                    <IconButton 
                      size="small" 
                      onClick={() => handleDeleteTask(task)}
                      title="删除"
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
    );
  }
};

export default ScheduledTaskManager; 