/* =======================================================================
   메타데이터베이스 스키마 정의서 (UTF-8, 상세 설명)

   0. 목적
   - 목적: 프로젝트/소스코드/DB 스키마 정보를 "메타" 형태로 저장하여 분석하고,
           컴포넌트 간 관계(호출, 사용, 의존)를 자동/수동으로 ERD/호출체인 리포트에 활용.
   - 범위: 백엔드/프론트엔드/메서드/SQL/API_URL 등등 components에 저장하여,
           relationships로 연결됨. 컨트롤러/서블릿은 같은 파일에 저장.
   - 특징:
     (1) 소스 분석 결과 저장된 스키마     (2) 관계/컴포넌트 정보 저장
     (3) 백엔드/프론트엔드/DB를 하나의 통합 DB로 관리 (특히 API_URL)

   1. 핵심 구조
   - components: 코드/SQL/API 등등 "컴포넌트"를 의미하는 범용 테이블
                 component_type으로 구분을 구분(METHOD/CLASS/API_URL/SQL_SELECT...).
   - relationships: 컴포넌트 간 관계를 표현(CALL_METHOD, CALL_QUERY, USE_TABLE...).
   - files: 소스 파일 경로를 (file_path=디렉터리, file_name=파일명)로 나눠 저장
   - controller_api_map: 컨트롤러 어노테이션 정보를 정밀 매칭으로 API_URL↔METHOD 연결을 위한 보조 테이블
   - mapper_map: MyBatis namespace+id 와 SQL 컴포넌트 연결을 위한 보조 테이블

   2. API_URL 표기 방식 (중요)
   - 표시명(component_name): "GET:selectUser" 형태(사람이 보기 좋은).
   - 실제 식별(identity): build_api_identity_key(HTTP+URL) 의 해시(hash_value)로 식별
     백엔드/프론트엔드가 동일 식별이므로 동일(HTTP,URL) API는 하나로 합쳐짐

   3. 관계(rel_type) 종류 정의
   - CALL_API: JSP/프론트엔드 컴포넌트 → API_URL
   - CALL_METHOD: API_URL → METHOD, METHOD → METHOD
   - CALL_QUERY: METHOD → SQL_xxx
   - USE_TABLE: SQL_xxx → TABLE

   4. 개발/운영 시 주의사항
   - 모든 DDL은 SQLite 방식 준수. 실제 DB 사용 시 인코딩 문제 주의.
   - 기본 키 생성 방식(해시/대소문자/길이/파일)은 프로젝트별로 다름.
   - 에러 발생 시 컴포넌트/관계에서 에러 플래그 및 에러 메시지 저장.

   ======================================================================= */

/* -----------------------------------------------------------------------
   1) 프로젝트/파일 기본 테이블   ----------------------------------------------------------------------- */
