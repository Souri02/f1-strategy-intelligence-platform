FROM node:20-alpine

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend ./

ENV NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

CMD ["npm", "run", "dev"]
