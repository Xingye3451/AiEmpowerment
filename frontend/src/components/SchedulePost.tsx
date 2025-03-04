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
  Zoom,
  Paper,
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
    <Dialog 
      open={open} 
      onClose={onClose} 
      maxWidth="sm" 
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 3,
          background: 'linear-gradient(45deg, #f5f5f5 30%, #ffffff 90%)',
          boxShadow: '0 3px 5px 2px rgba(0, 0, 0, .2)',
        }
      }}
    >
      <DialogTitle
        sx={{
          fontWeight: 'bold',
          color: theme => theme.palette.primary.main,
          borderBottom: '1px solid rgba(0, 0, 0, 0.12)',
          pb: 2,
        }}
      >
        定时发布设置
      </DialogTitle>
      <DialogContent>
        <Box sx={{ mt: 2 }}>
          {error && (
            <Zoom in={!!error}>
              <Alert 
                severity="error" 
                sx={{ 
                  mb: 2,
                  borderRadius: 2,
                  boxShadow: '0 2px 8px rgba(244, 67, 54, 0.2)',
                }}
              >
                {error}
              </Alert>
            </Zoom>
          )}

          <Paper
            elevation={0}
            sx={{
              p: 2,
              mb: 3,
              backgroundColor: 'rgba(0, 0, 0, 0.02)',
              borderRadius: 2,
            }}
          >
            <Typography 
              variant="subtitle1" 
              gutterBottom
              sx={{ 
                fontWeight: 'bold',
                color: theme => theme.palette.primary.main,
              }}
            >
              视频信息
            </Typography>
            <Typography 
              variant="body2" 
              color="textSecondary"
              sx={{ mb: 1 }}
            >
              标题: {videoTitle}
            </Typography>
            {videoDescription && (
              <Typography 
                variant="body2" 
                color="textSecondary"
              >
                描述: {videoDescription}
              </Typography>
            )}
          </Paper>

          <Box sx={{ my: 3 }}>
            <FormControl 
              fullWidth 
              sx={{ 
                mb: 3,
                '& .MuiOutlinedInput-root': {
                  borderRadius: 2,
                  backgroundColor: '#ffffff',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
                },
              }}
            >
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
                    sx: {
                      '& .MuiOutlinedInput-root': {
                        borderRadius: 2,
                        backgroundColor: '#ffffff',
                        boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
                      },
                    },
                  },
                }}
                minDateTime={new Date()}
              />
            </LocalizationProvider>
          </Box>

          <Typography 
            variant="body2" 
            color="textSecondary"
            sx={{
              p: 2,
              backgroundColor: 'rgba(33, 150, 243, 0.08)',
              borderRadius: 2,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            将发布到 {selectedGroup
              ? groups.find(g => g.id === selectedGroup)?.accounts.length
              : accounts.length} 个账号
          </Typography>
        </Box>
      </DialogContent>
      <DialogActions sx={{ p: 3, borderTop: '1px solid rgba(0, 0, 0, 0.12)' }}>
        <Button 
          onClick={onClose}
          sx={{
            borderRadius: 2,
            px: 3,
            color: theme => theme.palette.text.secondary,
          }}
        >
          取消
        </Button>
        <Button
          onClick={handleSchedule}
          variant="contained"
          color="primary"
          disabled={isSubmitting || !scheduleTime}
          sx={{
            borderRadius: 2,
            px: 3,
            background: 'linear-gradient(45deg, #3f51b5 30%, #757de8 90%)',
            boxShadow: '0 3px 5px 2px rgba(63, 81, 181, .3)',
            transition: 'transform 0.3s',
            '&:hover': {
              transform: 'translateY(-1px)',
            },
            '&:disabled': {
              background: theme => theme.palette.action.disabledBackground,
            },
          }}
        >
          {isSubmitting ? '创建中...' : '创建定时任务'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default SchedulePost;