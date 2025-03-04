import React, { useState, useRef, useEffect } from 'react';
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
  Divider,
  FormGroup,
  FormControlLabel,
  Checkbox,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Stepper,
  Step,
  StepLabel,
  Grid
} from '@mui/material';
import { 
  CloudUpload as CloudUploadIcon,
  Delete as DeleteIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  NavigateNext as NavigateNextIcon,
  NavigateBefore as NavigateBeforeIcon
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

interface VideoPreview {
  file: File;
  previewUrl: string;
  selectedArea?: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
}

const AIVideoProcessor: React.FC = () => {
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null);
  const [text, setText] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingTasks, setProcessingTasks] = useState<ProcessingTask[]>([]);
  const [error, setError] = useState('');
  const [removeSubtitles, setRemoveSubtitles] = useState(true);
  const [generateSubtitles, setGenerateSubtitles] = useState(false);
  const [videoPreviews, setVideoPreviews] = useState<VideoPreview[]>([]);
  const [currentPreviewIndex, setCurrentPreviewIndex] = useState(0);
  const [isAreaSelectionOpen, setIsAreaSelectionOpen] = useState(false);
  const [selectionComplete, setSelectionComplete] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [startPos, setStartPos] = useState({ x: 0, y: 0 });
  const theme = useTheme();

  // 生成视频预览
  const generateVideoPreviews = async (files: FileList) => {
    const previews: VideoPreview[] = [];
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const previewUrl = URL.createObjectURL(file);
      previews.push({ file, previewUrl });
    }
    setVideoPreviews(previews);
    if (previews.length > 0) {
      setIsAreaSelectionOpen(true);
    }
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      setSelectedFiles(event.target.files);
      generateVideoPreviews(event.target.files);
      setError('');
    }
  };

  const handleTextChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setText(event.target.value);
    setError('');
  };

  // 处理区域选择
  const handleCanvasMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!canvasRef.current) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    setIsDrawing(true);
    setStartPos({ x, y });
  };

  const handleCanvasMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing || !canvasRef.current) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    const ctx = canvasRef.current.getContext('2d');
    if (!ctx) return;

    // 清除之前的绘制
    ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
    
    // 绘制视频帧
    const video = document.createElement('video');
    video.src = videoPreviews[currentPreviewIndex].previewUrl;
    ctx.drawImage(video, 0, 0, canvasRef.current.width, canvasRef.current.height);
    
    // 绘制选择框
    ctx.strokeStyle = '#00ff00';
    ctx.lineWidth = 2;
    ctx.strokeRect(
      startPos.x,
      startPos.y,
      x - startPos.x,
      y - startPos.y
    );
  };

  const handleCanvasMouseUp = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing || !canvasRef.current) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    setIsDrawing(false);
    
    // 保存选择区域
    const newPreviews = [...videoPreviews];
    newPreviews[currentPreviewIndex].selectedArea = {
      x: Math.min(startPos.x, x),
      y: Math.min(startPos.y, y),
      width: Math.abs(x - startPos.x),
      height: Math.abs(y - startPos.y)
    };
    setVideoPreviews(newPreviews);
  };

  const handleNextVideo = () => {
    if (currentPreviewIndex < videoPreviews.length - 1) {
      setCurrentPreviewIndex(currentPreviewIndex + 1);
    } else {
      setIsAreaSelectionOpen(false);
      setSelectionComplete(true);
    }
  };

  const handlePrevVideo = () => {
    if (currentPreviewIndex > 0) {
      setCurrentPreviewIndex(currentPreviewIndex - 1);
    }
  };

  useEffect(() => {
    if (isAreaSelectionOpen && canvasRef.current) {
      const video = document.createElement('video');
      video.src = videoPreviews[currentPreviewIndex].previewUrl;
      video.onloadeddata = () => {
        if (!canvasRef.current) return;
        const ctx = canvasRef.current.getContext('2d');
        if (!ctx) return;
        ctx.drawImage(video, 0, 0, canvasRef.current.width, canvasRef.current.height);
      };
    }
  }, [currentPreviewIndex, isAreaSelectionOpen]);

  const handleSubmit = async () => {
    if (!selectedFiles || selectedFiles.length === 0) {
      setError('请选择要处理的视频文件');
      return;
    }

    if (!selectionComplete) {
      setError('请先完成所有视频的字幕区域选择');
      return;
    }

    setIsProcessing(true);
    setError('');

    const formData = new FormData();
    videoPreviews.forEach((preview, index) => {
      formData.append('videos', preview.file);
      formData.append(`video_areas[${index}]`, JSON.stringify(preview.selectedArea));
    });
    formData.append('text', text);
    formData.append('remove_subtitles', removeSubtitles.toString());
    formData.append('generate_subtitles', generateSubtitles.toString());

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
      setVideoPreviews([]);
      setSelectionComplete(false);
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

          <FormGroup sx={{ mb: 3 }}>
            <Box sx={{ 
              p: 2, 
              bgcolor: 'background.paper', 
              borderRadius: 2,
              boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
            }}>
              <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 'medium', color: theme.palette.primary.main }}>
                字幕处理选项
              </Typography>
              <Tooltip title="移除视频中已有的字幕">
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={removeSubtitles}
                      onChange={(e) => setRemoveSubtitles(e.target.checked)}
                      color="primary"
                    />
                  }
                  label="移除原字幕"
                />
              </Tooltip>
              <Tooltip title="为新的配音生成对应的字幕">
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={generateSubtitles}
                      onChange={(e) => setGenerateSubtitles(e.target.checked)}
                      color="primary"
                    />
                  }
                  label="生成新字幕"
                />
              </Tooltip>
            </Box>
          </FormGroup>

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

      {/* 区域选择对话框 */}
      <Dialog
        open={isAreaSelectionOpen}
        maxWidth="md"
        fullWidth
        onClose={() => setIsAreaSelectionOpen(false)}
      >
        <DialogTitle>
          选择字幕区域 ({currentPreviewIndex + 1}/{videoPreviews.length})
        </DialogTitle>
        <DialogContent>
          <Box sx={{ position: 'relative', width: '100%', height: '400px' }}>
            <canvas
              ref={canvasRef}
              width={640}
              height={360}
              onMouseDown={handleCanvasMouseDown}
              onMouseMove={handleCanvasMouseMove}
              onMouseUp={handleCanvasMouseUp}
              style={{
                border: '1px solid #ccc',
                cursor: 'crosshair'
              }}
            />
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            请在视频预览中框选需要擦除字幕的区域
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button
            onClick={handlePrevVideo}
            disabled={currentPreviewIndex === 0}
            startIcon={<NavigateBeforeIcon />}
          >
            上一个
          </Button>
          <Button
            onClick={handleNextVideo}
            color="primary"
            endIcon={<NavigateNextIcon />}
          >
            {currentPreviewIndex === videoPreviews.length - 1 ? '完成' : '下一个'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AIVideoProcessor;