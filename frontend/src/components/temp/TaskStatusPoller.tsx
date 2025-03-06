import React, { useEffect } from 'react';
import axios from 'axios';
import { DOUYIN_API } from '../../config/api';

interface ProcessingTask {
  task_id: string;
  original_filename: string;
  processed_filename: string;
  status?: string;
  progress?: number;
  result?: any;
}

interface TaskStatusPollerProps {
  processingTasks: ProcessingTask[];
  setProcessingTasks: React.Dispatch<React.SetStateAction<ProcessingTask[]>>;
}

const TaskStatusPoller: React.FC<TaskStatusPollerProps> = ({ 
  processingTasks, 
  setProcessingTasks 
}) => {
  useEffect(() => {
    // 只有当有处理任务时才开始轮询
    if (processingTasks.length === 0) return;
    
    console.log('TaskStatusPoller: 开始轮询任务状态', processingTasks);

    const updateTaskStatus = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          console.error('TaskStatusPoller: 未找到认证令牌');
          return;
        }

        // 创建新的任务数组，用于更新状态
        const updatedTasks = [...processingTasks];
        let hasUpdates = false;

        // 对每个任务进行状态查询
        for (let i = 0; i < updatedTasks.length; i++) {
          const task = updatedTasks[i];
          
          // 只查询未完成的任务
          if (task.status !== 'completed' && task.status !== 'failed') {
            console.log(`TaskStatusPoller: 查询任务 ${task.task_id} 状态`);
            try {
              const response = await axios.get(DOUYIN_API.PROCESS_STATUS(task.task_id), {
                headers: {
                  'Authorization': `Bearer ${token}`
                }
              });
              
              // 更新任务状态
              if (response.data) {
                console.log(`TaskStatusPoller: 任务 ${task.task_id} 状态更新:`, response.data);
                updatedTasks[i] = {
                  ...task,
                  status: response.data.status,
                  progress: response.data.progress,
                  result: response.data.result
                };
                hasUpdates = true;
              }
            } catch (err) {
              console.error(`TaskStatusPoller: 获取任务 ${task.task_id} 状态失败:`, err);
            }
          } else {
            console.log(`TaskStatusPoller: 跳过已完成或失败的任务 ${task.task_id}`);
          }
        }

        // 只有在有更新时才设置状态
        if (hasUpdates) {
          console.log('TaskStatusPoller: 更新任务状态:', updatedTasks);
          setProcessingTasks(updatedTasks);
        } else {
          console.log('TaskStatusPoller: 没有任务状态更新');
        }
      } catch (err) {
        console.error('TaskStatusPoller: 更新任务状态失败:', err);
      }
    };

    // 立即执行一次
    updateTaskStatus();

    // 设置轮询间隔
    const interval = setInterval(updateTaskStatus, 3000);
    console.log('TaskStatusPoller: 设置轮询间隔 3000ms');

    // 清理函数
    return () => {
      console.log('TaskStatusPoller: 清理轮询');
      clearInterval(interval);
    };
  }, [processingTasks, setProcessingTasks]);

  // 这个组件不渲染任何内容
  return null;
};

export default TaskStatusPoller; 