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
  Zoom,
  Fade,
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
      <Box 
        display="flex" 
        justifyContent="center" 
        alignItems="center" 
        minHeight="200px"
      >
        <CircularProgress 
          sx={{ 
            color: theme => theme.palette.primary.main 
          }} 
        />
      </Box>
    );
  }

  if (error) {
    return (
      <Zoom in>
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
    );
  }

  if (!stats) {
    return (
      <Typography 
        variant="body2" 
        align="center" 
        color="textSecondary"
        sx={{
          mt: 3,
          fontStyle: 'italic',
        }}
      >
        暂无统计数据
      </Typography>
    );
  }

  return (
    <Fade in>
      <Box>
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} md={4}>
            <Paper 
              sx={{ 
                p: 3,
                textAlign: 'center',
                background: 'linear-gradient(45deg, #e3f2fd 30%, #ffffff 90%)',
                borderRadius: 3,
                boxShadow: '0 3px 5px 2px rgba(33, 150, 243, .3)',
                transition: 'transform 0.3s ease-in-out',
                '&:hover': {
                  transform: 'translateY(-4px)',
                },
              }}
            >
              <Typography 
                variant="h6" 
                color="textSecondary"
                sx={{ mb: 2, fontWeight: 500 }}
              >
                总发布次数
              </Typography>
              <Typography 
                variant="h4"
                sx={{ 
                  fontWeight: 'bold',
                  color: theme => theme.palette.primary.main,
                }}
              >
                {stats.total_posts}
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} md={4}>
            <Paper 
              sx={{ 
                p: 3,
                textAlign: 'center',
                background: 'linear-gradient(45deg, #e8f5e9 30%, #ffffff 90%)',
                borderRadius: 3,
                boxShadow: '0 3px 5px 2px rgba(76, 175, 80, .3)',
                transition: 'transform 0.3s ease-in-out',
                '&:hover': {
                  transform: 'translateY(-4px)',
                },
              }}
            >
              <Typography 
                variant="h6" 
                color="textSecondary"
                sx={{ mb: 2, fontWeight: 500 }}
              >
                发布成功率
              </Typography>
              <Typography 
                variant="h4"
                sx={{ 
                  fontWeight: 'bold',
                  color: theme => theme.palette.success.main,
                }}
              >
                {(stats.success_rate * 100).toFixed(1)}%
              </Typography>
            </Paper>
          </Grid>
          <Grid item xs={12} md={4}>
            <Paper 
              sx={{ 
                p: 3,
                textAlign: 'center',
                background: 'linear-gradient(45deg, #f3e5f5 30%, #ffffff 90%)',
                borderRadius: 3,
                boxShadow: '0 3px 5px 2px rgba(156, 39, 176, .3)',
                transition: 'transform 0.3s ease-in-out',
                '&:hover': {
                  transform: 'translateY(-4px)',
                },
              }}
            >
              <Typography 
                variant="h6" 
                color="textSecondary"
                sx={{ mb: 2, fontWeight: 500 }}
              >
                活跃账号数
              </Typography>
              <Typography 
                variant="h4"
                sx={{ 
                  fontWeight: 'bold',
                  color: theme => theme.palette.secondary.main,
                }}
              >
                {Object.keys(stats.account_stats).length}
              </Typography>
            </Paper>
          </Grid>
        </Grid>

        <Paper 
          sx={{ 
            p: 3,
            background: 'linear-gradient(45deg, #fafafa 30%, #ffffff 90%)',
            borderRadius: 3,
            boxShadow: '0 3px 5px 2px rgba(0, 0, 0, .1)',
          }}
        >
          <Typography 
            variant="h6" 
            gutterBottom
            sx={{ 
              fontWeight: 'bold',
              color: theme => theme.palette.primary.main,
              mb: 3,
            }}
          >
            账号发布统计
          </Typography>
          <TableContainer>
            <Table 
              size="small"
              sx={{
                '& .MuiTableCell-head': {
                  fontWeight: 'bold',
                  backgroundColor: theme => theme.palette.primary.light,
                  color: theme => theme.palette.primary.contrastText,
                },
                '& .MuiTableRow-root:hover': {
                  backgroundColor: 'rgba(0, 0, 0, 0.04)',
                },
              }}
            >
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
                    <TableRow 
                      key={account}
                      sx={{
                        transition: 'background-color 0.3s',
                      }}
                    >
                      <TableCell sx={{ fontWeight: 500 }}>{account}</TableCell>
                      <TableCell 
                        align="right"
                        sx={{ color: theme => theme.palette.success.main }}
                      >
                        {data.success}
                      </TableCell>
                      <TableCell 
                        align="right"
                        sx={{ color: theme => theme.palette.error.main }}
                      >
                        {data.failed}
                      </TableCell>
                      <TableCell 
                        align="right"
                        sx={{ 
                          fontWeight: 'bold',
                          color: successRate >= 80 
                            ? theme => theme.palette.success.main
                            : successRate >= 50
                            ? theme => theme.palette.warning.main
                            : theme => theme.palette.error.main,
                        }}
                      >
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
    </Fade>
  );
};

export default PublishStats;