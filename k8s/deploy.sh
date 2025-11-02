#!/bin/bash

# AI Agent MVP Kubernetes 배포 스크립트

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 로깅 함수
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 도움말 출력
show_help() {
    cat << EOF
AI Agent MVP Kubernetes 배포 스크립트

사용법: $0 [옵션]

옵션:
    -h, --help              이 도움말을 표시합니다
    -n, --namespace NS       네임스페이스 지정 (기본값: default)
    -c, --config-only        ConfigMap과 Secret만 적용
    -a, --all                모든 리소스 적용 (기본값)
    --backend-only           Backend만 배포
    --frontend-only          Frontend만 배포
    --delete                 리소스 삭제
    --status                 배포 상태 확인

예시:
    $0                      # 모든 리소스 배포
    $0 -n production         # production 네임스페이스에 배포
    $0 --backend-only        # Backend만 배포
    $0 --delete              # 모든 리소스 삭제
    $0 --status              # 배포 상태 확인

EOF
}

# 네임스페이스 확인 및 생성
ensure_namespace() {
    local namespace=$1
    if ! kubectl get namespace "$namespace" &> /dev/null; then
        log_info "네임스페이스 '$namespace' 생성 중..."
        kubectl create namespace "$namespace"
        log_success "네임스페이스 '$namespace' 생성 완료"
    else
        log_info "네임스페이스 '$namespace' 이미 존재합니다"
    fi
}

# Minikube 실행 확인
check_minikube_running() {
    if ! command -v minikube &> /dev/null; then
        log_error "minikube 명령어가 없습니다."
        return 1
    fi
    
    if ! minikube status > /dev/null 2>&1; then
        log_error "Minikube가 실행 중이지 않습니다."
        log_error "Minikube를 시작하세요: minikube start 또는 k8s/minikube.sh start"
        return 1
    fi
    
    return 0
}

# Minikube 이미지 확인
check_minikube_image() {
    local image_name=$1
    # Minikube 이미지 목록에서 찾기
    # Minikube는 docker.io/library/image:tag 형식으로 저장할 수 있으므로
    # 이미지 이름(image:tag)으로 끝나는 라인을 찾음
    # 예: docker.io/library/ai-agent-backend:latest 또는 ai-agent-backend:latest
    if minikube image ls 2>/dev/null | grep -qE "(^|/)$image_name$"; then
        return 0
    else
        return 1
    fi
}

# Minikube 이미지 로드
load_minikube_image() {
    local image_name=$1
    log_info "이미지 '$image_name' 로컬 존재 확인 중..."
    
    # 로컬 Docker 이미지 확인
    if ! docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "^${image_name}$"; then
        log_error "로컬에 이미지 '$image_name'이 없습니다."
        log_error "먼저 이미지를 빌드하세요: docker/docker_build.sh --backend-only 또는 --frontend-only"
        return 1
    fi
    
    log_info "Minikube에 이미지 '$image_name' 로드 중..."
    if minikube image load "$image_name"; then
        log_success "이미지 '$image_name' Minikube 로드 완료"
        return 0
    else
        log_error "이미지 '$image_name' Minikube 로드 실패"
        return 1
    fi
}

# 이미지 확인 및 로드 (필요시)
ensure_minikube_image() {
    local image_name=$1
    local component_name=$2
    
    # Minikube 실행 확인
    if ! check_minikube_running; then
        return 1
    fi
    
    log_info "[$component_name] 이미지 확인 중: $image_name"
    
    if check_minikube_image "$image_name"; then
        log_info "[$component_name] 이미지가 이미 Minikube에 로드되어 있습니다"
        return 0
    else
        log_warning "[$component_name] 이미지가 Minikube에 없습니다. 로드 중..."
        if load_minikube_image "$image_name"; then
            return 0
        else
            return 1
        fi
    fi
}

# ConfigMap과 Secret 적용
apply_config() {
    local namespace=$1
    log_info "ConfigMap과 Secret 적용 중..."
    
    kubectl apply -f configmap.yaml -n "$namespace"
    kubectl apply -f secret.yaml -n "$namespace"
    
    log_success "ConfigMap과 Secret 적용 완료"
}

# Backend 배포
deploy_backend() {
    local namespace=$1
    log_info "Backend 배포 중..."
    
    # Backend 이미지 확인 및 로드
    if ! ensure_minikube_image "ai-agent-backend:latest" "Backend"; then
        log_error "Backend 이미지 로드 실패. 배포를 중단합니다."
        return 1
    fi
    
    kubectl apply -f backend.yaml -n "$namespace"
    
    log_success "Backend 배포 완료"
}

