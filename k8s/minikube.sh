#!/bin/bash

# Minikube 시작/중지 및 Tunnel 관리 스크립트

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

# PID 파일 경로
PID_FILE="$HOME/.minikube-tunnel.pid"

# 도움말 출력
show_help() {
    cat << EOF
Minikube 시작/중지 및 Tunnel 관리 스크립트

사용법: $0 [옵션]

옵션:
    start           Minikube 시작 및 Tunnel 실행
    stop            Minikube Tunnel 중지 및 Minikube 종료
    stop --delete   Minikube Tunnel 중지, Minikube 종료 및 클러스터 삭제
    restart         Minikube 재시작 (stop 후 start)
    status          Minikube 및 Tunnel 상태 확인
    tunnel          Tunnel만 시작 (Minikube가 이미 실행 중인 경우)
    tunnel-stop     Tunnel만 중지
    coredns         CoreDNS 설정 적용 (Minikube가 이미 실행 중인 경우)
    -h, --help      이 도움말을 표시합니다

예시:
    $0 start        # Minikube 시작 및 Tunnel 실행
    $0 stop         # Minikube Tunnel 중지 및 Minikube 종료
    $0 status       # 상태 확인
    $0 tunnel       # Tunnel만 시작

참고:
    - Dynamic Provisioning 사용 (데이터는 minikube 내부에 저장)
    - minikube stop/start 시 데이터 보존
    - minikube delete 시 데이터 삭제
    - Tunnel은 백그라운드로 실행되며 PID는 $PID_FILE에 저장됩니다
    
권한 안내:
    - 스크립트는 일반 사용자로 실행해야 합니다 (sudo ./minikube.sh 불가)
    - Tunnel만 sudo 권한이 필요합니다 (privileged ports 80, 443 사용)

EOF
}

# Tunnel 프로세스 확인
check_tunnel_process() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$PID_FILE"
            return 1
        fi
    else
        # PID 파일이 없어도 프로세스 확인
        if pgrep -f "minikube tunnel" > /dev/null; then
            return 0
        else
            return 1
        fi
    fi
}

# Tunnel 중지
stop_tunnel() {
    if check_tunnel_process; then
        log_info "Minikube Tunnel 중지 중..."
        
        if [ -f "$PID_FILE" ]; then
            local pid=$(cat "$PID_FILE")
            if ps -p "$pid" > /dev/null 2>&1; then
                            kill "$pid" 2>/dev/null || true
                log_info "Tunnel 프로세스 (PID: $pid) 종료 신호 전송"
            fi
            rm -f "$PID_FILE"
        fi
        
        # 추가로 실행 중인 tunnel 프로세스 확인 및 종료
        # Tunnel은 sudo로 실행되므로 sudo kill 사용
        local tunnel_pids=$(pgrep -f "minikube tunnel" || true)
        if [ -n "$tunnel_pids" ]; then
            echo "$tunnel_pids" | xargs sudo kill 2>/dev/null || \
            echo "$tunnel_pids" | xargs kill 2>/dev/null || true
            log_info "실행 중인 Tunnel 프로세스 종료"
        fi
        
        # 잠시 대기
        sleep 2
        
        log_success "Minikube Tunnel 중지 완료"
    else
        log_info "실행 중인 Tunnel이 없습니다"
    fi
}

# CoreDNS 설정 적용
configure_coredns() {
    # Minikube가 실행 중인지 확인
    if ! minikube status > /dev/null 2>&1; then
        log_error "Minikube가 실행 중이지 않습니다. 먼저 '$0 start'를 실행하세요."
        return 1
    fi
    
    # Kubernetes API 서버가 준비될 때까지 대기
    log_info "Kubernetes API 서버 준비 대기 중..."
    local max_attempts=30
    local attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if kubectl cluster-info > /dev/null 2>&1; then
            break
        fi
        attempt=$((attempt + 1))
        sleep 1
    done
    
    if [ $attempt -eq $max_attempts ]; then
        log_error "Kubernetes API 서버가 준비되지 않았습니다."
        return 1
    fi
    
    log_info "CoreDNS 설정 적용 중..."
    
    # CoreDNS ConfigMap 생성/업데이트
    kubectl -n kube-system create configmap coredns --dry-run=client -o yaml \
      --from-literal=Corefile='.:53 {
    errors
    health
    ready
    kubernetes cluster.local in-addr.arpa ip6.arpa {
       pods insecure
       fallthrough in-addr.arpa ip6.arpa
       ttl 30
    }
    prometheus :9153
    forward . 8.8.8.8 8.8.4.4
    cache 30
    loop
    reload
    loadbalance
}' | kubectl apply -f - > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        log_success "CoreDNS 설정 적용 완료"
        
        # CoreDNS Pod 재시작 (설정 적용)
        log_info "CoreDNS Pod 재시작 중..."
        kubectl -n kube-system rollout restart deployment/coredns > /dev/null 2>&1
        if [ $? -eq 0 ]; then
            log_success "CoreDNS Pod 재시작 완료"
            log_info "CoreDNS가 재시작되는 동안 잠시 대기 중..."
            sleep 5
        else
            log_warning "CoreDNS Pod 재시작 실패 (Pod가 이미 재시작되었을 수 있습니다)"
        fi
    else
        log_error "CoreDNS 설정 적용 실패"
        return 1
    fi
}

