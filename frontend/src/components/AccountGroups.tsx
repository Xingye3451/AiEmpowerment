import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  TextField,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Chip,
  Zoom,
  Fade,
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import GroupAddIcon from '@mui/icons-material/GroupAdd';
import axios from 'axios';
import { DOUYIN_API } from '../config/api';

interface Group {
  id: string;
  name: string;
  accounts: string[];
  created_at: string;
}

interface Account {
  username: string;
  status: 'active' | 'inactive';
}

const AccountGroups: React.FC = () => {
  const [groups, setGroups] = useState<Group[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [groupName, setGroupName] = useState('');
  const [selectedAccounts, setSelectedAccounts] = useState<string[]>([]);
  const [message, setMessage] = useState({ type: '', content: '' });
  const [openDialog, setOpenDialog] = useState(false);
  const [editingGroup, setEditingGroup] = useState<Group | null>(null);

  useEffect(() => {
    fetchGroups();
    fetchAccounts();
  }, []);

  const fetchGroups = async () => {
    try {
      const response = await axios.get(DOUYIN_API.GROUPS);
      const groupsData = Object.entries(response.data).map(([id, data]: [string, any]) => ({
        id,
        ...data,
      }));
      setGroups(groupsData);
    } catch (error) {
      console.error('Failed to fetch groups:', error);
      setMessage({ type: 'error', content: '获取分组失败' });
    }
  };

  const fetchAccounts = async () => {
    try {
      const response = await axios.get(DOUYIN_API.ACCOUNTS);
      setAccounts(response.data);
    } catch (error) {
      console.error('Failed to fetch accounts:', error);
    }
  };

  const handleCreateGroup = async () => {
    if (!groupName || selectedAccounts.length === 0) {
      setMessage({ type: 'error', content: '请填写分组名称并选择账号' });
      return;
    }

    try {
      await axios.post(DOUYIN_API.GROUPS, {
        name: groupName,
        accounts: selectedAccounts,
      });

      setMessage({ type: 'success', content: '创建分组成功' });
      setGroupName('');
      setSelectedAccounts([]);
      fetchGroups();
      setOpenDialog(false);
    } catch (error) {
      setMessage({ type: 'error', content: '创建分组失败' });
    }
  };

  const handleEditGroup = async (group: Group) => {
    setEditingGroup(group);
    setGroupName(group.name);
    setSelectedAccounts(group.accounts);
    setOpenDialog(true);
  };

  const handleUpdateGroup = async () => {
    if (!editingGroup || !groupName || selectedAccounts.length === 0) {
      return;
    }

    try {
      await axios.put(DOUYIN_API.GROUP(editingGroup.id), {
        name: groupName,
        accounts: selectedAccounts,
      });

      setMessage({ type: 'success', content: '更新分组成功' });
      setGroupName('');
      setSelectedAccounts([]);
      setEditingGroup(null);
      fetchGroups();
      setOpenDialog(false);
    } catch (error) {
      setMessage({ type: 'error', content: '更新分组失败' });
    }
  };

  const handleDeleteGroup = async (groupId: string) => {
    try {
      await axios.delete(DOUYIN_API.GROUP(groupId));
      setMessage({ type: 'success', content: '删除分组成功' });
      fetchGroups();
    } catch (error) {
      setMessage({ type: 'error', content: '删除分组失败' });
    }
  };

  const toggleAccount = (username: string) => {
    setSelectedAccounts(prev =>
      prev.includes(username)
        ? prev.filter(acc => acc !== username)
        : [...prev, username]
    );
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography 
        variant="h5" 
        gutterBottom
        sx={{
          fontWeight: 'bold',
          color: theme => theme.palette.primary.main,
          mb: 3,
        }}
      >
        账号分组管理
      </Typography>

      {message.content && (
        <Zoom in={!!message.content}>
          <Alert 
            severity={message.type as 'success' | 'error'} 
            sx={{ 
              mb: 2,
              borderRadius: 2,
              boxShadow: message.type === 'success'
                ? '0 2px 8px rgba(76, 175, 80, 0.2)'
                : '0 2px 8px rgba(244, 67, 54, 0.2)',
            }}
          >
            {message.content}
          </Alert>
        </Zoom>
      )}

      <Button
        variant="contained"
        startIcon={<GroupAddIcon />}
        onClick={() => {
          setEditingGroup(null);
          setGroupName('');
          setSelectedAccounts([]);
          setOpenDialog(true);
        }}
        sx={{
          mb: 3,
          background: 'linear-gradient(45deg, #3f51b5 30%, #757de8 90%)',
          borderRadius: 2,
          boxShadow: '0 3px 5px 2px rgba(63, 81, 181, .3)',
          transition: 'transform 0.3s',
          '&:hover': {
            transform: 'translateY(-2px)',
          },
        }}
      >
        创建新分组
      </Button>

      <Fade in>
        <Paper 
          elevation={3}
          sx={{
            background: 'linear-gradient(45deg, #f5f5f5 30%, #ffffff 90%)',
            borderRadius: 3,
            boxShadow: '0 3px 5px 2px rgba(0, 0, 0, .1)',
            overflow: 'hidden',
          }}
        >
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell 
                    sx={{ 
                      fontWeight: 'bold',
                      backgroundColor: theme => theme.palette.primary.light,
                      color: theme => theme.palette.primary.contrastText,
                    }}
                  >
                    分组名称
                  </TableCell>
                  <TableCell 
                    sx={{ 
                      fontWeight: 'bold',
                      backgroundColor: theme => theme.palette.primary.light,
                      color: theme => theme.palette.primary.contrastText,
                    }}
                  >
                    账号数量
                  </TableCell>
                  <TableCell 
                    sx={{ 
                      fontWeight: 'bold',
                      backgroundColor: theme => theme.palette.primary.light,
                      color: theme => theme.palette.primary.contrastText,
                    }}
                  >
                    创建时间
                  </TableCell>
                  <TableCell 
                    sx={{ 
                      fontWeight: 'bold',
                      backgroundColor: theme => theme.palette.primary.light,
                      color: theme => theme.palette.primary.contrastText,
                    }}
                  >
                    操作
                  </TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {groups.map((group) => (
                  <TableRow 
                    key={group.id}
                    sx={{
                      transition: 'background-color 0.3s',
                      '&:hover': {
                        backgroundColor: 'rgba(0, 0, 0, 0.04)',
                      },
                    }}
                  >
                    <TableCell sx={{ fontWeight: 500 }}>{group.name}</TableCell>
                    <TableCell>
                      <Chip 
                        label={group.accounts.length}
                        color="primary"
                        size="small"
                        sx={{ 
                          fontWeight: 'bold',
                          background: 'linear-gradient(45deg, #3f51b5 30%, #757de8 90%)',
                        }}
                      />
                    </TableCell>
                    <TableCell>
                      {new Date(group.created_at).toLocaleString()}
                    </TableCell>
                    <TableCell>
                      <IconButton 
                        onClick={() => handleEditGroup(group)}
                        sx={{
                          color: theme => theme.palette.primary.main,
                          transition: 'transform 0.2s',
                          '&:hover': {
                            transform: 'scale(1.1)',
                          },
                        }}
                      >
                        <EditIcon />
                      </IconButton>
                      <IconButton 
                        onClick={() => handleDeleteGroup(group.id)}
                        sx={{
                          color: theme => theme.palette.error.main,
                          transition: 'transform 0.2s',
                          '&:hover': {
                            transform: 'scale(1.1)',
                          },
                        }}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      </Fade>

      <Dialog 
        open={openDialog} 
        onClose={() => setOpenDialog(false)} 
        maxWidth="md" 
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
          {editingGroup ? '编辑分组' : '创建新分组'}
        </DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="分组名称"
            value={groupName}
            onChange={(e) => setGroupName(e.target.value)}
            sx={{
              mt: 2,
              mb: 2,
              '& .MuiOutlinedInput-root': {
                borderRadius: 2,
                backgroundColor: '#ffffff',
                boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
              },
            }}
          />
          <Typography 
            variant="subtitle1" 
            gutterBottom
            sx={{
              fontWeight: 'bold',
              color: theme => theme.palette.primary.main,
            }}
          >
            选择账号
          </Typography>
          <List sx={{ maxHeight: 400, overflow: 'auto' }}>
            {accounts.map((account) => (
              <ListItem 
                key={account.username} 
                dense 
                button 
                onClick={() => toggleAccount(account.username)}
                sx={{
                  borderRadius: 1,
                  mb: 0.5,
                  transition: 'all 0.3s',
                  '&:hover': {
                    backgroundColor: 'rgba(63, 81, 181, 0.08)',
                  },
                }}
              >
                <ListItemText 
                  primary={account.username}
                  sx={{
                    '& .MuiTypography-root': {
                      fontWeight: selectedAccounts.includes(account.username) ? 'bold' : 'normal',
                    },
                  }}
                />
                <ListItemSecondaryAction>
                  <Chip
                    label={selectedAccounts.includes(account.username) ? '已选择' : '未选择'}
                    color={selectedAccounts.includes(account.username) ? 'primary' : 'default'}
                    onClick={() => toggleAccount(account.username)}
                    sx={{
                      transition: 'all 0.3s',
                      ...(selectedAccounts.includes(account.username) && {
                        background: 'linear-gradient(45deg, #3f51b5 30%, #757de8 90%)',
                      }),
                    }}
                  />
                </ListItemSecondaryAction>
              </ListItem>
            ))}
          </List>
        </DialogContent>
        <DialogActions sx={{ p: 3, borderTop: '1px solid rgba(0, 0, 0, 0.12)' }}>
          <Button 
            onClick={() => setOpenDialog(false)}
            sx={{
              borderRadius: 2,
              px: 3,
              color: theme => theme.palette.text.secondary,
            }}
          >
            取消
          </Button>
          <Button
            onClick={editingGroup ? handleUpdateGroup : handleCreateGroup}
            variant="contained"
            color="primary"
            sx={{
              borderRadius: 2,
              px: 3,
              background: 'linear-gradient(45deg, #3f51b5 30%, #757de8 90%)',
              boxShadow: '0 3px 5px 2px rgba(63, 81, 181, .3)',
              transition: 'transform 0.3s',
              '&:hover': {
                transform: 'translateY(-1px)',
              },
            }}
          >
            {editingGroup ? '更新' : '创建'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AccountGroups;