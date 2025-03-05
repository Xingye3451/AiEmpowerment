import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  TextField,
  Button,
  IconButton,
  Grid,
  Card,
  CardContent,
  CardActions,
  CardMedia,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
  TablePagination,
  CircularProgress,
  Alert,
  Snackbar,
  Tooltip,
  Stack,
  Autocomplete
} from '@mui/material';
import {
  Search as SearchIcon,
  Download as DownloadIcon,
  Favorite as FavoriteIcon,
  Comment as CommentIcon,
  Share as ShareIcon,
  Visibility as VisibilityIcon,
  FilterList as FilterListIcon,
  Refresh as RefreshIcon,
  PlayArrow as PlayArrowIcon
} from '@mui/icons-material';
import axios from 'axios';
import { API_BASE_URL } from '../config';

interface VideoInfo {
  id: string;
  platform: string;
  title: string;
  description: string;
  author: string;
  thumbnail: string;
  video_url: string;
  duration: number;
  stats: {
    likes: number;
    comments: number;
    shares: number;
    views: number;
  };
  tags: string[];
  created_at: string;
}

interface SearchFilters {
  platform: string;
  timeRange: string;
  sortBy: string;
  minLikes?: number;
  minViews?: number;
  tags: string[];
}

const ContentCollector: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<SearchFilters>({
    platform: 'douyin',
    timeRange: 'today',
    sortBy: 'likes',
    tags: []
  });
  const [videos, setVideos] = useState<VideoInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [filterDialogOpen, setFilterDialogOpen] = useState(false);
  const [selectedVideo, setSelectedVideo] = useState<VideoInfo | null>(null);
  const [previewDialogOpen, setPreviewDialogOpen] = useState(false);
  const [availableTags, setAvailableTags] = useState<string[]>([]);

  // 获取视频列表
  useEffect(() => {
    if (searchQuery) {
      searchVideos();
    }
  }, [searchQuery, filters, page, rowsPerPage]);

  // 获取可用标签
  useEffect(() => {
    fetchAvailableTags();
  }, []);

  const fetchAvailableTags = async () => {
    try {
      // 这里应该调用实际的API
      // const response = await axios.get(`${API_BASE_URL}/content/tags`);
      // setAvailableTags(response.data);
      
      // 模拟数据
      setAvailableTags(['搞笑', '美食', '旅游', '音乐', '舞蹈', '游戏', '知识', '生活', '时尚', '运动']);
    } catch (err) {
      console.error('获取标签失败:', err);
    }
  };

  const searchVideos = async () => {
    setLoading(true);
    try {
      // 这里应该调用实际的API
      // const response = await axios.get(`${API_BASE_URL}/content/search`, {
      //   params: {
      //     q: searchQuery,
      //     ...filters,
      //     page,
      //     per_page: rowsPerPage
      //   }
      // });
      // setVideos(response.data);
      
      // 模拟数据
      const mockVideos: VideoInfo[] = Array(10).fill(null).map((_, index) => ({
        id: `video-${index}`,
        platform: 'douyin',
        title: `测试视频 ${index + 1}`,
        description: '这是一个测试视频描述',
        author: '测试作者',
        thumbnail: 'https://picsum.photos/300/200',
        video_url: 'https://example.com/video.mp4',
        duration: 60,
        stats: {
          likes: Math.floor(Math.random() * 10000),
          comments: Math.floor(Math.random() * 1000),
          shares: Math.floor(Math.random() * 500),
          views: Math.floor(Math.random() * 50000)
        },
        tags: ['搞笑', '生活'],
        created_at: new Date().toISOString()
      }));
      setVideos(mockVideos);
    } catch (err) {
      console.error('搜索视频失败:', err);
      setError('搜索视频失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    setPage(0);
    searchVideos();
  };

  const handleFilterChange = (event: SelectChangeEvent<unknown>) => {
    const { name, value } = event.target;
    setFilters({
      ...filters,
      [name]: value
    });
  };

  const handleTagsChange = (event: any, newValue: string[]) => {
    setFilters({
      ...filters,
      tags: newValue
    });
  };

  const handleDownload = async (video: VideoInfo) => {
    try {
      // 这里应该调用实际的API
      // await axios.post(`${API_BASE_URL}/content/download`, {
      //   video_id: video.id,
      //   platform: video.platform
      // });
      setSuccess('开始下载视频');
    } catch (err) {
      console.error('下载视频失败:', err);
      setError('下载视频失败');
    }
  };

  const handlePreview = (video: VideoInfo) => {
    setSelectedVideo(video);
    setPreviewDialogOpen(true);
  };

  const formatNumber = (num: number): string => {
    if (num >= 10000) {
      return (num / 10000).toFixed(1) + 'w';
    }
    if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'k';
    }
    return num.toString();
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Typography variant="h5" gutterBottom>
        内容采集中心
      </Typography>
      
      {/* 搜索栏 */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="搜索关键词"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <Stack direction="row" spacing={1}>
              <Button
                variant="contained"
                startIcon={<SearchIcon />}
                onClick={handleSearch}
                disabled={!searchQuery || loading}
              >
                搜索
              </Button>
              <Button
                variant="outlined"
                startIcon={<FilterListIcon />}
                onClick={() => setFilterDialogOpen(true)}
              >
                筛选
              </Button>
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={searchVideos}
                disabled={loading}
              >
                刷新
              </Button>
            </Stack>
          </Grid>
        </Grid>
      </Paper>
      
      {/* 视频列表 */}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
          <CircularProgress />
        </Box>
      ) : videos.length === 0 ? (
        <Paper sx={{ p: 3, textAlign: 'center' }}>
          <Typography color="textSecondary">
            暂无视频数据
          </Typography>
        </Paper>
      ) : (
        <Grid container spacing={2}>
          {videos.map((video) => (
            <Grid item xs={12} sm={6} md={4} key={video.id}>
              <Card>
                <CardMedia
                  component="img"
                  height="200"
                  image={video.thumbnail}
                  alt={video.title}
                  sx={{ cursor: 'pointer' }}
                  onClick={() => handlePreview(video)}
                />
                <CardContent>
                  <Typography variant="h6" noWrap>
                    {video.title}
                  </Typography>
                  <Typography variant="body2" color="textSecondary" noWrap>
                    {video.author}
                  </Typography>
                  <Box sx={{ mt: 1, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {video.tags.map((tag) => (
                      <Chip key={tag} label={tag} size="small" />
                    ))}
                  </Box>
                  <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between' }}>
                    <Tooltip title="点赞数">
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <FavoriteIcon fontSize="small" sx={{ mr: 0.5 }} />
                        <Typography variant="body2">
                          {formatNumber(video.stats.likes)}
                        </Typography>
                      </Box>
                    </Tooltip>
                    <Tooltip title="评论数">
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <CommentIcon fontSize="small" sx={{ mr: 0.5 }} />
                        <Typography variant="body2">
                          {formatNumber(video.stats.comments)}
                        </Typography>
                      </Box>
                    </Tooltip>
                    <Tooltip title="分享数">
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <ShareIcon fontSize="small" sx={{ mr: 0.5 }} />
                        <Typography variant="body2">
                          {formatNumber(video.stats.shares)}
                        </Typography>
                      </Box>
                    </Tooltip>
                    <Tooltip title="播放量">
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <VisibilityIcon fontSize="small" sx={{ mr: 0.5 }} />
                        <Typography variant="body2">
                          {formatNumber(video.stats.views)}
                        </Typography>
                      </Box>
                    </Tooltip>
                  </Box>
                </CardContent>
                <CardActions>
                  <Button
                    size="small"
                    startIcon={<PlayArrowIcon />}
                    onClick={() => handlePreview(video)}
                  >
                    预览
                  </Button>
                  <Button
                    size="small"
                    startIcon={<DownloadIcon />}
                    onClick={() => handleDownload(video)}
                  >
                    下载
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
      
      {/* 分页控制 */}
      <TablePagination
        component="div"
        count={100} // 总数应该从API获取
        page={page}
        onPageChange={(event, newPage) => setPage(newPage)}
        rowsPerPage={rowsPerPage}
        onRowsPerPageChange={(event) => {
          setRowsPerPage(parseInt(event.target.value, 10));
          setPage(0);
        }}
        labelRowsPerPage="每页显示"
      />
      
      {/* 筛选对话框 */}
      <Dialog
        open={filterDialogOpen}
        onClose={() => setFilterDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>筛选条件</DialogTitle>
        <DialogContent>
          <FormControl fullWidth margin="normal">
            <InputLabel>平台</InputLabel>
            <Select
              name="platform"
              value={filters.platform}
              label="平台"
              onChange={handleFilterChange}
            >
              <MenuItem value="douyin">抖音</MenuItem>
              <MenuItem value="kuaishou">快手</MenuItem>
              <MenuItem value="bilibili">哔哩哔哩</MenuItem>
            </Select>
          </FormControl>
          
          <FormControl fullWidth margin="normal">
            <InputLabel>时间范围</InputLabel>
            <Select
              name="timeRange"
              value={filters.timeRange}
              label="时间范围"
              onChange={handleFilterChange}
            >
              <MenuItem value="today">今天</MenuItem>
              <MenuItem value="week">本周</MenuItem>
              <MenuItem value="month">本月</MenuItem>
              <MenuItem value="all">全部</MenuItem>
            </Select>
          </FormControl>
          
          <FormControl fullWidth margin="normal">
            <InputLabel>排序方式</InputLabel>
            <Select
              name="sortBy"
              value={filters.sortBy}
              label="排序方式"
              onChange={handleFilterChange}
            >
              <MenuItem value="likes">按点赞数</MenuItem>
              <MenuItem value="views">按播放量</MenuItem>
              <MenuItem value="comments">按评论数</MenuItem>
              <MenuItem value="shares">按分享数</MenuItem>
              <MenuItem value="date">按发布时间</MenuItem>
            </Select>
          </FormControl>
          
          <FormControl fullWidth margin="normal">
            <Autocomplete
              multiple
              options={availableTags}
              value={filters.tags}
              onChange={handleTagsChange}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="标签"
                  placeholder="选择标签"
                />
              )}
            />
          </FormControl>
          
          <TextField
            fullWidth
            margin="normal"
            label="最小点赞数"
            type="number"
            name="minLikes"
            value={filters.minLikes || ''}
            onChange={(e) => handleFilterChange({
              target: { name: 'minLikes', value: e.target.value }
            } as any)}
          />
          
          <TextField
            fullWidth
            margin="normal"
            label="最小播放量"
            type="number"
            name="minViews"
            value={filters.minViews || ''}
            onChange={(e) => handleFilterChange({
              target: { name: 'minViews', value: e.target.value }
            } as any)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setFilterDialogOpen(false)}>取消</Button>
          <Button
            variant="contained"
            onClick={() => {
              setFilterDialogOpen(false);
              searchVideos();
            }}
          >
            应用
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* 预览对话框 */}
      <Dialog
        open={previewDialogOpen}
        onClose={() => setPreviewDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>视频预览</DialogTitle>
        <DialogContent>
          {selectedVideo && (
            <>
              <Box sx={{ position: 'relative', paddingTop: '56.25%' }}>
                <Box
                  component="video"
                  src={selectedVideo.video_url}
                  controls
                  sx={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    height: '100%'
                  }}
                />
              </Box>
              <Typography variant="h6" sx={{ mt: 2 }}>
                {selectedVideo.title}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                {selectedVideo.description}
              </Typography>
              <Box sx={{ mt: 1 }}>
                <Typography variant="subtitle2">
                  作者: {selectedVideo.author}
                </Typography>
                <Typography variant="subtitle2">
                  发布时间: {new Date(selectedVideo.created_at).toLocaleString()}
                </Typography>
              </Box>
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPreviewDialogOpen(false)}>关闭</Button>
          {selectedVideo && (
            <Button
              variant="contained"
              startIcon={<DownloadIcon />}
              onClick={() => {
                handleDownload(selectedVideo);
                setPreviewDialogOpen(false);
              }}
            >
              下载
            </Button>
          )}
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
};

export default ContentCollector; 