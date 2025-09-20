# 연관관계 도출 최종 개발 계획서 (v_final)

## 1. 최종 목표 및 핵심 원칙

### 1.1. 최종 목표

- **유일 목표**: `relationships` 테이블에 `프론트엔드 → DB 테이블/컬럼` 까지 이어지는 모든 연관관계를 **누락 없이** 저장한다.
- **핵심 결과물**: 모든 연관관계 데이터가 저장된 `metadata.db` 파일.

### 1.2. 핵심 원칙

1.  **탐색 우선 (Recall > Precision)**: 잘못된 연결이 일부 포함되더라도, 놓치는 연결이 없도록 모든 가능성을 탐지한다.
2.  **단순한 규칙과 패턴**: 복잡한 AST 파싱 대신, 정규식, 명명 규칙, 키워드 검색 등 가볍고 빠른 규칙 기반으로 분석한다.
3.  **역할 분리 (Parser-Builder 패턴)**: **파서(Parser)**는 각 파일에서 연관관계의 '단서'만 추출하고, 모든 분석이 끝난 후 **빌더(Builder)**가 이 단서들을 종합하여 최종 관계를 설정한다. 이를 통해 분석 순서에 상관없이 일관된 결과를 보장한다.

---

## 2. 소스 코드 레벨 상세 개발 계획

### **Phase 1: 기반 구축 (DB 유틸리티 강화)**

- **목표**: `relationships` 테이블에 데이터를 저장하고, 관계 설정에 필요한 컴포넌트 ID를 효율적으로 조회하는 함수를 구현한다.

#### **1.1. `util/database_utils.py` 수정**

- **`insert_relationship` 함수 수정/추가**
  - **설명**: `relationships` 테이블에 `src_id`, `dst_id`, `rel_type`을 받아 관계를 저장한다. `UNIQUE` 제약조건을 활용하여 중복 저장을 방지한다.
  - **코드**:
    ```python
    # util/database_utils.py 내 DatabaseUtils 클래스
    def insert_relationship(self, src_id: int, dst_id: int, rel_type: str):
        """ relationships 테이블에 연관관계를 저장합니다. (중복 시 무시) """
        if src_id is None or dst_id is None:
            app_logger.warning(f"소스(src) 또는 타겟(dst) ID가 없어 관계 저장을 건너뜁니다: {rel_type}")
            return

        # 기존 relationships 테이블 스키마 활용 (confidence 등은 기본값 사용)
        sql = """
            INSERT OR IGNORE INTO relationships (src_id, dst_id, rel_type, confidence, has_error, del_yn)
            VALUES (?, ?, ?, 1.0, 'N', 'N')
        """
        self.execute_update(sql, (src_id, dst_id, rel_type))
    ```

- **`find_component_id` 함수 수정/추가**
  - **설명**: 관계 설정 시 필요한 컴포넌트 ID를 이름, 타입, 파일 ID 등 다양한 조건으로 빠르게 조회한다.
  - **코드**:
    ```python
    # util/database_utils.py 내 DatabaseUtils 클래스
    def find_component_id(self, project_id: int, component_name: str, component_type: str = None, file_id: int = None) -> Optional[int]:
        """이름, 타입, 파일 ID로 컴포넌트 ID를 찾습니다."""
        query = "SELECT component_id FROM components WHERE project_id = ? AND component_name = ? AND del_yn = 'N'"
        params = [project_id, component_name]
        if component_type:
            query += " AND component_type = ?"
            params.append(component_type)
        if file_id:
            query += " AND file_id = ?"
            params.append(file_id)
        query += " LIMIT 1"
        
        result = self.execute_query(query, tuple(params))
        return result[0]['component_id'] if result else None
    ```

### **Phase 2: 프론트엔드 → API URL 관계 단서 추출**

- **목표**: 모든 종류의 프론트엔드 파일(`jsp`, `jsx`, `vue`, `tsx`)에서 API 호출 URL을 추출하여 '단서'를 수집한다.

#### **2.1. `parser/jsp_parser.py` (및 신규 프론트엔드 파서) 수정**

