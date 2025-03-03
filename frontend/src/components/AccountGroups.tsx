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
      <Typography variant="h5" gutterBottom>
        账号分组管理
      </Typography>

      {message.content && (
        <Alert severity={message.type as 'success' | 'error'} sx={{ mb: 2 }}>
          {message.content}
        </Alert>
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
        sx={{ mb: 2 }}
      >
        创建新分组
      </Button>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>分组名称</TableCell>
              <TableCell>账号数量</TableCell>
              <TableCell>创建时间</TableCell>
              <TableCell>操作</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {groups.map((group) => (
              <TableRow key={group.id}>
                <TableCell>{group.name}</TableCell>
                <TableCell>{group.accounts.length}</TableCell>
                <TableCell>
                  {new Date(group.created_at).toLocaleString()}
                </TableCell>
                <TableCell>
                  <IconButton onClick={() => handleEditGroup(group)}>
                    <EditIcon />
                  </IconButton>
                  <IconButton onClick={() => handleDeleteGroup(group.id)}>
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingGroup ? '编辑分组' : '创建新分组'}
        </DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="分组名称"
            value={groupName}
            onChange={(e) => setGroupName(e.target.value)}
            sx={{ mb: 2, mt: 2 }}
          />
          <Typography variant="subtitle1" gutterBottom>
            选择账号
          </Typography>
          <List>
            {accounts.map((account) => (
              <ListItem key={account.username} dense button onClick={() => toggleAccount(account.username)}>
                <ListItemText primary={account.username} />
                <ListItemSecondaryAction>
                  <Chip
                    label={selectedAccounts.includes(account.username) ? '已选择' : '未选择'}
                    color={selectedAccounts.includes(account.username) ? 'primary' : 'default'}
                    onClick={() => toggleAccount(account.username)}
                  />
                </ListItemSecondaryAction>
              </ListItem>
            ))}
          </List>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>取消</Button>
          <Button
            onClick={editingGroup ? handleUpdateGroup : handleCreateGroup}
            variant="contained"
            color="primary"
          >
            {editingGroup ? '更新' : '创建'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AccountGroups;