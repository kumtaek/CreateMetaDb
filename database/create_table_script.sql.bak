------------------------------------------------------------------------------------------------------------------------
-- 프로젝트 메타데이터 (기본 정보만)
CREATE TABLE IF NOT EXISTS projects (
    project_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name VARCHAR(100) NOT NULL,
    project_path VARCHAR(500) NOT NULL,
    hash_value VARCHAR(64),                        -- 변경 감지용
    created_at DATETIME DEFAULT (datetime('now', '+9 hours')),
    updated_at DATETIME DEFAULT (datetime('now', '+9 hours')),
    del_yn CHAR(1) DEFAULT 'N',                    -- 삭제 여부 (Y/N) - COALESCE(UPPER(DEL_YN),'N') = 'N'
    total_files INTEGER DEFAULT 0
);
CREATE UNIQUE INDEX ix_projects_01 ON projects (project_name, project_path);

-- 데이터베이스 테이블 정보
CREATE TABLE IF NOT EXISTS tables (
    table_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    component_id INTEGER,
    table_name VARCHAR(100) NOT NULL,
    table_owner VARCHAR(50) NOT NULL,
    table_comments TEXT,                           -- 추가된 테이블 코멘트 필드
    has_error CHAR(1) DEFAULT 'N',                 -- 오류 여부 (Y/N)
    error_message TEXT,                            -- 오류 메시지
    hash_value VARCHAR(64) NOT NULL,                        -- 변경 감지용
    created_at DATETIME DEFAULT (datetime('now', '+9 hours')),
    updated_at DATETIME DEFAULT (datetime('now', '+9 hours')),
    del_yn CHAR(1) DEFAULT 'N',                    -- 삭제 여부 (Y/N) - COALESCE(UPPER(DEL_YN),'N') = 'N'
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
    FOREIGN KEY (component_id) REFERENCES components(component_id)
);
CREATE UNIQUE INDEX ix_tables_01 ON tables (table_name, table_owner, project_id);

-- 데이터베이스 컬럼 정보
CREATE TABLE IF NOT EXISTS columns (
    column_id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_id INTEGER NOT NULL,
    component_id INTEGER,                               -- 컴포넌트 ID (COLUMN 타입 컴포넌트와 연결)
    column_name VARCHAR(100) NOT NULL,
    data_type VARCHAR(50),
    data_length INTEGER,
    nullable CHAR(1) DEFAULT 'Y',
    column_comments TEXT,
    position_pk INTEGER,                                    -- PK 순번 (null이면 PK 아님)
    data_default TEXT,                                   -- 기본값 - CSV의 DATA_DEFAULT 필드
    owner VARCHAR(50),                                   -- 소유자 - CSV의 OWNER 필드
    has_error CHAR(1) DEFAULT 'N',                 -- 오류 여부 (Y/N)
    error_message TEXT,                            -- 오류 메시지
    hash_value VARCHAR(64) NOT NULL,                        -- 변경 감지용
    created_at DATETIME DEFAULT (datetime('now', '+9 hours')),
    updated_at DATETIME DEFAULT (datetime('now', '+9 hours')),
    del_yn CHAR(1) DEFAULT 'N',                    -- 삭제 여부 (Y/N) - COALESCE(UPPER(DEL_YN),'N') = 'N'
    FOREIGN KEY (table_id) REFERENCES tables(table_id),
    FOREIGN KEY (component_id) REFERENCES components(component_id)
);
CREATE UNIQUE INDEX ix_columns_01 ON columns (table_id, column_name);

------------------------------------------------------------------------------------------------------------------------
-- 파일
CREATE TABLE IF NOT EXISTS files (
    file_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    file_path VARCHAR(500) NOT NULL,               -- 상대경로
    file_name VARCHAR(200) NOT NULL,
    file_type VARCHAR(20) NOT NULL,                         -- java, jsp, sql, xml
    has_error CHAR(1) DEFAULT 'N',                 -- 오류 여부 (Y/N)
    error_message TEXT,                            -- 오류 메시지
    hash_value VARCHAR(64) NOT NULL,                        -- 변경 감지용
    created_at DATETIME DEFAULT (datetime('now', '+9 hours')),
    updated_at DATETIME DEFAULT (datetime('now', '+9 hours')),
    del_yn CHAR(1) DEFAULT 'N',                    -- 삭제 여부 (Y/N) - COALESCE(UPPER(DEL_YN),'N') = 'N'
    line_count INTEGER,
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);
CREATE UNIQUE INDEX ix_files_01 ON files (file_name, file_path, project_id);

