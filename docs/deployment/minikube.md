# Minikube로 로컬 실행

Minikube는 로컬에서 Kubernetes를 실행하기 위한 도구입니다. 개발 및 테스트 환경에서 사용하며, 프로덕션 환경에서는 관리형 Kubernetes 서비스(EKS, GKE, AKS 등)를 사용하세요.

---

## 사전 요구사항

| 항목 | 버전 | 설치 링크 |
|-----|------|----------|
| Docker | 20.10+ | https://docs.docker.com/get-docker/ |
| Minikube | 1.25+ | https://minikube.sigs.k8s.io/docs/start/ |
| kubectl | 1.25+ | https://kubernetes.io/docs/tasks/tools/ |
| OpenAI API Key | - | https://platform.openai.com/ |

---

## 빠른 시작

### 1단계: Minikube 시작

```bash
cd k8s
./minikube.sh start
```

이 명령은 다음을 자동으로 수행합니다:
- Minikube 클러스터 시작 (Docker 드라이버 사용)
- Ingress addon 활성화
- Minikube Tunnel 실행 (백그라운드)

**출력 예시:**
```
😄  minikube v1.32.0 on Darwin 14.0
✨  Using the docker driver based on existing profile
👍  Starting control plane node minikube in cluster minikube
🚜  Pulling base image ...
🔄  Restarting existing docker container for "minikube" ...
🐳  Preparing Kubernetes v1.28.3 on Docker 24.0.7 ...
🔎  Verifying Kubernetes components...
🔗  Configuring Ingress addon...
🌟  Enabled addons: storage-provisioner, default-storageclass, ingress
🏄  Done! kubectl is now configured to use "minikube" cluster and "default" namespace by default

🚇  Starting minikube tunnel...
✅  Tunnel is running in background (PID: 12345)
```

### 2단계: Docker 이미지 빌드

```bash
cd ../docker
./docker_build.sh
```

**빌드 대상:**
- `ai-agent-backend:latest`
- `ai-agent-frontend:latest`

**빌드 시간:** 약 5-10분 (첫 빌드 시)

### 3단계: Minikube에 이미지 로드

```bash
cd ../k8s
minikube image load ai-agent-backend:latest
minikube image load ai-agent-frontend:latest
```

**주의:** Minikube는 독립적인 Docker 환경을 사용하므로, 로컬에서 빌드한 이미지를 Minikube로 로드해야 합니다.

### 4단계: Secret 설정

```bash
# secret.example.yaml을 참고하여 secret.yaml 생성
cp secret.example.yaml secret.yaml
vim secret.yaml  # OpenAI API 키 및 DB 크레덴셜 입력
```

**secret.yaml 예시:**

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: ai-agent-secret
type: Opaque
stringData:
  OPENAI_SECRET_KEY: "sk-your-openai-api-key-here"
  DB_USER: "postgres"
  DB_PASSWORD: "your-secure-password"
  DB_DATABASE: "ai_agent_db"
```

**보안 주의사항:**
- ⚠️ `secret.yaml`은 `.gitignore`에 포함되어 있으므로 Git에 커밋되지 않습니다
- ⚠️ OpenAI API 키는 절대 공개 저장소에 푸시하지 마세요

### 5단계: 애플리케이션 배포

```bash
./deploy.sh
```

이 스크립트는 다음을 순차적으로 배포합니다:

1. **ConfigMap**: 환경 변수 설정
2. **Secret**: 민감 정보 설정
3. **PostgreSQL**: 
   - Persistent Volume Claim (10Gi)
   - Deployment
   - Service (ClusterIP)
4. **Backend**:
   - Deployment (1 replica)
   - Service (ClusterIP, 포트 8000)
5. **Frontend**:
   - Deployment (1 replica)
   - Service (ClusterIP, 포트 3000)
6. **Ingress**:
   - Nginx Ingress Controller
   - 호스트: `aiagent.local`

**배포 시간:** 약 2-3분

### 6단계: 접속 설정

```bash
# /etc/hosts 파일에 도메인 추가 (최초 1회만)
sudo sh -c 'echo "127.0.0.1 aiagent.local" >> /etc/hosts'
```

**수동 추가 방법:**

```bash
sudo vim /etc/hosts
```

다음 줄 추가:
```
127.0.0.1 aiagent.local
```

### 7단계: 브라우저에서 접속

- **Frontend**: http://aiagent.local/
- **Backend API Docs**: http://aiagent.local/api/docs

**접속 테스트:**
```bash
# Health check
curl http://aiagent.local/api/v1/health

