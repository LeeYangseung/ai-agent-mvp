# AI Agent MVP Kubernetes 배포

이 디렉토리에는 AI Agent MVP 애플리케이션을 Kubernetes에 배포하기 위한 매니페스트 파일들이 포함되어 있습니다.

## 📁 파일 구조

```
k8s/
├── backend.yaml          # Backend (FastAPI) Deployment & Service
├── frontend.yaml         # Frontend (Next.js) Deployment & Service
├── db.yaml              # PostgreSQL Deployment & Service
├── pv.yaml              # PersistentVolumeClaim (Dynamic Provisioning)
├── configmap.yaml       # ConfigMap (환경변수)
├── secret.yaml          # Secret (민감한 정보)
├── secret.example.yaml  # Secret 예제 파일
├── ingress.yaml         # Ingress (외부 접근)
├── deploy.sh            # 배포 스크립트
├── minikube.sh          # Minikube 관리 스크립트 (선택사항)
├── init-db.sql          # 데이터베이스 초기화 스크립트
└── README.md            # 이 파일
```

## 🚀 빠른 시작

### 사전 요구사항

- Kubernetes 클러스터 (minikube, kind, EKS, GKE, AKS 등)
- `kubectl` CLI 도구 설치 및 클러스터 연결
- Docker 이미지 빌드 완료 (`docker/docker_build.sh` 실행)

### 1. Minikube 사용 (선택사항)

로컬 개발 환경에서 minikube를 사용하는 경우:

```bash
# Minikube 시작 및 Tunnel 실행
./minikube.sh start

# 상태 확인
./minikube.sh status

# 중지 (데이터 보존)
./minikube.sh stop

# 삭제 (데이터 삭제)
./minikube.sh stop --delete
```

**주의**: minikube는 로컬 개발용이며, 프로덕션 환경에서는 관리형 Kubernetes 서비스를 사용하세요.

### 2. Secret 설정

`secret.example.yaml`을 참고하여 `secret.yaml`을 생성합니다:

```bash
# Base64 인코딩 예시
echo -n "your-openai-key" | base64
echo -n "your-db-password" | base64

# secret.yaml 편집
vim secret.yaml
```

### 3. 전체 배포

```bash
# 모든 리소스 배포
./deploy.sh

# 배포 상태 확인
./deploy.sh --status
```

### 4. 개별 배포

```bash
# Backend만 배포
./deploy.sh --backend-only

# Frontend만 배포
./deploy.sh --frontend-only

# ConfigMap과 Secret만 적용
./deploy.sh --config-only
```

### 5. 리소스 삭제

```bash
./deploy.sh --delete
```

## 🔧 설정

### 환경변수

**ConfigMap (`configmap.yaml`):**
- `NEXT_PUBLIC_API_BASE_URL`: Frontend에서 사용할 Backend API URL (비어있으면 자동 설정)
- `NODE_ENV`: Node.js 환경 설정 (production 권장)
- `LOG_LEVEL`: Backend 로그 레벨 (info/debug/warning/error)
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
- Storage: 10Gi (Dynamic Provisioning)

## 🗄️ 데이터베이스 및 스토리지

### PostgreSQL 연결 정보

- **Host**: postgres-service
- **Port**: 5432
- **Database**: agent
- **Username**: admin
- **Password**: (secret.yaml에서 설정)

### 데이터 영속성

이 프로젝트는 **Dynamic Provisioning**을 사용합니다:

- ✅ **Pod 재시작**: 데이터 보존
- ✅ **Deployment 재배포**: 데이터 보존
- ✅ **노드 재시작**: 데이터 보존 (클러스터에 따라 다름)
- ❌ **PVC 삭제**: 데이터 삭제

**Minikube 환경:**
- ✅ `minikube stop` → `minikube start`: 데이터 보존
- ❌ `minikube delete`: 데이터 삭제 (클러스터 전체 삭제)

**프로덕션 환경:**
- 클러스터의 기본 StorageClass 사용
- AWS EBS, GCP Persistent Disk, Azure Disk 등 자동 프로비저닝
- 백업 정책 및 스냅샷 설정 권장

### StorageClass 확인

```bash
# 기본 StorageClass 확인
kubectl get storageclass

# PV/PVC 상태 확인
kubectl get pv
kubectl get pvc
```

## 🔐 보안

1. **Secret 관리**: 
   - `secret.yaml`은 `.gitignore`에 포함되어 있습니다
   - 실제 환경에서는 Kubernetes Secret 관리 도구 사용 권장 (Sealed Secrets, External Secrets Operator 등)

2. **네임스페이스 분리**: 
   ```bash
   ./deploy.sh -n production     # 프로덕션 네임스페이스
   ./deploy.sh -n development    # 개발 네임스페이스
   ```

3. **최소 권한 원칙**: 
   - 컨테이너는 non-root 사용자로 실행
   - 필요한 최소 권한만 부여

## 📊 모니터링 및 로깅

### Pod 상태 확인

```bash
# 전체 Pod 확인
kubectl get pods

# 특정 애플리케이션 Pod 확인
kubectl get pods -l app=ai-agent-backend
kubectl get pods -l app=ai-agent-frontend
kubectl get pods -l app=postgres

# Pod 상세 정보
kubectl describe pod <pod-name>
```

