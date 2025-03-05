# AI 赋能中心 - 通知系统

## 功能概述

通知系统是 AI 赋能中心的重要组成部分，用于向用户提供实时的系统消息、任务状态更新和重要事件提醒。该系统包括以下主要功能：

1. **实时通知提醒**：在顶部导航栏显示通知图标，未读通知数量以红色徽章显示
2. **通知中心下拉菜单**：点击通知图标显示最近的通知列表，可快速查看和管理通知
3. **通知分类**：支持系统通知、任务通知、定时任务通知等多种类型
4. **通知状态管理**：支持已读/未读状态标记，可一键标记所有通知为已读
5. **通知详情查看**：点击通知可查看完整内容和相关信息
6. **通知删除**：支持删除单条通知或批量删除通知
7. **通知页面**：提供专门的通知页面，支持分页查看所有历史通知

## 技术实现

### 后端实现

1. **数据模型**：

   - `Notification` 模型存储通知数据，包括标题、内容、类型、状态等字段
   - 与 `User` 模型建立关联，实现用户特定的通知

2. **API 接口**：

   - `/api/v1/notifications`：获取通知列表，支持分页和筛选
   - `/api/v1/notifications/count`：获取未读通知数量
   - `/api/v1/notifications/{id}/read`：标记单条通知为已读
   - `/api/v1/notifications/read-all`：标记所有通知为已读
   - `/api/v1/notifications/{id}`：删除单条通知
   - `/api/v1/notifications`：批量删除通知（带查询参数）

3. **通知服务**：
   - 提供创建、更新、删除通知的服务方法
   - 集成到任务调度系统，在任务完成时自动发送通知

### 前端实现

1. **通知中心组件**：

   - `NotificationCenter.tsx`：实现顶部导航栏的通知图标和下拉菜单
   - 显示未读通知数量，支持查看最近通知
   - 提供标记已读、删除等快捷操作

2. **通知页面组件**：

   - `NotificationsPage.tsx`：实现完整的通知管理页面
   - 支持通知分类查看（全部/未读/已读）
   - 提供批量操作功能（全部标记已读、清空通知）
   - 实现分页加载，高效处理大量通知

3. **集成到 Dashboard**：
   - 在主界面顶部导航栏集成通知中心组件
   - 在侧边菜单添加通知中心入口
   - 实现通知与相关功能页面的联动（如点击任务通知跳转到对应任务）

## 使用流程

1. 用户登录系统后，顶部导航栏显示通知图标，未读通知数量以红色徽章显示
2. 点击通知图标，显示最近的通知列表，可查看通知内容、标记已读或删除通知
3. 点击"查看全部通知"，进入通知中心页面，可以更全面地管理所有通知
4. 在通知中心页面，可以按类型筛选通知，批量标记已读或删除通知
5. 点击通知可查看详细内容，如果通知关联了特定任务，可以直接跳转到相关页面

## 未来扩展

1. **实时推送**：集成 WebSocket，实现服务器向客户端的实时通知推送
2. **通知偏好设置**：允许用户自定义接收哪些类型的通知
3. **邮件/短信通知**：重要通知同时通过邮件或短信发送给用户
4. **通知模板**：实现可配置的通知模板，提高通知内容的一致性和可维护性
5. **通知统计分析**：提供通知发送和阅读情况的统计分析功能
