#!/bin/bash

# AI Agent MVP Advanced Docker Build Script
# 고급 기능이 포함된 Docker 빌드 스크립트

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# 로깅 함수
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_debug() { echo -e "${PURPLE}[DEBUG]${NC} $1"; }

# 도움말 출력
show_help() {
    cat << EOF
AI Agent MVP Docker Build Script

사용법: $0 [옵션]

옵션:
    -h, --help              이 도움말을 표시합니다
    -a, --arch ARCH         특정 아키텍처로 빌드 (amd64, arm64, arm/v7)
    -t, --tag TAG           이미지 태그 설정 (기본값: latest)
    -c, --clean             빌드 전 기존 이미지 정리
    -n, --no-cache          Docker 캐시를 사용하지 않고 빌드
    -p, --push              빌드 후 레지스트리에 푸시 (DOCKER_REGISTRY 환경변수 필요)
    -r, --registry REGISTRY Docker 레지스트리 URL 설정
    -v, --verbose           상세 로그 출력
    --backend-only          Backend만 빌드
    --frontend-only         Frontend만 빌드
    --multi-arch            멀티 아키텍처 빌드 (amd64, arm64)

예시:
    $0                      # 기본 빌드
    $0 -a arm64             # ARM64 아키텍처로 빌드
    $0 -t v1.0.0            # v1.0.0 태그로 빌드
    $0 -c -n                # 캐시 없이 깨끗하게 빌드
    $0 --multi-arch         # 멀티 아키텍처 빌드
    $0 --backend-only       # Backend만 빌드

EOF
}

# 아키텍처 감지
detect_architecture() {
    local arch=$(uname -m)
    case $arch in
        x86_64) echo "amd64" ;;
        arm64|aarch64) echo "arm64" ;;
        armv7l) echo "arm/v7" ;;
        *) log_warning "알 수 없는 아키텍처: $arch. amd64로 기본 설정합니다."; echo "amd64" ;;
    esac
}

# Docker 확인
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker가 설치되어 있지 않습니다."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker가 실행 중이지 않습니다."
        exit 1
    fi
}

# 기존 이미지 정리
clean_images() {
    log_info "기존 이미지 정리 중..."
    
    # 기존 ai-agent 이미지들 제거
    if docker images --format "{{.Repository}}" | grep -q "ai-agent-"; then
        docker rmi $(docker images --format "{{.Repository}}:{{.Tag}}" | grep "ai-agent-") 2>/dev/null || true
        log_success "기존 이미지 정리 완료"
    else
        log_info "정리할 기존 이미지가 없습니다"
    fi
}

# 이미지 빌드 함수
build_image() {
    local service=$1
    local dockerfile_path=$2
    local image_name=$3
    local arch=$4
    local no_cache=$5
    local verbose=$6
    
    log_info "$service 이미지 빌드 시작... (아키텍처: $arch)"
    
    if [ ! -f "$dockerfile_path" ]; then
        log_error "Dockerfile을 찾을 수 없습니다: $dockerfile_path"
        return 1
    fi
    
    local build_args="--platform linux/$arch --tag $image_name --file $dockerfile_path"
    
    if [ "$no_cache" = true ]; then
        build_args="$build_args --no-cache"
    fi
    
    if [ "$verbose" = true ]; then
        build_args="$build_args --progress=plain"
    fi
    
    build_args="$build_args $(dirname "$dockerfile_path")"
    
    if [ "$verbose" = true ]; then
        log_debug "빌드 명령어: docker build $build_args"
    fi
    
    if docker build $build_args; then
        log_success "$service 이미지 빌드 완료: $image_name"
        return 0
    else
        log_error "$service 이미지 빌드 실패"
        return 1
    fi
}

# 멀티 아키텍처 빌드
build_multi_arch() {
    local service=$1
    local dockerfile_path=$2
    local image_name=$3
    local registry=$4
    
    log_info "$service 멀티 아키텍처 빌드 시작..."
    
    if [ ! -f "$dockerfile_path" ]; then
        log_error "Dockerfile을 찾을 수 없습니다: $dockerfile_path"
        return 1
    fi
    
    # Docker buildx 사용 가능한지 확인
    if ! docker buildx version &> /dev/null; then
        log_error "Docker buildx가 설치되어 있지 않습니다. 멀티 아키텍처 빌드를 위해 Docker buildx가 필요합니다."
        return 1
    fi
    
    # buildx builder 생성 및 사용
    docker buildx create --name multiarch --use 2>/dev/null || docker buildx use multiarch
    
    local full_image_name="$image_name"
    if [ -n "$registry" ]; then
        full_image_name="$registry/$image_name"
    fi
    
    if docker buildx build \
        --platform linux/amd64,linux/arm64 \
        --tag "$full_image_name" \
        --file "$dockerfile_path" \
        --push \
        "$(dirname "$dockerfile_path")"; then
        log_success "$service 멀티 아키텍처 빌드 완료: $full_image_name"
        return 0
    else
        log_error "$service 멀티 아키텍처 빌드 실패"
        return 1
    fi
}