### 로그 확인

```bash
# 실시간 로그 스트리밍
kubectl logs -f deployment/ai-agent-backend-deployment
kubectl logs -f deployment/ai-agent-frontend-deployment
kubectl logs -f deployment/postgres-deployment

# 특정 Pod 로그
kubectl logs <pod-name>

# 이전 컨테이너 로그 (재시작된 경우)
kubectl logs <pod-name> --previous
```

### 리소스 사용량 확인

```bash
# Pod 리소스 사용량
kubectl top pods

# 노드 리소스 사용량
kubectl top nodes
```

## 🌐 접속 방법

### 접속 방법 요약

| 방법 | Minikube Tunnel | 용도 | 접속 URL |
|------|----------------|------|----------|
| **Ingress** (권장) | ✅ 필요 | 프로덕션과 유사한 환경 | http://aiagent.local/ |
| **Port Forward** | ❌ 불필요 | 개별 Service 테스트 | http://localhost:PORT |
| **LoadBalancer** | ✅ 필요 | Service 직접 노출 | http://SERVICE-IP:PORT |

### 1. Ingress 사용 (권장 - Minikube 환경)

**사전 준비:**

1. Minikube Tunnel 실행:
```bash
# Tunnel 상태 확인
./minikube.sh status

# Tunnel 시작 (자동으로 시작되지 않은 경우)
./minikube.sh tunnel
```

2. `/etc/hosts` 파일 설정:
```bash
# aiagent.local 도메인 추가
sudo sh -c 'echo "127.0.0.1 aiagent.local" >> /etc/hosts'

# 확인
cat /etc/hosts | grep aiagent
# 출력: 127.0.0.1 aiagent.local
```

**Ingress IP 확인 및 접속:**

```bash
# Ingress Controller Service 확인
kubectl get svc -n ingress-nginx ingress-nginx-controller

# 예시 출력:
# NAME                      TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)
# ingress-nginx-controller  LoadBalancer   10.96.254.220   127.0.0.1     80:31492/TCP,443:30213/TCP

# Ingress 확인
kubectl get ingress

# 예시 출력:
# NAME              CLASS   HOSTS           ADDRESS     PORTS   AGE
# aiagent-ingress   nginx   aiagent.local   127.0.0.1   80      5m
```

**접속 URL (Minikube Tunnel 사용 시):**
- Frontend: `http://aiagent.local/`
- Backend API: `http://aiagent.local/api/`
- API Docs: `http://aiagent.local/api/docs`
- Redoc: `http://aiagent.local/api/redoc`

**참고:** 
- Ingress에 `host: aiagent.local`이 설정되어 있어 해당 도메인으로만 접속 가능합니다
- `/etc/hosts` 파일에 `127.0.0.1 aiagent.local` 추가 필요:
  ```bash
  # /etc/hosts에 추가
  sudo sh -c 'echo "127.0.0.1 aiagent.local" >> /etc/hosts'
  
  # 확인
  cat /etc/hosts | grep aiagent
  ```
- `localhost`로 접속하려면 `ingress.yaml`의 `host: aiagent.local` 부분을 제거하거나 주석 처리하세요

**Ingress 상세 정보:**
```bash
kubectl describe ingress aiagent-ingress
```

### 2. Port Forwarding (개별 Service 테스트)

Tunnel 없이 개별 Service를 로컬에서 테스트할 때 사용:

```bash
# Backend API
kubectl port-forward svc/ai-agent-backend-service 8000:8000

# Frontend
kubectl port-forward svc/ai-agent-frontend-service 3000:3000

# PostgreSQL
kubectl port-forward svc/postgres-service 5432:5432
```

**접속 URL:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Backend Docs: http://localhost:8000/docs
- PostgreSQL: localhost:5432

**주의:** Port Forward는 터미널이 실행되는 동안만 유효합니다.

### 3. LoadBalancer Service (프로덕션 환경)

관리형 Kubernetes 클러스터(EKS, GKE, AKS)에서는 LoadBalancer 타입 Service가 자동으로 외부 IP를 받습니다:

```bash
# Service 확인
kubectl get services

# External IP 확인
kubectl get svc ai-agent-frontend-service -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
```

### 접속 문제 해결

**Ingress IP가 할당되지 않는 경우:**
```bash
# 1. Tunnel 상태 확인
./minikube.sh status

# 2. Ingress Controller 확인
kubectl get pods -n ingress-nginx

# 3. Ingress 이벤트 확인
kubectl describe ingress aiagent-ingress
```

**Port Forward 연결 실패:**
```bash
# Pod 상태 확인
kubectl get pods

# Pod가 Running 상태인지 확인
kubectl describe pod <pod-name>
```

## 🔄 업데이트 및 롤백

### 이미지 업데이트

