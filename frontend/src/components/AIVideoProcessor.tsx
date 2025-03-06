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
  Grid,
  RadioGroup,
  Radio,
  FormControl,
  FormLabel,
  Switch
} from '@mui/material';
import { 
  CloudUpload as CloudUploadIcon,
  Delete as DeleteIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  NavigateNext as NavigateNextIcon,
  NavigateBefore as NavigateBeforeIcon,
  Close as CloseIcon,
  Cloud as CloudIcon,
  Computer as ComputerIcon
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
  const [processingMode, setProcessingMode] = useState<'cloud' | 'local'>('cloud');
  const [localProcessingAvailable, setLocalProcessingAvailable] = useState<boolean>(false);

  // 辅助函数：构建完整URL
  const buildFullUrl = (url: string): string => {
    if (url.startsWith('http') || url.startsWith('data:')) {
      return url; // 已经是完整URL或者是data URL
    }
    
    // 如果是相对路径，添加基础URL
    // 强制使用后端服务器地址
    const baseUrl = 'http://localhost:8000';
    return url.startsWith('/') ? `${baseUrl}${url}` : `${baseUrl}/${url}`;
  };

  // 从视频文件生成预览图
  const generatePreviewFromVideo = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      try {
        // 创建视频元素
        const video = document.createElement('video');
        video.preload = 'metadata';
        
        // 创建对象URL
        const objectUrl = URL.createObjectURL(file);
        video.src = objectUrl;
        
        // 视频加载完成后生成预览图
        video.onloadedmetadata = () => {
          // 设置视频时间到1秒处
          video.currentTime = 1;
          
          // 当视频跳转到指定时间后生成预览图
          video.onseeked = () => {
            // 创建canvas
            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            
            // 绘制视频帧
            const ctx = canvas.getContext('2d');
            if (ctx) {
              ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
              
              // 转换为base64
              const dataUrl = canvas.toDataURL('image/jpeg');
              
              // 释放资源
              URL.revokeObjectURL(objectUrl);
              
              resolve(dataUrl);
            } else {
              reject(new Error('无法获取canvas上下文'));
            }
          };
          
          // 处理视频跳转失败
          video.onerror = () => {
            URL.revokeObjectURL(objectUrl);
            reject(new Error('视频跳转失败'));
          };
        };
        
        // 处理视频加载失败
        video.onerror = () => {
          URL.revokeObjectURL(objectUrl);
          reject(new Error('视频加载失败'));
        };
      } catch (error) {
        reject(error);
      }
    });
  };

  const adjustCanvasSize = () => {
    if (!canvasRef.current || !imgRef.current) return;
    
    canvasRef.current.width = imgRef.current.offsetWidth;
    canvasRef.current.height = imgRef.current.offsetHeight;
    
    // 如果当前预览已有选区，则绘制它
    drawSelectedArea();
  };

  const drawSelectedArea = () => {
    if (!canvasRef.current) return;
    
    const ctx = canvasRef.current.getContext('2d');
    if (!ctx) return;
    
    // 清除画布
    ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
    
    // 获取当前预览的选区
    const selectedArea = videoPreviews[currentPreviewIndex]?.selectedArea;
    
    if (selectedArea) {
      ctx.strokeStyle = 'red';
      ctx.lineWidth = 2;
      ctx.strokeRect(
        selectedArea.x, 
        selectedArea.y, 
        selectedArea.width, 
        selectedArea.height
      );
      
      ctx.fillStyle = 'rgba(255, 0, 0, 0.2)';
      ctx.fillRect(
        selectedArea.x, 
        selectedArea.y, 
        selectedArea.width, 
        selectedArea.height
      );
    }
  };

  useEffect(() => {
    if (imgRef.current) {
      const handleImageLoad = () => {
        adjustCanvasSize();
        imgRef.current?.removeEventListener('load', handleImageLoad);
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

  useEffect(() => {
    if (isAreaSelectionOpen && videoPreviews.length > 0) {
      // 确保图片加载后调整画布大小
      if (imgRef.current) {
        if (imgRef.current.complete) {
          adjustCanvasSize();
        } else {
          const handleImageLoad = () => {
            adjustCanvasSize();
            imgRef.current?.removeEventListener('load', handleImageLoad);
          };
          
          const handleImageError = (e: Event) => {
            // 获取当前图片URL
            const currentUrl = imgRef.current?.src || '';
            
            // 如果当前URL已经是默认预览图，则不再尝试加载
            if (currentUrl.includes('default_preview.jpg')) {
              // 创建一个简单的内联预览图
              try {
                const canvas = document.createElement('canvas');
                canvas.width = 480;
                canvas.height = 270;
                const ctx = canvas.getContext('2d');
                if (ctx) {
                  // 绘制灰色背景
                  ctx.fillStyle = '#f0f0f0';
                  ctx.fillRect(0, 0, canvas.width, canvas.height);
                  
                  // 绘制文字
                  ctx.fillStyle = '#808080';
                  ctx.font = '16px Arial';
                  ctx.textAlign = 'center';
                  ctx.textBaseline = 'middle';
                  ctx.fillText('预览图加载失败', canvas.width / 2, canvas.height / 2);
                  
                  // 转换为data URL
                  const dataUrl = canvas.toDataURL('image/jpeg');
                  
                  if (imgRef.current) {
                    imgRef.current.src = dataUrl;
                  }
                  
                  // 更新预览数组
                  setVideoPreviews(prev => {
                    const newPreviews = [...prev];
                    if (newPreviews[currentPreviewIndex]) {
                      newPreviews[currentPreviewIndex] = {
                        ...newPreviews[currentPreviewIndex],
                        previewUrl: dataUrl
                      };
                    }
                    return newPreviews;
                  });
                }
              } catch (error) {
                console.error('创建内联预览图失败:', error);
              }
              
              return;
            }
            
            // 使用默认预览图
            const defaultPreviewUrl = buildFullUrl('/static/previews/default_preview.jpg');
            
            if (imgRef.current) {
              imgRef.current.src = defaultPreviewUrl;
            }
            
            // 更新预览数组
            setVideoPreviews(prev => {
              const newPreviews = [...prev];
              if (newPreviews[currentPreviewIndex]) {
                newPreviews[currentPreviewIndex] = {
                  ...newPreviews[currentPreviewIndex],
                  previewUrl: defaultPreviewUrl
                };
              }
              return newPreviews;
            });
            
            imgRef.current?.removeEventListener('error', handleImageError);
          };
          
          imgRef.current.addEventListener('load', handleImageLoad);
          imgRef.current.addEventListener('error', handleImageError);
          
          return () => {
            imgRef.current?.removeEventListener('load', handleImageLoad);
            imgRef.current?.removeEventListener('error', handleImageError);
          };
        }
      }
    }
  }, [currentPreviewIndex, videoPreviews, isAreaSelectionOpen]);

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
          formData.append('file', file);
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

          if (uploadResponse.data) {
            // 检查后端返回的数据中是否包含预览图和视频URL
            const hasPreviewUrl = 'preview_url' in uploadResponse.data;
            const hasVideoUrl = 'video_url' in uploadResponse.data;
            const hasSuccess = 'success' in uploadResponse.data;
            
            // 如果响应中包含success字段且为false，则表示上传失败
            if (hasSuccess && !uploadResponse.data.success) {
              throw new Error(`视频 ${file.name} 上传失败: ${uploadResponse.data.detail || '未知错误'}`);
            }
            
            // 直接使用后端返回的URL
            let previewUrl = uploadResponse.data.preview_url;
            let videoUrl = uploadResponse.data.video_url;
            
            // 如果后端没有返回预览图URL，则根据文件名构造一个
            if (!previewUrl) {
              // 从文件路径中提取文件名
              const filePath = uploadResponse.data.saved_path || uploadResponse.data.file_path || '';
              const fileName = filePath.split('/').pop() || file.name;
              const fileNameWithoutExt = fileName.split('.')[0];
              
              // 构造预览图URL
              previewUrl = `/static/previews/${fileNameWithoutExt}.jpg`;
            }
            
            // 如果后端没有返回视频URL，则根据文件名构造一个
            if (!videoUrl) {
              // 从文件路径中提取文件名
              const filePath = uploadResponse.data.saved_path || uploadResponse.data.file_path || '';
              const fileName = filePath.split('/').pop() || file.name;
              
              // 构造视频URL
              videoUrl = `/static/videos/${fileName}`;
            }
            
            // 确保URL是完整的
            previewUrl = buildFullUrl(previewUrl);
            videoUrl = buildFullUrl(videoUrl);
            
            // 验证预览图URL是否有效
            try {
              const previewResponse = await fetch(previewUrl, { method: 'HEAD' });
              
              if (!previewResponse.ok) {
                // 尝试生成本地预览图
                try {
                  const localPreviewUrl = await generatePreviewFromVideo(file);
                  previewUrl = localPreviewUrl;
                } catch (previewError) {
                  // 使用默认预览图
                  previewUrl = buildFullUrl('/static/previews/default_preview.jpg');
                }
              }
            } catch (error) {
              // 尝试生成本地预览图
              try {
                const localPreviewUrl = await generatePreviewFromVideo(file);
                previewUrl = localPreviewUrl;
              } catch (previewError) {
                // 使用默认预览图
                previewUrl = buildFullUrl('/static/previews/default_preview.jpg');
              }
            }
            
            previews.push({ 
              file, 
              previewUrl: previewUrl,
              uploadPath: uploadResponse.data.saved_path || uploadResponse.data.file_path || ''
            });
          } else {
            throw new Error(`视频 ${file.name} 上传失败: 服务器响应格式不正确`);
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
        setIsAreaSelectionOpen(true);
        setCurrentPreviewIndex(0);
        setIsUploading(false);
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
    formData.append('processing_mode', processingMode);

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

  useEffect(() => {
    const checkLocalProcessingAvailability = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) return;
        
        const response = await axios.get(DOUYIN_API.CHECK_LOCAL_PROCESSING, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (response.data && typeof response.data === 'object' && 'available' in response.data) {
          setLocalProcessingAvailable(response.data.available);
        } else {
          console.error('本地处理可用性数据格式不正确:', response.data);
          setLocalProcessingAvailable(false);
        }
      } catch (error) {
        console.error('检查本地处理可用性失败:', error);
        setLocalProcessingAvailable(false);
      }
    };
    
    checkLocalProcessingAvailability();
  }, []);

  // 监控区域选择对话框状态
  useEffect(() => {
    console.log('isAreaSelectionOpen状态变化:', isAreaSelectionOpen);
    console.log('videoPreviews状态:', videoPreviews);
  }, [isAreaSelectionOpen, videoPreviews]);

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

          <Box sx={{ mb: 3, p: 2, bgcolor: 'rgba(63, 81, 181, 0.04)', borderRadius: 2 }}>
            <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'medium' }}>
              处理模式
            </Typography>
            
            <FormControl component="fieldset">
              <RadioGroup
                row
                value={processingMode}
                onChange={(e) => setProcessingMode(e.target.value as 'cloud' | 'local')}
              >
                <FormControlLabel 
                  value="cloud" 
                  control={<Radio />} 
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <CloudIcon sx={{ mr: 1, color: theme.palette.primary.main }} />
                      <Typography>云服务处理</Typography>
                    </Box>
                  }
                />
                <FormControlLabel 
                  value="local" 
                  disabled={!localProcessingAvailable}
                  control={<Radio />} 
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <ComputerIcon sx={{ mr: 1, color: localProcessingAvailable ? theme.palette.success.main : theme.palette.text.disabled }} />
                      <Typography>本地处理</Typography>
                      {!localProcessingAvailable && (
                        <Typography variant="caption" sx={{ ml: 1, color: theme.palette.text.secondary }}>
                          (即将推出)
                        </Typography>
                      )}
                    </Box>
                  }
                />
              </RadioGroup>
            </FormControl>
            
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
              {processingMode === 'cloud' 
                ? '云服务处理: 使用专业AI云服务进行处理，速度快，质量高，无需本地GPU' 
                : '本地处理: 使用您的计算机进行处理，保护隐私，无需联网，但需要较高配置'}
            </Typography>
          </Box>

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
        onClose={() => {
          console.log('对话框关闭事件触发');
          setIsAreaSelectionOpen(false);
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
            onClick={() => {
              console.log('关闭按钮点击');
              setIsAreaSelectionOpen(false);
            }}
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
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            bgcolor: '#000',
            overflow: 'hidden',
            padding: '20px'
          }}>
            {videoPreviews.length > 0 ? (
              <>
                <Typography color="white" sx={{ mb: 2 }}>
                  请在预览图上框选需要移除字幕的区域
                </Typography>
                
                {videoPreviews[currentPreviewIndex]?.previewUrl ? (
                  <>
                    <Box sx={{ position: 'relative', width: '100%', textAlign: 'center' }}>
                      <img
                        ref={imgRef}
                        src={videoPreviews[currentPreviewIndex]?.previewUrl}
                        alt={`视频预览 ${currentPreviewIndex + 1}`}
                        style={{ 
                          maxWidth: '100%', 
                          maxHeight: '60vh',
                          display: 'block',
                          margin: '0 auto',
                          objectFit: 'contain'
                        }}
                        onLoad={(e) => {
                          adjustCanvasSize();
                        }}
                        onError={(e) => {
                          // 获取当前图片URL
                          const currentUrl = imgRef.current?.src || '';
                          
                          // 如果当前URL已经是默认预览图，则不再尝试加载
                          if (currentUrl.includes('default_preview.jpg')) {
                            // 创建一个简单的内联预览图
                            try {
                              const canvas = document.createElement('canvas');
                              canvas.width = 480;
                              canvas.height = 270;
                              const ctx = canvas.getContext('2d');
                              if (ctx) {
                                // 绘制灰色背景
                                ctx.fillStyle = '#f0f0f0';
                                ctx.fillRect(0, 0, canvas.width, canvas.height);
                                
                                // 绘制文字
                                ctx.fillStyle = '#808080';
                                ctx.font = '16px Arial';
                                ctx.textAlign = 'center';
                                ctx.textBaseline = 'middle';
                                ctx.fillText('预览图加载失败', canvas.width / 2, canvas.height / 2);
                                
                                // 转换为data URL
                                const dataUrl = canvas.toDataURL('image/jpeg');
                                
                                if (imgRef.current) {
                                  imgRef.current.src = dataUrl;
                                }
                                
                                // 更新预览数组
                                setVideoPreviews(prev => {
                                  const newPreviews = [...prev];
                                  if (newPreviews[currentPreviewIndex]) {
                                    newPreviews[currentPreviewIndex] = {
                                      ...newPreviews[currentPreviewIndex],
                                      previewUrl: dataUrl
                                    };
                                  }
                                  return newPreviews;
                                });
                              }
                            } catch (error) {
                              console.error('创建内联预览图失败:', error);
                            }
                            
                            return;
                          }
                          
                          // 使用默认预览图
                          const defaultPreviewUrl = buildFullUrl('/static/previews/default_preview.jpg');
                          
                          if (imgRef.current) {
                            imgRef.current.src = defaultPreviewUrl;
                          }
                          
                          // 更新预览数组
                          setVideoPreviews(prev => {
                            const newPreviews = [...prev];
                            if (newPreviews[currentPreviewIndex]) {
                              newPreviews[currentPreviewIndex] = {
                                ...newPreviews[currentPreviewIndex],
                                previewUrl: defaultPreviewUrl
                              };
                            }
                            return newPreviews;
                          });
                        }}
                      />
                      <canvas
                        ref={canvasRef}
                        onMouseDown={handleCanvasMouseDown}
                        onMouseMove={handleCanvasMouseMove}
                        onMouseUp={handleCanvasMouseUp}
                        style={{
                          position: 'absolute',
                          top: '0',
                          left: '50%',
                          transform: 'translateX(-50%)',
                          cursor: 'crosshair',
                          width: imgRef.current?.offsetWidth || '100%',
                          height: imgRef.current?.offsetHeight || '100%',
                          pointerEvents: 'auto'
                        }}
                      />
                      
                      {/* 刷新预览图按钮 */}
                      <Button
                        variant="contained"
                        color="primary"
                        size="small"
                        sx={{ 
                          position: 'absolute', 
                          top: 10, 
                          right: 10,
                          opacity: 0.8,
                          '&:hover': {
                            opacity: 1
                          }
                        }}
                        onClick={() => {
                          if (imgRef.current) {
                            // 构造一个带有时间戳的URL，强制刷新
                            const currentUrl = videoPreviews[currentPreviewIndex]?.previewUrl;
                            const refreshUrl = currentUrl.includes('?') 
                              ? `${currentUrl}&t=${Date.now()}` 
                              : `${currentUrl}?t=${Date.now()}`;
                            
                            console.log('刷新预览图:', refreshUrl);
                            
                            // 更新预览数组
                            setVideoPreviews(prev => {
                              const updated = [...prev];
                              if (updated[currentPreviewIndex]) {
                                updated[currentPreviewIndex] = {
                                  ...updated[currentPreviewIndex],
                                  previewUrl: refreshUrl
                                };
                              }
                              return updated;
                            });
                            
                            // 直接设置图片源
                            imgRef.current.src = refreshUrl;
                          }
                        }}
                      >
                        刷新预览
                      </Button>
                    </Box>
                    <Typography color="white" sx={{ mt: 2 }}>
                      提示：如果预览图不清晰，您仍可以大致框选字幕区域
                    </Typography>
                  </>
                ) : (
                  <Typography color="error">
                    预览图加载失败，请重试
                  </Typography>
                )}
              </>
            ) : (
              <Typography color="white">没有可用的预览图</Typography>
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