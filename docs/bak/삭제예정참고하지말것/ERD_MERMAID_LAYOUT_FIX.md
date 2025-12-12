# ERD (Mermaid) 레이아웃 겹침 개선

## 문제 상황

사용자가 `python create_report.py --project-name sampleSrc --report-type erd`로 생성한 ERD는 **Mermaid.js 기반**이었으나,
처음에 **Cytoscape.js 기반** ERD (`erd-dagre`) 파일을 수정하여 변경사항이 반영되지 않았음.

### 두 가지 ERD 타입

| 타입 | 라이브러리 | 생성 명령 | 생성기 클래스 | 템플릿 파일 |
|------|-----------|----------|--------------|------------|
| **erd** | Mermaid.js | `--report-type erd` | ERDReportGenerator | report_templates.py |
| **erd-dagre** | Cytoscape.js | `--report-type erd-dagre` | ERDDagreReportGenerator | erd_dagre_templates.py |

**사용자는 `erd` (Mermaid)를 사용 중** → `report_templates.py` 수정 필요

## 해결 과정

### 1단계: 잘못된 파일 수정 (실패)
- ✗ `erd_dagre_templates.py` 수정 → Cytoscape 기반 ERD (사용자가 생성 안함)
- ✗ 변경사항이 HTML에 반영되지 않음

### 2단계: 올바른 파일 확인
- ✓ 생성된 HTML 파일 분석 → Mermaid 사용 확인
- ✓ `create_report.py` 코드 확인 → `erd` 타입은 `ERDReportGenerator` 사용
- ✓ `report_templates.py`의 Mermaid 설정 수정 필요

### 3단계: Mermaid ERD 레이아웃 개선

**파일**: `reports/report_templates.py`
**라인**: 1174-1179

#### 변경 전
```javascript
er: {
    useMaxWidth: true,
    htmlLabels: true,
    diagramPadding: 20,
    layoutDirection: 'TB'
},
```

**문제점**:
- `diagramPadding: 20` - 여백이 너무 좁음
- `useMaxWidth: true` - 너비 제한으로 엔티티가 밀집됨
- 엔티티 간 최소 간격 설정 없음

#### 변경 후
```javascript
er: {
    useMaxWidth: false,         // 최대 너비 제한 해제 (넓게 배치)
    htmlLabels: true,
    diagramPadding: 50,         // 20 → 50 (150% 증가) - 여백 확보
    layoutDirection: 'TB',      // Top-Bottom 유지
    minEntityWidth: 200,        // 엔티티 최소 너비 설정
    minEntityHeight: 80,        // 엔티티 최소 높이 설정
    entityPadding: 30,          // 엔티티 간 패딩 (겹침 방지)
    fontSize: 14                // 폰트 크기 명시
},
```

## 개선 효과

### 주요 변경사항

| 항목 | 변경 전 | 변경 후 | 증가율 | 효과 |
|------|---------|---------|--------|------|
| **diagramPadding** | 20 | 50 | +150% | 다이어그램 전체 여백 증가 |
| **useMaxWidth** | true | false | - | 너비 제한 해제 (넓게 배치) |
| **minEntityWidth** | 없음 | 200 | - | 엔티티 최소 너비 보장 |
| **minEntityHeight** | 없음 | 80 | - | 엔티티 최소 높이 보장 |
| **entityPadding** | 없음 | 30 | - | 엔티티 간 간격 확보 |
| **fontSize** | 없음 | 14 | - | 일관된 폰트 크기 |

### 시각적 개선

**Before (개선 전)**:
```
[Table A] ──── [Table B]
   ╱│              │
[Table C]      [Table D]
(좁고 겹침)
```

**After (개선 후)**:
```
[  Table A  ]         [  Table B  ]
      │                     │
      │                     │
      │                     │
[  Table C  ]         [  Table D  ]
(넓고 깔끔, 간격 확보)
```

## 검증 결과

### 생성된 파일
- **파일**: `projects/sampleSrc/report/[sampleSrc]_ERD_20251126_154225.html`
- **라이브러리**: Mermaid.js
- **설정 반영**: ✓ 모든 설정값이 HTML에 정확히 반영됨

### 확인 사항
```javascript
✓ useMaxWidth: false         // 너비 제한 해제
✓ diagramPadding: 50         // 여백 150% 증가
✓ minEntityWidth: 200        // 최소 너비 설정
✓ minEntityHeight: 80        // 최소 높이 설정
✓ entityPadding: 30          // 엔티티 간 패딩
✓ fontSize: 14               // 폰트 크기
```

## Mermaid vs Cytoscape 비교

| 특징 | Mermaid (erd) | Cytoscape (erd-dagre) |
|------|--------------|----------------------|
| **사용 목적** | 간단한 ERD, 문서화 | 복잡한 ERD, 인터랙티브 |
| **레이아웃** | 자동 (제한적 제어) | 수동 제어 가능 |
| **설정 옵션** | 적음 (padding, width 등) | 많음 (nodeSep, edgeSep, 물리 엔진) |
| **성능** | 빠름 | 느림 (대용량 시) |
| **인터랙티브** | 제한적 | 강력 (줌, 드래그, 레이아웃 전환) |
| **생성 명령** | `--report-type erd` | `--report-type erd-dagre` |

## 권장사항

### Mermaid ERD (erd) 사용 권장
- ✓ 간단한 ERD (20-30개 테이블)
- ✓ 빠른 생성 필요
- ✓ 정적인 문서화 목적
- ✓ 인쇄 출력 필요

### Cytoscape ERD (erd-dagre) 사용 권장
- ✓ 복잡한 ERD (50개 이상 테이블)
- ✓ 인터랙티브 탐색 필요
- ✓ 레이아웃 세밀 조정 필요
- ✓ 동적 필터링/검색 필요

**현재 프로젝트** (26개 테이블):
- Mermaid ERD로 충분 ✓
- 필요시 `--report-type erd-dagre`로 Cytoscape 버전 생성 가능

## 추가 개선 가능성

Mermaid는 자동 레이아웃이므로 세밀한 제어가 어렵습니다.
더 정밀한 레이아웃이 필요한 경우:

### 옵션 1: Cytoscape ERD 사용
```bash
python create_report.py --project-name sampleSrc --report-type erd-dagre
```

Cytoscape ERD는 이미 개선 완료:
- nodeSep: 150
- edgeSep: 100
- rankSep: 200
- fcose 물리 엔진 최적화

### 옵션 2: Mermaid 고급 설정
```javascript
er: {
    // ... 현재 설정 ...
    curve: 'basis',           // 곡선 스타일
    padding: 10,              // 요소 내부 패딩
    textHeight: 14,           // 텍스트 높이
}
```

## 수정 이력

1. **1차 시도** (실패): erd_dagre_templates.py 수정 → 잘못된 파일
2. **2차 수정** (성공): report_templates.py의 Mermaid 설정 수정
3. **검증 완료**: HTML 파일에 설정 정확히 반영 확인

## 수정 일시

2025-11-26 15:42 KST
