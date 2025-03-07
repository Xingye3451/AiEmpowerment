import React, { useState } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  TextField,
  FormControlLabel,
  Switch,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  Alert,
  Divider,
  SelectChangeEvent
} from '@mui/material';
import { updateSystemConfig } from '../services/ai_config';

interface SystemConfigPanelProps {
  systemConfig: any;
  onSystemConfigUpdate: (config: any) => void;
}

const SystemConfigPanel: React.FC<SystemConfigPanelProps> = ({ 
  systemConfig, 
  onSystemConfigUpdate 
}) => {
  const [formData, setFormData] = useState({
    queue_size: systemConfig?.queue_size || 5,
    upload_dir: systemConfig?.upload_dir || '/app/uploads',
    result_dir: systemConfig?.result_dir || '/app/static/results',
    temp_dir: systemConfig?.temp_dir || '/app/temp',
    auto_clean: systemConfig?.auto_clean !== undefined ? systemConfig.auto_clean : true,
    retention_days: systemConfig?.retention_days || 30,
    notify_completion: systemConfig?.notify_completion !== undefined ? systemConfig.notify_completion : true,
    notify_error: systemConfig?.notify_error !== undefined ? systemConfig.notify_error : true,
    log_level: systemConfig?.log_level || 'INFO'
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, checked } = e.target;
    
    if (name === 'auto_clean' || name === 'notify_completion' || name === 'notify_error') {
      setFormData({
        ...formData,
        [name]: checked
      });
    } else if (name === 'queue_size' || name === 'retention_days') {
      setFormData({
        ...formData,
        [name]: parseInt(value, 10) || 0
      });
    } else {
      setFormData({
        ...formData,
        [name]: value
      });
    }
  };

  const handleSelectChange = (e: SelectChangeEvent) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);
    setSuccess(false);
    
    try {
      const updatedConfig = await updateSystemConfig(formData);
      onSystemConfigUpdate(updatedConfig);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      console.error('更新系统配置失败:', err);
      setError('更新系统配置失败，请检查输入并重试');
    } finally {
      setLoading(false);
    }
  };

  if (!systemConfig) {
    return (
      <Box sx={{ p: 2 }}>
        <Alert severity="warning">
          无法加载系统配置，请刷新页面重试。
        </Alert>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        系统配置
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      {success && (
        <Alert severity="success" sx={{ mb: 2 }}>
          系统配置已成功更新
        </Alert>
      )}
      
      <Card>
        <CardContent>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle1" gutterBottom>
                基本设置
              </Typography>
              <Divider sx={{ mb: 2 }} />
              
              <TextField
                fullWidth
                margin="normal"
                label="处理队列大小"
                name="queue_size"
                type="number"
                value={formData.queue_size}
                onChange={handleInputChange}
                helperText="同时处理的最大视频数量"
              />
              
              <FormControl fullWidth margin="normal">
                <InputLabel id="log-level-label">日志级别</InputLabel>
                <Select
                  labelId="log-level-label"
                  name="log_level"
                  value={formData.log_level}
                  label="日志级别"
                  onChange={handleSelectChange}
                >
                  <MenuItem value="DEBUG">DEBUG</MenuItem>
                  <MenuItem value="INFO">INFO</MenuItem>
                  <MenuItem value="WARNING">WARNING</MenuItem>
                  <MenuItem value="ERROR">ERROR</MenuItem>
                </Select>
              </FormControl>
              
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.auto_clean}
                    onChange={handleInputChange}
                    name="auto_clean"
                  />
                }
                label="自动清理临时文件"
                sx={{ mt: 2 }}
              />
              
              <TextField
                fullWidth
                margin="normal"
                label="保留天数"
                name="retention_days"
                type="number"
                value={formData.retention_days}
                onChange={handleInputChange}
                disabled={!formData.auto_clean}
                helperText="临时文件保留天数"
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle1" gutterBottom>
                目录设置
              </Typography>
              <Divider sx={{ mb: 2 }} />
              
              <TextField
                fullWidth
                margin="normal"
                label="上传目录"
                name="upload_dir"
                value={formData.upload_dir}
                onChange={handleInputChange}
                helperText="视频上传存储目录"
              />
              
              <TextField
                fullWidth
                margin="normal"
                label="结果目录"
                name="result_dir"
                value={formData.result_dir}
                onChange={handleInputChange}
                helperText="处理结果存储目录"
              />
              
              <TextField
                fullWidth
                margin="normal"
                label="临时目录"
                name="temp_dir"
                value={formData.temp_dir}
                onChange={handleInputChange}
                helperText="处理过程中的临时文件目录"
              />
              
              <Typography variant="subtitle1" gutterBottom sx={{ mt: 3 }}>
                通知设置
              </Typography>
              <Divider sx={{ mb: 2 }} />
              
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.notify_completion}
                    onChange={handleInputChange}
                    name="notify_completion"
                  />
                }
                label="任务完成通知"
              />
              
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.notify_error}
                    onChange={handleInputChange}
                    name="notify_error"
                  />
                }
                label="错误通知"
              />
            </Grid>
          </Grid>
          
          <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
            <Button
              variant="contained"
              onClick={handleSubmit}
              disabled={loading}
            >
              {loading ? <CircularProgress size={24} /> : '保存配置'}
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default SystemConfigPanel; 