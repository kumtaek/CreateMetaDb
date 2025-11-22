/* =======================================================================
   ë©”í? ?°ì´?°ë² ?´ìŠ¤ ?¤í‚¤ë§?(UTF-8, ?ì„¸ ì£¼ì„)

   0. ê°œìš”
   - ëª©ì : ?„ë¡œ?íŠ¸???ŒìŠ¤/DB ?¤í‚¤ë§?ì½”ë“œ êµ¬ì¡°ë¥?"ë©”í?" ?•íƒœë¡??œì??”í•´ ?€?¥í•˜ê³?
           ì»´í¬?ŒíŠ¸ ê°?"ê´€ê³?(?¸ì¶œ, ?¬ìš©, ?˜ì¡´)ë¥?ì¶”ì /?œê°??ERD/?¸ì¶œì²´ì¸ ???˜ëŠ” ???œìš©.
   - ë²”ìœ„: ?Œì¼/?´ë˜??ë©”ì„œ??SQL/API_URL ????„“?€ ?”í‹°?°ë? componentsë¡??˜ìš©?˜ê³ ,
           relationshipsë¡??°ê²°?œë‹¤. ì»¨íŠ¸ë¡¤ëŸ¬/ë§¤í¼?€ ê°™ì? ?•ë? ë§¤í•‘?€ ë³´ì¡° ?Œì´ë¸”ì— ë³´ê?.
   - ?ì¹™:
     (1) ?½ê¸° ?¬ìš´ ?•ê·œ?”ëœ ?¤í‚¤ë§?     (2) ?…ì„œ??? ë‹ˆ???¸ë±??ê¸°ë°˜??ì¤‘ë³µ ë°©ì?
     (3) ?„ëŸ°??ë°±ì—”??DBë¥?ê°€ë¡œì?ë¥´ëŠ” ?¼ê????ë³„ ê·œì¹™(?¹íˆ API_URL)

   1. ?µì‹¬ ì»¨ì…‰
   - components: ì½”ë“œ/SQL/API ???¤ì–‘??"ì»´í¬?ŒíŠ¸"ë¥???ê³³ì— ?€?¥í•˜??ë²”ìš© ?Œì´ë¸?
                 component_type?¼ë¡œ ì¢…ë¥˜ë¥?êµ¬ë¶„(METHOD/CLASS/API_URL/SQL_SELECT...).
   - relationships: ì»´í¬?ŒíŠ¸ ê°?"ê´€ê³?ë¥??€??CALL_METHOD, CALL_QUERY, USE_TABLE...).
   - files: ë¬¼ë¦¬ ?Œì¼ ê²½ë¡œë¥?(file_path=?”ë ‰?°ë¦¬, file_name=?Œì¼ëª?ë¡?ë¶„ë¦¬ ?€??
   - controller_api_map: ì»¨íŠ¸ë¡¤ëŸ¬ ?´ë…¸?Œì´?˜ì„ ë°”íƒ•?¼ë¡œ API_URL?’METHOD ?•í™• ë§¤ì¹­???„í•œ ë³´ì¡° ?°ì´??
   - mapper_map: MyBatis namespace+id ??SQL ì»´í¬?ŒíŠ¸ ë§¤í•‘???„í•œ ë³´ì¡° ?°ì´??

   2. API_URL ?ë³„ ê·œì¹™(ì¤‘ìš”)
   - ?œì‹œëª?component_name): "GET:selectUser" ?•ì‹(?¬ëŒ ì¹œí™”??.
   - ?´ë? ?ë³„(identity): build_api_identity_key(HTTP+URL) ???´ì‹œ(hash_value)ë¡??€??
     ?„ëŸ°??ë°±ì—”???™ì¼ ê·œì¹™???°ë?ë¡??™ì¼(HTTP,URL) API???˜ë‚˜ë¡?ë³‘í•©??

   3. ê´€ê³?rel_type) ?œì? ?ˆì‹œ
   - CALL_API: JSP/?„ëŸ°??ì»´í¬?ŒíŠ¸ ??API_URL
   - CALL_METHOD: API_URL ??METHOD, METHOD ??METHOD
   - CALL_QUERY: METHOD ??SQL_xxx
   - USE_TABLE: SQL_xxx ??TABLE

   4. êµ¬í˜„/?±ëŠ¥ ?ì˜ ê³ ë ¤
   - ëª¨ë“  DDL?€ SQLite ë¬¸ë²• ê¸°ì?. ?¤ë¥¸ DB ?¬ìš© ???¸í™˜??ê³ ë ¤ ?„ìš”.
   - ì£¼ìš” ì¡°íšŒ ì»¬ëŸ¼(?´ì‹œ/?´ë¦„/? í˜•/?„ë¡œ?íŠ¸/?Œì¼)???¸ë±???œê³µ.
   - ?€?©ëŸ‰ ?„ë¡œ?íŠ¸??ê²½ìš° components/relationships???€??ë°°ì¹˜ ?…ì„œ??ê¶Œì¥.

   ======================================================================= */

