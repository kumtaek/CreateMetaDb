-- SQL Content 전용 데이터베이스 스키마
-- 용도: 정제된 SQL 내용 압축 저장 및 분석용
-- 파일명: SqlContent.db

-- 프로젝트 정보 테이블
CREATE TABLE IF NOT EXISTS projects (
    project_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name VARCHAR(100) NOT NULL,
    project_path VARCHAR(500) NOT NULL,
    created_at DATETIME DEFAULT (datetime('now', '+9 hours')),
    updated_at DATETIME DEFAULT (datetime('now', '+9 hours')),
    del_yn CHAR(1) DEFAULT 'N'
);

-- 정제된 SQL 내용 테이블 (XML파싱 쿼리 + INFERRED쿼리 지원)
CREATE TABLE IF NOT EXISTS sql_contents (
    project_id INTEGER NOT NULL,
    file_id INTEGER NOT NULL,                         -- 파일 ID (XML파일 또는 Java파일)
    component_id INTEGER NOT NULL,                    -- 컴포넌트 ID (SQL_* 타입 또는 QUERY 타입)
    component_name VARCHAR(200) NOT NULL,             -- 컴포넌트명 (쿼리 ID)
    sql_content_compressed BLOB NOT NULL,    -- gzip 압축된 정제된 SQL 내용 (XML파싱결과 또는 Java소스에서 추출한 SQL)
    file_path VARCHAR(500) NOT NULL,                  -- 파일 경로 (XML파일 또는 Java파일)
    file_name VARCHAR(200) NOT NULL,                  -- 파일명 (XML파일 또는 Java파일)
    hash_value VARCHAR(64),                  -- SQL 내용 해시값
    created_at DATETIME DEFAULT (datetime('now', '+9 hours')),
    updated_at DATETIME DEFAULT (datetime('now', '+9 hours')),
    del_yn CHAR(1) DEFAULT 'N',
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

-- 인덱스 생성
CREATE UNIQUE INDEX IF NOT EXISTS ix_sql_contents_01 ON sql_contents(component_name, file_id, project_id);
CREATE INDEX IF NOT EXISTS ix_sql_contents_02 ON sql_contents(component_id);
CREATE INDEX IF NOT EXISTS ix_sql_contents_03 ON sql_contents(hash_value);
 