# 第一阶段：构建环境
FROM node:16-alpine AS build

WORKDIR /app

# 设置环境变量
ENV NODE_ENV=production

# 设置 npm 使用阿里云镜像源
RUN npm config set registry https://registry.npmmirror.com \
    && npm config set sass_binary_site https://npmmirror.com/mirrors/node-sass/

# 复制包管理文件
COPY package*.json ./

# 安装依赖
RUN npm install

# 复制源代码
COPY . .

# 构建生产版本
RUN npm run build

# 生产环境
FROM nginx:alpine

# 设置 nginx 使用阿里云镜像源
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories

# 复制构建产物到 Nginx 目录
COPY --from=build /app/build /usr/share/nginx/html

# 复制 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]