-- 1. classes 테이블 생성
CREATE TABLE IF NOT EXISTS classes (
    class_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    file_id INTEGER NOT NULL,
    class_name VARCHAR(200) NOT NULL,
    parent_class_id INTEGER, -- ★ 상속/구현 부모 class
    -- ★ package_name은 file_path에서 추출하므로 별도 컬럼 불필요
    line_start INTEGER,                            -- 시작 라인
    line_end INTEGER,                              -- 종료 라인
    has_error CHAR(1) DEFAULT 'N',                 -- 오류 여부 (Y/N)
    error_message TEXT,                            -- 오류 메시지
    hash_value VARCHAR(64) NOT NULL,                        -- 변경 감지용
    created_at DATETIME DEFAULT (datetime('now', '+9 hours')),
    updated_at DATETIME DEFAULT (datetime('now', '+9 hours')),
    del_yn CHAR(1) DEFAULT 'N',                    -- 삭제 여부 (Y/N)
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
    FOREIGN KEY (file_id) REFERENCES files(file_id)
);
CREATE UNIQUE INDEX ix_classes_01 ON classes (class_name, file_id, project_id);
CREATE INDEX ix_classes_02 ON classes (parent_class_id);

-- 코드 구성 요소 (클래스, 메서드 등의 기본 정보만)
CREATE TABLE IF NOT EXISTS components (
    component_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    file_id INTEGER NOT NULL,
    component_name VARCHAR(200) NOT NULL,
    component_type VARCHAR(20) NOT NULL,        
    -- ★ files.file_path로 대체 -> package_name VARCHAR(500),
    parent_id INTEGER, -- ★ 부모 컴포넌트/CLASS ID (COLUMN일떄는 TABLE의 compoennt_id, METHOD일때는 classes의 class_Id)
    layer VARCHAR(30),                             
    line_start INTEGER,                            -- 시작 라인
    line_end INTEGER,                              -- 종료 라인
    has_error CHAR(1) DEFAULT 'N',                 -- 오류 여부 (Y/N)
    error_message TEXT,                            -- 오류 메시지
    hash_value VARCHAR(64) NOT NULL,                        -- 변경 감지용
    created_at DATETIME DEFAULT (datetime('now', '+9 hours')),
    updated_at DATETIME DEFAULT (datetime('now', '+9 hours')),
    del_yn CHAR(1) DEFAULT 'N',                    -- 삭제 여부 (Y/N) - COALESCE(UPPER(DEL_YN),'N') = 'N'
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
    FOREIGN KEY (file_id) REFERENCES files(file_id)
);
CREATE UNIQUE INDEX ix_components_01 ON components (component_name, file_id, project_id);
CREATE INDEX ix_components_parent_id ON components (parent_id);

-- 통합 관계 정보 (모든 관계를 통합 관리)
CREATE TABLE IF NOT EXISTS relationships (
    relationship_id INTEGER PRIMARY KEY AUTOINCREMENT,
    src_id INTEGER NOT NULL,                       -- 소스 component_id
    dst_id INTEGER NOT NULL,                       -- 대상 component_id
    rel_type VARCHAR(30) NOT NULL,                
    is_conditional CHAR(1) Default 'N',
    condition_expression VARCHAR(1024),
    confidence FLOAT DEFAULT 1.0,
    has_error CHAR(1) DEFAULT 'N',                 -- 오류 여부 (Y/N)
    error_message TEXT,                            -- 오류 메시지
    created_at DATETIME DEFAULT (datetime('now', '+9 hours')),
    updated_at DATETIME DEFAULT (datetime('now', '+9 hours')),
    del_yn CHAR(1) DEFAULT 'N',                    -- 삭제 여부 (Y/N) - COALESCE(UPPER(DEL_YN),'N') = 'N'
    CHECK (src_id != dst_id)
);
CREATE UNIQUE INDEX ix_relationships_01 ON relationships (src_id, dst_id, rel_type);

-- 데이터베이스 최적화 설정
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = 10000;
PRAGMA temp_store = MEMORY;
PRAGMA foreign_keys = ON;