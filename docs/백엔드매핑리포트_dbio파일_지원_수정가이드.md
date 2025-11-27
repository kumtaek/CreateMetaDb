# 백엔드 매핑 리포트 .dbio 파일 지원 수정 가이드

## 문제
- `.dbio` 파일이 백엔드 매핑 리포트에서 Java String으로 분류됨
- MyBatis XML로 분류되어야 함

## 수정 파일
`reports/backend_mapping_report_generator.py`

## 수정 위치
**Line 162-172** (약 167번 라인 근처)

### 수정 전
```python
# 파일 경로 기반 분류
lower_path = normalized_path.lower()
lower_file = (file_name or '').lower()
is_repository_ctx = 'repository' in lower_path or 'repository' in lower_file or 'repository' in component_name.lower()
is_java_file = lower_path.endswith('.java') or lower_file.endswith('.java')
if lower_path.endswith('.xml') or 'mybatis' in lower_path:
    categorized['MyBatis'].append(entry)
elif is_repository_ctx and (is_java_file or lower_file.endswith('.java')):
    categorized['JPA'].append(entry)
else:
    categorized['JavaString'].append(entry)
```

### 수정 후
```python
# 파일 경로 기반 분류
lower_path = normalized_path.lower()
lower_file = (file_name or '').lower()
is_repository_ctx = 'repository' in lower_path or 'repository' in lower_file or 'repository' in component_name.lower()
is_java_file = lower_path.endswith('.java') or lower_file.endswith('.java')

# MyBatis XML 파일 확장자: .xml, .dbio (운영 환경)
is_mybatis_file = (lower_path.endswith('.xml') or lower_path.endswith('.dbio') or 
                  lower_file.endswith('.xml') or lower_file.endswith('.dbio') or 
                  'mybatis' in lower_path)

if is_mybatis_file:
    categorized['MyBatis'].append(entry)
elif is_repository_ctx and (is_java_file or lower_file.endswith('.java')):
    categorized['JPA'].append(entry)
else:
    categorized['JavaString'].append(entry)
```

## 수정 내용
1. `is_mybatis_file` 변수 추가
2. `.xml`과 `.dbio` 확장자 모두 체크
3. 파일명(`lower_file`)과 경로(`lower_path`) 모두 확인

## 검증 방법
```bash
# 리포트 재생성
python create_report.py --project-name {project_name} --report-type backend

# 생성된 리포트 확인
# projects/{project_name}/report/BackendMappingReport_*.html 열기
# .dbio 파일이 "MyBatis SQL 매핑" 섹션에 있는지 확인
```

## 참고
- 이 수정은 `config/parser/xml_parser_config.yaml`의 `mybatis_file_extensions` 설정과 일관성을 유지합니다
- `.dbio` 확장자는 폐쇄망 운영 환경에서 사용되는 MyBatis XML 파일 확장자입니다
