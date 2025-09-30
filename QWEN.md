# SourceAnalyzer - QWEN Context Documentation

## Project Overview

SourceAnalyzer is a comprehensive source code analysis tool that creates metadata databases for complex software projects. It analyzes multiple technology stacks including Java, Spring Framework, JSP, MyBatis, JPA, XML, SQL, and various frontend technologies (JSX, Vue, TypeScript, JavaScript, HTML, CSS) to build a complete model of code relationships, dependencies, and architecture.

The system follows a 7-stage processing pipeline that extracts and analyzes source code, database schemas, and API relationships to create a metadata database that can be used for architecture visualization, call chain analysis, ERD diagrams, and system understanding.

### Key Features

- **Multi-language Support**: Java, JSP, XML (MyBatis), SQL, JSX, Vue, TypeScript, JavaScript, HTML, CSS
- **Database Schema Integration**: CSV-based table/column metadata import and relationship mapping
- **API Call Chain Analysis**: Frontend to backend to database call tracking
- **Framework Detection**: Spring, MyBatis, JPA, jQuery, Axios, Fetch API, XMLHttpRequest
- **SQL Query Analysis**: MyBatis XML parsing with JOIN relationship extraction
- **Dynamic SQL Support**: StringBuilder and variable concatenation SQL extraction
- **Complete Relationship Mapping**: Methods to queries, queries to tables, frontend to backend
- **Consistency Validation**: Metadata database integrity checks

## Architecture & Processing Stages

The system follows a 7-stage pipeline that runs in a single transaction:

### 1. File Scanning (file_loading.py)
- Scans project directory recursively
- Filters files based on `target_source_config.yaml` include/exclude patterns
- Creates file metadata in `files` table with hash values for change detection

### 2. Database Structure Loading (file_loading.py) 
- Loads CSV files (ALL_TABLES.csv, ALL_TAB_COLUMNS.csv) into database
- Creates TABLE and COLUMN components in `components` table
- Establishes parent-child relationships between tables and columns

### 3. XML Analysis (xml_loading.py)
- Parses MyBatis XML files using dual-parser architecture (Enhanced + Fallback)
- Extracts SQL queries and creates SQL_* components
- Analyzes JOIN relationships (explicit and implicit)
- Handles complex dynamic SQL patterns with `<include>`, `<if>`, `<foreach>` tags

### 4. Java Analysis (java_loading.py)
- Parses Java classes and methods
- Extracts SQL queries from Java code (including StringBuilder concatenation)
- Creates CLASS and METHOD components
- Builds relationships between code elements

### 5. Backend API Analysis (backend_entry_loading.py)
- Identifies REST Controllers and API endpoints
- Creates API_URL components for Spring/Servlet endpoints
- Maps URL patterns to controller methods

### 6. Frontend Analysis (frontend_loading.py)
- Supports JSP, JSX, Vue, TS, JS, HTML files
- Detects API calls (jQuery, Axios, Fetch, XHR)
- Traces frontend to backend API connections
- Tracks frameworks and technology stack usage

### 7. Consistency Validation (consistency_validator.py)
- Validates foreign key constraints
- Checks for API_URL duplicates
- Ensures parent_id type consistency
- Reports data integrity issues

## Database Schema

The system uses SQLite databases with the following key tables:

- `projects`: Project metadata
- `files`: Source code files with paths and hashes  
- `tables`: Database table information
- `columns`: Database column information
- `classes`: Java class definitions
- `components`: Code components (METHOD, CLASS, SQL_SELECT, SQL_UPDATE, etc.)
- `relationships`: Relationships between components (CALL_METHOD, USE_TABLE, JOIN_EXPLICIT, etc.)

## Key Configuration Files

- `config/target_source_config.yaml`: File filtering rules, path mappings, supported file types
- `config/parser/mybatis_keyword.yaml`: MyBatis parsing rules  
- `config/parser/java_keyword.yaml`: Java parsing rules
- `config/logging.yaml`: Logging configuration

## Building and Running

### Prerequisites
- Python 3.8+
- SQLite 3

### Running the Analyzer

```bash
# Run with project name
python main.py <project_name>

# With options
python main.py <project_name> --clear-metadb --verbose --output-format html

# Show help
python main.py --help
```

### Project Structure Requirements

```
projects/
└── <project_name>/
    ├── db_schema/
    │   ├── ALL_TABLES.csv
    │   └── ALL_TAB_COLUMNS.csv
    └── src/
        ├── main/
        │   ├── java/
        │   └── resources/
        │       └── mapper/ (MyBatis XML files)
        └── webapp/ (for JSP files)
```

## Development Conventions

### Code Structure
- Core logic in root directory
- Parser modules in `parser/` directory
- Utility functions in `util/` directory
- Database schema in `database/` directory
- Documentation in `docs/` directory

### Error Handling
- Use `handle_error()` for critical failures that should terminate execution
- Log warnings for recoverable issues and continue processing
- All database operations run in a single transaction for consistency

### File Processing
- Support streaming processing for memory efficiency
- Use hash values for change detection
- Follow `target_source_config.yaml` filtering rules

### Database Operations
- Use `DatabaseUtils` for all database interactions
- Implement upsert operations for idempotent behavior
- Maintain data integrity through foreign key constraints

## Key Modules

### Parser Components
- `parser/xml_parser.py`: MyBatis XML parsing with DOM fallback
- `parser/java_parser.py`: Java class/method extraction
- `parser/frontend_parser.py`: Frontend API call detection
- `parser/simple_query_analyzer.py`: SQL query extraction from Java

### Utility Components
- `util/database_utils.py`: Database connection and operations
- `util/file_utils.py`: File system operations
- `util/path_utils.py`: Path manipulation and resolution
- `util/sql_content_manager.py`: SQL content storage and retrieval

### Analysis Components
- `relationship_builder.py`: Build relationships between all components
- `consistency_validator.py`: Validate metadata database integrity
- `create_report.py`: Generate architecture, ERD, and call chain reports