# AI Agent MVP Kubernetes 배포

이 디렉토리에는 AI Agent MVP 애플리케이션을 Kubernetes에 배포하기 위한 매니페스트 파일들이 포함되어 있습니다.

## 📁 파일 구조

```
k8s/
├── backend.yaml          # Backend (FastAPI) Deployment & Service
├── frontend.yaml         # Frontend (Next.js) Deployment & Service
├── db.yaml              # PostgreSQL Deployment & Service
├── pv.yaml              # PersistentVolume & PersistentVolumeClaim
├── configmap.yaml       # ConfigMap (환경변수)
├── secret.yaml          # Secret (민감한 정보)
├── ingress.yaml         # Ingress (외부 접근)
├── deploy.sh            # 배포 스크립트
├── init-db.sql          # 데이터베이스 초기화 스크립트
└── README.md            # 이 파일
```

## 🚀 빠른 시작

### 1. 전체 배포
```bash
cd k8s
./deploy.sh
```

### 2. 개별 배포
```bash
# PostgreSQL만 배포
./deploy.sh --db-only

# Backend만 배포
./deploy.sh --backend-only

# Frontend만 배포
./deploy.sh --frontend-only
```

### 3. 상태 확인
```bash
./deploy.sh --status
```

### 4. 리소스 삭제
```bash
./deploy.sh --delete
```

## 🔧 설정

### 환경변수

**ConfigMap (`configmap.yaml`):**
- `NEXT_PUBLIC_API_BASE_URL`: Frontend에서 사용할 Backend API URL
- `NODE_ENV`: Node.js 환경 설정
- `LOG_LEVEL`: Backend 로그 레벨
- `DATABASE_URL`: PostgreSQL 연결 URL

**Secret (`secret.yaml`):**
- `OPENAI_SECRET_KEY`: OpenAI API 키 (Base64 인코딩)
- `DB_PASSWORD`: PostgreSQL 비밀번호 (Base64 인코딩)

### 리소스 제한

**Backend:**
- CPU: 100m 요청, 1000m 제한
- Memory: 256Mi 요청, 1Gi 제한

**Frontend:**
- CPU: 100m 요청, 1000m 제한
- Memory: 128Mi 요청, 512Mi 제한

**PostgreSQL:**
- CPU: 100m 요청, 500m 제한
- Memory: 256Mi 요청, 1Gi 제한
- Storage: 10Gi

## 🔐 보안

1. **Secret 사용**: 민감한 정보는 Kubernetes Secret으로 관리
2. **ConfigMap 분리**: 일반 설정은 ConfigMap으로 관리
3. **네임스페이스 분리**: 환경별 네임스페이스 사용 가능

## 📊 모니터링

### Pod 상태 확인
```bash
kubectl get pods -l app=ai-agent-backend
kubectl get pods -l app=ai-agent-frontend
kubectl get pods -l app=postgres
```

### 서비스 상태 확인
```bash
kubectl get services
```

### 로그 확인
```bash
kubectl logs -l app=ai-agent-backend
kubectl logs -l app=ai-agent-frontend
kubectl logs -l app=postgres
```

## 🌐 접속

### 포트 포워딩
```bash
# Backend API
kubectl port-forward svc/ai-agent-backend-service 8000:8000

# Frontend
kubectl port-forward svc/ai-agent-frontend-service 3000:3000

# PostgreSQL
kubectl port-forward svc/postgres-service 5432:5432
```

### 접속 URL
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- PostgreSQL: localhost:5432

## 🗄️ 데이터베이스

### 연결 정보
- **Host**: postgres-service
- **Port**: 5432
- **Database**: agent
- **Username**: admin
- **Password**: admin

### 데이터 영속성
- PostgreSQL 데이터는 PersistentVolume에 저장됩니다
- 기본 저장소 클래스: `standard`
- 저장소 크기: 10Gi

## 🔄 업데이트

### 이미지 업데이트
```bash
# 이미지 빌드
docker build -t ai-agent-backend:latest ./backend
docker build -t ai-agent-frontend:latest ./frontend

# 배포 업데이트
kubectl rollout restart deployment/ai-agent-backend-deployment
kubectl rollout restart deployment/ai-agent-frontend-deployment
```

### 설정 업데이트
```bash
# ConfigMap 업데이트
kubectl apply -f configmap.yaml

# Secret 업데이트
kubectl apply -f secret.yaml

# Pod 재시작
kubectl rollout restart deployment/ai-agent-backend-deployment
kubectl rollout restart deployment/ai-agent-frontend-deployment
```

## 🐛 문제 해결

### 일반적인 문제들

1. **Pod가 시작되지 않는 경우**
   ```bash
   kubectl describe pod <pod-name>
   kubectl logs <pod-name>
   ```

2. **서비스 연결 문제**
   ```bash
   kubectl get endpoints
   kubectl describe service <service-name>
   ```

3. **PersistentVolume 문제**
   ```bash
   kubectl get pv
   kubectl get pvc
   kubectl describe pvc postgres-pvc
   ```

4. **환경변수 문제**
   ```bash
   kubectl exec -it <pod-name> -- env | grep -E "(API|DB|NODE)"
   ```

## 📝 참고사항

- 이 설정은 개발 환경에 최적화되어 있습니다
- 프로덕션 환경에서는 추가적인 보안 설정이 필요할 수 있습니다
- 클러스터의 StorageClass에 따라 PersistentVolume 설정을 조정해야 할 수 있습니다
