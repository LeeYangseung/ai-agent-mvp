# 문제 해결 가이드

일반적인 문제와 해결 방법을 정리한 문서입니다.

---

## 목차

- [일반적인 문제](#일반적인-문제)
- [Minikube 관련](#minikube-관련)
- [Backend 관련](#backend-관련)
- [Frontend 관련](#frontend-관련)
- [데이터베이스 관련](#데이터베이스-관련)
- [네트워킹 관련](#네트워킹-관련)

---

## 일반적인 문제

### 1. Ingress 접속 불가

**증상**: `aiagent.local`로 접속되지 않음

**원인**:
- Minikube Tunnel이 실행되지 않음
- `/etc/hosts`에 도메인이 추가되지 않음
- Ingress Controller가 실행되지 않음

**해결 방법**:

```bash
# 1. Tunnel 상태 확인
cd k8s
./minikube.sh status

# 2. Tunnel이 중지되어 있으면 재시작
./minikube.sh tunnel

# 3. /etc/hosts에 도메인이 추가되었는지 확인
cat /etc/hosts | grep aiagent.local

# 없으면 추가
sudo sh -c 'echo "127.0.0.1 aiagent.local" >> /etc/hosts'

# 4. Ingress Controller 상태 확인
kubectl get pods -n ingress-nginx

# 5. Ingress 리소스 확인
kubectl get ingress
```

### 2. Pod가 ImagePullBackOff 상태

**증상**: `kubectl get pods`에서 Pod가 `ImagePullBackOff` 상태

**원인**: Minikube가 로컬 이미지를 찾지 못함

**해결 방법**:

```bash
# 1. 이미지를 Minikube에 로드
minikube image load ai-agent-backend:latest
minikube image load ai-agent-frontend:latest

# 2. Pod 재시작
kubectl rollout restart deployment/ai-agent-backend-deployment
kubectl rollout restart deployment/ai-agent-frontend-deployment

# 3. 상태 확인
kubectl get pods
```

### 3. Pod가 CrashLoopBackOff 상태

**증상**: Pod가 계속 재시작됨

**원인**: 
- 애플리케이션 에러
- 환경 변수 누락
- 의존성 문제

**해결 방법**:

```bash
# 1. 로그 확인
kubectl logs deployment/ai-agent-backend-deployment

# 2. 이전 로그 확인 (Pod가 재시작된 경우)
kubectl logs deployment/ai-agent-backend-deployment --previous

# 3. 상세 정보 확인
kubectl describe pod <pod-name>

# 4. 환경 변수 확인
kubectl exec deployment/ai-agent-backend-deployment -- env
```

### 4. Pod가 Pending 상태

**증상**: Pod가 Pending 상태에서 멈춤

**원인**:
- 리소스 부족 (CPU, 메모리)
- PVC가 바인딩되지 않음

**해결 방법**:

```bash
# 1. 상세 정보 확인
kubectl describe pod <pod-name>

# 2. 리소스 확인
kubectl top nodes
kubectl top pods

# 3. PVC 상태 확인
kubectl get pvc

# 4. Minikube 리소스 증가
minikube delete
minikube start --cpus=4 --memory=8192
```

---

## Minikube 관련

### 1. Minikube 시작 실패

**증상**: `minikube start` 실패

**해결 방법**:

```bash
# 1. 기존 클러스터 삭제
minikube delete

# 2. Docker 실행 확인
docker ps

# 3. Minikube 재시작
minikube start --driver=docker

# 4. 드라이버 변경 (Docker가 안 되면 VirtualBox 등)
minikube start --driver=virtualbox
```

### 2. Minikube Tunnel 권한 오류

**증상**: `sudo` 비밀번호 요청이 계속됨

**해결 방법**:

```bash
# 1. sudoers 파일에 tunnel 권한 추가
sudo visudo

# 다음 줄 추가 (YOUR_USERNAME을 실제 사용자명으로)
YOUR_USERNAME ALL=(ALL) NOPASSWD: /usr/local/bin/minikube tunnel

# 2. Tunnel 재시작
./minikube.sh tunnel-stop
./minikube.sh tunnel
```

### 3. Minikube 디스크 공간 부족

**증상**: `no space left on device`

**해결 방법**:

```bash
# 1. 사용하지 않는 Docker 이미지 정리
docker image prune -a

# 2. Minikube 이미지 정리
minikube image rm <unused-image>

# 3. Minikube 재생성 (디스크 크기 증가)
minikube delete
minikube start --disk-size=50g
```

---

## Backend 관련

### 1. OpenAI API 키 오류

**증상**: `AuthenticationError: Invalid API key`

**해결 방법**:

```bash
# 1. Secret 확인
kubectl get secret ai-agent-secret -o yaml

# 2. Secret 재생성
vim k8s/secret.yaml  # OPENAI_SECRET_KEY 수정
kubectl delete secret ai-agent-secret
kubectl apply -f k8s/secret.yaml

# 3. Backend Pod 재시작
kubectl rollout restart deployment/ai-agent-backend-deployment

# 4. 로그 확인
kubectl logs -f deployment/ai-agent-backend-deployment
```

### 2. ChromaDB 권한 오류

**증상**: `PermissionError: [Errno 13] Permission denied`

**원인**: 벡터 스토어 데이터 디렉토리 권한 문제

**해결 방법**:

```bash
# 1. Backend Pod에 접속
kubectl exec -it deployment/ai-agent-backend-deployment -- /bin/bash

# 2. 데이터 디렉토리 권한 확인
ls -la /app/app/data/index/

# 3. 권한 수정
chmod -R 777 /app/app/data/index/

# 4. Pod 재시작
kubectl rollout restart deployment/ai-agent-backend-deployment
```

### 3. 그래프 실행 실패

**증상**: 그래프 실행 시 에러 발생

**원인**:
- 노드 파라미터 누락
- 엣지 연결 오류
- State 키 불일치

**해결 방법**:

```bash
# 1. Backend 로그 확인
kubectl logs deployment/ai-agent-backend-deployment | grep -i error

# 2. API 응답 확인 (Frontend Console)
# 브라우저 개발자 도구 → Network 탭

# 3. 그래프 정의 확인
# - 필수 노드 파라미터가 모두 설정되었는지
# - 엣지가 올바르게 연결되었는지
# - State 키 이름이 일치하는지
```

### 4. 문서 업로드 실패

**증상**: 문서 업로드 시 에러 발생

**원인**:
- 파일 형식 미지원
- 파일 크기 초과
- 임베딩 API 에러

**해결 방법**:

```bash
# 1. 지원 형식 확인 (PDF, TXT만)
# 2. 파일 크기 확인 (100MB 이하 권장)

# 3. Backend 로그 확인
kubectl logs deployment/ai-agent-backend-deployment

# 4. 임베딩 API 키 확인
kubectl get secret ai-agent-secret -o yaml | grep OPENAI
```

---

## Frontend 관련

### 1. API 호출 실패 (CORS 에러)

**증상**: `CORS policy: No 'Access-Control-Allow-Origin' header`

**원인**: Backend의 `allow_origins`에 Frontend URL이 없음

**해결 방법**:

```python
# backend/app/main.py 수정
origins = [
    "http://localhost:3000",
    "http://aiagent.local",  # 추가
    # ... 기타 도메인
]
```

```bash
# 이미지 재빌드 및 재배포
cd docker && ./docker_build.sh --backend-only
cd ../k8s && minikube image load ai-agent-backend:latest
kubectl rollout restart deployment/ai-agent-backend-deployment
```

### 2. 페이지 로딩 실패

**증상**: 빈 화면 또는 에러 페이지

**해결 방법**:

```bash
# 1. Frontend 로그 확인
kubectl logs deployment/ai-agent-frontend-deployment

# 2. 브라우저 콘솔 확인
# 개발자 도구 → Console 탭

# 3. Next.js 빌드 에러 확인
# 로컬에서 빌드 테스트
cd frontend
npm run build
```

### 3. API 베이스 URL 오류

**증상**: API 호출이 잘못된 URL로 전송됨

**해결 방법**:

```bash
# 1. ConfigMap 확인
kubectl get configmap ai-agent-configmap -o yaml

# 2. ConfigMap 수정
kubectl edit configmap ai-agent-configmap

# 3. Frontend Pod 재시작
kubectl rollout restart deployment/ai-agent-frontend-deployment
```

---

## 데이터베이스 관련

### 1. DB 연결 실패

**증상**: Backend 로그에 `could not connect to server`

**해결 방법**:

```bash
# 1. PostgreSQL Pod 상태 확인
kubectl get pods | grep postgres

# 2. PostgreSQL 로그 확인
kubectl logs deployment/postgres-deployment

# 3. Service 확인
kubectl get svc | grep postgres

# 4. DATABASE_URL 확인
kubectl exec deployment/ai-agent-backend-deployment -- env | grep DATABASE_URL

# 5. PostgreSQL 직접 접속 테스트
kubectl exec -it deployment/postgres-deployment -- psql -U postgres -d ai_agent_db
```

### 2. 마이그레이션 실패

**증상**: Backend 시작 시 테이블 생성 실패

**해결 방법**:

```bash
# 1. Backend Pod에 접속
kubectl exec -it deployment/ai-agent-backend-deployment -- /bin/bash

# 2. 마이그레이션 실행
alembic upgrade head

# 3. 현재 버전 확인
alembic current

# 4. 마이그레이션 이력 확인
alembic history
```

### 3. 데이터 손실

**증상**: DB 데이터가 사라짐

**원인**:
- `minikube delete` 실행
- PVC 삭제
- Pod 재시작 시 PV가 바인딩되지 않음

**해결 방법**:

```bash
# 1. PVC 상태 확인
kubectl get pvc

# 2. PV 상태 확인
kubectl get pv

# 3. 백업 복원 (백업이 있는 경우)
kubectl exec -i deployment/postgres-deployment -- psql -U postgres ai_agent_db < backup.sql
```

**예방책**:

```bash
# 정기적인 백업 설정
# cron으로 매일 백업
0 2 * * * kubectl exec deployment/postgres-deployment -- pg_dump -U postgres ai_agent_db > /backup/db_$(date +\%Y\%m\%d).sql
```

---

## 네트워킹 관련

### 1. Service 내부 통신 실패

**증상**: Backend가 PostgreSQL에 연결 못 함

**해결 방법**:

```bash
# 1. Service DNS 확인
kubectl exec deployment/ai-agent-backend-deployment -- nslookup postgres-service

# 2. Service 포트 확인
kubectl get svc postgres-service

# 3. 네트워크 정책 확인 (있는 경우)
kubectl get networkpolicy

# 4. 직접 연결 테스트
kubectl exec deployment/ai-agent-backend-deployment -- curl postgres-service:5432
```

### 2. Ingress Path 라우팅 오류

**증상**: `/api` 경로가 작동하지 않음

**해결 방법**:

```bash
# 1. Ingress 설정 확인
kubectl describe ingress aiagent-ingress

# 2. Backend ROOT_PATH 확인
kubectl exec deployment/ai-agent-backend-deployment -- env | grep ROOT_PATH

# 3. Ingress annotation 확인
kubectl get ingress aiagent-ingress -o yaml
```

---

## 기타 문제

### 1. 로그 파일이 너무 큼

**해결 방법**:

```bash
# 1. 로그 정리
kubectl exec deployment/ai-agent-backend-deployment -- rm -rf logs/*.log.*

# 2. 로그 레벨 변경
kubectl set env deployment/ai-agent-backend-deployment LOG_LEVEL=warning
```

### 2. 리소스 사용량이 높음

**해결 방법**:

```bash
# 1. 리소스 사용량 확인
kubectl top pods

# 2. 리소스 제한 설정
# Deployment YAML에 추가:
# resources:
#   limits:
#     cpu: "1"
#     memory: "1Gi"
#   requests:
#     cpu: "500m"
#     memory: "512Mi"

# 3. Horizontal Pod Autoscaler 설정
kubectl autoscale deployment ai-agent-backend-deployment --cpu-percent=80 --min=1 --max=3
```

### 3. Secret 값이 보이지 않음

**해결 방법**:

```bash
# 1. Secret 디코딩
kubectl get secret ai-agent-secret -o jsonpath='{.data.OPENAI_SECRET_KEY}' | base64 --decode

# 2. 모든 Secret 값 확인
kubectl get secret ai-agent-secret -o json | jq '.data | map_values(@base64d)'
```

---

## 도움이 필요한 경우

### 정보 수집

문제 해결을 위해 다음 정보를 수집하세요:

```bash
# 1. 전체 리소스 상태
kubectl get all > debug_all.txt

# 2. Pod 로그
kubectl logs deployment/ai-agent-backend-deployment > debug_backend.log
kubectl logs deployment/ai-agent-frontend-deployment > debug_frontend.log
kubectl logs deployment/postgres-deployment > debug_postgres.log

# 3. Pod 상세 정보
kubectl describe pod <failing-pod-name> > debug_pod.txt

# 4. 이벤트 확인
kubectl get events --sort-by='.lastTimestamp' > debug_events.txt
```

### 문의처

- GitHub Issues: 프로젝트 저장소에 이슈 등록
- 팀 담당자: 내부 Slack 채널 또는 이메일

---

[← 메인 README로 돌아가기](../README.md)