# Frontend 배포
deploy_frontend() {
    local namespace=$1
    log_info "Frontend 배포 중..."
    
    # Frontend 이미지 확인 및 로드
    if ! ensure_minikube_image "ai-agent-frontend:latest" "Frontend"; then
        log_error "Frontend 이미지 로드 실패. 배포를 중단합니다."
        return 1
    fi
    
    kubectl apply -f frontend.yaml -n "$namespace"
    
    log_success "Frontend 배포 완료"
}

# PostgreSQL 배포
deploy_postgres() {
    local namespace=$1
    log_info "PostgreSQL 배포 중..."
    
    # PersistentVolume 먼저 생성 (동적 프로비저닝이 없는 경우)
    if kubectl apply -f pv.yaml -n "$namespace" 2>/dev/null; then
        log_info "PersistentVolume 생성 완료"
    else
        log_warning "PersistentVolume 생성 실패 (동적 프로비저닝 사용 중일 수 있음)"
    fi
    
    # PostgreSQL 배포
    kubectl apply -f db.yaml -n "$namespace"
    
    log_success "PostgreSQL 배포 완료"
}

# Ingress 배포
deploy_ingress() {
    local namespace=$1
    log_info "Ingress 배포 중..."
    
    kubectl apply -f ingress.yaml -n "$namespace"
    
    log_success "Ingress 배포 완료"
}

# 배포 상태 확인
check_status() {
    local namespace=$1
    log_info "배포 상태 확인 중..."
    
    echo ""
    log_info "=== Pods 상태 ==="
    kubectl get pods -n "$namespace" -l app=ai-agent-backend
    kubectl get pods -n "$namespace" -l app=ai-agent-frontend
    kubectl get pods -n "$namespace" -l app=postgres
    
    echo ""
    log_info "=== Services 상태 ==="
    kubectl get services -n "$namespace"
    
    echo ""
    log_info "=== ConfigMaps 상태 ==="
    kubectl get configmaps -n "$namespace"
    
    echo ""
    log_info "=== Secrets 상태 ==="
    kubectl get secrets -n "$namespace"
}

# 리소스 삭제
delete_resources() {
    local namespace=$1
    log_warning "모든 리소스 삭제 중..."
    
    # 일반 리소스 삭제
    kubectl delete -f backend.yaml -n "$namespace" 2>/dev/null || true
    kubectl delete -f frontend.yaml -n "$namespace" 2>/dev/null || true
    kubectl delete -f db.yaml -n "$namespace" 2>/dev/null || true
    kubectl delete -f ingress.yaml -n "$namespace" 2>/dev/null || true
    kubectl delete -f configmap.yaml -n "$namespace" 2>/dev/null || true
    kubectl delete -f secret.yaml -n "$namespace" 2>/dev/null || true
    
    # PVC 강제 삭제
    log_info "PVC 강제 삭제 중..."
    kubectl delete pvc postgres-pvc -n "$namespace" --force --grace-period=0 2>/dev/null || true
    
    # PV 강제 삭제
    log_info "PV 강제 삭제 중..."
    kubectl delete pv postgres-pv --force --grace-period=0 2>/dev/null || true
    
    # PV 파일로 삭제 시도
    kubectl delete -f pv.yaml 2>/dev/null || true
    
    log_success "모든 리소스 삭제 완료"
}

