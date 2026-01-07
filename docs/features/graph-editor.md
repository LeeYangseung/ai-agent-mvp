# 그래프 에디터

드래그 앤 드롭 방식으로 AI 워크플로우를 시각적으로 설계할 수 있는 에디터입니다.

## 지원 노드 타입

| 노드 타입 | 설명 | 입력 | 출력 |
|---------|------|------|------|
| **InputNode** | 워크플로우 시작점, 초기 상태 설정 | 사용자 입력 (질문, 파라미터) | 초기화된 state |
| **PromptNode** | LLM 호출, 템플릿 기반 프롬프트 생성 | state (컨텍스트) | LLM 응답 추가된 state |
| **RetrievalNode** | 벡터 검색, 관련 문서 조회 | query, collection_name | 검색된 컨텍스트 추가된 state |
| **ConditionNode** | 조건 분기, 동적 경로 결정 | state | 다음 노드 ID (분기 경로) |
| **MergeNode** | 여러 경로 합류, 상태 병합 | 여러 state | 병합된 state |
| **OutputNode** | 워크플로우 종료점, 최종 결과 포맷팅 | state | 최종 응답 |

---

## 노드 설정 상세

### InputNode
- **역할**: 사용자의 질문이나 초기 파라미터를 받아 그래프 실행의 시작점 역할
- **설정 항목**:
  - `output`: input node의 출력이 저장될 state 키 (user_input으로 고정)

### PromptNode
- **역할**: 템플릿 기반으로 프롬프트를 생성하고 LLM을 호출하여 응답 생성
- **설정 항목**:
  - `system_prompt`: 시스템 메시지 템플릿
  - `user_prompt`: 사용자 메시지 템플릿
  - `assistant_prompt`: 어시스턴트 메시지 템플릿(선택사항)
  - `inputs`: 노드 내에서 사용될 variables(고정값 또는 타 노드의 output 참조 가능)
  - `output`: 응답이 저장될 state 키

### RetrievalNode
- **역할**: 지정된 컬렉션에서 벡터 유사도 검색을 수행하여 관련 문서 조회
- **설정 항목**:
  - `collection`: 검색할 컬렉션 이름 (필수)
  - `top_k`: 반환할 최대 문서 개수 (기본값: 4)
  - `inputs`: 노드 내에서 사용될 variables(고정값 또는 타 노드의 output 참조 가능, query는 필수)
  - `output`: 검색 결과가 저장될 state 키 (기본값: "context")

### ConditionNode
- **역할**: state 값을 평가하여 다음 실행 경로를 결정 (if-else, 루프 구현 가능)
- **설정 항목**:
  - `evaluation_mode`: 분기 유형
    - `First Match`: 조건을 만족하는 첫 분기만 실행
    - `All Matches`: 조건을 만족하는 모든 분기를 병렬 실행(Fan-out)
  - `inputs`: 노드 내에서 사용될 variables(고정값 또는 타 노드의 output 참조 가능)
  - `conditions`: inputs에서 받은 값에 대해 특정 값과 비교해 True이면 match, 모든 값이 false이면 else 분기 실행
    - `operator`: 연산자
    - `target`: match시 분기할 타겟 노드
    - `value`: 비교할 값
    - `variable`: input으로 받은 variables 중 비교할 variable

### MergeNode
- **역할**: 여러 병렬 실행 경로의 결과를 하나로 합침
- **설정 항목**:
  - `merge_strategy`: 병합 전략 (concat, list, dict)
  - `inputs`: 병합할 state 키 목록
  - `output`: 병합 결과가 저장될 state 키

### OutputNode
- **역할**: 최종 결과를 포맷팅하고 워크플로우 종료
- **설정 항목**:
  - `inputs`: 노드 내에서 사용될 variables(고정값 또는 타 노드의 output 참조 가능)
  - `output`: 응답이 저장될 state 키(agent_output 고정)

---

## 사용 방법

### 1. 노드 추가
좌측 노드 팔레트에서 추가하고싶은 노드를 클릭해 캔버스에 배치합니다.

### 2. 노드 설정
노드 내부의 설정값을 편집합니다.

### 3. 엣지 연결
노드의 출력 핸들(우측)을 다음 노드의 입력 핸들(좌측)로 드래그하여 연결합니다.

### 4. 그래프 저장
하단 "저장" 버튼으로 그래프를 데이터베이스에 저장합니다.

**저장 정보:**
- 그래프 이름 (필수)
- 설명
- 버전
- 모든 노드와 엣지 정보

### 5. 실행 및 테스트
우측 챗 패널에서:
1. 입력값을 메시지 형태로 입력
2. "전속" 버튼 클릭
3. 결과 확인:
   - **실행결과**: 그래프 실행 결과
   - **노드별 입출력**: 각 노드의 실행 결과
   - **그래프 히스토리**: 그래프 실행 히스토리
   - **그래프 스테이트**: 전체 그래프 state


[← 메인 README로 돌아가기](../../README.md) | [기능 목록으로](../features.md)