- **설명**: `parse` 메소드가 파일 내용을 분석하여 API 호출 URL과 해당 코드의 라인 번호를 찾아내고, 그 결과를 딕셔너리 리스트 형태로 반환하도록 수정한다. 이 데이터는 나중에 `Builder`가 사용한다.
- **코드 (예시: `jsp_parser.py`)**:
  ```python
  # parser/jsp_parser.py 내 JspParser 클래스
  def parse(self, file_path, content):
      api_calls = []
      # SampleSrc에 존재하는 모든 종류의 API 호출 패턴 추가
      api_patterns = [
          r'axios\.get(["\\]?)(.*?)[\"\\]?$',      # axios.get('/api/url')
          r'axios\.post(["\\]?)(.*?)[\"\\]?$',     # axios.post('/api/url')
          r'fetch(["\\]?)(.*?)[\"\\]?$',          # fetch('/api/url')
          r'url\s*:\s*["\\]?(.*?)[\"\\]?'         # $.ajax({ url: '/api/url' })
      ]
      for pattern in api_patterns:
          for match in re.finditer(pattern, content):
              url = match.group(1)
              line_number = content[:match.start()].count('\n') + 1
              if not url.startswith('http'):
                  api_calls.append({
                      'type': 'API_CALL', # 단서의 종류
                      'source_file_path': file_path,
                      'api_url': url.strip(),
                      'line': line_number
                  })
      return api_calls # 추출한 단서 리스트만 반환
  ```

### **Phase 3: API URL → Controller Method 관계 단서 추출**

- **목표**: Spring Controller 파일에서 URL과 이를 처리하는 메소드를 매핑하는 '단서'를 추출한다.

#### **3.1. `parser/java_parser.py` 수정**

- **설명**: `parse` 메소드 내에 Controller를 식별하는 로직을 추가한다. `@RequestMapping`, `@GetMapping` 등을 분석하여 URL과 메소드명 정보를 추출하고, `Builder`가 사용할 수 있는 형태로 반환한다.
- **코드**:
  ```python
  # parser/java_parser.py 내 JavaParser 클래스
  def parse(self, file_path, content):
      # ... 기존 클래스/메소드 분석 로직 ...
      extracted_data = [] # 기존 분석 결과에 추가

      if '@RestController' in content or '@Controller' in content:
          class_name = self._find_class_for_method(content, content.find('@Controller'))
          base_url_match = re.search(r'@RequestMappingackpack"(.*?)"\)', content)
          base_url = base_url_match.group(1) if base_url_match else ''

          method_pattern = r'@(Get|Post|Put|Delete)Mapping\("(.*?)"\)[\s\S]*?(?:public|private|protected)[\s\S]*?(\w+)\s*\([^)]*\)'
          for match in re.finditer(method_pattern, content):
              http_method, method_url, method_name = match.groups()
              full_url = (base_url + method_url).replace('//', '/')
              extracted_data.append({
                  'type': 'API_IMPLEMENTATION', # 단서의 종류
                  'api_url': full_url.strip(),
                  'class_name': class_name,
                  'method_name': method_name
              })
      # ...
      return extracted_data # 다른 분석 결과와 함께 반환
  ```

### **Phase 4: Method → Query → Table/Join 관계 단서 추출**

- **목표**: Java와 XML 파일에서 SQL 쿼리를 찾아내고, 쿼리가 어떤 테이블을 사용하고 어떻게 조인하는지에 대한 '단서'를 추출한다.

#### **4.1. `parser/xml_parser.py` 수정**

- **설명**: MyBatis XML을 분석하여 `namespace`와 각 쿼리(`select`, `insert` 등)의 `id`, 그리고 쿼리 본문(`sql_content`)을 추출한다. 
- **코드**:
  ```python
  # parser/xml_parser.py 내 XmlParser 클래스
  def parse(self, file_path, content):
      # ...
      extracted_data = []
      namespace_match = re.search(r'<mapper\s+namespace="([^"]+)">', content)
      if namespace_match:
          namespace = namespace_match.group(1)
          query_tags = re.findall(r'<(select|insert|update|delete)\s+id="([^"]+)">([\s\S]*?)</\1>', content)
          for tag, query_id, sql_content in query_tags:
              # 테이블 및 조인 분석
              tables = re.findall(r'FROM\s+(\w+)', sql_content, re.IGNORECASE)
              joins = re.findall(r'JOIN\s+(\w+)', sql_content, re.IGNORECASE)
              join_conditions = re.findall(r'ON\s+(.*?)(?:WHERE|GROUP BY|ORDER BY|;)', sql_content, re.IGNORECASE | re.DOTALL)

              extracted_data.append({
                  'type': 'QUERY_DEFINITION',
                  'namespace': namespace,
                  'query_id': query_id,
                  'sql_content': sql_content,
                  'used_tables': list(set(tables + joins)),
                  'join_conditions': join_conditions
              })
      return extracted_data
  ```

#### **4.2. `parser/java_parser.py` 수정**

- **설명**: Java 파일 내에서 `sqlSession.selectList(