import React, { useState } from 'react';
import {
  Box,
  Button,
  Container,
  Paper,
  Typography,
  TextField,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  Alert,
  Card,
  CardContent,
  Fade,
  Zoom,
  IconButton,
  useTheme,
  Divider
} from '@mui/material';
import { 
  CloudUpload as CloudUploadIcon,
  Delete as DeleteIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import axios from 'axios';
import { DOUYIN_API } from '../config/api';

interface ProcessingTask {
  task_id: string;
  original_filename: string;
  processed_filename: string;
  status?: string;
  progress?: number;
}

const AIVideoProcessor: React.FC = () => {
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null);
  const [text, setText] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingTasks, setProcessingTasks] = useState<ProcessingTask[]>([]);
  const [error, setError] = useState('');
  const theme = useTheme();

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      setSelectedFiles(event.target.files);
      setError('');
    }
  };

  const handleTextChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setText(event.target.value);
    setError('');
  };

  const updateTaskStatus = async (tasks: ProcessingTask[]) => {
    const updatedTasks = await Promise.all(
      tasks.map(async (task) => {
        try {
          const response = await axios.get(DOUYIN_API.PROCESS_STATUS(task.task_id));
          return {
            ...task,
            status: response.data.status,
            progress: response.data.progress,
          };
        } catch (error) {
          console.error(`Error updating task status: ${task.task_id}`, error);
          return task;
        }
      })
    );
    setProcessingTasks(updatedTasks);
  };

  const handleSubmit = async () => {
    if (!selectedFiles || selectedFiles.length === 0) {
      setError('请选择要处理的视频文件');
      return;
    }

    setIsProcessing(true);
    setError('');

    const formData = new FormData();
    Array.from(selectedFiles).forEach((file) => {
      formData.append('files', file);
    });
    formData.append('text', text);

    try {
      const response = await axios.post(DOUYIN_API.BATCH_PROCESS_VIDEOS, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setProcessingTasks([...processingTasks, ...response.data.tasks]);
    } catch (err: any) {
      setError(err.response?.data?.detail || '视频处理失败');
      console.error('Error processing video:', err);
    } finally {
      setIsProcessing(false);
      setSelectedFiles(null);
      setText('');
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <Card 
        elevation={3} 
        sx={{ 
          borderRadius: 3,
          background: 'linear-gradient(45deg, #e8eaf6 30%, #ffffff 90%)',
          mb: 3
        }}
      >
        <CardContent>
          <Typography 
            variant="h5" 
            gutterBottom 
            sx={{ 
              fontWeight: 'bold',
              color: theme.palette.primary.main,
              mb: 2
            }}
          >
            AI视频处理
          </Typography>

          <Box 
            component="label"
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              p: 3,
              mb: 3,
              border: '2px dashed',
              borderColor: theme.palette.primary.main,
              borderRadius: 2,
              cursor: 'pointer',
              transition: 'all 0.3s',
              backgroundColor: 'rgba(63, 81, 181, 0.04)',
              '&:hover': {
                backgroundColor: 'rgba(63, 81, 181, 0.08)',
                transform: 'translateY(-2px)',
              }
            }}
          >
            <input
              type="file"
              multiple
              onChange={handleFileChange}
              style={{ display: 'none' }}
              accept="video/*"
            />
            <CloudUploadIcon 
              sx={{ 
                fontSize: 48,
                color: theme.palette.primary.main,
                mb: 2
              }} 
            />
            <Typography variant="h6" sx={{ mb: 1, fontWeight: 'medium' }}>
              点击或拖拽上传视频
            </Typography>
            <Typography variant="body2" color="text.secondary">
              支持多个视频文件同时上传
            </Typography>
          </Box>

          <TextField
            fullWidth
            multiline
            rows={4}
            label="AI处理文本"
            value={text}
            onChange={handleTextChange}
            sx={{
              mb: 3,
              '& .MuiOutlinedInput-root': {
                backgroundColor: '#ffffff',
                borderRadius: 1,
                boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
              }
            }}
          />

          <Button
            variant="contained"
            onClick={handleSubmit}
            disabled={isProcessing || !selectedFiles}
            sx={{
              background: 'linear-gradient(45deg, #3f51b5 30%, #757de8 90%)',
              boxShadow: '0 3px 5px 2px rgba(63, 81, 181, .3)',
              transition: 'transform 0.3s',
              '&:hover': {
                transform: 'translateY(-2px)',
              }
            }}
          >
            {isProcessing ? '处理中...' : '开始处理'}
          </Button>
        </CardContent>
      </Card>

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

      {processingTasks.length > 0 && (
        <Card 
          elevation={3} 
          sx={{ 
            borderRadius: 3,
            background: 'linear-gradient(45deg, #e8eaf6 30%, #ffffff 90%)',
          }}
        >
          <CardContent>
            <Typography 
              variant="h5" 
              gutterBottom 
              sx={{ 
                fontWeight: 'bold',
                color: theme.palette.primary.main,
                mb: 2
              }}
            >
              处理任务
            </Typography>

            <List>
              {processingTasks.map((task, index) => (
                <Fade in={true} key={task.task_id}>
                  <ListItem
                    sx={{
                      bgcolor: 'background.paper',
                      borderRadius: 2,
                      mb: 1,
                      boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
                      transition: 'transform 0.2s',
                      '&:hover': {
                        transform: 'translateX(8px)'
                      }
                    }}
                  >
                    <ListItemText
                      primary={task.original_filename}
                      secondary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          {task.status === 'completed' ? (
                            <CheckCircleIcon sx={{ color: theme.palette.success.main }} />
                          ) : task.status === 'failed' ? (
                            <ErrorIcon sx={{ color: theme.palette.error.main }} />
                          ) : (
                            <CircularProgress
                              variant="determinate"
                              value={task.progress || 0}
                              size={20}
                              sx={{ color: theme.palette.primary.main }}
                            />
                          )}
                          <Typography variant="body2" color="text.secondary">
                            {task.status === 'completed' ? '处理完成' : 
                             task.status === 'failed' ? '处理失败' :
                             `处理中 ${task.progress}%`}
                          </Typography>
                        </Box>
                      }
                    />
                  </ListItem>
                </Fade>
              ))}
            </List>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default AIVideoProcessor;