```bash
# 1. 이미지 빌드
cd ../docker
./docker_build.sh

# 2. Minikube에 이미지 로드 (Minikube 사용 시)
minikube image load ai-agent-backend:latest
minikube image load ai-agent-frontend:latest

# 3. Deployment 업데이트
kubectl rollout restart deployment/ai-agent-backend-deployment
kubectl rollout restart deployment/ai-agent-frontend-deployment

# 4. 롤아웃 상태 확인
kubectl rollout status deployment/ai-agent-backend-deployment
kubectl rollout status deployment/ai-agent-frontend-deployment
```

### 설정 업데이트

```bash
# ConfigMap 업데이트
kubectl apply -f configmap.yaml

# Secret 업데이트
kubectl apply -f secret.yaml

# 변경사항 적용을 위해 Pod 재시작
kubectl rollout restart deployment/ai-agent-backend-deployment
kubectl rollout restart deployment/ai-agent-frontend-deployment
```

### 롤백

```bash
# 이전 버전으로 롤백
kubectl rollout undo deployment/ai-agent-backend-deployment

# 특정 버전으로 롤백
kubectl rollout history deployment/ai-agent-backend-deployment
kubectl rollout undo deployment/ai-agent-backend-deployment --to-revision=2
```

## 🐛 문제 해결

### 1. Pod가 시작되지 않는 경우

```bash
# Pod 상태 확인
kubectl get pods
kubectl describe pod <pod-name>

# 로그 확인
kubectl logs <pod-name>

# 이벤트 확인
kubectl get events --sort-by=.metadata.creationTimestamp
```

**일반적인 원인:**
- 이미지를 찾을 수 없음 (ImagePullBackOff)
- 리소스 부족 (Insufficient memory/cpu)
- ConfigMap/Secret 누락
- 볼륨 마운트 실패

### 2. 서비스 연결 문제

```bash
# 서비스 확인
kubectl get services
kubectl describe service <service-name>

# Endpoint 확인
kubectl get endpoints <service-name>

# Pod 간 네트워크 테스트
kubectl exec -it <pod-name> -- curl http://postgres-service:5432
```

### 3. PersistentVolume 문제

```bash
# PV/PVC 상태 확인
kubectl get pv
kubectl get pvc
kubectl describe pvc postgres-pvc

# StorageClass 확인
kubectl get storageclass
```

**일반적인 원인:**
- StorageClass가 없음 (Dynamic Provisioning 미지원)
- 스토리지 할당량 부족
- 권한 문제

**해결 방법:**
```bash
# StorageClass 확인 및 생성
kubectl get storageclass

# PVC 재생성
kubectl delete pvc postgres-pvc
kubectl apply -f pv.yaml
```

### 4. 환경변수 문제

```bash
# Pod 내 환경변수 확인
kubectl exec -it <pod-name> -- env | grep -E "(API|DB|NODE|OPENAI)"

# ConfigMap 확인
kubectl get configmap ai-agent-config -o yaml

# Secret 확인 (주의: 민감 정보)
kubectl get secret ai-agent-secrets -o yaml
```

### 5. Minikube 관련 문제

```bash
# Minikube 상태 확인
minikube status

# Minikube 로그 확인
minikube logs

# Minikube 재시작
./minikube.sh restart

# Minikube 완전 초기화
./minikube.sh stop --delete
./minikube.sh start
```

## 📝 추가 정보

### Minikube vs 프로덕션 클러스터

| 항목 | Minikube | 프로덕션 (EKS/GKE/AKS) |
|------|----------|------------------------|
| 용도 | 로컬 개발/테스트 | 실제 서비스 운영 |
| 노드 수 | 단일 노드 | 다중 노드 |
| 가용성 | 낮음 | 높음 (HA 구성) |
| 스토리지 | 로컬 디스크 | 클라우드 스토리지 |
| 네트워크 | Tunnel 필요 | LoadBalancer 자동 |
| 스케일링 | 제한적 | 자동 스케일링 |
| 비용 | 무료 | 사용량에 따라 과금 |

### 프로덕션 체크리스트

- [ ] Secret을 환경변수가 아닌 Vault/AWS Secrets Manager 등으로 관리
- [ ] Resource Limits/Requests 적절히 설정
- [ ] Liveness/Readiness Probe 구성
- [ ] Horizontal Pod Autoscaler (HPA) 설정
- [ ] Ingress TLS/SSL 인증서 구성
- [ ] 모니터링/알림 시스템 연동 (Prometheus, Grafana 등)
- [ ] 로그 수집 시스템 연동 (ELK Stack, Loki 등)
- [ ] 백업 정책 수립 (데이터베이스 스냅샷 등)
- [ ] 네트워크 정책 (NetworkPolicy) 구성
- [ ] Pod Security Policy 적용

### 참고 자료

- [Kubernetes 공식 문서](https://kubernetes.io/docs/)
- [Minikube 공식 문서](https://minikube.sigs.k8s.io/docs/)
- [kubectl 치트시트](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)

## 📞 지원

문제가 발생하거나 질문이 있는 경우:
1. 이 README의 문제 해결 섹션 참고
2. 프로젝트 이슈 트래커에 이슈 등록
3. 팀 담당자에게 문의

---

**참고**: 이 설정은 개발 환경에 최적화되어 있습니다. 프로덕션 환경에서는 추가적인 보안, 모니터링, 백업 설정이 필요합니다.
