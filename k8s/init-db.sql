-- AI Agent MVP 데이터베이스 초기화 스크립트

-- 데이터베이스 생성 (이미 agent로 생성됨)
-- CREATE DATABASE agent;

-- 사용자 권한 설정
GRANT ALL PRIVILEGES ON DATABASE agent TO admin;

-- 확장 기능 활성화 (필요한 경우)
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
-- CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 테이블 생성은 Alembic 마이그레이션을 통해 수행됩니다.
