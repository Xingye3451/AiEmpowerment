import { useState, useEffect, useRef } from 'react';

interface WebSocketMessage {
  data: string;
  type: string;
  target: WebSocket;
}

export const useWebSocket = (url?: string) => {
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [readyState, setReadyState] = useState<number>(WebSocket.CONNECTING);
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // 如果没有提供URL，使用当前主机的WebSocket URL
    const wsUrl = url || `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws`;
    
    // 创建WebSocket连接
    const socket = new WebSocket(wsUrl);
    socketRef.current = socket;

    // 连接打开时
    socket.onopen = () => {
      console.log('WebSocket连接已建立');
      setReadyState(WebSocket.OPEN);
    };

    // 收到消息时
    socket.onmessage = (event) => {
      console.log('收到WebSocket消息:', event.data);
      setLastMessage({
        data: event.data,
        type: 'message',
        target: socket
      });
    };

    // 连接关闭时
    socket.onclose = () => {
      console.log('WebSocket连接已关闭');
      setReadyState(WebSocket.CLOSED);
    };

    // 发生错误时
    socket.onerror = (error) => {
      console.error('WebSocket错误:', error);
      setReadyState(WebSocket.CLOSED);
    };

    // 组件卸载时关闭连接
    return () => {
      if (socket.readyState === WebSocket.OPEN) {
        socket.close();
      }
    };
  }, [url]);

  // 发送消息的函数
  const sendMessage = (message: string | object) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      const data = typeof message === 'string' ? message : JSON.stringify(message);
      socketRef.current.send(data);
    } else {
      console.error('WebSocket未连接，无法发送消息');
    }
  };

  return {
    lastMessage,
    readyState,
    sendMessage
  };
}; 