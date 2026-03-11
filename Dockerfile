FROM nginx:1.27-alpine

COPY docs/ /usr/share/nginx/html/

EXPOSE 80
