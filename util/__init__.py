"""
SourceAnalyzer 공통 유틸리티 모듈
"""

from .logger import SourceAnalyzerLogger, app_logger, debug, info, warning, error, critical, get_log_file_path, handle_error
from .file_utils import FileUtils, read_file, write_file, get_file_type, get_file_hash, get_content_hash
from .database_utils import DatabaseUtils, create_database_connection, execute_sql_script
from .config_utils import ConfigUtils, load_yaml_config, load_project_config, get_config_value
from .hash_utils import HashUtils, generate_md5, generate_sha256, generate_file_hash, is_file_changed
from .validation_utils import ValidationUtils, is_valid_project_name, is_valid_file_path, validate_file_exists, validate_directory_exists, validate_required_fields
from .path_utils import (
    PathUtils, DatabaseCache, normalize_path, get_relative_path, get_absolute_path, is_within_project, join_path,
    get_project_source_path, get_project_config_path, get_project_src_path, get_project_db_schema_path,
    get_project_report_path, get_project_metadata_db_path, get_config_path, get_database_schema_path,
    get_parser_config_path, list_projects, project_exists
)
from .arg_utils import (
    ArgUtils, parse_command_line_args, get_project_name_from_args, validate_and_get_project_name,
    create_simple_parser, print_usage_and_exit
)

__all__ = [
    # Logger
    'SourceAnalyzerLogger',
    'app_logger',
    'debug',
    'info', 
    'warning',
    'error',
    'critical',
    'get_log_file_path',
    'handle_error',
    
    # File Utils
    'FileUtils',
    'read_file',
    'write_file',
    'get_file_type',
    'get_file_hash',
    'get_content_hash',
    
    # Database Utils
    'DatabaseUtils',
    'create_database_connection',
    'execute_sql_script',
    
    # Config Utils
    'ConfigUtils',
    'load_yaml_config',
    'load_project_config',
    'get_config_value',
    
    # Hash Utils
    'HashUtils',
    'generate_md5',
    'generate_sha256',
    'generate_file_hash',
    'is_file_changed',
    
    # Validation Utils
    'ValidationUtils',
    'is_valid_project_name',
    'is_valid_file_path',
    'validate_file_exists',
    'validate_directory_exists',
    'validate_required_fields',
    
    # Path Utils
    'PathUtils',
    'DatabaseCache',
    'normalize_path',
    'get_relative_path',
    'get_absolute_path',
    'is_within_project',
    'join_path',
    'get_project_source_path',
    'get_project_config_path',
    'get_project_src_path',
    'get_project_db_schema_path',
    'get_project_report_path',
    'get_project_metadata_db_path',
    'get_config_path',
    'get_database_schema_path',
    'get_parser_config_path',
    'list_projects',
    'project_exists',
    
    # Arg Utils
    'ArgUtils',
    'parse_command_line_args',
    'get_project_name_from_args',
    'validate_and_get_project_name',
    'create_simple_parser',
    'print_usage_and_exit'
]