# 메인 함수
main() {
    local namespace="default"
    local config_only=false
    local all=true
    local backend_only=false
    local frontend_only=false
    local delete=false
    local status=false
    
    # 인수 파싱
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -n|--namespace)
                namespace="$2"
                shift 2
                ;;
            -c|--config-only)
                config_only=true
                all=false
                shift
                ;;
            -a|--all)
                all=true
                shift
                ;;
            --backend-only)
                backend_only=true
                all=false
                shift
                ;;
            --frontend-only)
                frontend_only=true
                all=false
                shift
                ;;
            --delete)
                delete=true
                all=false
                shift
                ;;
            --status)
                status=true
                all=false
                shift
                ;;
            *)
                log_error "알 수 없는 옵션: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 스크립트 디렉토리로 이동
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    cd "$SCRIPT_DIR"
    
    log_info "AI Agent MVP Kubernetes 배포 스크립트 시작"
    log_info "네임스페이스: $namespace"
    
    # kubectl 설치 확인
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl이 설치되어 있지 않습니다."
        exit 1
    fi
    
    # kubectl 연결 확인
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Kubernetes 클러스터에 연결할 수 없습니다."
        exit 1
    fi
    
    # 네임스페이스 확인
    ensure_namespace "$namespace"
    
    # 삭제 모드
    if [ "$delete" = true ]; then
        delete_resources "$namespace"
        exit 0
    fi
    
    # 상태 확인 모드
    if [ "$status" = true ]; then
        check_status "$namespace"
        exit 0
    fi
    
    # ConfigMap과 Secret 적용
    apply_config "$namespace"
    
    # 배포 실행
    if [ "$config_only" = true ]; then
        log_info "ConfigMap과 Secret만 적용했습니다."
    elif [ "$backend_only" = true ]; then
        deploy_backend "$namespace"
    elif [ "$frontend_only" = true ]; then
        deploy_frontend "$namespace"
    elif [ "$all" = true ]; then
        deploy_postgres "$namespace"
        deploy_backend "$namespace"
        deploy_frontend "$namespace"
        deploy_ingress "$namespace"
    fi
    
    log_success "배포 완료!"
    
    # 배포 상태 확인
    check_status "$namespace"
    
    echo ""
    log_info "=== 접속 정보 ==="
    echo ""
    
    # Ingress 접속 정보 (Minikube Tunnel 사용 시)
    log_info "1) Ingress 사용 (권장 - Minikube Tunnel 실행 시):"
    if kubectl get ingress -n "$namespace" &> /dev/null; then
        local ingress_info=$(kubectl get ingress -n "$namespace" 2>/dev/null)
        if echo "$ingress_info" | grep -q "aiagent-ingress"; then
            echo "$ingress_info" | grep -v "^NAME"
            local ingress_ip=$(kubectl get ingress aiagent-ingress -n "$namespace" -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null)
            if [ -n "$ingress_ip" ]; then
                # Ingress host 확인
                local ingress_host=$(kubectl get ingress aiagent-ingress -n "$namespace" -o jsonpath='{.spec.rules[0].host}' 2>/dev/null)
                
                if [ -n "$ingress_host" ] && [ "$ingress_host" != "null" ]; then
                    log_success "접속 URL: http://$ingress_host"
                    log_info "  - Frontend: http://$ingress_host/"
                    log_info "  - Backend API: http://$ingress_host/api/"
                    log_info "  - API Docs: http://$ingress_host/api/docs"
                    
                    if [ "$ingress_ip" = "127.0.0.1" ]; then
                        log_info ""
                        log_info "  💡 /etc/hosts 설정 필요:"
                        log_info "      sudo sh -c 'echo \"127.0.0.1 $ingress_host\" >> /etc/hosts'"
                        
                        # /etc/hosts에 이미 설정되어 있는지 확인
                        if grep -q "$ingress_host" /etc/hosts 2>/dev/null; then
                            log_success "      ✅ /etc/hosts에 이미 설정되어 있습니다"
                        else
                            log_warning "      ⚠️  /etc/hosts에 설정이 필요합니다"
                        fi
                    fi
                else
                    log_success "접속 URL: http://$ingress_ip"
                    log_info "  - Frontend: http://$ingress_ip/"
                    log_info "  - Backend API: http://$ingress_ip/api/"
                    log_info "  - API Docs: http://$ingress_ip/api/docs"
                fi
            else
                log_warning "Ingress IP가 아직 할당되지 않았습니다. 잠시 후 다시 확인하세요."
                log_info "확인 명령: kubectl get ingress -n $namespace"
            fi
        else
            log_warning "Ingress가 배포되지 않았습니다"
        fi
    else
        log_info "Ingress를 사용하려면 'kubectl apply -f ingress.yaml -n $namespace'를 실행하세요"
    fi
    
    echo ""
    log_info "2) Port Forward 사용 (개별 Service 테스트용):"
    log_info "  Backend:    kubectl port-forward svc/ai-agent-backend-service 8000:8000 -n $namespace"
    log_info "  Frontend:   kubectl port-forward svc/ai-agent-frontend-service 3000:3000 -n $namespace"
    log_info "  PostgreSQL: kubectl port-forward svc/postgres-service 5432:5432 -n $namespace"
    
    echo ""
    log_info "참고:"
    log_info "  - Minikube Tunnel이 실행 중이어야 Ingress를 통한 접속이 가능합니다"
    log_info "  - Tunnel 확인: k8s/minikube.sh status"
    log_info "  - Tunnel 시작: k8s/minikube.sh tunnel"
}

# 스크립트 실행
main "$@"
