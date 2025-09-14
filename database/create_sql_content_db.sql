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

-- 정제된 SQL 내용 테이블
CREATE TABLE IF NOT EXISTS sql_contents (
    content_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    file_id INTEGER,
    component_id INTEGER,
    component_name VARCHAR(200),             -- 컴포넌트명
    sql_content_compressed BLOB NOT NULL,    -- gzip 압축된 정제된 SQL 내용
    query_type VARCHAR(20) NOT NULL,         -- 'SQL_SELECT', 'SQL_INSERT', 'SQL_UPDATE', 'SQL_DELETE', 'SQL_MERGE'
    file_path VARCHAR(500),                  -- 파일 경로
    file_name VARCHAR(200),                  -- 파일명
    line_start INTEGER,                      -- 시작 라인
    line_end INTEGER,                        -- 종료 라인
    hash_value VARCHAR(64),                  -- SQL 내용 해시값
    error_message TEXT,                      -- 오류 메시지 (있는 경우)
    created_at DATETIME DEFAULT (datetime('now', '+9 hours')),
    updated_at DATETIME DEFAULT (datetime('now', '+9 hours')),
    del_yn CHAR(1) DEFAULT 'N',
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);


-- 인덱스 생성
CREATE INDEX IF NOT EXISTS ix_sql_contents_01 ON sql_contents(project_id, created_at);
CREATE INDEX IF NOT EXISTS ix_sql_contents_02 ON sql_contents(query_type, created_at);
CREATE INDEX IF NOT EXISTS ix_sql_contents_03 ON sql_contents(file_path, created_at);
CREATE INDEX IF NOT EXISTS ix_sql_contents_04 ON sql_contents(component_name, created_at);
CREATE INDEX IF NOT EXISTS ix_sql_contents_05 ON sql_contents(hash_value);


-- 데이터베이스 최적화 설정
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = 10000;
PRAGMA temp_store = MEMORY;
PRAGMA foreign_keys = OFF;  -- 별도 데이터베이스이므로 외래키 제약조건 비활성화
