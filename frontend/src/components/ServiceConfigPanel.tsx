import React, { useState } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  CardActions,
  Typography,
  Grid,
  Divider,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Switch,
  IconButton,
  Tooltip,
  Alert,
  CircularProgress,
  SelectChangeEvent
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import { createAIService, updateAIService, deleteAIService, testServiceConnection } from '../services/ai_config';
import InfoIcon from '@mui/icons-material/Info';

interface ServiceConfigPanelProps {
  services: any[];
  onServicesUpdate: (services: any[]) => void;
}

const ServiceConfigPanel: React.FC<ServiceConfigPanelProps> = ({ services, onServicesUpdate }) => {
  const [openDialog, setOpenDialog] = useState(false);
  const [dialogMode, setDialogMode] = useState<'create' | 'edit'>('create');
  const [selectedService, setSelectedService] = useState<any>(null);
  const [formData, setFormData] = useState({
    service_type: 'subtitle_removal',
    service_name: '',
    service_url: '',
    is_active: true,
    default_mode: '',
    timeout: 60,
    advanced_params: '',
    
    // 字幕擦除特定
    auto_detect: true,
    
    // 语音合成特定
    language: 'zh',
    quality: 'high',
    
    // 唇形同步特定
    model_type: 'wav2lip',
    batch_size: 8,
    smooth: true
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [testingConnection, setTestingConnection] = useState(false);
  const [testResult, setTestResult] = useState<{success: boolean, message: string} | null>(null);

  const handleOpenCreateDialog = () => {
    setDialogMode('create');
    setSelectedService(null);
    setFormData({
      service_type: 'subtitle_removal',
      service_name: '',
      service_url: '',
      is_active: true,
      default_mode: '',
      timeout: 60,
      advanced_params: '',
      auto_detect: true,
      language: 'zh',
      quality: 'high',
      model_type: 'wav2lip',
      batch_size: 8,
      smooth: true
    });
    setOpenDialog(true);
    setError(null);
    setTestResult(null);
  };

  const handleOpenEditDialog = (service: any) => {
    setDialogMode('edit');
    setSelectedService(service);
    setFormData({
      service_type: service.service_type,
      service_name: service.service_name,
      service_url: service.service_url,
      is_active: service.is_active,
      default_mode: service.default_mode || '',
      timeout: service.timeout,
      advanced_params: service.advanced_params ? JSON.stringify(service.advanced_params) : '',
      auto_detect: service.auto_detect !== null ? service.auto_detect : true,
      language: service.language || 'zh',
      quality: service.quality || 'high',
      model_type: service.model_type || 'wav2lip',
      batch_size: service.batch_size || 8,
      smooth: service.smooth !== null ? service.smooth : true
    });
    setOpenDialog(true);
    setError(null);
    setTestResult(null);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, checked } = e.target;
    
    if (name === 'is_active' || name === 'auto_detect' || name === 'smooth') {
      setFormData({
        ...formData,
        [name]: checked
      });
    } else if (name === 'timeout' || name === 'batch_size') {
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

  const handleTestConnection = async () => {
    setTestingConnection(true);
    setTestResult(null);
    try {
      const result = await testServiceConnection({
        service_type: formData.service_type,
        service_url: formData.service_url
      });
      setTestResult(result);
    } catch (err) {
      setTestResult({
        success: false,
        message: '连接测试失败，请检查URL是否正确'
      });
    } finally {
      setTestingConnection(false);
    }
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);
    
    try {
      let advancedParams = {};
      if (formData.advanced_params) {
        try {
          advancedParams = JSON.parse(formData.advanced_params);
        } catch (err) {
          setError('高级参数格式不正确，请使用有效的JSON格式');
          setLoading(false);
          return;
        }
      }
      
      const serviceData = {
        ...formData,
        advanced_params: advancedParams
      };
      
      let updatedServices;
      
      if (dialogMode === 'create') {
        const newService = await createAIService(serviceData);
        updatedServices = [...services, newService];
      } else {
        const updatedService = await updateAIService(selectedService.id, serviceData);
        updatedServices = services.map(service => 
          service.id === selectedService.id ? updatedService : service
        );
      }
      
      onServicesUpdate(updatedServices);
      handleCloseDialog();
    } catch (err) {
      console.error('保存服务配置失败:', err);
      setError('保存服务配置失败，请检查输入并重试');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteService = async (serviceId: number) => {
    if (window.confirm('确定要删除此服务配置吗？此操作不可撤销。')) {
      try {
        await deleteAIService(serviceId);
        const updatedServices = services.filter(service => service.id !== serviceId);
        onServicesUpdate(updatedServices);
      } catch (err) {
        console.error('删除服务配置失败:', err);
        alert('删除服务配置失败，请重试');
      }
    }
  };

  const renderServiceTypeSpecificFields = () => {
    switch (formData.service_type) {
      case 'subtitle_removal':
        return (
          <FormControlLabel
            control={
              <Switch
                checked={formData.auto_detect}
                onChange={handleInputChange}
                name="auto_detect"
              />
            }
            label="自动检测字幕区域"
          />
        );
      case 'voice_synthesis':
        return (
          <>
            <FormControl fullWidth margin="normal">
              <InputLabel id="language-label">语言</InputLabel>
              <Select
                labelId="language-label"
                name="language"
                value={formData.language}
                label="语言"
                onChange={handleSelectChange}
              >
                <MenuItem value="zh">中文</MenuItem>
                <MenuItem value="en">英文</MenuItem>
                <MenuItem value="ja">日语</MenuItem>
                <MenuItem value="ko">韩语</MenuItem>
              </Select>
            </FormControl>
            <FormControl fullWidth margin="normal">
              <InputLabel id="quality-label">音质</InputLabel>
              <Select
                labelId="quality-label"
                name="quality"
                value={formData.quality}
                label="音质"
                onChange={handleSelectChange}
              >
                <MenuItem value="low">低质量</MenuItem>
                <MenuItem value="medium">中等质量</MenuItem>
                <MenuItem value="high">高质量</MenuItem>
              </Select>
            </FormControl>
          </>
        );
      case 'lip_sync':
        return (
          <>
            <FormControl fullWidth margin="normal">
              <InputLabel id="model-type-label">模型类型</InputLabel>
              <Select
                labelId="model-type-label"
                name="model_type"
                value={formData.model_type}
                label="模型类型"
                onChange={handleSelectChange}
              >
                <MenuItem value="wav2lip">Wav2Lip</MenuItem>
                <MenuItem value="wav2lip_gan">Wav2Lip GAN</MenuItem>
              </Select>
            </FormControl>
            <TextField
              fullWidth
              margin="normal"
              label="批处理大小"
              name="batch_size"
              type="number"
              value={formData.batch_size}
              onChange={handleInputChange}
            />
            <FormControlLabel
              control={
                <Switch
                  checked={formData.smooth}
                  onChange={handleInputChange}
                  name="smooth"
                />
              }
              label="平滑处理"
            />
          </>
        );
      default:
        return null;
    }
  };

  const getServiceTypeLabel = (serviceType: string): string => {
    switch (serviceType) {
      case 'subtitle_removal':
        return '字幕擦除';
      case 'voice_synthesis':
        return '语音合成';
      case 'lip_sync':
        return '唇形同步';
      case 'video_enhancement':
        return '视频增强';
      default:
        return serviceType;
    }
  };

  const renderServiceList = () => {
    if (services.length === 0) {
      return (
        <Box sx={{ 
          p: 4, 
          display: 'flex', 
          flexDirection: 'column', 
          alignItems: 'center',
          bgcolor: '#f5f9ff',
          borderRadius: 2,
          border: '1px dashed #3498db'
        }}>
          <Box sx={{ color: '#3498db', mb: 2, display: 'flex', alignItems: 'center' }}>
            <InfoIcon sx={{ mr: 1 }} />
            <Typography variant="body1">暂无服务配置，请点击"添加服务"按钮创建新的服务配置。</Typography>
          </Box>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleOpenCreateDialog}
            sx={{
              mt: 2,
              bgcolor: '#3498db',
              '&:hover': {
                bgcolor: '#2980b9'
              }
            }}
          >
            添加服务
          </Button>
        </Box>
      );
    }

    return (
      <Grid container spacing={3}>
        {services.map((service) => (
          <Grid item xs={12} md={6} lg={4} key={service.id}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <Typography variant="h6" component="div">
                    {service.service_name}
                  </Typography>
                  <Chip
                    label={getServiceTypeLabel(service.service_type)}
                    color="primary"
                    size="small"
                  />
                </Box>
                <Divider sx={{ my: 1 }} />
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  服务URL: {service.service_url}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  状态: {service.is_active ? 
                    <Chip size="small" icon={<CheckCircleIcon />} label="已启用" color="success" /> : 
                    <Chip size="small" icon={<ErrorIcon />} label="已禁用" color="error" />
                  }
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  超时: {service.timeout}秒
                </Typography>
                {service.service_type === 'subtitle_removal' && (
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    自动检测: {service.auto_detect ? '是' : '否'}
                  </Typography>
                )}
                {service.service_type === 'voice_synthesis' && (
                  <>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      语言: {service.language}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      音质: {service.quality}
                    </Typography>
                  </>
                )}
                {service.service_type === 'lip_sync' && (
                  <>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      模型: {service.model_type}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      批处理大小: {service.batch_size}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      平滑处理: {service.smooth ? '是' : '否'}
                    </Typography>
                  </>
                )}
              </CardContent>
              <CardActions>
                <Tooltip title="编辑">
                  <IconButton onClick={() => handleOpenEditDialog(service)}>
                    <EditIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="删除">
                  <IconButton onClick={() => handleDeleteService(service.id)}>
                    <DeleteIcon />
                  </IconButton>
                </Tooltip>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>
    );
  };

  return (
    <Box>
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {renderServiceList()}

      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {dialogMode === 'create' ? '添加服务配置' : '编辑服务配置'}
        </DialogTitle>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          {testResult && (
            <Alert severity={testResult.success ? "success" : "error"} sx={{ mb: 2 }}>
              {testResult.message}
            </Alert>
          )}
          <FormControl fullWidth margin="normal">
            <InputLabel id="service-type-label">服务类型</InputLabel>
            <Select
              labelId="service-type-label"
              name="service_type"
              value={formData.service_type}
              label="服务类型"
              onChange={handleSelectChange}
              disabled={dialogMode === 'edit'}
            >
              <MenuItem value="subtitle_removal">字幕擦除</MenuItem>
              <MenuItem value="voice_synthesis">语音合成</MenuItem>
              <MenuItem value="lip_sync">唇形同步</MenuItem>
            </Select>
          </FormControl>
          <TextField
            fullWidth
            margin="normal"
            label="服务名称"
            name="service_name"
            value={formData.service_name}
            onChange={handleInputChange}
            required
          />
          <TextField
            fullWidth
            margin="normal"
            label="服务URL"
            name="service_url"
            value={formData.service_url}
            onChange={handleInputChange}
            required
            helperText="例如: http://localhost:8001/api/v1"
          />
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 1 }}>
            <Button 
              variant="outlined" 
              onClick={handleTestConnection}
              disabled={testingConnection || !formData.service_url}
              startIcon={testingConnection ? <CircularProgress size={20} /> : null}
            >
              测试连接
            </Button>
          </Box>
          <TextField
            fullWidth
            margin="normal"
            label="默认模式"
            name="default_mode"
            value={formData.default_mode}
            onChange={handleInputChange}
            helperText="可选，服务的默认处理模式"
          />
          <TextField
            fullWidth
            margin="normal"
            label="超时时间(秒)"
            name="timeout"
            type="number"
            value={formData.timeout}
            onChange={handleInputChange}
          />
          <TextField
            fullWidth
            margin="normal"
            label="高级参数(JSON)"
            name="advanced_params"
            value={formData.advanced_params}
            onChange={handleInputChange}
            multiline
            rows={3}
            helperText="可选，JSON格式的高级参数配置"
          />
          <FormControlLabel
            control={
              <Switch
                checked={formData.is_active}
                onChange={handleInputChange}
                name="is_active"
              />
            }
            label="启用服务"
          />
          
          <Divider sx={{ my: 2 }} />
          <Typography variant="subtitle1" gutterBottom>
            服务特定配置
          </Typography>
          
          {renderServiceTypeSpecificFields()}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>取消</Button>
          <Button 
            onClick={handleSubmit} 
            variant="contained" 
            disabled={loading || !formData.service_name || !formData.service_url}
          >
            {loading ? <CircularProgress size={24} /> : '保存'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ServiceConfigPanel; 