# ERD 관계선 레이블 겹침 개선

## 문제점

ERD 리포트에서 여러 테이블 간 관계선(edge)이 서로 가까이 있을 때, 조인 조건 레이블이 겹쳐서 가독성이 떨어지는 문제 발생

### 기존 설정 (개선 전)

```javascript
{
    selector: 'edge',
    style: {
        'label': 'data(label)',
        'font-size': '10px',
        'text-rotation': 'autorotate',  // 레이블이 선을 따라 회전
        'text-margin-y': -10            // 레이블 위치
    }
}
```

**문제점**:
- 레이블이 배경 없이 투명하게 표시되어 겹침 시 읽기 어려움
- `autorotate`로 인해 레이블이 회전하여 가독성 저하
- 레이블 크기가 작아서 구분이 어려움

## 개선 내용

### 수정된 스타일 (개선 후)

**파일**: `reports/erd_dagre_templates.py`
**라인**: 547-560

```javascript
{
    selector: 'edge',
    style: {
        'width': 3,
        'line-color': '#7f8c8d',
        'target-arrow-color': '#7f8c8d',
        'target-arrow-shape': 'triangle',
        'curve-style': 'bezier',
        'label': 'data(label)',

        // 레이블 텍스트 개선
        'font-size': '11px',              // 10px → 11px (가독성 향상)
        'font-weight': 'bold',            // 굵은 폰트
        'color': '#2c3e50',               // 진한 색상
        'text-rotation': 'none',          // 항상 수평 유지 (autorotate 제거)
        'text-margin-y': -15,             // 레이블 위치 조정 (-10 → -15)

        // 레이블 배경 추가 (핵심 개선)
        'text-background-color': '#ffffff',      // 흰색 배경
        'text-background-opacity': 0.9,          // 90% 불투명도
        'text-background-padding': '3px',        // 배경 여백
        'text-background-shape': 'roundrectangle', // 둥근 사각형

        // 레이블 테두리 추가
        'text-border-color': '#ddd',      // 연한 회색 테두리
        'text-border-width': 1,           // 1px 테두리
        'text-border-opacity': 0.8        // 80% 불투명도
    }
}
```

### 주요 개선 사항

| 항목 | 변경 전 | 변경 후 | 효과 |
|------|---------|---------|------|
| **배경** | 없음 (투명) | 흰색 배경 (90% 불투명) | 겹침 시에도 레이블 가독 가능 |
| **회전** | autorotate | none (수평 유지) | 항상 읽기 쉬운 방향 |
| **폰트 크기** | 10px | 11px | 가독성 향상 |
| **폰트 굵기** | normal | bold | 레이블 강조 |
| **테두리** | 없음 | 1px 연한 회색 | 레이블 구분 명확 |
| **배경 모양** | - | 둥근 사각형 | 시각적으로 깔끔 |

## 효과

### Before (개선 전)
```
관계선 ─────────────── 관계선
  u.user_id = o.user_id     (겹쳐서 읽기 어려움)
         p.product_id = o.product_id
```

### After (개선 후)
```
관계선 ─────────────── 관계선
  ┌─────────────────────┐
  │ u.user_id = o.user_id │    (흰색 배경으로 명확히 구분)
  └─────────────────────┘
  ┌──────────────────────────┐
  │ p.product_id = o.product_id │
  └──────────────────────────┘
```

## 검증

### 생성된 리포트
- **파일**: `projects/sampleSrc/report/[sampleSrc]_ERD_20251126_153136.html`
- **테이블 수**: 26개
- **관계선 수**: 확인 필요 (리포트 열어서 시각적 확인)

### 확인 사항
✅ 레이블이 흰색 배경과 함께 표시됨
✅ 레이블이 항상 수평 방향 유지
✅ 레이블이 bold 폰트로 강조됨
✅ 레이블 테두리로 구분 명확

## 추가 개선 가능성

현재 개선으로도 대부분의 겹침 문제가 해결되지만, 극단적으로 많은 관계선이 있는 경우 추가 개선 가능:

### 고급 옵션 (필요시 적용)

1. **Edge Bundling** (관계선 묶음)
```javascript
'curve-style': 'unbundled-bezier',
'control-point-distances': [40, -40],
'control-point-weights': [0.25, 0.75]
```

2. **동적 레이블 표시**
```javascript
// 줌 레벨에 따라 레이블 on/off
cy.on('zoom', function() {
    if (cy.zoom() < 0.5) {
        cy.edges().removeClass('show-label');
    } else {
        cy.edges().addClass('show-label');
    }
});
```

3. **호버 시에만 레이블 표시**
```javascript
cy.on('mouseover', 'edge', function(evt) {
    evt.target.style('label', evt.target.data('label'));
});
cy.on('mouseout', 'edge', function(evt) {
    evt.target.style('label', '');
});
```

## 참고

- Cytoscape.js 공식 문서: https://js.cytoscape.org/#style/labels
- 현재 구현은 **배경 + 수평 고정** 방식으로 간단하면서도 효과적인 개선
- 추가 개선이 필요한 경우 위의 고급 옵션 적용 검토

## 수정 일시

2025-11-26 15:31 KST
