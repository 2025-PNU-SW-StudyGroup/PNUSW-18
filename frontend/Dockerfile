FROM node:22.14.0 AS build

WORKDIR /app
COPY . ./

RUN \
      npm install && \
      npm run build

FROM nginx:stable-alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