# 응답 예시:
# {"message":"health check"}
```

---

## 상태 확인

### 배포 상태 확인

```bash
./deploy.sh --status
```

**출력 예시:**
```
=== Deployment Status ===

Pods:
NAME                                    READY   STATUS    RESTARTS   AGE
ai-agent-backend-deployment-xxx         1/1     Running   0          5m
ai-agent-frontend-deployment-xxx        1/1     Running   0          5m
postgres-deployment-xxx                 1/1     Running   0          5m

Services:
NAME                        TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)
ai-agent-backend-service    ClusterIP   10.96.1.100     <none>        8000/TCP
ai-agent-frontend-service   ClusterIP   10.96.1.101     <none>        3000/TCP
postgres-service            ClusterIP   10.96.1.102     <none>        5432/TCP

Ingress:
NAME              CLASS   HOSTS           ADDRESS     PORTS   AGE
aiagent-ingress   nginx   aiagent.local   127.0.0.1   80      5m

Persistent Volume Claims:
NAME              STATUS   VOLUME          CAPACITY   ACCESS MODES
postgres-pvc      Bound    pvc-xxx         10Gi       RWO
```

### kubectl로 직접 확인

```bash
# Pod 상태
kubectl get pods

# Service 상태
kubectl get svc

# Ingress 상태
kubectl get ingress

# PVC 상태
kubectl get pvc

# 전체 리소스 확인
kubectl get all
```

---

## 로그 확인

### Backend 로그

```bash
kubectl logs -f deployment/ai-agent-backend-deployment
```

**유용한 로그 필터링:**
```bash
# 에러만 보기
kubectl logs deployment/ai-agent-backend-deployment | grep -i error

# 특정 시간대 로그
kubectl logs --since=10m deployment/ai-agent-backend-deployment
```

### Frontend 로그

```bash
kubectl logs -f deployment/ai-agent-frontend-deployment
```

### PostgreSQL 로그

```bash
kubectl logs -f deployment/postgres-deployment
```

### 모든 Pod 로그

```bash
# 모든 Pod의 로그를 한 번에
kubectl logs -f -l app=ai-agent-backend
kubectl logs -f -l app=ai-agent-frontend
kubectl logs -f -l app=postgres
```

---

## 이미지 업데이트

코드를 수정한 후 재배포하는 방법:

### 1. 이미지 재빌드

```bash
cd docker

# Backend만
./docker_build.sh --backend-only

# Frontend만
./docker_build.sh --frontend-only

# 둘 다
./docker_build.sh
```

### 2. Minikube에 이미지 로드

```bash
cd ../k8s

# Backend만
minikube image load ai-agent-backend:latest

# Frontend만
minikube image load ai-agent-frontend:latest

# 둘 다
minikube image load ai-agent-backend:latest
minikube image load ai-agent-frontend:latest
```

### 3. Deployment 재시작

```bash
# Backend만
kubectl rollout restart deployment/ai-agent-backend-deployment

# Frontend만
kubectl rollout restart deployment/ai-agent-frontend-deployment

# 둘 다
kubectl rollout restart deployment/ai-agent-backend-deployment
kubectl rollout restart deployment/ai-agent-frontend-deployment
```

**재시작 완료 대기:**
```bash
kubectl rollout status deployment/ai-agent-backend-deployment
kubectl rollout status deployment/ai-agent-frontend-deployment
```

---

## Minikube 관리

### 상태 확인

```bash
cd k8s
./minikube.sh status
```

**출력 예시:**
```
minikube
type: Control Plane
host: Running
kubelet: Running
apiserver: Running
kubeconfig: Configured

Tunnel status:
✅ Tunnel is running (PID: 12345)
```

### Tunnel 시작/중지

```bash
# Tunnel 시작
./minikube.sh tunnel

# Tunnel 중지
./minikube.sh tunnel-stop
```

### 중지 (데이터 보존)

```bash
./minikube.sh stop
```

**효과:**
- Minikube VM 중지
- 데이터는 보존됨 (PV, DB 데이터)
- `minikube start`로 재시작 가능

### 완전 삭제 (모든 데이터 삭제)

```bash
./minikube.sh stop --delete
```

**효과:**
- Minikube 클러스터 완전 삭제
- 모든 데이터 삭제 (복구 불가)
- 처음부터 다시 시작해야 함

---

## 데이터 영속성

### 데이터가 보존되는 경우
- ✅ `minikube stop` → `minikube start`
- ✅ Pod 재시작
- ✅ Deployment 재배포 (이미지 업데이트)

### 데이터가 삭제되는 경우
- ❌ `minikube delete`
- ❌ PVC 삭제 (`kubectl delete pvc postgres-pvc`)
- ❌ Namespace 삭제

### 백업 권장
프로덕션 환경에서는 정기적인 백업이 필수입니다:
```bash
# PostgreSQL 백업
kubectl exec deployment/postgres-deployment -- pg_dump -U postgres ai_agent_db > backup.sql