# Tunnel 시작
start_tunnel() {
    # sudo로 실행 중인지 확인 (Tunnel은 root로 직접 실행 불가)
    if [ "$EUID" -eq 0 ]; then
        log_error "Tunnel은 root 권한으로 직접 실행할 수 없습니다."
        log_error "일반 사용자로 스크립트를 실행하세요: ./minikube.sh tunnel"
        return 1
    fi
    
    if check_tunnel_process; then
        log_warning "Tunnel이 이미 실행 중입니다"
        return 0
    fi
    
    if ! minikube status > /dev/null 2>&1; then
        log_error "Minikube가 실행 중이지 않습니다. 먼저 '$0 start'를 실행하세요."
        return 1
    fi
    
    log_info "Minikube Tunnel 시작 중..."
    log_info "Tunnel은 privileged ports (80, 443) 사용을 위해 sudo 권한이 필요합니다."
    
    # sudo 권한 확인 및 확보
    # 실제 sudo 명령을 실행하여 비밀번호 입력 프롬프트 표시
    log_info "sudo 권한 확인 중..."
    log_info "비밀번호 입력이 필요합니다. 아래에 비밀번호를 입력해주세요:"
    if ! sudo -p "Password: " echo "sudo 권한 확인 완료" > /dev/null 2>&1; then
        log_error "sudo 권한을 확보할 수 없습니다."
        log_error "Tunnel 실행을 위해서는 sudo 권한이 필요합니다."
        return 1
    fi
    log_success "sudo 권한 확인 완료"
    
    # Tunnel을 sudo로 백그라운드 실행
    log_info "Tunnel 시작 중..."
    sudo nohup minikube tunnel > /tmp/minikube-tunnel.log 2>&1 &
    local tunnel_pid=$!
    
    # PID 파일에 저장
    echo "$tunnel_pid" > "$PID_FILE"
    
    # 잠시 대기하여 시작 확인
    sleep 3
    
    if ps -p "$tunnel_pid" > /dev/null 2>&1; then
        log_success "Minikube Tunnel이 sudo 권한으로 백그라운드에서 시작되었습니다 (PID: $tunnel_pid)"
        log_info "Tunnel 로그: /tmp/minikube-tunnel.log"
        log_info "Tunnel PID 파일: $PID_FILE"
    else
        log_error "Tunnel 시작 실패. 로그를 확인하세요: /tmp/minikube-tunnel.log"
        log_error "비밀번호 입력이 필요한 경우, 수동으로 'sudo minikube tunnel'을 실행하세요."
        rm -f "$PID_FILE"
        return 1
    fi
}

# Minikube 시작
start_minikube() {
    # sudo로 실행 중인지 확인
    if [ "$EUID" -eq 0 ]; then
        log_error "Minikube는 root 권한으로 실행할 수 없습니다."
        log_error "일반 사용자로 실행하세요: ./minikube.sh start"
        log_info "Tunnel만 sudo 권한이 필요합니다 (privileged ports 80, 443 사용)."
        return 1
    fi
    
    log_info "Minikube 상태 확인 중..."
    
    # 기존 Minikube가 있는 경우
    if minikube status > /dev/null 2>&1; then
        local host_status=$(minikube status --format '{{.Host}}' 2>/dev/null || echo "unknown")
        if [ "$host_status" = "Running" ]; then
            log_info "Minikube가 이미 실행 중입니다"
            
            # Tunnel 시작
            start_tunnel
            
            log_success "Minikube 시작 완료!"
            return 0
        fi
    fi
    
    log_info "Minikube 시작 중..."
    log_info "리소스: CPU 4개, 메모리 4GiB"
    log_info "Dynamic Provisioning 사용 (데이터는 minikube 내부에 저장)"
    
    # Minikube 시작
    if minikube start --driver=docker \
        --cpus=4 \
        --memory=4000; then
        log_success "Minikube 시작 완료"
        
        # Kubernetes API 서버가 준비될 때까지 대기
        log_info "Kubernetes API 서버 준비 대기 중..."
        sleep 5
        
        # Ingress addon 활성화
        log_info "Ingress addon 활성화 중..."
        if minikube addons enable ingress > /dev/null 2>&1; then
            log_success "Ingress addon 활성화 완료"
            log_info "Ingress Controller Pod가 시작되는 동안 대기 중..."
            sleep 10
        else
            log_warning "Ingress addon 활성화 실패 (이미 활성화되었을 수 있음)"
        fi
        
        # Ingress DNS addon 활성화 (선택사항)
        log_info "Ingress DNS addon 활성화 중..."
        if minikube addons enable ingress-dns > /dev/null 2>&1; then
            log_success "Ingress DNS addon 활성화 완료"
        else
            log_warning "Ingress DNS addon 활성화 실패 (이미 활성화되었을 수 있음)"
        fi
        
        # Ingress Controller Service를 LoadBalancer 타입으로 설정 (Tunnel 작동을 위해)
        log_info "Ingress Controller Service를 LoadBalancer로 설정 중..."
        if kubectl patch svc ingress-nginx-controller -n ingress-nginx -p '{"spec":{"type":"LoadBalancer"}}' > /dev/null 2>&1; then
            log_success "Ingress Controller Service를 LoadBalancer로 설정 완료"
        else
            log_warning "Ingress Controller Service 설정 실패 (이미 설정되었을 수 있음)"
        fi
        
        # CoreDNS 설정 적용
        configure_coredns
        
        # Tunnel 시작
        start_tunnel
        
        log_success "Minikube 및 Tunnel 시작 완료!"
        log_info ""
        log_info "다음 명령어로 상태를 확인할 수 있습니다:"
        log_info "  kubectl get nodes"
        log_info "  kubectl get pods -A"
        log_info "  $0 status"
    else
        log_error "Minikube 시작 실패"
        return 1
    fi
}

