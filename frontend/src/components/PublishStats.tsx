import React, { useEffect, useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import axios from 'axios';
import { DOUYIN_API } from '../config/api';

interface AccountStats {
  [key: string]: {
    success: number;
    failed: number;
  };
}

interface StatsData {
  total_posts: number;
  success_rate: number;
  account_stats: AccountStats;
}

const PublishStats: React.FC = () => {
  const [stats, setStats] = useState<StatsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await axios.get<StatsData>(DOUYIN_API.STATS);
      setStats(response.data);
    } catch (error: any) {
      setError(error.response?.data?.detail || '获取统计信息失败');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" p={4}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  if (!stats) {
    return (
      <Typography variant="body2" align="center" color="textSecondary">
        暂无统计数据
      </Typography>
    );
  }

  return (
    <Box>
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h6" color="textSecondary">
              总发布次数
            </Typography>
            <Typography variant="h4">
              {stats.total_posts}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h6" color="textSecondary">
              发布成功率
            </Typography>
            <Typography variant="h4">
              {(stats.success_rate * 100).toFixed(1)}%
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="h6" color="textSecondary">
              活跃账号数
            </Typography>
            <Typography variant="h4">
              {Object.keys(stats.account_stats).length}
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          账号发布统计
        </Typography>
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>账号</TableCell>
                <TableCell align="right">发布成功</TableCell>
                <TableCell align="right">发布失败</TableCell>
                <TableCell align="right">成功率</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {Object.entries(stats.account_stats).map(([account, data]) => {
                const total = data.success + data.failed;
                const successRate = total > 0 ? (data.success / total * 100) : 0;
                return (
                  <TableRow key={account}>
                    <TableCell>{account}</TableCell>
                    <TableCell align="right">{data.success}</TableCell>
                    <TableCell align="right">{data.failed}</TableCell>
                    <TableCell align="right">
                      {successRate.toFixed(1)}%
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Box>
  );
};

export default PublishStats;