# 복원
kubectl exec -i deployment/postgres-deployment -- psql -U postgres ai_agent_db < backup.sql
```

---

## 접속 방법

### 1. Ingress (권장)

Minikube Tunnel이 실행되면 Ingress를 통해 접속:

```bash
# Frontend
open http://aiagent.local/

# Backend API
open http://aiagent.local/api/docs
```

**장점:**
- 실제 프로덕션 환경과 유사
- 하나의 URL로 Frontend + Backend 접속

**주의사항:**
- `/etc/hosts`에 `aiagent.local` 추가 필요
- Tunnel이 실행 중이어야 함

### 2. Port Forwarding

개별 Service를 직접 테스트할 때:

```bash
# Backend API
kubectl port-forward svc/ai-agent-backend-service 8000:8000

# Frontend
kubectl port-forward svc/ai-agent-frontend-service 3000:3000

# PostgreSQL
kubectl port-forward svc/postgres-service 5432:5432
```

**접속:**
- Backend: http://localhost:8000/docs
- Frontend: http://localhost:3000
- PostgreSQL: `psql -h localhost -U postgres -d ai_agent_db`

**장점:**
- Tunnel 없이 사용 가능
- 개별 서비스 테스트에 유용

**단점:**
- 각 서비스마다 별도 터미널 필요
- Frontend에서 Backend API 호출 시 CORS 문제 발생 가능

---

## 문제 해결

### Pod가 Pending 상태

**원인:** 리소스 부족

**해결:**
```bash
# Minikube 리소스 증가
minikube delete
minikube start --cpus=4 --memory=8192
```

### Pod가 ImagePullBackOff 상태

**원인:** Minikube가 로컬 이미지를 찾지 못함

**해결:**
```bash
# 이미지를 Minikube에 로드
minikube image load ai-agent-backend:latest
minikube image load ai-agent-frontend:latest

# Pod 재시작
kubectl rollout restart deployment/ai-agent-backend-deployment
```

### Ingress 접속 불가

**증상:** `aiagent.local`로 접속되지 않음

**해결:**

1. Tunnel 상태 확인:
```bash
./minikube.sh status
```

2. Tunnel 재시작:
```bash
./minikube.sh tunnel-stop
./minikube.sh tunnel
```

3. `/etc/hosts` 확인:
```bash
cat /etc/hosts | grep aiagent
```

4. Ingress 상태 확인:
```bash
kubectl get ingress
```

### Database 연결 실패

**증상:** Backend 로그에 `could not connect to server`

**해결:**

1. PostgreSQL Pod 상태 확인:
```bash
kubectl get pods | grep postgres
```

2. PostgreSQL 로그 확인:
```bash
kubectl logs deployment/postgres-deployment
```

3. Secret 확인:
```bash
kubectl get secret ai-agent-secret -o yaml
```

### OpenAI API 에러

**증상:** `AuthenticationError: Invalid API key`

**해결:**

1. Secret 재생성:
```bash
vim k8s/secret.yaml  # OPENAI_SECRET_KEY 수정
kubectl delete secret ai-agent-secret
kubectl apply -f k8s/secret.yaml
```

2. Backend Pod 재시작:
```bash
kubectl rollout restart deployment/ai-agent-backend-deployment
```

---

## 개발 팁

### 빠른 재배포

코드 수정 후 가장 빠르게 재배포하는 방법:

```bash
# 1. Backend 수정 시
cd docker && ./docker_build.sh --backend-only && cd ../k8s
minikube image load ai-agent-backend:latest
kubectl rollout restart deployment/ai-agent-backend-deployment

# 2. Frontend 수정 시
cd docker && ./docker_build.sh --frontend-only && cd ../k8s
minikube image load ai-agent-frontend:latest
kubectl rollout restart deployment/ai-agent-frontend-deployment
```

### 로그 실시간 모니터링

여러 터미널에서:

```bash
# 터미널 1: Backend 로그
kubectl logs -f deployment/ai-agent-backend-deployment

# 터미널 2: Frontend 로그
kubectl logs -f deployment/ai-agent-frontend-deployment

# 터미널 3: PostgreSQL 로그
kubectl logs -f deployment/postgres-deployment
```

### 리소스 사용량 확인

```bash
# Pod 리소스 사용량
kubectl top pods

# Node 리소스 사용량
kubectl top nodes
```


[← 메인 README로 돌아가기](../../README.md)

