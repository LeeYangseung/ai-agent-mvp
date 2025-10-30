# 멀티스테이지 빌드 - 빌드 스테이지
FROM node:18-alpine AS builder

# 빌드 시 사용할 환경변수 정의
ARG NEXT_PUBLIC_API_BASE_URL
ARG NODE_ENV=production

# 작업 디렉토리 설정
WORKDIR /app

# 패키지 매니저 파일들 복사
COPY package*.json package-lock.json ./

# 의존성 설치 (빌드에 필요한 모든 의존성 포함)
RUN npm ci --legacy-peer-deps --include=dev

# 소스 코드 복사
COPY . .

# 환경변수를 빌드 시 주입
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL
ENV NODE_ENV=$NODE_ENV

# Next.js 애플리케이션 빌드
RUN npm run build

# 프로덕션 스테이지
FROM node:18-alpine AS runner

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 사용자를 생성하여 보안 강화
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# 빌드된 애플리케이션 복사
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# 사용자 변경
USER nextjs

# 포트 노출
EXPOSE 3000

# 환경 변수 설정
ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

# 애플리케이션 실행
CMD ["node", "server.js"]
