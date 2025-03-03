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
} from '@mui/material';
import { CloudUpload as CloudUploadIcon } from '@mui/icons-material';
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

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      setSelectedFiles(event.target.files);
    }
  };

  const handleTextChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setText(event.target.value);
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

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    
    if (!selectedFiles || selectedFiles.length === 0) {
      setError('请选择至少一个视频文件');
      return;
    }

    if (!text.trim()) {
      setError('请输入要替换的文字内容');
      return;
    }

    setIsProcessing(true);
    setError('');

    try {
      const formData = new FormData();
      Array.from(selectedFiles).forEach(file => {
        formData.append('videos', file);
      });
      formData.append('text', text);

      const response = await axios.post(DOUYIN_API.BATCH_PROCESS_VIDEOS, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data.success) {
        setProcessingTasks(response.data.tasks);
        // 开始定期检查任务状态
        const interval = setInterval(async () => {
          await updateTaskStatus(response.data.tasks);
          // 如果所有任务都完成了，停止检查
          const allCompleted = response.data.tasks.every(
            (task: ProcessingTask) => task.status === 'completed' || task.status === 'failed'
          );
          if (allCompleted) {
            clearInterval(interval);
            setIsProcessing(false);
          }
        }, 3000);
      }
    } catch (error: any) {
      setError(error.response?.data?.detail || '处理失败，请重试');
      setIsProcessing(false);
    }
  };

  return (
    <Container component="main" maxWidth="lg">
      <Paper elevation={3} sx={{ p: 4, mt: 8 }}>
        <Typography component="h1" variant="h4" align="center" gutterBottom>
          AI视频处理
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        <Box component="form" onSubmit={handleSubmit} sx={{ mt: 3 }}>
          <input
            type="file"
            multiple
            accept="video/*"
            onChange={handleFileChange}
            style={{ display: 'none' }}
            id="video-upload-input"
          />
          <label htmlFor="video-upload-input">
            <Button
              variant="contained"
              component="span"
              startIcon={<CloudUploadIcon />}
              sx={{ mb: 3 }}
              fullWidth
            >
              选择视频文件
            </Button>
          </label>

          {selectedFiles && selectedFiles.length > 0 && (
            <Typography variant="body2" sx={{ mb: 2 }}>
              已选择 {selectedFiles.length} 个文件
            </Typography>
          )}

          <TextField
            fullWidth
            multiline
            rows={4}
            variant="outlined"
            label="要替换的文字内容"
            value={text}
            onChange={handleTextChange}
            sx={{ mb: 3 }}
          />

          <Button
            type="submit"
            fullWidth
            variant="contained"
            color="primary"
            disabled={isProcessing || !selectedFiles || !text.trim()}
            sx={{ mb: 3 }}
          >
            {isProcessing ? '处理中...' : '开始处理'}
          </Button>

          {processingTasks.length > 0 && (
            <List>
              {processingTasks.map((task) => (
                <ListItem key={task.task_id}>
                  <ListItemText
                    primary={`文件: ${task.original_filename}`}
                    secondary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <Typography variant="body2">
                          状态: {task.status || '等待中'}
                        </Typography>
                        {task.progress !== undefined && (
                          <CircularProgress
                            variant="determinate"
                            value={task.progress}
                            size={20}
                          />
                        )}
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
          )}
        </Box>
      </Paper>
    </Container>
  );
};

export default AIVideoProcessor;