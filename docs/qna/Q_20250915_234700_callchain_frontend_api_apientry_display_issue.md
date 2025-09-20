# CallChain 리포트 FRONTEND_API/API_ENTRY 표시 문제 분석 질문서

## 문제 상황
CallChain 리포트에서 FRONTEND_API와 API_ENTRY 컬럼이 비어있게 표시되는 문제가 발생하고 있습니다.

## 현재 상황 분석

### 1. 데이터베이스 현황 확인
- **API_ENTRY 컴포넌트**: 35개 존재
- **FRONTEND_API 컴포넌트**: 35개 존재  
- **CALL_API_F2B 관계**: 35개 존재
- **API_ENTRY -> METHOD 관계**: 65개 존재
- **METHOD -> QUERY 관계**: 66개 존재

### 2. 개별 쿼리 테스트 결과
```sql
-- FRONTEND_API -> API_ENTRY 관계 확인
SELECT frontend.component_name, api.component_name 
FROM components frontend 
JOIN relationships r1 ON frontend.component_id = r1.src_id AND r1.rel_type = 'CALL_API_F2B'
JOIN components api ON r1.dst_id = api.component_id 
WHERE frontend.component_type = 'FRONTEND_API' AND api.component_type = 'API_ENTRY'
-- 결과: 정상적으로 35개 관계 확인됨

-- API_ENTRY -> METHOD 관계 확인  
SELECT api.component_name, m.component_name
FROM components api 
JOIN relationships r2 ON api.component_id = r2.src_id AND r2.rel_type = 'CALL_METHOD'
JOIN components m ON r2.dst_id = m.component_id 
WHERE api.component_type = 'API_ENTRY' AND m.component_type = 'METHOD'
-- 결과: 정상적으로 65개 관계 확인됨

-- 전체 체인 확인
SELECT COUNT(*) FROM components frontend 
JOIN relationships r1 ON frontend.component_id = r1.src_id AND r1.rel_type = 'CALL_API_F2B'
JOIN components api ON r1.dst_id = api.component_id 
JOIN relationships r2 ON api.component_id = r2.src_id AND r2.rel_type = 'CALL_METHOD'
JOIN components m ON r2.dst_id = m.component_id AND m.component_type = 'METHOD'
JOIN relationships r3 ON m.component_id = r3.src_id AND r3.rel_type = 'CALL_QUERY'
JOIN components q ON r3.dst_id = q.component_id AND (q.component_type = 'QUERY' OR q.component_type LIKE 'SQL_%')
-- 결과: 7개 체인 확인됨
```

### 3. 현재 api_chain_query 구조
```sql
SELECT 
    ROW_NUMBER() OVER (ORDER BY frontend.component_name, api.component_name, m.component_name, q.component_name) as chain_id,
    '' as jsp_file,
    api.component_name as api_entry,
    frontend.component_name as virtual_endpoint,
    f.file_name as class_name,
    m.component_name as method_name,
    xml_file.file_name as xml_file,
    q.component_name as query_id,
    q.component_type as query_type,
    '' as related_tables
FROM components frontend
JOIN relationships r1 ON frontend.component_id = r1.src_id AND r1.rel_type = 'CALL_API_F2B'
JOIN components api ON r1.dst_id = api.component_id
JOIN relationships r2 ON api.component_id = r2.src_id AND r2.rel_type = 'CALL_METHOD'
JOIN components m ON r2.dst_id = m.component_id AND m.component_type = 'METHOD'
JOIN files f ON m.file_id = f.file_id
JOIN relationships r3 ON m.component_id = r3.src_id AND r3.rel_type = 'CALL_QUERY'
JOIN components q ON r3.dst_id = q.component_id AND (q.component_type = 'QUERY' OR q.component_type LIKE 'SQL_%')
JOIN files xml_file ON q.file_id = xml_file.file_id
JOIN projects p ON frontend.project_id = p.project_id
WHERE p.project_name = ? 
  AND frontend.component_type = 'FRONTEND_API'
  AND api.component_type = 'API_ENTRY'
  AND frontend.del_yn = 'N'
  AND api.del_yn = 'N'
  AND m.del_yn = 'N'
  AND q.del_yn = 'N'
```

### 4. UNION ALL 구조
```sql
{method_chain_query}
UNION ALL
{sql_chain_query}  
UNION ALL
{api_chain_query}
ORDER BY method_name, class_name
```

## 예상되는 문제점들

### 1. UNION ALL 컬럼 구조 불일치
- `method_chain_query`와 `sql_chain_query`의 컬럼 구조와 `api_chain_query`의 컬럼 구조가 다를 수 있음
- 특히 `related_tables` 컬럼에서 `GROUP_CONCAT` vs 빈 문자열 차이

### 2. ORDER BY 정렬 문제
- `ORDER BY method_name, class_name`으로 인해 api_chain_query 결과가 뒤로 밀려날 수 있음
- api_chain_query의 method_name이 다른 쿼리들과 다른 패턴을 가질 수 있음

### 3. 데이터 처리 로직 문제
- `callchain_report_generator.py`의 데이터 정제 과정에서 api_entry와 virtual_endpoint가 빈 문자열로 처리될 수 있음
- 접두사 제거 로직에서 예상과 다른 결과가 나올 수 있음

### 4. GROUP BY 제거로 인한 중복 문제
- api_chain_query에서 GROUP BY를 제거했는데, 이로 인해 중복 데이터가 발생할 수 있음
- UNION ALL에서 중복 제거가 제대로 되지 않을 수 있음

## 질문사항

1. **UNION ALL 컬럼 구조**: 세 쿼리의 컬럼 구조가 정확히 일치하는지 확인이 필요합니다. 특히 `related_tables` 컬럼의 데이터 타입과 내용이 일치하는지요?

2. **ORDER BY 영향**: `ORDER BY method_name, class_name`이 api_chain_query 결과를 뒤로 밀어내는지 확인이 필요합니다. api_chain_query만 단독으로 실행했을 때는 7개 결과가 나오는데 UNION ALL에서는 보이지 않습니다.

3. **데이터 처리 로직**: `callchain_report_generator.py`의 285-300번 라인에서 api_entry와 virtual_endpoint 처리 로직이 올바르게 작동하는지 확인이 필요합니다.

4. **GROUP BY 복원**: api_chain_query에서 GROUP BY를 제거했는데, 이로 인해 중복 데이터나 예상치 못한 결과가 발생할 수 있습니다. GROUP BY를 복원하되 다른 방식으로 수정해야 할까요?

5. **프로젝트 필터링**: `p.project_name = ?` 조건이 올바르게 적용되고 있는지 확인이 필요합니다.

## 해결 방향 제안

1. **단계별 디버깅**: UNION ALL을 제거하고 api_chain_query만 단독으로 실행해서 결과 확인
2. **컬럼 구조 통일**: 세 쿼리의 컬럼 구조를 정확히 일치시키기
3. **ORDER BY 수정**: api_chain_query 결과가 보이도록 정렬 순서 조정
4. **데이터 처리 로직 검증**: api_entry와 virtual_endpoint 처리 로직 단계별 확인

## 관련 파일
- `CreateMetaDb/reports/callchain_report_generator.py` (라인 224-253)
- `CreateMetaDb/projects/sampleSrc/metadata.db`
- 생성된 리포트: `sampleSrc_CallChainReport_20250915_234612.html`
