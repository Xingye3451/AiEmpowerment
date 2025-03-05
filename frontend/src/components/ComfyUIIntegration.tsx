import React, { useState, useEffect, useRef } from 'react';
import { 
  Box, Typography, Paper, Button, TextField, Grid, 
  Card, CardContent, Divider, Alert, CircularProgress,
  Tabs, Tab, IconButton, Tooltip
} from '@mui/material';
import axios from 'axios';
import RefreshIcon from '@mui/icons-material/Refresh';
import SaveIcon from '@mui/icons-material/Save';
import SettingsIcon from '@mui/icons-material/Settings';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import FullscreenIcon from '@mui/icons-material/Fullscreen';
import FullscreenExitIcon from '@mui/icons-material/FullscreenExit';

interface ComfyUIIntegrationProps {
  // 可以添加任何需要的属性
}

const ComfyUIIntegration: React.FC<ComfyUIIntegrationProps> = () => {
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');
  const [activeTab, setActiveTab] = useState<number>(0);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);
  const [savedWorkflows, setSavedWorkflows] = useState<any[]>([]);
  const [proxyUrl, setProxyUrl] = useState<string>('');
  const iframeRef = useRef<HTMLIFrameElement>(null);

  useEffect(() => {
    // 尝试连接到ComfyUI
    checkConnection();
    // 加载保存的工作流
    fetchSavedWorkflows();
    // 获取代理URL
    fetchProxyUrl();
  }, []);

  const fetchProxyUrl = async () => {
    try {
      const response = await axios.get('/api/comfyui/proxy-url');
      setProxyUrl(response.data.url);
    } catch (err) {
      console.error('获取代理URL失败:', err);
      setError('无法获取ComfyUI代理URL');
    }
  };

  const checkConnection = async () => {
    setIsLoading(true);
    setError('');
    try {
      // 通过后端API检查ComfyUI是否可访问
      const response = await axios.get('/api/comfyui/check-connection');
      setIsConnected(response.data.connected);
      if (!response.data.connected) {
        setError(response.data.message);
      }
    } catch (err) {
      console.error('连接ComfyUI失败:', err);
      setError('无法连接到ComfyUI服务，请联系管理员');
      setIsConnected(false);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchSavedWorkflows = async () => {
    try {
      const response = await axios.get('/api/comfyui/workflows');
      setSavedWorkflows(response.data);
    } catch (err) {
      console.error('获取保存的工作流失败:', err);
    }
  };

  const saveCurrentWorkflow = async () => {
    try {
      if (!iframeRef.current) return;
      
      // 向iframe发送消息获取当前工作流
      iframeRef.current.contentWindow?.postMessage({ type: 'getWorkflow' }, '*');
      
      // 监听来自iframe的消息
      const handleMessage = (event: MessageEvent) => {
        if (event.data.type === 'workflow') {
          // 保存工作流到后端
          axios.post('/api/comfyui/workflows', {
            name: `工作流 ${new Date().toLocaleString()}`,
            data: event.data.workflow
          }).then(() => {
            fetchSavedWorkflows();
          });
          
          window.removeEventListener('message', handleMessage);
        }
      };
      
      window.addEventListener('message', handleMessage);
    } catch (err) {
      console.error('保存工作流失败:', err);
      setError('保存工作流失败');
    }
  };

  const loadWorkflow = (workflow: any) => {
    if (!iframeRef.current) return;
    
    // 向iframe发送消息加载工作流
    iframeRef.current.contentWindow?.postMessage({ 
      type: 'loadWorkflow', 
      workflow: workflow.data 
    }, '*');
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Paper elevation={3} sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={6}>
            <Typography variant="h5" component="h2" gutterBottom>
              ComfyUI 集成
              <Tooltip title="ComfyUI是一个功能强大的AI图像生成工具，支持节点式工作流">
                <IconButton size="small" sx={{ ml: 1 }}>
                  <HelpOutlineIcon />
                </IconButton>
              </Tooltip>
            </Typography>
          </Grid>
          <Grid item xs={12} md={6}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, justifyContent: 'flex-end' }}>
              <Tooltip title="刷新连接">
                <IconButton onClick={checkConnection} disabled={isLoading}>
                  {isLoading ? <CircularProgress size={24} /> : <RefreshIcon />}
                </IconButton>
              </Tooltip>
              <Tooltip title={isFullscreen ? "退出全屏" : "全屏模式"}>
                <IconButton onClick={toggleFullscreen}>
                  {isFullscreen ? <FullscreenExitIcon /> : <FullscreenIcon />}
                </IconButton>
              </Tooltip>
            </Box>
          </Grid>
        </Grid>
        
        {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
        
        {isConnected && (
          <Alert severity="success" sx={{ mt: 2 }}>
            已成功连接到ComfyUI服务
          </Alert>
        )}
      </Paper>

      <Box sx={{ 
        flexGrow: 1, 
        display: 'flex',
        flexDirection: isFullscreen ? 'column' : { xs: 'column', md: 'row' },
        height: isFullscreen ? 'calc(100vh - 180px)' : '700px'
      }}>
        <Box sx={{ 
          width: isFullscreen ? '100%' : { xs: '100%', md: '80%' },
          height: isFullscreen ? '100%' : { xs: '70%', md: '100%' }
        }}>
          {isConnected && proxyUrl ? (
            <iframe
              ref={iframeRef}
              src={proxyUrl}
              style={{
                width: '100%',
                height: '100%',
                border: '1px solid #ddd',
                borderRadius: '4px'
              }}
              title="ComfyUI"
            />
          ) : (
            <Box sx={{ 
              display: 'flex', 
              justifyContent: 'center', 
              alignItems: 'center',
              height: '100%',
              border: '1px dashed #ccc',
              borderRadius: '4px'
            }}>
              {isLoading ? (
                <CircularProgress />
              ) : (
                <Typography variant="h6" color="text.secondary">
                  {error || '正在连接到ComfyUI服务...'}
                </Typography>
              )}
            </Box>
          )}
        </Box>

        {!isFullscreen && (
          <Box sx={{ 
            width: { xs: '100%', md: '20%' },
            height: { xs: '30%', md: '100%' },
            ml: { xs: 0, md: 2 },
            mt: { xs: 2, md: 0 }
          }}>
            <Paper elevation={2} sx={{ height: '100%', p: 2, display: 'flex', flexDirection: 'column' }}>
              <Tabs value={activeTab} onChange={handleTabChange} sx={{ mb: 2 }}>
                <Tab label="工作流" />
                <Tab label="设置" />
              </Tabs>
              
              {activeTab === 0 && (
                <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
                  <Button
                    variant="contained"
                    startIcon={<SaveIcon />}
                    onClick={saveCurrentWorkflow}
                    disabled={!isConnected}
                    fullWidth
                    sx={{ mb: 2 }}
                  >
                    保存当前工作流
                  </Button>
                  
                  <Typography variant="subtitle2" gutterBottom>
                    已保存的工作流
                  </Typography>
                  
                  <Divider sx={{ mb: 1 }} />
                  
                  {savedWorkflows.length === 0 ? (
                    <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', mt: 2 }}>
                      暂无保存的工作流
                    </Typography>
                  ) : (
                    savedWorkflows.map((workflow, index) => (
                      <Card key={index} sx={{ mb: 1, cursor: 'pointer' }} onClick={() => loadWorkflow(workflow)}>
                        <CardContent sx={{ p: 1, '&:last-child': { pb: 1 } }}>
                          <Typography variant="body2">{workflow.name}</Typography>
                          <Typography variant="caption" color="text.secondary">
                            {new Date(workflow.created_at).toLocaleString()}
                          </Typography>
                        </CardContent>
                      </Card>
                    ))
                  )}
                </Box>
              )}
              
              {activeTab === 1 && (
                <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
                  <Typography variant="subtitle2" gutterBottom>
                    ComfyUI设置
                  </Typography>
                  
                  <Divider sx={{ mb: 2 }} />
                  
                  <Typography variant="body2" paragraph>
                    ComfyUI服务由系统管理员配置，如需调整设置请联系管理员。
                  </Typography>
                </Box>
              )}
            </Paper>
          </Box>
        )}
      </Box>
    </Box>
  );
};

export default ComfyUIIntegration; 