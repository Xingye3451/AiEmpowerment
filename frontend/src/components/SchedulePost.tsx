import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
} from '@mui/material';
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { parseISO } from 'date-fns';
import axios from 'axios';
import { DOUYIN_API } from '../config/api';

interface SchedulePostProps {
  open: boolean;
  onClose: () => void;
  videoPath: string;
  videoTitle: string;
  videoDescription: string | undefined;
  accounts: string[];
  groups: Array<{
    id: string;
    name: string;
    accounts: string[];
  }>;
  onScheduled: () => void;
}

const SchedulePost: React.FC<SchedulePostProps> = ({
  open,
  onClose,
  videoPath,
  videoTitle,
  videoDescription,
  accounts,
  groups,
  onScheduled,
}) => {
  const [scheduleTime, setScheduleTime] = useState<Date | null>(null);
  const [selectedGroup, setSelectedGroup] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSchedule = async () => {
    if (!scheduleTime) {
      setError('请选择发布时间');
      return;
    }

    if (scheduleTime < new Date()) {
      setError('发布时间不能早于当前时间');
      return;
    }

    setIsSubmitting(true);
    setError('');

    try {
      const targetAccounts = selectedGroup
        ? groups.find(g => g.id === selectedGroup)?.accounts || []
        : accounts;

      await axios.post(DOUYIN_API.SCHEDULE, {
        video_path: videoPath,
        title: videoTitle,
        description: videoDescription,
        accounts: targetAccounts,
        schedule_time: scheduleTime.toISOString(),
        group_id: selectedGroup || null,
      });

      onScheduled();
      onClose();
    } catch (error: any) {
      setError(error.response?.data?.detail || '创建定时任务失败');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>定时发布设置</DialogTitle>
      <DialogContent>
        <Box sx={{ mt: 2 }}>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          <Typography variant="subtitle1" gutterBottom>
            视频信息
          </Typography>
          <Typography variant="body2" color="textSecondary">
            标题: {videoTitle}
          </Typography>
          {videoDescription && (
            <Typography variant="body2" color="textSecondary">
              描述: {videoDescription}
            </Typography>
          )}

          <Box sx={{ my: 3 }}>
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>选择发布账号组</InputLabel>
              <Select
                value={selectedGroup}
                onChange={(e) => setSelectedGroup(e.target.value as string)}
                label="选择发布账号组"
              >
                <MenuItem value="">
                  <em>使用当前选择的账号 ({accounts.length}个)</em>
                </MenuItem>
                {groups.map((group) => (
                  <MenuItem key={group.id} value={group.id}>
                    {group.name} ({group.accounts.length}个账号)
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <LocalizationProvider dateAdapter={AdapterDateFns}>
              <DateTimePicker
                label="选择发布时间"
                value={scheduleTime}
                onChange={(newValue) => setScheduleTime(newValue)}
                slotProps={{
                  textField: {
                    fullWidth: true,
                    helperText: '请选择未来的时间点',
                  },
                }}
                minDateTime={new Date()}
              />
            </LocalizationProvider>
          </Box>

          <Typography variant="body2" color="textSecondary">
            将发布到 {selectedGroup
              ? groups.find(g => g.id === selectedGroup)?.accounts.length
              : accounts.length} 个账号
          </Typography>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>取消</Button>
        <Button
          onClick={handleSchedule}
          variant="contained"
          color="primary"
          disabled={isSubmitting || !scheduleTime}
        >
          {isSubmitting ? '创建中...' : '创建定时任务'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default SchedulePost;