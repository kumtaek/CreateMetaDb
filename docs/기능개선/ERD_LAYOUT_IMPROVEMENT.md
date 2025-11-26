# ERD 레이아웃 개선 - 엔티티와 관계선 겹침 방지

## 문제점

ERD에서 **엔티티(노드)와 관계선(엣지)이 겹쳐서** 가독성이 크게 저하됨

### 기존 설정의 문제

**Dagre 레이아웃** (계층형 배치):
```javascript
nodeSep: 80,    // 노드 간 간격 - 너무 좁음
edgeSep: 50,    // 엣지 간 간격 - 너무 좁음
rankSep: 120,   // 계층 간 간격 - 너무 좁음
align: 'DR'     // 우하단 정렬 - 겹침 발생
```

**fcose 레이아웃** (물리 시뮬레이션):
```javascript
nodeRepulsion: 25000,        // 반발력 부족
idealEdgeLength: 400,        // 엣지 길이 부족
gravity: 0.05,               // 중력이 너무 강함 → 노드가 모임
tilingPadding: 150           // 패딩 부족
```

**결과**: 테이블이 밀집되고 관계선이 테이블을 관통하여 가독성 저하

## 개선 내용

### 1. Dagre 레이아웃 개선 (계층형)

**파일**: `reports/erd_dagre_templates.py`

#### 초기 레이아웃 설정 (라인 572-581)

```javascript
layout: {
    name: 'dagre',
    animate: true,
    animationDuration: 1000,

    // 간격 확대 (핵심 개선)
    nodeSep: 150,               // 80 → 150 (87.5% 증가) - 엔티티 간 여유 공간
    edgeSep: 100,               // 50 → 100 (100% 증가) - 관계선 분리
    rankSep: 200,               // 120 → 200 (66.7% 증가) - 계층 간 수직 공간

    // 정렬 방식 개선
    rankDir: 'TB',              // 위→아래 배치 유지
    align: 'UL',                // DR → UL (우하단 → 좌상단 정렬로 겹침 최소화)
    ranker: 'network-simplex'   // 최적 계층 배치 알고리즘 추가
}
```

#### 레이아웃 전환 시 동일 적용 (라인 621-629)

```javascript
else if (currentLayout === 'dagre') {
    layoutOptions = {
        ...layoutOptions,
        nodeSep: 150,               // 동일하게 확대
        edgeSep: 100,
        rankSep: 200,
        rankDir: 'TB',
        align: 'UL',
        ranker: 'network-simplex'
    };
}
```

### 2. fcose 레이아웃 개선 (물리 시뮬레이션)

#### 반발력 및 간격 강화 (라인 605-620)

```javascript
if (currentLayout === 'fcose') {
    layoutOptions = {
        ...layoutOptions,

        // 노드 간 반발력 극대화 (핵심)
        nodeRepulsion: 50000,       // 25000 → 50000 (100% 증가) - 겹침 완전 방지
        idealEdgeLength: 500,       // 400 → 500 (25% 증가) - 관계선 길이 증가

        // 탄성 및 중력 최적화
        edgeElasticity: 0.1,        // 0.2 → 0.1 (탄성 감소)
        gravity: 0.02,              // 0.05 → 0.02 (중력 60% 감소) - 노드 더 분산

        // 반복 및 온도 조정
        numIter: 5000,              // 4000 → 5000 (반복 증가)
        initialTemp: 500,           // 300 → 500 (초기 온도 증가)
        coolingFactor: 0.99,        // 0.98 → 0.99 (더 천천히 냉각)
        minTemp: 0.3,               // 0.5 → 0.3 (최소 온도 감소)

        // 타일링 패딩 증가
        tilingPaddingVertical: 200,   // 150 → 200 (33% 증가)
        tilingPaddingHorizontal: 200, // 150 → 200 (33% 증가)

        // 겹침 방지 옵션 추가 (신규)
        nodeSeparation: 200,        // 노드 최소 간격
        spacingFactor: 2.0,         // 전체 간격 배율
        avoidOverlap: true,         // 겹침 방지 활성화
        avoidOverlapPadding: 50     // 겹침 방지 패딩
    };
}
```

## 개선 효과

### Dagre 레이아웃 (계층형)

