# ERD 고아 테이블 제거 수정 가이드

## 문제
`--include-orphan` 옵션을 사용하지 않았는데도 고아 테이블(조인 관계 없는 테이블)이 ERD에 표시됨

## 원인
`reports/erd_report_generator.py`의 110-114번 라인에서:
- 관계 데이터가 없으면 자동으로 **모든 테이블**을 포함하도록 fallback 로직이 있음
- 이 로직이 `include_orphan_tables` 설정을 무시함

## 수정 파일
`reports/erd_report_generator.py`

## 수정 위치
**Line 109-114**

### 수정 전
```python
# 데이터 유효성 검증 (빈 리포트 생성 방지)
if not tables_data or not relationships:
    # 관계가 없거나 관계 기반 테이블 조회가 비어 있으면 전체 테이블로 대체
    app_logger.warning("관계 데이터가 없거나 테이블 조회 결과가 비어 전체 테이블로 ERD를 생성합니다.")
    tables_data = self.metadata_service.get_all_tables_with_columns()
    relationships = relationships or []
```

### 수정 후
```python
# 데이터 유효성 검증 (빈 리포트 생성 방지)
if not tables_data or not relationships:
    # include_orphan_tables 옵션이 True일 때만 전체 테이블로 대체
    if self.include_orphan_tables:
        app_logger.warning("관계 데이터가 없거나 테이블 조회 결과가 비어 전체 테이블로 ERD를 생성합니다.")
        tables_data = self.metadata_service.get_all_tables_with_columns()
        relationships = relationships or []
    else:
        # include_orphan_tables=False인 경우, 관계가 없으면 빈 ERD 생성
        app_logger.warning("관계 데이터가 없습니다. 고아 테이블 제외 옵션으로 인해 빈 ERD가 생성됩니다.")
        if not tables_data:
            tables_data = {}
        if not relationships:
            relationships = []
```

## 동일한 수정 필요 파일
`reports/erd_dagre_report_generator.py`도 동일한 로직이 있으므로 같이 수정 필요

### erd_dagre_report_generator.py 수정 위치
**Line 109-114** (동일한 위치)

## 검증 방법
```bash
# 1. 메타DB 재생성 (기존 데이터 사용)
python main.py --project-name {project_name}

# 2. ERD 생성 (고아 테이블 제외 - 기본값)
python create_report.py --project-name {project_name} --report-type erd

# 3. 생성된 ERD 확인
# projects/{project_name}/report/ 폴더의 ERD HTML 파일 열기
# 조인 관계가 있는 테이블만 표시되는지 확인

# 4. 고아 테이블 포함 ERD 생성 (비교용)
python create_report.py --project-name {project_name} --report-type erd --include-orphan

# 5. 두 ERD 비교
# 기본 ERD: 조인 관계 있는 테이블만
# --include-orphan ERD: 모든 테이블
```

## 추가 개선 사항
관계가 전혀 없는 프로젝트의 경우:
- 기본 동작: 빈 ERD 생성 + 경고 메시지
- `--include-orphan` 사용 시: 모든 테이블 표시

이렇게 하면 사용자가 의도하지 않은 고아 테이블이 표시되지 않습니다.

## 참고
- `include_orphan_tables` 기본값: `False`
- `create_report.py`의 `--include-orphan` 옵션: 기본값 `False`
- ERD 생성 시 관계가 있는 테이블만 표시하는 것이 기본 동작이어야 함