# Minikube 중지
stop_minikube() {
    local delete_cluster=false
    
    # 옵션 파싱 (두 번째 인자가 --delete인 경우)
    if [ "$2" = "--delete" ]; then
        delete_cluster=true
    fi
    
    log_info "Minikube 상태 확인 중..."
    
    # Tunnel 먼저 중지
    stop_tunnel
    
    if minikube status > /dev/null 2>&1; then
        log_info "Minikube 중지 중..."
        if minikube stop; then
            log_success "Minikube 중지 완료"
            
            if [ "$delete_cluster" = true ]; then
                log_info "Minikube 클러스터 삭제 중..."
                log_warning "주의: 모든 데이터가 삭제됩니다!"
                if minikube delete; then
                    log_success "Minikube 클러스터 삭제 완료"
                else
                    log_error "Minikube 클러스터 삭제 실패"
                    return 1
                fi
            fi
        else
            log_error "Minikube 중지 실패"
            return 1
        fi
    else
        log_info "Minikube가 실행 중이지 않습니다"
        if [ "$delete_cluster" = true ]; then
            log_info "Minikube 클러스터 삭제 중..."
            if minikube delete; then
                log_success "Minikube 클러스터 삭제 완료"
            fi
        fi
    fi
}

# 상태 확인
check_status() {
    log_info "Minikube 및 Tunnel 상태 확인 중..."
    echo ""
    
    # Minikube 상태
    log_info "=== Minikube 상태 ==="
    if minikube status > /dev/null 2>&1; then
        minikube status
    else
        log_warning "Minikube가 실행 중이지 않습니다"
    fi
    
    echo ""
    
    # Tunnel 상태
    log_info "=== Tunnel 상태 ==="
    if check_tunnel_process; then
        if [ -f "$PID_FILE" ]; then
            local pid=$(cat "$PID_FILE")
            log_success "Tunnel 실행 중 (PID: $pid)"
        else
            local pid=$(pgrep -f "minikube tunnel" | head -1)
            if [ -n "$pid" ]; then
                log_success "Tunnel 실행 중 (PID: $pid)"
            fi
        fi
        log_info "Tunnel 로그: /tmp/minikube-tunnel.log"
    else
        log_warning "Tunnel이 실행 중이지 않습니다"
    fi
    
    echo ""
    
    # Kubernetes 클러스터 상태
    log_info "=== Kubernetes 클러스터 상태 ==="
    if kubectl cluster-info > /dev/null 2>&1; then
        kubectl get nodes 2>/dev/null || log_warning "노드 정보를 가져올 수 없습니다"
    else
        log_warning "Kubernetes 클러스터에 연결할 수 없습니다"
    fi
}

# 재시작
restart_minikube() {
    log_info "Minikube 재시작 중..."
    stop_minikube
    sleep 2
    start_minikube
}

# 메인 함수
main() {
    local command="${1:-start}"
    
    # 명령어 파싱
    case "$command" in
        start)
            start_minikube
            ;;
        stop)
            stop_minikube "$@"
            ;;
        restart)
            restart_minikube
            ;;
        status)
            check_status
            ;;
        tunnel)
            start_tunnel
            ;;
        tunnel-stop)
            stop_tunnel
            ;;
        coredns)
            configure_coredns
            ;;
        -h|--help|help)
            show_help
            exit 0
            ;;
        *)
            log_error "알 수 없는 명령어: $command"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 스크립트 실행
main "$@"
