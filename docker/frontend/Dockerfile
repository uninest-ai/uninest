FROM nginx:alpine

# 复制已构建的文件
COPY frontend/housing-web/dist /usr/share/nginx/html

# 复制nginx配置
COPY docker/frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]