CREATE TABLE IF NOT EXISTS projects (
    project_id    INTEGER PRIMARY KEY AUTOINCREMENT, -- 프로젝트 고유 ID
    project_name  VARCHAR(100) NOT NULL,             -- 프로젝트명 (예: sampleSrc)
    project_path  VARCHAR(500) NOT NULL,             -- 프로젝트 루트 경로(절대/상대)
    created_at    DATETIME DEFAULT (datetime('now', '+9 hours')),
    updated_at    DATETIME DEFAULT (datetime('now', '+9 hours')),
    del_yn        CHAR(1)  DEFAULT 'N'               -- 삭제 여부
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_projects_01 ON projects (project_name, project_path);

/* 파일 메타: 실제 파일은 (디렉터리 경로,file_name)로 나눠 저장 */
CREATE TABLE IF NOT EXISTS files (
    file_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id  INTEGER NOT NULL,                   -- 참조: projects.project_id
    file_path   VARCHAR(1000) NOT NULL,             -- 디렉터리 경로(Unix 방식으로, 예: src/main/java/...)
    file_name   VARCHAR(300)  NOT NULL,             -- 파일명
    file_type   VARCHAR(50)   NOT NULL,             -- JAVA/XML/JSP/JS/TS/CSV/HTML 등
    line_count  INTEGER DEFAULT 0,                  -- 라인 수 (생성)
    hash_value  VARCHAR(64),                        -- 파일 내용 해시(생성)
    frameworks  VARCHAR(200),                       -- 프레임워크 정보(생성, 예: spring,mybatis)
    created_at  DATETIME DEFAULT (datetime('now', '+9 hours')),
    updated_at  DATETIME DEFAULT (datetime('now', '+9 hours')),
    del_yn      CHAR(1)  DEFAULT 'N',
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);
CREATE INDEX IF NOT EXISTS ix_files_01 ON files (project_id, file_path, file_name);

/* -----------------------------------------------------------------------
   2) DB 스키마 정보 (TABLE/COLUMN)
   - 데이터베이스에서 직접 생성된DB 정보는 별도 CSV로 존재
   - components와 병행하여 사용하거나, 필요 시 별도 저장
   ----------------------------------------------------------------------- */
CREATE TABLE IF NOT EXISTS tables (
    table_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id    INTEGER NOT NULL,
    component_id  INTEGER,                           -- 참조: components.component_id (TABLE 참조)
    table_name    VARCHAR(100) NOT NULL,             -- 테이블명
    table_owner   VARCHAR(50)  NOT NULL,             -- 스키마 소유자(예: HR, SCOTT)
    table_comments TEXT,                             -- 설명/주석(생성)
    hash_value    VARCHAR(64) NOT NULL,
    created_at    DATETIME DEFAULT (datetime('now', '+9 hours')),
    updated_at    DATETIME DEFAULT (datetime('now', '+9 hours')),
    del_yn        CHAR(1) DEFAULT 'N',
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_tables_01 ON tables (table_name, table_owner, project_id);

CREATE TABLE IF NOT EXISTS columns (
    column_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    table_id      INTEGER NOT NULL,                   -- 참조: tables.table_id
    component_id  INTEGER,                            -- 참조: components.component_id (COLUMN 참조)
    column_name   VARCHAR(100) NOT NULL,
    data_type     VARCHAR(50),                        -- 데이터 타입(예: VARCHAR2, NUMBER)
    data_length   INTEGER,                            -- 길이(예: VARCHAR2(50) 에서 50)
    nullable      CHAR(1) DEFAULT 'Y',                -- Y 허용 / N 필수
    column_comments TEXT,
    position_pk   INTEGER,                            -- PK 순서(생성)
    data_default  TEXT,
    owner         VARCHAR(50),
    hash_value    VARCHAR(64) NOT NULL,
    created_at    DATETIME DEFAULT (datetime('now', '+9 hours')),
    updated_at    DATETIME DEFAULT (datetime('now', '+9 hours')),
    del_yn        CHAR(1) DEFAULT 'N',
    FOREIGN KEY (table_id) REFERENCES tables(table_id)
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_columns_01 ON columns (table_id, column_name);

/* -----------------------------------------------------------------------
   3) 백엔드 컴포넌트/관계(코드/SQL/API 등)
   ----------------------------------------------------------------------- */
CREATE TABLE IF NOT EXISTS classes (
    class_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id     INTEGER NOT NULL,
    file_id        INTEGER NOT NULL,
    parent_class_id INTEGER,                          -- 상속/구현 관계(생성)
    class_name     VARCHAR(200) NOT NULL,
    hash_value     VARCHAR(64) NOT NULL,
    created_at     DATETIME DEFAULT (datetime('now', '+9 hours')),
    updated_at     DATETIME DEFAULT (datetime('now', '+9 hours')),
    del_yn         CHAR(1) DEFAULT 'N',
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
    FOREIGN KEY (file_id)    REFERENCES files(file_id)
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_classes_01 ON classes (class_name, file_id, project_id);
CREATE INDEX IF NOT EXISTS ix_classes_02 ON classes (parent_class_id);

/* 모든 컴포넌트(METHOD/CLASS/API_URL/SQL_SELECT 등등을 저장하는 범용 테이블*/
CREATE TABLE IF NOT EXISTS components (
    component_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER NOT NULL,
    file_id         INTEGER NOT NULL,                -- 소속 파일
    component_name  VARCHAR(500) NOT NULL,           -- 표시명 : 예: GET:selectUser, findUsers 등.  Mybatis는 namespace.query_id를 표현함(com.example.user.UserMapper.selectById)
    component_type  VARCHAR(20)  NOT NULL,           -- 컴포넌트 유형(전체 나열)
                                                     --  - 코드 구조: CLASS, METHOD, JSP
                                                     --  - API     : API_URL
                                                     --  - SQL     : SQL_SELECT, SQL_INSERT, SQL_UPDATE, SQL_DELETE, SQL_MERGE
                                                     --             QUERY(동적/추정 SQL 보관 시 사용 가능)
                                                     --  - DB 개념 : TABLE, COLUMN (필요 시 병행 보관)
    parent_id       INTEGER,                         -- 부모(예: METHOD의 부모 CLASS, COLUMN의 소속 테이블의 Component_id)
    layer           VARCHAR(30),                     -- 계층(전체 나열, 선택)
                                                     --  - 코드: CONTROLLER, SERVICE, DAO, REPOSITORY, ENTITY
                                                     --  - 프런트: FRONTEND
                                                     --  - API 엔트리: API_ENTRY (API_URL에 사용)
    line_start      INTEGER,
    line_end        INTEGER,
    has_error       CHAR(1) DEFAULT 'N',
    error_message   TEXT,
    hash_value      VARCHAR(64) NOT NULL,              -- 내용/식별 해시(API_URL은 HTTP+URL 해시)
    created_at      DATETIME DEFAULT (datetime('now', '+9 hours')),
    updated_at      DATETIME DEFAULT (datetime('now', '+9 hours')),
    del_yn          CHAR(1) DEFAULT 'N',
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
    FOREIGN KEY (file_id)    REFERENCES files(file_id)
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_components_01 ON components (component_name, file_id, project_id);
CREATE INDEX IF NOT EXISTS ix_components_parent_id ON components (parent_id);

/* 컴포넌트 간 관계(호출/사용/의존 등) */
CREATE TABLE IF NOT EXISTS relationships (
    relationship_id INTEGER PRIMARY KEY AUTOINCREMENT,
    src_id          INTEGER NOT NULL,                 -- 시작 컴포넌트
    dst_id          INTEGER NOT NULL,                 -- 대상 컴포넌트
    rel_type        VARCHAR(50) NOT NULL,             -- 관계 종류
                                                     --  - CALL_API   : JSP/프론트엔드 → API_URL
                                                     --  - CALL_METHOD: API_URL → METHOD, METHOD → METHOD
                                                     --  - CALL_QUERY : METHOD → SQL_xxx
                                                     --  - USE_TABLE  : SQL_xxx → TABLE
    confidence      FLOAT DEFAULT 1.0,
    created_at      DATETIME DEFAULT (datetime('now', '+9 hours')),
    updated_at      DATETIME DEFAULT (datetime('now', '+9 hours')),
    del_yn          CHAR(1) DEFAULT 'N',
    CHECK (src_id != dst_id),
    FOREIGN KEY (src_id) REFERENCES components(component_id),
    FOREIGN KEY (dst_id) REFERENCES components(component_id)
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_relationships_01 ON relationships (src_id, dst_id, rel_type);

--/* -----------------------------------------------------------------------
--    4) 컨트롤러/서블릿 매핑 정보 (정밀 매칭)
--    ----------------------------------------------------------------------- */
-- /* 컨트롤러 어노테이션 정보(@GetMapping 등)를 통해 API↔METHOD 연결
--    - 백엔드에서 추출한 (http_method, url)을 저장.
--    - API_URL의 hash_value(HTTP+URL)와 동일 식별으로 정밀 매칭에 사용. */
-- CREATE TABLE IF NOT EXISTS controller_api_map (
--     project_id     INTEGER NOT NULL,
--     component_id   INTEGER NOT NULL,                   -- 메소드의 component_id
--     http_method    VARCHAR(10),                        -- GET/POST/...
--     url            TEXT,
--     hash_value     VARCHAR(64) NOT NULL,               -- HTTP+URL 조합 해시(API_URL과 동일 식별)
--     created_at     DATETIME DEFAULT (datetime('now', '+9 hours')),
--     del_yn         CHAR(1) DEFAULT 'N',
--     FOREIGN KEY (project_id) REFERENCES projects(project_id),
--     FOREIGN KEY (component_id) REFERENCES components(component_id)
-- );
-- CREATE UNIQUE INDEX IF NOT EXISTS ix_controller_api_map_01 ON controller_api_map (component_id, hash_value, project_id);
-- CREATE INDEX IF NOT EXISTS ix_controller_api_map_02 ON controller_api_map (hash_value);
