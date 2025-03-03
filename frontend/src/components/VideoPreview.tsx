import React, { useState, useEffect } from 'react';
import {
  Box,
  Dialog,
  DialogTitle,
  DialogContent,
  Typography,
  CircularProgress,
  IconButton,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import axios from 'axios';
import { DOUYIN_API } from '../config/api';

interface VideoPreviewProps {
  videoPath: string;
  open: boolean;
  onClose: () => void;
}

interface VideoInfo {
  size: number;
  duration: number;
  created: string;
}

const VideoPreview: React.FC<VideoPreviewProps> = ({ videoPath, open, onClose }) => {
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
    >
      <DialogTitle>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          视频预览
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>
      <DialogContent>
        {loading ? (
          <Box display="flex" justifyContent="center" alignItems="center" p={4}>
            <CircularProgress />
          </Box>
        ) : error ? (
          <Typography color="error" align="center">
            {error}
          </Typography>
        ) : (
          <Box>
            <Box
              component="video"
              width="100%"
              controls
              src={`/api/v1/douyin/video/${videoPath.split('/').pop()}`}
              sx={{ mb: 2 }}
            />
            {videoInfo && (
              <Box>
                <Typography variant="body2">
                  文件大小: {formatFileSize(videoInfo.size)}
                </Typography>
                <Typography variant="body2">
                  视频时长: {formatDuration(videoInfo.duration)}
                </Typography>
                <Typography variant="body2">
                  创建时间: {new Date(videoInfo.created).toLocaleString()}
                </Typography>
              </Box>
            )}
          </Box>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default VideoPreview;