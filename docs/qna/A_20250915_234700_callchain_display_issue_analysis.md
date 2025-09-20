# CallChain 리포트 FRONTEND_API/API_ENTRY 표시 문제 분석 답변서

## 문제 요약

CallChain 리포트 생성 시, 데이터베이스에는 `FRONTEND_API`와 `API_ENTRY` 관련 데이터가 존재함에도 불구하고 최종 리포트에서 해당 컬럼들이 비어있는 문제.

이는 `UNION ALL`로 결합되는 SQL 쿼리들 간의 구조적 불일치 및 `chain_id` 생성 방식의 오류로 인해 발생한 것으로 분석됩니다.

## 질문에 대한 상세 답변

1.  **UNION ALL 컬럼 구조는 일치하는가?**

    아니요, 결정적인 차이가 있습니다. `method_chain_query`와 `sql_chain_query`는 `related_tables` 컬럼을 `GROUP_CONCAT`을 포함한 서브쿼리로 생성합니다. 반면, `api_chain_query`는 해당 컬럼을 단순한 빈 문자열(`''`)로 정의합니다.
    
    두 결과 모두 텍스트 타입이라 SQL 구문 오류는 없지만, 이렇게 컬럼의 생성 방식이 다를 경우 데이터베이스 옵티마이저가 비효율적인 실행 계획을 수립하거나 예기치 않은 동작을 할 수 있습니다. 이것이 `api_chain_query`의 결과 7건이 `UNION ALL` 결합 시 누락되는 가장 유력한 원인입니다.

2.  **ORDER BY가 영향을 주는가?**

    `ORDER BY` 절 자체는 데이터를 누락시키지 않습니다. 하지만 더 근본적인 문제는 각 서브쿼리가 `ROW_NUMBER()`를 사용해 `chain_id`를 개별적으로 생성하여, 최종 결과셋에 중복된 `chain_id`가 포함된다는 점입니다. 이는 명백한 버그이며, 데이터 정렬 순서를 예측 불가능하게 만들고 리포트 UI에서 문제를 일으킬 수 있습니다. `chain_id`는 모든 데이터가 합쳐진 최종 결과에 대해 한 번만 생성되어야 합니다.

3.  **`callchain_report_generator.py`의 처리 로직은 올바른가?**

    네, 285-300번 라인의 파이썬 코드는 정상입니다. 해당 코드는 `API_ENTRY:` 와 `FRONTEND_API:` 같은 접두사를 제거하는 역할을 하며, 필드에 값이 있을 때만 동작합니다. 현재 문제는 SQL 조회 결과에서부터 값이 비어있기 때문에, 이 파이썬 로직은 문제의 원인이 아닙니다.

4.  **GROUP BY를 복원해야 하는가?**

    아니요, `GROUP BY`를 추가할 필요가 없습니다. `GROUP_CONCAT` 함수는 `related_tables` 컬럼을 위한 스칼라 서브쿼리(Scalar Subquery) 내에서 올바르게 사용되고 있으며, 이 방식은 외부 쿼리에 `GROUP BY`를 요구하지 않습니다.

5.  **프로젝트 필터링은 올바른가?**

    네, `p.project_name = ?` 필터는 올바르게 동작하고 있습니다. `api_chain_query`를 단독 실행 시 정상적으로 결과를 반환하므로, 필터링 조건은 문제가 없습니다.

## 해결 방안

문제 해결을 위해 `reports/callchain_report_generator.py` 파일의 SQL 쿼리를 다음과 같이 수정해야 합니다.

### 1. `api_chain_query`의 `related_tables` 컬럼 수정

`api_chain_query`가 다른 쿼리들과 동일한 방식으로 `related_tables`를 조회하도록 `'' as related_tables` 부분을 아래와 같이 서브쿼리로 교체합니다.

**기존 코드 (251 라인):**
```python
'' as related_tables
```

**수정 코드:**
```python
(
    SELECT GROUP_CONCAT(DISTINCT tbl.component_name)
    FROM relationships rel_query_table
    JOIN components tbl ON rel_query_table.dst_id = tbl.component_id AND tbl.component_type = 'TABLE'
    WHERE rel_query_table.src_id = q.component_id
) as related_tables
```

### 2. `chain_id` 생성 로직 수정

모든 서브쿼리(`method_chain_query`, `sql_chain_query`, `api_chain_query`)에서 `ROW_NUMBER() OVER (...) as chain_id,` 부분을 삭제합니다.

그리고 `generate_callchain_report` 함수의 최종 쿼리 실행 부분을 수정하여, `UNION ALL`로 합쳐진 전체 결과에 대해 `chain_id`를 생성하도록 변경합니다.

**기존 코드 (267-268 라인):**
```python
query = "\nUNION ALL\n".join(queries)
order_by_clause = "ORDER BY method_name, class_name, jsp_file, api_entry, virtual_endpoint"
query = f"SELECT * FROM ({query}) AS combined_query {order_by_clause}"
```

**수정 코드:**
```python
# 각 서브쿼리에서 ROW_NUMBER() 제거 후
query_part = "\nUNION ALL\n".join(queries)

# 정렬 순서 정의
order_by_clause = "ORDER BY method_name, class_name, jsp_file, api_entry, virtual_endpoint"

# 최종 쿼리: UNION ALL 결과에 대해 ROW_NUMBER() 적용
query = f"""
SELECT 
    ROW_NUMBER() OVER ({order_by_clause}) as chain_id,
    t.*
FROM ({query_part}) AS t
{order_by_clause}
"""
```
*주의: 위 코드 변경 시, `row[0]`부터 시작하는 인덱스 기반의 데이터 처리가 `chain_id` 추가로 인해 한 칸씩 밀릴 수 있습니다. `chain_id`를 `row[0]`으로 유지하고 나머지 데이터를 `row[1]`, `row[2]`... 로 처리하려면, `SELECT` 절의 순서를 `ROW_NUMBER() OVER (...) as chain_id, t.*` 와 같이 조정해야 합니다. 위 제안 코드는 이 순서를 따르고 있으므로, 기존 파이썬 로직의 인덱스(row[0], row[1]...)는 `chain_id`가 추가된 것을 감안하여 조정해야 할 수 있습니다.*

**권장되는 최종 파이썬 로직:**
인덱스 혼란을 피하기 위해, 데이터베이스 커서를 `dictionary cursor` 형태로 사용하여 `row['column_name']`과 같이 이름 기반으로 데이터에 접근하는 것이 더 안정적입니다.

## 요약

1.  `api_chain_query`의 `related_tables` 컬럼 생성 방식을 다른 쿼리들과 동일하게 맞춰줍니다.
2.  개별 쿼리에서 `ROW_NUMBER()`를 제거하고, `UNION ALL`로 합쳐진 최종 결과에 대해 `ROW_NUMBER()`를 적용하여 유일하고 순차적인 `chain_id`를 부여합니다.

위 두 가지 사항을 수정하면 `api_chain_query`의 결과가 정상적으로 포함되어 리포트에 `FRONTEND_API`와 `API_ENTRY` 정보가 올바르게 표시될 것입니다.