# 이미지 푸시
push_image() {
    local image_name=$1
    local registry=$2
    
    if [ -z "$registry" ]; then
        log_error "레지스트리가 설정되지 않았습니다. -r 옵션을 사용하세요."
        return 1
    fi
    
    local full_image_name="$registry/$image_name"
    
    log_info "이미지 태그 변경: $image_name -> $full_image_name"
    docker tag "$image_name" "$full_image_name"
    
    log_info "이미지 푸시 중: $full_image_name"
    if docker push "$full_image_name"; then
        log_success "이미지 푸시 완료: $full_image_name"
    else
        log_error "이미지 푸시 실패"
        return 1
    fi
}

# 메인 함수
main() {
    # 기본값 설정
    local arch=""
    local tag="latest"
    local clean=false
    local no_cache=false
    local push=false
    local registry=""
    local verbose=false
    local backend_only=false
    local frontend_only=false
    local multi_arch=false
    
    # 인수 파싱
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -a|--arch)
                arch="$2"
                shift 2
                ;;
            -t|--tag)
                tag="$2"
                shift 2
                ;;
            -c|--clean)
                clean=true
                shift
                ;;
            -n|--no-cache)
                no_cache=true
                shift
                ;;
            -p|--push)
                push=true
                shift
                ;;
            -r|--registry)
                registry="$2"
                shift 2
                ;;
            -v|--verbose)
                verbose=true
                shift
                ;;
            --backend-only)
                backend_only=true
                shift
                ;;
            --frontend-only)
                frontend_only=true
                shift
                ;;
            --multi-arch)
                multi_arch=true
                shift
                ;;
            *)
                log_error "알 수 없는 옵션: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 아키텍처 설정
    if [ -z "$arch" ]; then
        arch=$(detect_architecture)
    fi
    
    log_info "AI Agent MVP Docker 빌드 스크립트 시작"
    log_info "아키텍처: $arch"
    log_info "태그: $tag"
    
    # 현재 디렉토리 설정
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
    
    # Docker 확인
    check_docker
    
    # 이미지 정리
    if [ "$clean" = true ]; then
        clean_images
    fi
    
    # 이미지 이름 설정
    local backend_image="ai-agent-backend:$tag"
    local frontend_image="ai-agent-frontend:$tag"
    
    # Dockerfile 경로
    local backend_dockerfile="$PROJECT_ROOT/backend/Dockerfile"
    local frontend_dockerfile="$PROJECT_ROOT/frontend/Dockerfile"
    
    # 빌드 시작 시간
    local start_time=$(date +%s)
    local build_success=true
    
    # 멀티 아키텍처 빌드
    if [ "$multi_arch" = true ]; then
        if [ "$backend_only" = false ] && [ "$frontend_only" = false ]; then
            # Backend와 Frontend 모두 빌드
            build_multi_arch "Backend" "$backend_dockerfile" "$backend_image" "$registry" || build_success=false
            build_multi_arch "Frontend" "$frontend_dockerfile" "$frontend_image" "$registry" || build_success=false
        elif [ "$backend_only" = true ]; then
            build_multi_arch "Backend" "$backend_dockerfile" "$backend_image" "$registry" || build_success=false
        elif [ "$frontend_only" = true ]; then
            build_multi_arch "Frontend" "$frontend_dockerfile" "$frontend_image" "$registry" || build_success=false
        fi
    else
        # 단일 아키텍처 빌드
        if [ "$backend_only" = false ] && [ "$frontend_only" = false ]; then
            # Backend와 Frontend 모두 빌드
            build_image "Backend" "$backend_dockerfile" "$backend_image" "$arch" "$no_cache" "$verbose" || build_success=false
            build_image "Frontend" "$frontend_dockerfile" "$frontend_image" "$arch" "$no_cache" "$verbose" || build_success=false
        elif [ "$backend_only" = true ]; then
            build_image "Backend" "$backend_dockerfile" "$backend_image" "$arch" "$no_cache" "$verbose" || build_success=false
        elif [ "$frontend_only" = true ]; then
            build_image "Frontend" "$frontend_dockerfile" "$frontend_image" "$arch" "$no_cache" "$verbose" || build_success=false
        fi
    fi
    
    # 푸시
    if [ "$push" = true ] && [ "$multi_arch" = false ]; then
        if [ "$backend_only" = false ] && [ "$frontend_only" = false ]; then
            push_image "$backend_image" "$registry" || build_success=false
            push_image "$frontend_image" "$registry" || build_success=false
        elif [ "$backend_only" = true ]; then
            push_image "$backend_image" "$registry" || build_success=false
        elif [ "$frontend_only" = true ]; then
            push_image "$frontend_image" "$registry" || build_success=false
        fi
    fi
    
    # 빌드 완료 시간
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    if [ "$build_success" = true ]; then
        log_success "=== 모든 빌드 작업 완료 ==="
        log_info "총 소요 시간: ${duration}초"
        
        if [ "$multi_arch" = false ]; then
            log_info "빌드된 이미지 목록:"
            docker images --filter "reference=ai-agent-*" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
        fi
    else
        log_error "빌드 중 오류가 발생했습니다."
        exit 1
    fi
}

# 스크립트 실행
main "$@"
