import React, { useState, useEffect } from 'react';
import {
  Upload,
  Button,
  Input,
  Checkbox,
  Progress,
  Card,
  Spin,
  message,
  Tabs,
  Space,
  Select,
  Typography,
  Row,
  Col,
  Divider,
  Form,
  InputNumber,
  Radio,
  Tag,
  Tooltip,
  Switch,
  Empty,
  Alert,
  Modal,
  Badge
} from 'antd';
import { 
  UploadOutlined,
  VideoCameraOutlined,
  PlayCircleOutlined,
  DownloadOutlined,
  InfoCircleOutlined,
  DeleteOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  SyncOutlined,
  ExclamationCircleOutlined,
  LeftOutlined,
  RightOutlined
} from '@ant-design/icons';
import type { RcFile, UploadFile } from 'antd/lib/upload/interface';
import type { CheckboxChangeEvent } from 'antd/lib/checkbox';
import axios from 'axios';
import { useWebSocket } from '../hooks/useWebSocket';
import { ColorPicker } from 'antd';
import { getAuthHeaders } from '../utils/auth';

const { TextArea } = Input;
const { TabPane } = Tabs;
const { Title, Text } = Typography;
const { Option } = Select;
const { Group: RadioGroup } = Radio;

interface VideoTask {
  task_id: string;
  original_filename: string;
  processing_pipeline: string[];
}

interface TaskStatus {
  status: string;
  progress: number;
  message: string;
  result?: any;
  error?: string;
  current_stage?: string;
}

interface SubtitleStyle {
  font_size?: number;
  font_color?: string;
  bg_color?: string;
  position?: 'top' | 'middle' | 'bottom';
  align?: 'left' | 'center' | 'right';
}

// 预设颜色选项
const PRESET_COLORS = [
  '#FFFFFF', // 白色
  '#000000', // 黑色
  '#FFFF00', // 黄色
  '#FF0000', // 红色
  '#00FF00', // 绿色
  '#0000FF', // 蓝色
  '#FF00FF', // 粉色
  '#00FFFF', // 青色
  '#FFA500', // 橙色
];

// 预设背景颜色选项
const BG_PRESET_COLORS = [
  'none',
  'rgba(0,0,0,0.5)', // 半透明黑
  'rgba(0,0,0,0.7)', // 深黑
  'rgba(0,0,0,0)', // 透明
  'rgba(0,0,255,0.3)', // 半透明蓝
  'rgba(255,0,0,0.3)', // 半透明红
];