/* -----------------------------------------------------------------------
   1) ?„ë¡œ?íŠ¸/?Œì¼ ë² ì´???Œì´ë¸?   ----------------------------------------------------------------------- */
CREATE TABLE IF NOT EXISTS projects (
    project_id    INTEGER PRIMARY KEY AUTOINCREMENT, -- ?„ë¡œ?íŠ¸ ê³ ìœ ??    project_name  VARCHAR(100) NOT NULL,             -- ?„ë¡œ?íŠ¸ëª?(?? sampleSrc)
    project_path  VARCHAR(500) NOT NULL,             -- ?„ë¡œ?íŠ¸ ë£¨íŠ¸ ê²½ë¡œ(?ë?/?ˆë?)
    hash_value    VARCHAR(64),                       -- ?„ë¡œ?íŠ¸ ?„ì²´ ?¤ëƒ…???´ì‹œ(? íƒ)
    created_at    DATETIME DEFAULT (datetime('now', '+9 hours')),
    updated_at    DATETIME DEFAULT (datetime('now', '+9 hours')),
    del_yn        CHAR(1)  DEFAULT 'N'               -- ?? œ ?Œë˜ê·?);
CREATE UNIQUE INDEX IF NOT EXISTS ix_projects_01 ON projects (project_name, project_path);

/* ?Œì¼ ë©”í?: ?¤ì œ ?Œì¼?€ (?”ë ‰?°ë¦¬ ê²½ë¡œ,file_name)ë¡?ë¶„ë¦¬ ?€??*/
CREATE TABLE IF NOT EXISTS files (
    file_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id  INTEGER NOT NULL,                   -- ì°¸ì¡°: projects.project_id
    file_path   VARCHAR(1000) NOT NULL,             -- ?”ë ‰?°ë¦¬ ê²½ë¡œ(Unix êµ¬ë¶„?? ?? src/main/java/...)
    file_name   VARCHAR(300)  NOT NULL,             -- ?Œì¼ëª?    file_type   VARCHAR(50)   NOT NULL,             -- JAVA/XML/JSP/JS/TS/CSV/HTML ??    line_count  INTEGER DEFAULT 0,                  -- ?¼ì¸ ??? íƒ)
    hash_value  VARCHAR(64),                        -- ?Œì¼ ?´ìš© ?´ì‹œ(? íƒ)
    frameworks  VARCHAR(200),                       -- ?Œì„œê°€ ê°ì????„ë ˆ?„ì›Œ??ëª©ë¡(? íƒ, ?? spring,mybatis)
    created_at  DATETIME DEFAULT (datetime('now', '+9 hours')),
    updated_at  DATETIME DEFAULT (datetime('now', '+9 hours')),
    del_yn      CHAR(1)  DEFAULT 'N',
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);
CREATE INDEX IF NOT EXISTS ix_files_01 ON files (project_id, file_path, file_name);

/* -----------------------------------------------------------------------
   2) DB ?¤í‚¤ë§?êµ¬ì¡° (TABLE/COLUMN)
   - ?ŒìŠ¤?ì„œ ??œ¼ë¡??ì„±??DB êµ¬ì¡° ?ëŠ” ?œê³µ??CSVë¡œë????ì¬
   - components?€ ?°ë™?????ˆìœ¼???„ìˆ˜???„ë‹˜
   ----------------------------------------------------------------------- */
