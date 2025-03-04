import React, { useState, useEffect } from 'react';
import {
  Box,
  Dialog,
  DialogTitle,
  DialogContent,
  Typography,
  CircularProgress,
  IconButton,
  Alert,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import axios from 'axios';
import { DOUYIN_API } from '../config/api';
import { useTheme } from '@mui/material/styles';

interface VideoPreviewProps {
  videoPath: string;
  open: boolean;
  onClose: () => void;
}

interface VideoInfo {
  size: number;
  duration: number;
  created: string;
  width: number;
  height: number;
}

const VideoPreview: React.FC<VideoPreviewProps> = ({ videoPath, open, onClose }) => {
  const theme = useTheme();
  const [loading, setLoading] = useState(true);
  const [previewUrl, setPreviewUrl] = useState('');
  const [videoInfo, setVideoInfo] = useState<VideoInfo | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!videoPath || !open) return;

    const loadPreview = async () => {
      try {
        setLoading(true);
        setError('');

        const filename = videoPath.split('/').pop();
        if (!filename) return;
        
        const response = await axios.post(DOUYIN_API.PREVIEW(filename));
        
        setPreviewUrl(response.data.preview_url);
        setVideoInfo(response.data.video_info);
      } catch (error: any) {
        setError(error.response?.data?.detail || '加载预览失败');
      } finally {
        setLoading(false);
      }
    };

    loadPreview();
  }, [videoPath, open]);

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  };

  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      sx={{
        '& .MuiDialog-paper': {
          borderRadius: 3,
          background: 'linear-gradient(45deg, #e8eaf6 30%, #ffffff 90%)',
          boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
        }
      }}
    >
      <DialogTitle sx={{ 
        display: 'flex', 
        justifyContent: 'space-between',
        alignItems: 'center',
        background: 'linear-gradient(45deg, #3f51b5 30%, #757de8 90%)',
        color: 'white',
        py: 2
      }}>
        <Typography variant="h6" component="div" sx={{ fontWeight: 'bold' }}>
          视频预览
        </Typography>
        <IconButton
          edge="end"
          color="inherit"
          onClick={onClose}
          aria-label="close"
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent sx={{ p: 3 }}>
        {loading ? (
          <Box sx={{ 
            display: 'flex', 
            justifyContent: 'center', 
            alignItems: 'center',
            minHeight: 300
          }}>
            <CircularProgress 
              sx={{ 
                color: theme.palette.primary.main 
              }} 
            />
          </Box>
        ) : error ? (
          <Alert 
            severity="error"
            sx={{ 
              borderRadius: 2,
              boxShadow: '0 2px 10px rgba(244, 67, 54, 0.2)'
            }}
          >
            {error}
          </Alert>
        ) : (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Box 
              sx={{ 
                position: 'relative',
                width: '100%',
                paddingTop: '56.25%', // 16:9 宽高比
                borderRadius: 2,
                overflow: 'hidden',
                boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
              }}
            >
              <Box
                component="video"
                src={previewUrl}
                controls
                sx={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  height: '100%',
                  objectFit: 'contain',
                  backgroundColor: 'black',
                }}
              />
            </Box>

            {videoInfo && (
              <Box 
                sx={{ 
                  mt: 2,
                  p: 2,
                  borderRadius: 2,
                  backgroundColor: 'rgba(63, 81, 181, 0.04)',
                  border: '1px solid',
                  borderColor: 'primary.light'
                }}
              >
                <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'medium', color: 'primary.main' }}>
                  视频信息
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                  <Typography variant="body2" color="text.secondary">
                    文件大小: {formatFileSize(videoInfo.size)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    时长: {formatDuration(videoInfo.duration)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    分辨率: {videoInfo.width} x {videoInfo.height}
                  </Typography>
                </Box>
              </Box>
            )}
          </Box>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default VideoPreview;