const AIVideoProcessor: React.FC = () => {
  // 上传文件状态
  const [fileList, setFileList] = useState<RcFile[]>([]);
  const [uploading, setUploading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  
  // 批量预览状态
  const [batchPreviewVisible, setBatchPreviewVisible] = useState(false);
  const [previewVideos, setPreviewVideos] = useState<{url: string, name: string}[]>([]);
  const [currentPreviewIndex, setCurrentPreviewIndex] = useState(0);
  
  // 任务视频预览状态
  const [taskPreviewVisible, setTaskPreviewVisible] = useState(false);
  const [taskPreviewUrl, setTaskPreviewUrl] = useState('');
  const [taskPreviewTitle, setTaskPreviewTitle] = useState('');
  
  // 处理选项状态
  const [text, setText] = useState('');
  const [voiceText, setVoiceText] = useState('');
  const [removeSubtitles, setRemoveSubtitles] = useState(true);
  const [extractVoice, setExtractVoice] = useState(true);
  const [generateSpeech, setGenerateSpeech] = useState(true);
  const [lipSync, setLipSync] = useState(true);
  const [addSubtitles, setAddSubtitles] = useState(true);
  const [autoDetectSubtitles, setAutoDetectSubtitles] = useState(true);
  const [subtitleRemovalMode, setSubtitleRemovalMode] = useState('balanced');
  const [processingMode, setProcessingMode] = useState('local'); // 默认使用本地处理模式
  const [localProcessingAvailable, setLocalProcessingAvailable] = useState(true); // 默认本地处理可用
  
  // 超分辨率处理选项
  const [enhanceResolution, setEnhanceResolution] = useState(false);
  const [resolutionScale, setResolutionScale] = useState(2);
  const [resolutionModel, setResolutionModel] = useState('realesrgan-x4plus');
  const [denoiseStrength, setDenoiseStrength] = useState(0.5);
  const [resolutionEnhancementAvailable, setResolutionEnhancementAvailable] = useState(false);
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  
  // 字幕样式
  const [subtitleStyle, setSubtitleStyle] = useState<SubtitleStyle>({
    font_size: 24,
    font_color: '#FFFFFF',
    bg_color: 'none',
    position: 'bottom',
    align: 'center'
  });
  
  // 任务状态
  const [tasks, setTasks] = useState<VideoTask[]>([]);
  const [taskStatuses, setTaskStatuses] = useState<Record<string, TaskStatus>>({});
  const [processingComplete, setProcessingComplete] = useState(false);
  
  // WebSocket连接
  const { lastMessage } = useWebSocket();
  
  // 添加键盘事件监听
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!batchPreviewVisible) return;
      
      if (e.key === 'ArrowLeft' && currentPreviewIndex > 0) {
        setCurrentPreviewIndex(currentPreviewIndex - 1);
      } else if (e.key === 'ArrowRight' && currentPreviewIndex < previewVideos.length - 1) {
        setCurrentPreviewIndex(currentPreviewIndex + 1);
      } else if (e.key === 'Escape') {
        setBatchPreviewVisible(false);
        // 释放所有URL对象
        previewVideos.forEach(video => {
          URL.revokeObjectURL(video.url);
        });
        setPreviewVideos([]);
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [batchPreviewVisible, currentPreviewIndex, previewVideos]);
  
  // 切换到上一个视频
  const handlePrevVideo = () => {
    if (currentPreviewIndex > 0) {
      setCurrentPreviewIndex(currentPreviewIndex - 1);
    }
  };
  
  // 切换到下一个视频
  const handleNextVideo = () => {
    if (currentPreviewIndex < previewVideos.length - 1) {
      setCurrentPreviewIndex(currentPreviewIndex + 1);
    }
  };
  
  // 关闭批量预览
  const handleBatchPreviewClose = () => {
    setBatchPreviewVisible(false);
    // 释放所有URL对象
    previewVideos.forEach(video => {
      URL.revokeObjectURL(video.url);
    });
    setPreviewVideos([]);
  };
  
  // 处理WebSocket消息
  useEffect(() => {
    if (lastMessage) {
      try {
        const data = JSON.parse(lastMessage.data);
        
        // 检查是否是视频处理进度更新
        if (data.type === 'video_processing_progress' && data.task_id) {
          setTaskStatuses(prev => ({
            ...prev,
            [data.task_id]: {
              status: 'running',
              progress: data.progress,
              message: data.message
            }
          }));
        }
        
        // 检查是否是视频处理完成
        else if (data.type === 'video_processing_completed' && data.task_id) {
          setTaskStatuses(prev => ({
            ...prev,
            [data.task_id]: {
              status: 'completed',
              progress: 100,
              message: data.message,
              result: {
                video_url: data.download_url,
                thumbnail_url: data.thumbnail_url
              }
            }
          }));
          
          message.success('视频处理完成！');
          setProcessingComplete(true);
        }
        
        // 检查是否是视频处理失败
        else if (data.type === 'video_processing_failed' && data.task_id) {
          setTaskStatuses(prev => ({
            ...prev,
            [data.task_id]: {
              status: 'failed',
              progress: 0,
              message: data.message,
              error: data.message
            }
          }));
          
          message.error(`视频处理失败: ${data.message}`);
        }
      } catch (e) {
        console.error('解析WebSocket消息失败', e);
      }
    }
  }, [lastMessage]);
  
  // 检查本地处理是否可用
  useEffect(() => {
    const checkLocalProcessing = async () => {
      try {
        // 使用getAuthHeaders获取认证头
        const headers = getAuthHeaders();
        
        const response = await axios.get('/api/v1/douyin/check-local-processing', { headers });
        setLocalProcessingAvailable(response.data.available);
        
        // 如果本地处理不可用，自动切换到云服务处理模式
        if (!response.data.available) {
          setProcessingMode('cloud');
          message.info('本地处理不可用，已自动切换到云服务处理模式');
        }
      } catch (error) {
        console.error('检查本地处理可用性失败', error);
        // 出错时默认本地处理可用
        setLocalProcessingAvailable(true);
      }
    };
    
    // 检查超分辨率处理服务是否可用
    const checkResolutionEnhancement = async () => {
      try {
        const headers = getAuthHeaders();
        
        const response = await axios.get('/api/v1/douyin/check-resolution-enhancement', { headers });
        setResolutionEnhancementAvailable(response.data.available);
        setAvailableModels(response.data.models || []);
        
        if (response.data.available) {
          message.success('超分辨率处理服务可用');
        } else {
          message.info(`超分辨率处理服务不可用: ${response.data.message}`);
        }
      } catch (error) {
        console.error('检查超分辨率处理服务可用性失败', error);
        setResolutionEnhancementAvailable(false);
      }
    };
    
    checkLocalProcessing();
    checkResolutionEnhancement();
  }, []);
  
  // 文件上传前检查
  const handleFileChange = (file: RcFile) => {
    // 检查文件类型
    const isVideo = file.type.startsWith('video/');
    if (!isVideo) {
      message.error('只能上传视频文件！');
      return false;
    }
    
    // 检查文件大小，限制为500MB
    const isLt500M = file.size / 1024 / 1024 < 500;
    if (!isLt500M) {
      message.error('视频文件大小不能超过500MB！');
      return false;
    }
    
    // 添加到文件列表
    setFileList(prev => [...prev, file]);
    return false; // 阻止自动上传
  };
  
  // 打开批量预览
  const handleBatchPreview = () => {
    if (fileList.length === 0) {
      message.info('请先选择视频文件');
      return;
    }
    
    try {
      // 为每个文件创建URL
      const videos = fileList.map(file => {
        try {
          // 创建视频URL
          const videoUrl = URL.createObjectURL(file);
          return {
            url: videoUrl,
            name: file.name
          };
        } catch (err) {
          console.error(`为文件 ${file.name} 创建URL失败:`, err);
          return null;
        }
      }).filter(Boolean) as {url: string, name: string}[];
      
      if (videos.length === 0) {
        message.error('无法预览任何视频文件');
        return;
      }
      
      setPreviewVideos(videos);
      setCurrentPreviewIndex(0);
      setBatchPreviewVisible(true);
    } catch (error) {
      console.error('创建预览URL失败:', error);
      message.error('无法预览视频');
    }
  };
  
  // 处理上传
  const handleUpload = async () => {
    if (fileList.length === 0) {
      message.error('请先选择视频文件！');
      return;
    }
    
    if (generateSpeech && !voiceText) {
      message.error('请输入语音文本！');
      return;
    }

    // 检查处理选项
    if (!removeSubtitles && !extractVoice && !generateSpeech && !lipSync && !addSubtitles && !enhanceResolution) {
      message.error('请至少选择一项处理功能！');
      return;
    }
    
    // 如果添加字幕但没有字幕文本，使用语音文本
    if (addSubtitles && !text && voiceText) {
      setText(voiceText);
    }

    // 开始上传
    setUploading(true);
    setIsProcessing(true);
    setTasks([]);
    setTaskStatuses({});
    setProcessingComplete(false);
    
    try {
      const formData = new FormData();
      
      // 添加视频文件
      fileList.forEach(file => {
        formData.append('videos', file);
      });
      
      // 添加处理选项
      formData.append('text', text);
      formData.append('remove_subtitles', removeSubtitles.toString());
      formData.append('extract_voice', extractVoice.toString());
      formData.append('generate_speech', generateSpeech.toString());
      formData.append('lip_sync', lipSync.toString());
      formData.append('add_subtitles', addSubtitles.toString());
      formData.append('auto_detect_subtitles', autoDetectSubtitles.toString());
      formData.append('subtitle_removal_mode', subtitleRemovalMode);
      formData.append('processing_mode', processingMode);
      
      // 添加字幕样式
      if (addSubtitles) {
        formData.append('subtitle_style', JSON.stringify(subtitleStyle));
      }
      
      if (voiceText) {
        formData.append('voice_text', voiceText);
      }
      
      // 添加超分辨率处理选项
      formData.append('enhance_resolution', enhanceResolution.toString());
      formData.append('resolution_scale', resolutionScale.toString());
      formData.append('resolution_model', resolutionModel);
      formData.append('denoise_strength', denoiseStrength.toString());

      // 发送请求
      const response = await axios.post('/api/v1/douyin/batch-process-videos', formData);
      
      if (response.data.success) {
        message.success('视频上传成功，开始处理...');
        setTasks(response.data.tasks);
        
        // 初始化任务状态
        const initialStatuses: Record<string, TaskStatus> = {};
        response.data.tasks.forEach((task: VideoTask) => {
          initialStatuses[task.task_id] = {
            status: 'pending',
            progress: 0,
            message: '等待处理...'
          };
        });
        setTaskStatuses(initialStatuses);
        
        // 开始轮询任务状态
        response.data.tasks.forEach((task: VideoTask) => {
          pollTaskStatus(task.task_id);
        });
      } else {
        message.error('视频上传失败！');
      }
    } catch (error) {
      console.error('上传视频失败', error);
      message.error('上传视频失败，请重试！');
    } finally {
      setUploading(false);
      setIsProcessing(false);
    }
  };
  
  // 轮询任务状态
  const pollTaskStatus = async (taskId: string) => {
    try {
      const response = await axios.get(`/api/v1/douyin/process-status/${taskId}`);
      const status = response.data;
      
      setTaskStatuses(prev => ({
        ...prev,
        [taskId]: {
          status: status.status,
          progress: status.progress || 0,
          message: status.message || '',
          result: status.result,
          error: status.error
        }
      }));
      
      // 如果任务未完成，继续轮询
      if (status.status !== 'completed' && status.status !== 'failed') {
        setTimeout(() => pollTaskStatus(taskId), 2000);
      } else if (status.status === 'completed') {
        message.success(`任务 ${taskId} 处理完成！`);
        setProcessingComplete(true);
      } else if (status.status === 'failed') {
        message.error(`任务 ${taskId} 处理失败: ${status.error || '未知错误'}`);
      }
    } catch (error) {
      console.error(`获取任务状态失败: ${taskId}`, error);
      setTimeout(() => pollTaskStatus(taskId), 5000); // 出错后延长轮询间隔
    }
  };
  
  // 下载处理后的视频
  const handleDownload = (taskId: string) => {
    window.open(`/api/v1/douyin/processed-video/${taskId}`, '_blank');
  };
  
  // 预览处理后的视频
  const handlePreview = (taskId: string, filename: string) => {
    setTaskPreviewUrl(`/api/v1/douyin/video/${taskId}`);
    setTaskPreviewTitle(filename);
    setTaskPreviewVisible(true);
  };
  
  // 关闭任务视频预览
  const handleTaskPreviewClose = () => {
    setTaskPreviewVisible(false);
    setTaskPreviewUrl('');
  };
  
  // 渲染任务列表
  const renderTasks = () => {
    if (tasks.length === 0) {
      return null;
    }
    
    return (
      <div className="tasks-container" style={{ marginTop: 24 }}>
        <Card 
          title={
            <Space>
              <SyncOutlined style={{ color: processingComplete ? '#52c41a' : '#1890ff' }} spin={!processingComplete} />
              <span>处理任务 ({tasks.length})</span>
              {processingComplete && <Tag color="success">全部完成</Tag>}
            </Space>
          } 
          style={{ marginBottom: 24, borderRadius: '8px' }}
          className="task-card"
        >
          {tasks.map((task, index) => {
            const status = taskStatuses[task.task_id] || { status: 'pending', progress: 0, message: '等待处理...' };
            
            // 获取处理流程的中文名称
            const getPipelineName = (step: string) => {
              const pipelineMap: Record<string, string> = {
                'subtitle_removal': '字幕擦除',
                'voice_extraction': '音色提取',
                'speech_generation': '语音生成',
                'lip_sync': '唇形同步',
                'add_subtitles': '添加字幕',
                'enhance_resolution': '超分辨率处理'
              };
              return pipelineMap[step] || step;
            };
            
            return (
              <Card 
                key={task.task_id} 
                size="small" 
                style={{ marginBottom: 16 }}
                title={
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Space>
                      <span>任务 #{index + 1}: {task.original_filename}</span>
                      {status.status === 'pending' && <Badge status="default" text="等待中" />}
                      {status.status === 'scheduled' && <Badge status="processing" text="已调度" />}
                      {status.status === 'running' && <Badge status="processing" text="处理中" />}
                      {status.status === 'completed' && <Badge status="success" text="已完成" />}
                      {status.status === 'failed' && <Badge status="error" text="失败" />}
                    </Space>
                    <Space>
                      {status.status === 'completed' && (
                        <>
                          <Button 
                            type="primary" 
                            size="small" 
                            icon={<DownloadOutlined />}
                            onClick={() => handleDownload(task.task_id)}
                          >
                            下载
                          </Button>
                          <Button 
                            type="default" 
                            size="small" 
                            icon={<PlayCircleOutlined />}
                            onClick={() => handlePreview(task.task_id, task.original_filename)}
                          >
                            预览
                          </Button>
                        </>
                      )}
                    </Space>
                  </div>
                }
              >
                <div>
                  <Text strong>处理流程: </Text>
                  <Space>
                    {task.processing_pipeline.map((step, i) => (
                      <React.Fragment key={i}>
                        {i > 0 && <span className="pipeline-arrow">→</span>}
                        <Tag 
                          color={
                            status.status === 'running' && status.current_stage === step ? 
                            'processing' : 
                            status.status === 'completed' ? 'success' : 'default'
                          }
                        >
                          {getPipelineName(step)}
                          {status.status === 'running' && status.current_stage === step && (
                            <SyncOutlined spin style={{ marginLeft: 4 }} />
                          )}
                        </Tag>
                      </React.Fragment>
                    ))}
                  </Space>
                </div>
                
                {status.message && (
                  <div style={{ marginTop: 12 }}>
                    <Text strong>消息: </Text>
                    <Text>{status.message}</Text>
                  </div>
                )}
                
                {status.error && (
                  <div style={{ marginTop: 12 }}>
                    <Text strong type="danger">错误: </Text>
                    <Text type="danger">{status.error}</Text>
                  </div>
                )}
                
                {status.status === 'running' && (
                  <Progress 
                    percent={Math.round(status.progress)} 
                    status="active" 
                    style={{ marginTop: 16 }} 
                    strokeColor={{
                      '0%': '#108ee9',
                      '100%': '#87d068',
                    }}
                  />
                )}
                
                {status.status === 'completed' && status.result && status.result.thumbnail_url && (
                  <div style={{ marginTop: 16, textAlign: 'center' }}>
                    <img 
                      src={status.result.thumbnail_url} 
                      alt="视频预览" 
                      style={{ maxWidth: '100%', maxHeight: 200, borderRadius: '8px', boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }} 
                    />
                  </div>
                )}
              </Card>
            );
          })}
        </Card>
      </div>
    );
  };
  
  return (
    <div className="ai-video-processor">
      <Card 
        title={
          <Space>
            <VideoCameraOutlined style={{ color: '#1890ff' }} />
            <span>AI视频处理</span>
          </Space>
        } 
        style={{ marginBottom: 24, borderRadius: '8px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}
        className="processor-card"
        extra={
          <Badge.Ribbon text={localProcessingAvailable ? "本地处理模式" : "云服务处理模式"} color={localProcessingAvailable ? "blue" : "purple"}>
            <Alert
              message={
                <Space>
                  <span>云服务处理即将上线</span>
                  <Badge status="processing" text="多种算法可选" />
                </Space>
              }
              type="info"
              showIcon
              style={{ marginLeft: 20 }}
            />
          </Badge.Ribbon>
        }
      >
        <Tabs defaultActiveKey="upload" type="card">
          <TabPane 
            tab={
              <span>
                <UploadOutlined />
                上传视频
              </span>
            } 
            key="upload"
          >
            <div className="upload-container" style={{ padding: '20px', background: '#f9f9f9', borderRadius: '8px', marginBottom: '20px' }}>
              <Upload
                beforeUpload={handleFileChange}
                onRemove={(file) => {
                  const index = fileList.indexOf(file as RcFile);
                  const newFileList = fileList.slice();
                  newFileList.splice(index, 1);
                  setFileList(newFileList);
                }}
                fileList={fileList.map(file => ({
                  uid: file.uid,
                  name: file.name,
                  status: 'done',
                  size: file.size,
                  type: file.type,
                  percent: 100
                }))}
                accept="video/*"
                multiple
                disabled={isProcessing}
                listType="picture"
                className="upload-list"
                showUploadList={{
                  showPreviewIcon: false,
                  showRemoveIcon: true
                }}
              >
                <Button 
                  icon={<UploadOutlined />} 
                  disabled={isProcessing}
                  size="large"
                  style={{ height: '60px', width: '100%', borderStyle: 'dashed' }}
                >
                  <div>选择视频文件</div>
                  <div style={{ fontSize: '12px', color: '#888' }}>支持多个视频同时上传</div>
                </Button>
              </Upload>
              
              {fileList.length > 0 && (
                <div style={{ marginTop: '16px', textAlign: 'center' }}>
                  <Button 
                    type="primary" 
                    icon={<PlayCircleOutlined />} 
                    onClick={handleBatchPreview}
                    size="large"
                  >
                    预览所有视频 ({fileList.length})
                  </Button>
                  <div style={{ fontSize: '12px', color: '#888', marginTop: '8px' }}>
                    点击上方按钮可预览所有已选择的视频
                  </div>
                </div>
              )}
            </div>
          </TabPane>
        </Tabs>
        
        {/* 批量视频预览模态框 */}
        <Modal
          open={batchPreviewVisible}
          title={
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <PlayCircleOutlined style={{ color: '#1890ff', marginRight: '8px' }} />
              {previewVideos.length > 0 ? 
                `预览视频 (${currentPreviewIndex + 1}/${previewVideos.length}): ${previewVideos[currentPreviewIndex]?.name || ''}` : 
                '预览视频'}
            </div>
          }
          footer={
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <Button 
                onClick={handlePrevVideo} 
                disabled={currentPreviewIndex === 0 || previewVideos.length <= 1}
                icon={<LeftOutlined />}
                type="default"
              >
                上一个
              </Button>
              <Space>
                <span style={{ color: '#888' }}>
                  {previewVideos.length > 0 ? `${currentPreviewIndex + 1}/${previewVideos.length}` : '0/0'}
                </span>
                <Button onClick={handleBatchPreviewClose} type="primary">
                  关闭预览
                </Button>
              </Space>
              <Button 
                onClick={handleNextVideo} 
                disabled={currentPreviewIndex === previewVideos.length - 1 || previewVideos.length <= 1}
                icon={<RightOutlined />}
                type="default"
              >
                下一个
              </Button>
            </div>
          }
          onCancel={handleBatchPreviewClose}
          width={800}
          centered
          destroyOnClose={true}
        >
          {previewVideos.length > 0 ? (
            <div style={{ textAlign: 'center' }}>
              <video
                controls
                autoPlay
                style={{ width: '100%', maxHeight: '70vh', borderRadius: '8px' }}
                src={previewVideos[currentPreviewIndex]?.url}
              />
              <div style={{ marginTop: '12px', color: '#888', fontSize: '12px' }}>
                提示: 使用键盘左右箭头键可快速切换视频
              </div>
            </div>
          ) : (
            <Empty description="没有可预览的视频" />
          )}
        </Modal>
        
        {/* 任务视频预览模态框 */}
        <Modal
          open={taskPreviewVisible}
          title={
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <PlayCircleOutlined style={{ color: '#1890ff', marginRight: '8px' }} />
              {`预览处理后的视频: ${taskPreviewTitle}`}
            </div>
          }
          footer={
            <Button onClick={handleTaskPreviewClose} type="primary">
              关闭预览
            </Button>
          }
          onCancel={handleTaskPreviewClose}
          width={800}
          centered
          destroyOnClose={true}
        >
          {taskPreviewUrl ? (
            <div style={{ textAlign: 'center' }}>
              <video
                controls
                autoPlay
                style={{ width: '100%', maxHeight: '70vh', borderRadius: '8px' }}
                src={taskPreviewUrl}
              />
              <div style={{ marginTop: '12px', color: '#888', fontSize: '12px' }}>
                提示: 您可以下载此视频以获得更好的播放体验
              </div>
            </div>
          ) : (
            <Empty description="无法加载视频" />
          )}
        </Modal>
        
        <Divider>
          <Space>
            <InfoCircleOutlined />
            处理选项
          </Space>
        </Divider>
        
        <div className="options-container" style={{ padding: '0 10px' }}>
          <Alert
            message={localProcessingAvailable ? 
              "当前使用本地处理模式，处理速度取决于您的计算机性能" : 
              "当前使用云服务处理模式（测试版），可能会有一定延迟"}
            description="云服务处理模式即将上线，届时将提供多种处理算法选择，方便您对比不同处理效果"
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
          
          <Row gutter={[24, 24]}>
            <Col xs={24} md={12}>
              <Card 
                title="字幕处理" 
                size="small" 
                className="option-card"
                style={{ height: '100%' }}
              >
                <div style={{ marginBottom: 16 }}>
                  <Space>
                    <Switch
                      checked={removeSubtitles}
                      onChange={(checked) => setRemoveSubtitles(checked)}
                      disabled={isProcessing}
                    />
                    <span>擦除字幕</span>
                    <Tooltip title="AI将自动检测并擦除视频中的字幕">
                      <InfoCircleOutlined style={{ color: '#1890ff' }} />
                    </Tooltip>
                  </Space>
                </div>
                
                {removeSubtitles && (
                  <div style={{ marginLeft: 24 }}>
                    <div style={{ marginBottom: 12 }}>
                      <Space>
                        <Switch
                          checked={autoDetectSubtitles}
                          onChange={(checked) => setAutoDetectSubtitles(checked)}
                          disabled={isProcessing}
                          size="small"
                        />
                        <span>智能检测字幕区域</span>
                        <Tooltip title="开启后AI将自动检测字幕区域，无需手动指定">
                          <InfoCircleOutlined style={{ color: '#1890ff' }} />
                        </Tooltip>
                      </Space>
                    </div>
                    
                    {!autoDetectSubtitles && (
                      <div style={{ marginBottom: 12 }}>
                        <div style={{ marginBottom: 8 }}>
                          <Text>字幕文本:</Text>
                          <Tooltip title="输入视频中的字幕文本，帮助AI更准确地识别字幕区域">
                            <InfoCircleOutlined style={{ marginLeft: 8, color: '#1890ff' }} />
                          </Tooltip>
                        </div>
                        <TextArea
                          rows={3}
                          value={text}
                          onChange={(e) => setText(e.target.value)}
                          placeholder="请输入视频中的字幕文本，用于辅助字幕擦除"
                          disabled={isProcessing}
                        />
                      </div>
                    )}
                    
                    <div style={{ marginBottom: 8 }}>
                      <Text>字幕擦除模式:</Text>
                      <Tooltip title="选择不同的擦除模式，平衡速度和质量">
                        <InfoCircleOutlined style={{ marginLeft: 8, color: '#1890ff' }} />
                      </Tooltip>
                    </div>
                    <Select
                      value={subtitleRemovalMode}
                      onChange={(value: string) => setSubtitleRemovalMode(value)}
                      style={{ width: '100%' }}
                      disabled={isProcessing}
                      options={[
                        { value: 'fast', label: '快速 (速度优先)' },
                        { value: 'balanced', label: '平衡 (推荐)' },
                        { value: 'quality', label: '高质量 (效果优先)' }
                      ]}
                    />
                  </div>
                )}
                
                <Divider style={{ margin: '16px 0' }} />
                
                <div style={{ marginBottom: 16 }}>
                  <Space>
                    <Switch
                      checked={addSubtitles}
                      onChange={(checked) => setAddSubtitles(checked)}
                      disabled={isProcessing}
                    />
                    <span>添加字幕</span>
                    <Tooltip title="在视频中添加自定义字幕">
                      <InfoCircleOutlined style={{ color: '#1890ff' }} />
                    </Tooltip>
                  </Space>
                  {addSubtitles && generateSpeech && (
                    <div style={{ marginLeft: 24, fontSize: '12px', color: '#1890ff', marginTop: '4px' }}>
                      <InfoCircleOutlined style={{ marginRight: '4px' }} />
                      如果未指定字幕文本，将使用语音文本作为字幕
                    </div>
                  )}
                </div>
                
                {addSubtitles && (
                  <div style={{ marginLeft: 24 }}>
                    <Form layout="vertical">
                      <Row gutter={16}>
                        <Col span={12}>
                          <Form.Item 
                            label={
                              <Space>
                                <span>字体大小</span>
                                <Tooltip title="设置字幕字体大小">
                                  <InfoCircleOutlined style={{ color: '#1890ff' }} />
                                </Tooltip>
                              </Space>
                            }
                          >
                            <InputNumber
                              min={12}
                              max={48}
                              value={subtitleStyle.font_size}
                              onChange={(value) => setSubtitleStyle({...subtitleStyle, font_size: value as number})}
                              disabled={isProcessing}
                              style={{ width: '100%' }}
                            />
                          </Form.Item>
                        </Col>
                        
                        <Col span={12}>
                          <Form.Item 
                            label={
                              <Space>
                                <span>字体颜色</span>
                                <Tooltip title="选择字幕字体颜色">
                                  <InfoCircleOutlined style={{ color: '#1890ff' }} />
                                </Tooltip>
                              </Space>
                            }
                          >
                            <div style={{ display: 'flex', alignItems: 'center' }}>
                              <ColorPicker
                                value={subtitleStyle.font_color}
                                onChange={(color) => {
                                  setSubtitleStyle({...subtitleStyle, font_color: color.toHexString()})
                                }}
                                disabled={isProcessing}
                                presets={[
                                  {
                                    label: '推荐颜色',
                                    colors: PRESET_COLORS,
                                  }
                                ]}
                                showText
                              />
                            </div>
                          </Form.Item>
                        </Col>
                        
                        <Col span={12}>
                          <Form.Item 
                            label={
                              <Space>
                                <span>背景颜色</span>
                                <Tooltip title="选择字幕背景颜色，可选择透明">
                                  <InfoCircleOutlined style={{ color: '#1890ff' }} />
                                </Tooltip>
                              </Space>
                            }
                          >
                            <Select
                              value={subtitleStyle.bg_color}
                              onChange={(value) => setSubtitleStyle({...subtitleStyle, bg_color: value})}
                              disabled={isProcessing}
                              style={{ width: '100%' }}
                              options={[
                                { value: 'none', label: '无背景' },
                                { value: 'rgba(0,0,0,0.5)', label: '半透明黑' },
                                { value: 'rgba(0,0,0,0.7)', label: '深黑' },
                                { value: 'rgba(0,0,255,0.3)', label: '半透明蓝' },
                                { value: 'rgba(255,0,0,0.3)', label: '半透明红' }
                              ]}
                            />
                          </Form.Item>
                        </Col>
                        
                        <Col span={12}>
                          <Form.Item 
                            label={
                              <Space>
                                <span>位置</span>
                                <Tooltip title="设置字幕在视频中的位置">
                                  <InfoCircleOutlined style={{ color: '#1890ff' }} />
                                </Tooltip>
                              </Space>
                            }
                          >
                            <RadioGroup
                              value={subtitleStyle.position}
                              onChange={(e) => setSubtitleStyle({...subtitleStyle, position: e.target.value})}
                              disabled={isProcessing}
                              optionType="button"
                              buttonStyle="solid"
                              style={{ width: '100%' }}
                            >
                              <Radio.Button value="top" style={{ width: '33.3%', textAlign: 'center' }}>顶部</Radio.Button>
                              <Radio.Button value="middle" style={{ width: '33.3%', textAlign: 'center' }}>中间</Radio.Button>
                              <Radio.Button value="bottom" style={{ width: '33.3%', textAlign: 'center' }}>底部</Radio.Button>
                            </RadioGroup>
                          </Form.Item>
                        </Col>
                        
                        <Col span={12}>
                          <Form.Item 
                            label={
                              <Space>
                                <span>对齐方式</span>
                                <Tooltip title="设置字幕的对齐方式">
                                  <InfoCircleOutlined style={{ color: '#1890ff' }} />
                                </Tooltip>
                              </Space>
                            }
                          >
                            <RadioGroup
                              value={subtitleStyle.align}
                              onChange={(e) => setSubtitleStyle({...subtitleStyle, align: e.target.value})}
                              disabled={isProcessing}
                              optionType="button"
                              buttonStyle="solid"
                              style={{ width: '100%' }}
                            >
                              <Radio.Button value="left" style={{ width: '33.3%', textAlign: 'center' }}>左对齐</Radio.Button>
                              <Radio.Button value="center" style={{ width: '33.3%', textAlign: 'center' }}>居中</Radio.Button>
                              <Radio.Button value="right" style={{ width: '33.3%', textAlign: 'center' }}>右对齐</Radio.Button>
                            </RadioGroup>
                          </Form.Item>
                        </Col>
                      </Row>
                    </Form>
                  </div>
                )}
              </Card>
            </Col>
            
            <Col xs={24} md={12}>
              <Row gutter={[0, 24]}>
                <Col span={24}>
                  <Card 
                    title="音频处理" 
                    size="small" 
                    className="option-card"
                  >
                    <div style={{ marginBottom: 16 }}>
                      <Space>
                        <Switch
                          checked={extractVoice}
                          onChange={(checked) => setExtractVoice(checked)}
                          disabled={isProcessing}
                        />
                        <span>提取音色</span>
                        <Tooltip title="从视频中提取人物音色，用于后续语音合成">
                          <InfoCircleOutlined style={{ color: '#1890ff' }} />
                        </Tooltip>
                      </Space>
                    </div>
                    
                    <div style={{ marginBottom: 16 }}>
                      <Space>
                        <Switch
                          checked={generateSpeech}
                          onChange={(checked) => {
                            setGenerateSpeech(checked);
                            if (checked && !extractVoice) {
                              setExtractVoice(true);
                            }
                          }}
                          disabled={isProcessing}
                        />
                        <span>生成语音</span>
                        <Tooltip title="使用提取的音色生成新的语音">
                          <InfoCircleOutlined style={{ color: '#1890ff' }} />
                        </Tooltip>
                      </Space>
                    </div>
                    
                    {generateSpeech && (
                      <div style={{ marginLeft: 24, marginBottom: 16 }}>
                        <div style={{ marginBottom: 8 }}>
                          <Text strong>语音文本: <span style={{ color: '#ff4d4f' }}>*</span></Text>
                          <Tooltip title="输入要生成的语音文本（必填）">
                            <InfoCircleOutlined style={{ marginLeft: 8, color: '#1890ff' }} />
                          </Tooltip>
                        </div>
                        <TextArea
                          rows={4}
                          value={voiceText}
                          onChange={(e) => setVoiceText(e.target.value)}
                          placeholder="请在此输入要生成的语音文本，这将用于语音合成和唇形同步"
                          disabled={isProcessing}
                          style={{ borderColor: !voiceText ? '#ff4d4f' : undefined }}
                          status={!voiceText ? 'error' : undefined}
                        />
                        {!voiceText && (
                          <div style={{ color: '#ff4d4f', fontSize: '12px', marginTop: '4px' }}>
                            请输入语音文本，这是生成语音和唇形同步所必需的
                          </div>
                        )}
                      </div>
                    )}
                    
                    <div style={{ marginBottom: 16 }}>
                      <Space>
                        <Switch
                          checked={lipSync}
                          onChange={(checked) => {
                            setLipSync(checked);
                            if (checked) {
                              if (!removeSubtitles) {
                                setRemoveSubtitles(true);
                              }
                              if (!generateSpeech) {
                                setGenerateSpeech(true);
                              }
                              if (!extractVoice) {
                                setExtractVoice(true);
                              }
                            }
                          }}
                          disabled={isProcessing}
                        />
                        <span>唇形同步</span>
                        <Tooltip title="使生成的语音与视频中人物的唇形同步">
                          <InfoCircleOutlined style={{ color: '#1890ff' }} />
                        </Tooltip>
                      </Space>
                    </div>
                    
                    {lipSync && (
                      <div style={{ marginLeft: 24 }}>
                        <Alert
                          message="唇形同步需要同时开启字幕擦除、音色提取和语音生成"
                          type="info"
                          showIcon
                          style={{ marginBottom: 16 }}
                        />
                      </div>
                    )}
                  </Card>
                </Col>
                
                <Col span={24}>
                  <Card 
                    title="视频超分辨率" 
                    size="small" 
                    className="option-card"
                    extra={
                      <Tag color={resolutionEnhancementAvailable ? "success" : "error"}>
                        {resolutionEnhancementAvailable ? "服务可用" : "服务不可用"}
                      </Tag>
                    }
                  >
                    <div style={{ marginBottom: 16 }}>
                      <Space>
                        <Switch
                          checked={enhanceResolution}
                          onChange={(checked) => setEnhanceResolution(checked)}
                          disabled={isProcessing || !resolutionEnhancementAvailable}
                        />
                        <span>启用视频超分辨率</span>
                        <Tooltip title="使用AI技术提高视频分辨率和清晰度">
                          <InfoCircleOutlined style={{ color: '#1890ff' }} />
                        </Tooltip>
                      </Space>
                    </div>
                    
                    {enhanceResolution && (
                      <div style={{ marginLeft: 24 }}>
                        <Form layout="vertical">
                          <Row gutter={16}>
                            <Col span={12}>
                              <Form.Item 
                                label={
                                  <Space>
                                    <span>放大倍数</span>
                                    <Tooltip title="设置视频放大的倍数">
                                      <InfoCircleOutlined style={{ color: '#1890ff' }} />
                                    </Tooltip>
                                  </Space>
                                }
                              >
                                <Select
                                  value={resolutionScale}
                                  onChange={(value) => setResolutionScale(value)}
                                  disabled={isProcessing}
                                  style={{ width: '100%' }}
                                  options={[
                                    { value: 2, label: '2倍' },
                                    { value: 3, label: '3倍' },
                                    { value: 4, label: '4倍' }
                                  ]}
                                />
                              </Form.Item>
                            </Col>
                            
                            <Col span={12}>
                              <Form.Item 
                                label={
                                  <Space>
                                    <span>模型选择</span>
                                    <Tooltip title="选择不同的超分辨率模型">
                                      <InfoCircleOutlined style={{ color: '#1890ff' }} />
                                    </Tooltip>
                                  </Space>
                                }
                              >
                                <Select
                                  value={resolutionModel}
                                  onChange={(value) => setResolutionModel(value)}
                                  disabled={isProcessing}
                                  style={{ width: '100%' }}
                                  options={[
                                    { value: 'realesrgan-x4plus', label: '通用模型 (推荐)' },
                                    { value: 'realesrgan-x4plus-anime', label: '动漫模型' },
                                    { value: 'realesrgan-x2plus', label: '2倍通用模型' }
                                  ].filter(option => availableModels.includes(option.value))}
                                />
                              </Form.Item>
                            </Col>
                            
                            <Col span={24}>
                              <Form.Item 
                                label={
                                  <Space>
                                    <span>降噪强度</span>
                                    <Tooltip title="调整降噪强度，值越大降噪效果越强">
                                      <InfoCircleOutlined style={{ color: '#1890ff' }} />
                                    </Tooltip>
                                  </Space>
                                }
                              >
                                <div style={{ display: 'flex', alignItems: 'center' }}>
                                  <InputNumber
                                    min={0}
                                    max={1}
                                    step={0.1}
                                    value={denoiseStrength}
                                    onChange={(value) => setDenoiseStrength(value as number)}
                                    disabled={isProcessing}
                                    style={{ width: '100%' }}
                                  />
                                </div>
                              </Form.Item>
                            </Col>
                          </Row>
                          
                          <Alert
                            message="超分辨率处理说明"
                            description={
                              <ul style={{ paddingLeft: '20px', margin: '8px 0' }}>
                                <li>处理时间取决于视频长度和分辨率，可能需要较长时间</li>
                                <li>通用模型适合真实视频，动漫模型适合动画内容</li>
                                <li>降噪强度建议值：0.5（平衡降噪和细节保留）</li>
                                <li>超分辨率处理会在添加字幕之前进行，以保证字幕清晰度</li>
                              </ul>
                            }
                            type="info"
                            showIcon
                          />
                        </Form>
                      </div>
                    )}
                    
                    {!resolutionEnhancementAvailable && (
                      <Alert
                        message="超分辨率服务不可用"
                        description="请联系管理员启用超分辨率服务"
                        type="warning"
                        showIcon
                      />
                    )}
                  </Card>
                </Col>
              </Row>
            </Col>
          </Row>
        </div>
        
        <div style={{ marginTop: 24, textAlign: 'center' }}>
          <Button
            type="primary"
            onClick={handleUpload}
            disabled={fileList.length === 0 || isProcessing}
            loading={isProcessing}
            icon={<VideoCameraOutlined />}
            size="large"
            style={{ height: '48px', width: '200px', fontSize: '16px' }}
          >
            {isProcessing ? '处理中...' : '开始处理'}
          </Button>
        </div>
      </Card>
      
      {renderTasks()}
      
      <style>{`
        .processor-card .ant-card-head {
          background-color: #f0f5ff;
          border-bottom: 1px solid #d6e4ff;
        }
        
        .task-card .ant-card-head {
          background-color: #f9f9f9;
        }
        
        .option-card .ant-card-head {
          background-color: #f5f5f5;
        }
        
        .pipeline-arrow {
          color: #999;
          margin: 0 4px;
        }
        
        .upload-list .ant-upload-list-item {
          border-radius: 4px;
          margin-bottom: 8px;
        }
      `}</style>
    </div>
  );
};

export default AIVideoProcessor;