CREATE TABLE IF NOT EXISTS tables (
    table_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id    INTEGER NOT NULL,
    component_id  INTEGER,                           -- ?€?? components.component_id (TABLE ?€??
    table_name    VARCHAR(100) NOT NULL,             -- ?Œì´ë¸”ëª…
    table_owner   VARCHAR(50)  NOT NULL,             -- ?¤í‚¤ë§??¤ë„ˆ(?? HR, SCOTT)
    table_comments TEXT,                             -- ?¤ëª…/ì£¼ì„(? íƒ)
    has_error     CHAR(1) DEFAULT 'N',
    error_message TEXT,
    hash_value    VARCHAR(64) NOT NULL,
    created_at    DATETIME DEFAULT (datetime('now', '+9 hours')),
    updated_at    DATETIME DEFAULT (datetime('now', '+9 hours')),
    del_yn        CHAR(1) DEFAULT 'N',
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_tables_01 ON tables (table_name, table_owner, project_id);

CREATE TABLE IF NOT EXISTS columns (
    column_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    table_id      INTEGER NOT NULL,                   -- ì°¸ì¡°: tables.table_id
    component_id  INTEGER,                            -- ?€?? components.component_id (COLUMN ?€??
    column_name   VARCHAR(100) NOT NULL,
    data_type     VARCHAR(50),                        -- ?°ì´???€???? VARCHAR2, NUMBER)
    data_length   INTEGER,                            -- ê¸¸ì´(?? VARCHAR2(50) ??50)
    nullable      CHAR(1) DEFAULT 'Y',                -- Y ?ˆìš© / N ë¶ˆê?
    column_comments TEXT,
    position_pk   INTEGER,                            -- PK ?œì„œ(? íƒ)
    data_default  TEXT,
    owner         VARCHAR(50),
    has_error     CHAR(1) DEFAULT 'N',
    error_message TEXT,
    hash_value    VARCHAR(64) NOT NULL,
    created_at    DATETIME DEFAULT (datetime('now', '+9 hours')),
    updated_at    DATETIME DEFAULT (datetime('now', '+9 hours')),
    del_yn        CHAR(1) DEFAULT 'N',
    FOREIGN KEY (table_id) REFERENCES tables(table_id)
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_columns_01 ON columns (table_id, column_name);

/* -----------------------------------------------------------------------
   3) ?´ë˜??ì»´í¬?ŒíŠ¸/ê´€ê³?(ì½”ë“œ/SQL/API ??
   ----------------------------------------------------------------------- */
CREATE TABLE IF NOT EXISTS classes (
    class_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id     INTEGER NOT NULL,
    file_id        INTEGER NOT NULL,
    parent_class_id INTEGER,                          -- ?ì†/?¬í•¨ ê´€ê³?? íƒ)
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

/* ëª¨ë“  ì»´í¬?ŒíŠ¸(METHOD/CLASS/API_URL/SQL_SELECT ??ë¥??˜ìš©?˜ëŠ” ë²”ìš© ?Œì´ë¸?*/
CREATE TABLE IF NOT EXISTS components (
    component_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER NOT NULL,
    file_id         INTEGER NOT NULL,                  -- ?„ì¹˜ ?Œì¼
    component_name  VARCHAR(200) NOT NULL,             -- ?œì‹œëª??? GET:selectUser, findUsers ??
    component_type  VARCHAR(20)  NOT NULL,             -- ÄÄÆ÷³ÍÆ® À¯Çü(ÀüÃ¼ ³ª¿­)
                                                     --  - ÄÚµå ±¸Á¶: CLASS, METHOD, JSP
                                                     --  - API     : API_URL
                                                     --  - SQL     : SQL_SELECT, SQL_INSERT, SQL_UPDATE, SQL_DELETE, SQL_MERGE
                                                     --             QUERY(µ¿Àû/ÃßÁ¤ SQL º¸°ü ½Ã »ç¿ë °¡´É)
                                                     --  - DB °³³ä : TABLE, COLUMN (ÇÊ¿ä ½Ã º´Çà º¸°ü)
    parent_id       INTEGER,                           -- ?Œì†(?? METHOD??ë¶€ëª?CLASS)
    layer           VARCHAR(30),                       -- °èÃş(ÀüÃ¼ ³ª¿­, ¼±ÅÃ)
                                                     --  - ÄÚµå: CONTROLLER, SERVICE, DAO, REPOSITORY, ENTITY
                                                     --  - ÇÁ·±Æ®: FRONTEND
                                                     --  - API ¿£Æ®¸®: API_ENTRY (API_URL¿¡ »ç¿ë)
    line_start      INTEGER,
    line_end        INTEGER,
    has_error       CHAR(1) DEFAULT 'N',
    error_message   TEXT,
    hash_value      VARCHAR(64) NOT NULL,              -- ?´ìš©/?ë³„ ?´ì‹œ(API_URL?€ HTTP+URL ?´ì‹œ)
    created_at      DATETIME DEFAULT (datetime('now', '+9 hours')),
    updated_at      DATETIME DEFAULT (datetime('now', '+9 hours')),
    del_yn          CHAR(1) DEFAULT 'N',
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
    FOREIGN KEY (file_id)    REFERENCES files(file_id)
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_components_01 ON components (component_name, file_id, project_id);
CREATE INDEX IF NOT EXISTS ix_components_parent_id ON components (parent_id);

/* ì»´í¬?ŒíŠ¸ ê°?ê´€ê³?(?¸ì¶œ/?˜ì¡´/?¬ìš© ?? */
CREATE TABLE IF NOT EXISTS relationships (
    relationship_id INTEGER PRIMARY KEY AUTOINCREMENT,
    src_id          INTEGER NOT NULL,                 -- ì¶œë°œ ì»´í¬?ŒíŠ¸
    dst_id          INTEGER NOT NULL,                 -- ?„ì°© ì»´í¬?ŒíŠ¸
    rel_type        VARCHAR(50) NOT NULL,             -- ê´€ê³?? í˜•
                                                     --  - CALL_API   : JSP/?„ë¡ ????API_URL
                                                     --  - CALL_METHOD: API_URL ??METHOD, METHOD ??METHOD
                                                     --  - CALL_QUERY : METHOD ??SQL_xxx
                                                     --  - USE_TABLE  : SQL_xxx ??TABLE
    confidence      FLOAT DEFAULT 1.0,
    has_error       CHAR(1) DEFAULT 'N',
    error_message   TEXT,
    created_at      DATETIME DEFAULT (datetime('now', '+9 hours')),
    updated_at      DATETIME DEFAULT (datetime('now', '+9 hours')),
    del_yn          CHAR(1) DEFAULT 'N',
    CHECK (src_id != dst_id),
    FOREIGN KEY (src_id) REFERENCES components(component_id),
    FOREIGN KEY (dst_id) REFERENCES components(component_id)
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_relationships_01 ON relationships (src_id, dst_id, rel_type);

/* -----------------------------------------------------------------------
   4) ì»¨íŠ¸ë¡¤ëŸ¬/ë§¤í¼ ë³´ì¡° ë§¤í•‘ (?•í™• ë§¤ì¹­??
   ----------------------------------------------------------------------- */
/* ì»¨íŠ¸ë¡¤ëŸ¬ ?´ë…¸?Œì´??@GetMapping ?? ê¸°ë°˜ API?’METHOD ë§¤í•‘
   - ?ŒìŠ¤?ì„œ ì¶”ì¶œ??(class_name, method_name, http_method, url)??ë³´ê?.
   - API_URL??identity_hash(HTTP+URL)?€ ?™ì¼ ê·œì¹™?¼ë¡œ ?€?¥í•˜???•í™• ë§¤ì¹­???¬ìš©. */
CREATE TABLE IF NOT EXISTS controller_api_map (
    map_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id     INTEGER NOT NULL,
    file_id        INTEGER,
    class_name     VARCHAR(200) NOT NULL,
    method_name    VARCHAR(200) NOT NULL,
    http_method    VARCHAR(10),                        -- GET/POST/...
    url            TEXT,
    identity_hash  VARCHAR(64),                        -- HTTP+URL ê¸°ë°˜ ?´ì‹œ(API_URLê³??™ì¼ ê·œì¹™)
    created_at     DATETIME DEFAULT (datetime('now', '+9 hours')),
    del_yn         CHAR(1) DEFAULT 'N',
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
    FOREIGN KEY (file_id)    REFERENCES files(file_id)
);
CREATE INDEX IF NOT EXISTS ix_controller_api_map_01 ON controller_api_map (project_id, identity_hash);
CREATE INDEX IF NOT EXISTS ix_controller_api_map_02 ON controller_api_map (project_id, class_name, method_name);

/* MyBatis: namespace + id ??SQL ì»´í¬?ŒíŠ¸(component_id)
   - XML mapper??namespace, ì¿¼ë¦¬ idë¥?SQL ì»´í¬?ŒíŠ¸(component_id)?€ ?°ê²°??ë³´ê?.
   - Java ?¸í„°?˜ì´??DAO??FQN.method?€ namespace.idë¥?ë§¤ì¹­??CALL_QUERY ?•ë? ?ì„±. */
CREATE TABLE IF NOT EXISTS mapper_map (
    map_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id       INTEGER NOT NULL,
    file_id          INTEGER,
    namespace        VARCHAR(500) NOT NULL,
    query_id         VARCHAR(200) NOT NULL,
    sql_component_id INTEGER NOT NULL,
    created_at       DATETIME DEFAULT (datetime('now', '+9 hours')),
    del_yn           CHAR(1) DEFAULT 'N',
    FOREIGN KEY (project_id)       REFERENCES projects(project_id),
    FOREIGN KEY (file_id)          REFERENCES files(file_id),
    FOREIGN KEY (sql_component_id) REFERENCES components(component_id)
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_mapper_map_01 ON mapper_map (project_id, namespace, query_id);

/* =======================================================================
   ?? (?„ìš” ??ì¶”ê? ë³´ì¡° ?Œì´ë¸??¸ë±?¤ëŠ” ?˜ë‹¨???•ì¥)
   ======================================================================= */