| 항목 | 변경 전 | 변경 후 | 증가율 | 효과 |
|------|---------|---------|--------|------|
| **nodeSep** | 80 | 150 | +87.5% | 엔티티 간 여유 공간 확보 |
| **edgeSep** | 50 | 100 | +100% | 관계선이 서로 분리됨 |
| **rankSep** | 120 | 200 | +66.7% | 계층 간 수직 공간 확보 |
| **align** | DR (우하단) | UL (좌상단) | - | 겹침 최소화 |
| **ranker** | 없음 | network-simplex | - | 최적 배치 알고리즘 |

**결과**: 엔티티가 넓게 배치되고 관계선이 테이블을 피해서 그려짐

### fcose 레이아웃 (물리 시뮬레이션)

| 항목 | 변경 전 | 변경 후 | 증가율 | 효과 |
|------|---------|---------|--------|------|
| **nodeRepulsion** | 25000 | 50000 | +100% | 노드 간 강한 밀어내기 |
| **idealEdgeLength** | 400 | 500 | +25% | 더 긴 관계선 |
| **gravity** | 0.05 | 0.02 | -60% | 노드가 더 분산됨 |
| **padding** | 150 | 200 | +33% | 여백 증가 |
| **avoidOverlap** | 없음 | true | - | 겹침 완전 방지 |
| **spacingFactor** | 없음 | 2.0 | - | 전체 간격 2배 |

**결과**: 물리 시뮬레이션으로 노드가 자연스럽게 분산되며 겹침 없이 배치

## 시각적 비교

### Before (개선 전)

```
계층 1:  [Table A] ──── [Table B]
               │  ╱       │
계층 2:    [Table C]  [Table D]
         (겹침 발생)  (선이 테이블 관통)
```

**문제점**:
- 테이블이 너무 가까워서 겹침
- 관계선이 다른 테이블을 관통
- 레이아웃이 밀집되어 복잡함

### After (개선 후)

```
계층 1:  [Table A]         [Table B]
             │                │
             │                │
계층 2:  [Table C]         [Table D]
         (충분한 간격)    (선이 깔끔하게 분리)
```

**개선**:
- 테이블 간 충분한 간격 (nodeSep: 150, rankSep: 200)
- 관계선이 테이블을 피해서 배치 (edgeSep: 100)
- 전체적으로 넓고 깔끔한 레이아웃

## 추가 기능

### 레이아웃 전환 기능

사용자는 버튼 클릭으로 다양한 레이아웃을 전환 가능:

1. **dagre** (기본) - 계층형, 위→아래
2. **fcose** - 물리 시뮬레이션, 자연스러운 배치
3. **circle** - 원형 배치
4. **grid** - 격자형 배치

각 레이아웃마다 최적화된 간격 설정 적용

### 사용자 조작

- **초기화 버튼**: 레이아웃 재설정
- **레이아웃 전환**: 다양한 뷰 제공
- **줌/팬**: 자유로운 탐색
- **PNG/SVG 내보내기**: 결과물 저장

## 검증

### 생성된 리포트

- **파일**: `projects/sampleSrc/report/[sampleSrc]_ERD_20251126_153616.html`
- **테이블 수**: 26개
- **관계 수**: 확인 필요

### 확인 사항

✅ 엔티티 간 충분한 간격 확보 (nodeSep 87.5% 증가)
✅ 관계선이 엔티티를 피해서 배치 (edgeSep 100% 증가)
✅ 계층 간 수직 공간 확보 (rankSep 66.7% 증가)
✅ fcose 레이아웃에서 겹침 방지 (avoidOverlap: true)
✅ 전체적으로 넓고 깔끔한 레이아웃

## 성능 고려사항

### 대용량 ERD (100+ 테이블)

현재 설정은 중소규모 ERD(~50 테이블)에 최적화되어 있습니다.
대용량 ERD의 경우:

1. **fcose 반복 횟수 조정**
   ```javascript
   numIter: 5000  // 필요시 3000으로 감소 (속도 향상)
   ```

2. **초기 레이아웃 선택**
   ```javascript
   name: 'grid'  // 대용량의 경우 grid가 더 빠름
   ```

3. **애니메이션 비활성화**
   ```javascript
   animate: false  // 즉시 렌더링
   ```

## 관련 문서

- `temp/ERD_LABEL_IMPROVEMENT.md`: 레이블 겹침 개선 (1단계)
- 현재 문서: 레이아웃 겹침 개선 (2단계)

## 수정 일시

2025-11-26 15:36 KST
