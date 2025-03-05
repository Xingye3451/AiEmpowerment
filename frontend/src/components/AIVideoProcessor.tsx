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
  NavigateBefore as NavigateBeforeIcon,
  Close as CloseIcon
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
  uploadPath?: string;
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
  const imgRef = useRef<HTMLImageElement>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadSuccess, setUploadSuccess] = useState(false);

  const adjustCanvasSize = () => {
    if (canvasRef.current && imgRef.current && imgRef.current.complete) {
      const imgWidth = imgRef.current.naturalWidth;
      const imgHeight = imgRef.current.naturalHeight;
      
      canvasRef.current.width = imgWidth;
      canvasRef.current.height = imgHeight;
      
      console.log(`调整canvas尺寸: ${imgWidth}x${imgHeight}`);
      
      drawSelectedArea();
    }
  };

  const drawSelectedArea = () => {
    if (!canvasRef.current || !videoPreviews.length || currentPreviewIndex >= videoPreviews.length) return;
    
    const ctx = canvasRef.current.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
    
    const currentPreview = videoPreviews[currentPreviewIndex];
    if (currentPreview.selectedArea) {
      const { x, y, width, height } = currentPreview.selectedArea;
      
      ctx.strokeStyle = 'red';
      ctx.lineWidth = 2;
      ctx.strokeRect(x, y, width, height);
      
      ctx.fillStyle = 'rgba(255, 0, 0, 0.2)';
      ctx.fillRect(x, y, width, height);
      
      console.log(`绘制选区 - 视频${currentPreviewIndex + 1}:`, { x, y, width, height });
    }
  };

  useEffect(() => {
    if (imgRef.current) {
      const handleImageLoad = () => {
        console.log(`图片加载完成 - 视频${currentPreviewIndex + 1}`);
        adjustCanvasSize();
      };

      if (imgRef.current.complete) {
        handleImageLoad();
      } else {
        imgRef.current.addEventListener('load', handleImageLoad);
        return () => {
          if (imgRef.current) {
            imgRef.current.removeEventListener('load', handleImageLoad);
          }
        };
      }
    }
  }, [currentPreviewIndex, videoPreviews]);

  const generateVideoPreviews = async (files: FileList) => {
    try {
      setIsUploading(true);
      setUploadProgress(0);
      setUploadSuccess(false);
      setError('');
      
      const previews: VideoPreview[] = [];
      const totalFiles = files.length;
      const token = localStorage.getItem('token');
      
      if (!token) {
        throw new Error('未登录或登录已过期，请重新登录');
      }
      
      for (let i = 0; i < files.length; i++) {
        try {
          const file = files[i];
          const formData = new FormData();
          formData.append('video', file);
          formData.append('title', file.name);
          
          const uploadResponse = await axios.post(DOUYIN_API.UPLOAD_VIDEO, formData, {
            headers: {
              'Content-Type': 'multipart/form-data',
              'Authorization': `Bearer ${token}`
            },
            onUploadProgress: (progressEvent) => {
              if (progressEvent.total) {
                const fileProgress = (progressEvent.loaded / progressEvent.total) * 100;
                const overallProgress = ((i / totalFiles) * 100) + (fileProgress / totalFiles);
                setUploadProgress(Math.min(Math.round(overallProgress), 99));
              }
            }
          });

          if (uploadResponse.data.success) {
            const previewUrl = uploadResponse.data.preview_url;
            const videoUrl = uploadResponse.data.video_url;
            
            console.log(`视频 ${i + 1}/${totalFiles} 上传成功:`, {
              previewUrl,
              videoUrl,
              fileName: file.name
            });
            
            previews.push({ 
              file, 
              previewUrl: previewUrl,
              uploadPath: uploadResponse.data.file_path
            });
          } else {
            throw new Error(`视频 ${file.name} 上传失败: ${uploadResponse.data.detail || '未知错误'}`);
          }
        } catch (error: any) {
          console.error(`视频 ${files[i].name} 上传失败:`, error);
          if (error.response?.status === 401) {
            throw new Error('认证失败，请重新登录');
          }
          throw new Error(`视频 ${files[i].name} 上传失败: ${error.response?.data?.detail || error.message || '未知错误'}`);
        }
      }
      
      setUploadProgress(100);
      setUploadSuccess(true);
      setVideoPreviews(previews);
      
      if (previews.length > 0) {
        setTimeout(() => {
          setIsAreaSelectionOpen(true);
          setIsUploading(false);
        }, 1000);
      } else {
        setIsUploading(false);
      }
    } catch (error: any) {
      console.error('视频上传失败:', error);
      setError(error.message || '视频上传失败，请重试');
      setIsUploading(false);
      setUploadSuccess(false);
      
      if (error.response?.status === 401 || error.message.includes('认证失败') || error.message.includes('未登录')) {
        localStorage.removeItem('token');
        window.location.href = '/login';
      }
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

  const handleCanvasMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!canvasRef.current) return;
    const rect = canvasRef.current.getBoundingClientRect();
    
    const scaleX = canvasRef.current.width / rect.width;
    const scaleY = canvasRef.current.height / rect.height;
    const x = (e.clientX - rect.left) * scaleX;
    const y = (e.clientY - rect.top) * scaleY;
    
    setIsDrawing(true);
    setStartPos({ x, y });
    
    const ctx = canvasRef.current.getContext('2d');
    if (ctx) {
      ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
    }
  };

  const handleCanvasMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing || !canvasRef.current) return;
    const rect = canvasRef.current.getBoundingClientRect();
    
    const scaleX = canvasRef.current.width / rect.width;
    const scaleY = canvasRef.current.height / rect.height;
    const x = (e.clientX - rect.left) * scaleX;
    const y = (e.clientY - rect.top) * scaleY;
    
    const ctx = canvasRef.current.getContext('2d');
    if (ctx) {
      ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
      
      const width = x - startPos.x;
      const height = y - startPos.y;
      
      ctx.strokeStyle = 'red';
      ctx.lineWidth = 2;
      ctx.strokeRect(startPos.x, startPos.y, width, height);
      
      ctx.fillStyle = 'rgba(255, 0, 0, 0.2)';
      ctx.fillRect(startPos.x, startPos.y, width, height);
    }
  };

  const handleCanvasMouseUp = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing || !canvasRef.current) return;
    setIsDrawing(false);
    
    const rect = canvasRef.current.getBoundingClientRect();
    
    const scaleX = canvasRef.current.width / rect.width;
    const scaleY = canvasRef.current.height / rect.height;
    const x = (e.clientX - rect.left) * scaleX;
    const y = (e.clientY - rect.top) * scaleY;
    
    const selectedArea = {
      x: Math.min(startPos.x, x),
      y: Math.min(startPos.y, y),
      width: Math.abs(x - startPos.x),
      height: Math.abs(y - startPos.y)
    };
    
    setVideoPreviews(prevPreviews => {
      const newPreviews = [...prevPreviews];
      newPreviews[currentPreviewIndex] = {
        ...newPreviews[currentPreviewIndex],
        selectedArea
      };
      console.log(`保存选区 - 视频${currentPreviewIndex + 1}:`, selectedArea);
      return newPreviews;
    });
    
    drawSelectedArea();
  };

  const handleNextVideo = () => {
    if (currentPreviewIndex < videoPreviews.length - 1) {
      setCurrentPreviewIndex(prevIndex => {
        console.log(`切换到下一个视频: ${prevIndex + 1} -> ${prevIndex + 2}`);
        return prevIndex + 1;
      });
    } else {
      setIsAreaSelectionOpen(false);
      setSelectionComplete(true);
    }
  };

  const handlePrevVideo = () => {
    if (currentPreviewIndex > 0) {
      setCurrentPreviewIndex(prevIndex => {
        console.log(`切换到上一个视频: ${prevIndex + 1} -> ${prevIndex}`);
        return prevIndex - 1;
      });
    }
  };

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

    const token = localStorage.getItem('token');
    if (!token) {
      setError('未登录或登录已过期，请重新登录');
      setIsProcessing(false);
      window.location.href = '/login';
      return;
    }

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
          'Authorization': `Bearer ${token}`
        },
      });
      setProcessingTasks([...processingTasks, ...response.data.tasks]);
    } catch (err: any) {
      console.error('视频处理失败:', err);
      const errorMessage = err.response?.data?.detail || '视频处理失败';
      setError(errorMessage);
      
      if (err.response?.status === 401) {
        localStorage.removeItem('token');
        window.location.href = '/login';
      }
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
              cursor: isUploading ? 'default' : 'pointer',
              transition: 'all 0.3s',
              backgroundColor: 'rgba(63, 81, 181, 0.04)',
              '&:hover': {
                backgroundColor: isUploading ? 'rgba(63, 81, 181, 0.04)' : 'rgba(63, 81, 181, 0.08)',
                transform: isUploading ? 'none' : 'translateY(-2px)',
              }
            }}
          >
            <input
              type="file"
              multiple
              onChange={handleFileChange}
              style={{ display: 'none' }}
              accept="video/*"
              disabled={isUploading}
            />
            
            {isUploading ? (
              <>
                <CircularProgress 
                  variant="determinate" 
                  value={uploadProgress} 
                  size={60}
                  thickness={4}
                  sx={{ 
                    color: theme.palette.primary.main,
                    mb: 2
                  }}
                />
                <Typography variant="h6" sx={{ mb: 1, fontWeight: 'medium' }}>
                  上传中... {uploadProgress}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  请耐心等待，视频正在上传
                </Typography>
              </>
            ) : uploadSuccess && videoPreviews.length > 0 ? (
              <>
                <CheckCircleIcon 
                  sx={{ 
                    fontSize: 48,
                    color: theme.palette.success.main,
                    mb: 2
                  }} 
                />
                <Typography variant="h6" sx={{ mb: 1, fontWeight: 'medium' }}>
                  上传成功
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  已上传 {videoPreviews.length} 个视频文件
                </Typography>
                <Button 
                  variant="outlined" 
                  color="primary" 
                  sx={{ mt: 2 }}
                  onClick={() => setIsAreaSelectionOpen(true)}
                >
                  选择字幕区域
                </Button>
              </>
            ) : (
              <>
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
              </>
            )}
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
              <Tooltip title="生成新的AI字幕">
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

      <Dialog
        open={isAreaSelectionOpen}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 2,
            boxShadow: '0 8px 32px rgba(0,0,0,0.2)',
            overflow: 'hidden'
          }
        }}
      >
        <DialogTitle sx={{ 
          bgcolor: theme.palette.primary.main, 
          color: 'white',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <Typography variant="h6">
            选择字幕区域 ({currentPreviewIndex + 1}/{videoPreviews.length})
          </Typography>
          <IconButton
            edge="end"
            color="inherit"
            onClick={() => setIsAreaSelectionOpen(false)}
            aria-label="close"
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent sx={{ p: 0, position: 'relative' }}>
          <Box sx={{ 
            position: 'relative', 
            width: '100%', 
            height: '100%',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            bgcolor: '#000',
            overflow: 'hidden'
          }}>
            {videoPreviews.length > 0 && (
              <>
                <img
                  ref={imgRef}
                  src={videoPreviews[currentPreviewIndex]?.previewUrl}
                  alt={`视频预览 ${currentPreviewIndex + 1}`}
                  style={{ 
                    maxWidth: '100%', 
                    maxHeight: '70vh',
                    display: 'block',
                    objectFit: 'contain'
                  }}
                  onLoad={adjustCanvasSize}
                />
                <canvas
                  ref={canvasRef}
                  onMouseDown={handleCanvasMouseDown}
                  onMouseMove={handleCanvasMouseMove}
                  onMouseUp={handleCanvasMouseUp}
                  style={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    cursor: 'crosshair',
                    width: imgRef.current?.offsetWidth || '100%',
                    height: imgRef.current?.offsetHeight || '100%',
                    pointerEvents: 'auto'
                  }}
                />
              </>
            )}
          </Box>
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
            onClick={() => {
              const newPreviews = [...videoPreviews];
              newPreviews[currentPreviewIndex] = {
                ...newPreviews[currentPreviewIndex],
                selectedArea: undefined
              };
              setVideoPreviews(newPreviews);
              
              if (canvasRef.current) {
                const ctx = canvasRef.current.getContext('2d');
                if (ctx) {
                  ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
                }
              }
            }}
            color="secondary"
          >
            重置选择
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