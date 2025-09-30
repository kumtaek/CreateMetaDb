"""
Simple Query Analyzer (UTF-8, ASCII comments)

Responsibilities
- Extract SQL from Java source (string literals, concatenation, StringBuilder, String.format)
- Extract JPA @Query strings
- Provide method list for downstream mapping

Notes
- This is a clean, minimal, cross-platform-safe implementation.
- Heuristics are conservative to avoid false positives.
"""

from __future__ import annotations

import re
import os
import sqlite3
from typing import Dict, List, Any

from util import info, handle_error, DatabaseUtils, ConfigUtils, PathUtils, HashUtils
from util.oracle_keyword_manager import get_oracle_keyword_manager
from parser.string_format_extractor import extract_string_format_queries


class SimpleQueryAnalyzer:
    """Analyze Java files to extract SQL queries and helper data."""

    def __init__(self, project_name: str, conn: sqlite3.Connection):
        try:
            self.project_name = project_name
            self.conn = conn
            self.db_utils = DatabaseUtils(None)
            self.config_utils = ConfigUtils()
            self.path_utils = PathUtils()
            self.hash_utils = HashUtils()

            self.oracle_keyword_manager = get_oracle_keyword_manager()
            self.oracle_keywords = self.oracle_keyword_manager.get_keywords()
            self.sql_start_patterns = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'MERGE']
            info("SimpleQueryAnalyzer initialized")
        except Exception as e:
            handle_error(e, "SimpleQueryAnalyzer initialization failed")

    # ===== Java file analysis =====

    def analyze_java_file(self, file_path: str, file_id: int) -> Dict[str, List[Dict]]:
        """Parse a Java file and extract queries per method."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            results = {'java_queries': [], 'jpa_queries': [], 'methods': []}
            methods = self._extract_java_methods(content)
            results['methods'] = methods

            for method in methods:
                method_name = method['name']
                method_content = method['content']

                java_queries = self._extract_java_queries(method_content, method_name)
                results['java_queries'].extend(java_queries)

                jpa_queries = self._extract_jpa_queries(method_content, method_name)
                results['jpa_queries'].extend(jpa_queries)

                fmt_queries = extract_string_format_queries(method_content, method_name)
                if fmt_queries:
                    results['java_queries'].extend(fmt_queries)

            info(f"Java analyzed: {file_path}, methods={len(methods)}, java={len(results['java_queries'])}, jpa={len(results['jpa_queries'])}")
            return results
        except Exception as e:
            handle_error(e, f"Java analysis failed: {file_path}")
            return {'java_queries': [], 'jpa_queries': [], 'methods': []}

    def _extract_java_methods(self, content: str) -> List[Dict]:
        """Very simple method body extractor."""
        try:
            methods: List[Dict] = []
            pattern = r'(public|private|protected)\s+[^{;]+?(\w+)\s*\([^)]*\)\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}'
            for m in re.finditer(pattern, content, re.DOTALL | re.IGNORECASE):
                methods.append({'name': m.group(2), 'content': m.group(3)})
            return methods
        except Exception as e:
            handle_error(e, "Java method extraction failed")
            return []

    def _extract_java_queries(self, method_content: str, method_name: str) -> List[Dict]:
        """Find SQL assembled via string literals/concat/StringBuilder."""
        try:
            queries: List[Dict] = []
            string_vars: Dict[str, str] = {}

            # String constants
            for i, const in enumerate(re.findall(r'"([^"\\]*(?:\\.[^"\\]*)*)"', method_content, re.DOTALL)):
                string_vars[f'STRING_CONST_{i}'] = const.strip()

            # var = "..."
            for m in re.finditer(r'String\s+(\w+)\s*=\s*"([^"]*)"', method_content, re.IGNORECASE):
                string_vars[m.group(1)] = m.group(2).strip()

            # var += "..."  /  var = var + "..."
            concat_patterns = [
                r'(\w+)\s*\+=\s*"([^"\\]*(?:\\.[^"\\]*)*)"',
                r'(\w+)\s*=\s*\w+\s*\+\s*"([^"\\]*(?:\\.[^"\\]*)*)"',
            ]
            for p in concat_patterns:
                for m in re.finditer(p, method_content, re.IGNORECASE):
                    var, append = m.group(1), m.group(2).strip()
                    string_vars[var] = (string_vars.get(var, '') + ' ' + append).strip()

            # StringBuilder.append("...")
            for m in re.finditer(r'StringBuilder\s+(\w+).*?\.append\("([^"\\]*(?:\\.[^"\\]*)*)"\)', method_content, re.DOTALL | re.IGNORECASE):
                var, append = m.group(1), m.group(2).strip()
                string_vars[var] = (string_vars.get(var, '') + ' ' + append).strip()

            # Keep only SQL-looking strings
            for var_name, var_content in string_vars.items():
                cleaned = re.sub(r'\s+', ' ', var_content.strip())
                if self._is_sql_query(cleaned):
                    queries.append({
                        'query_id': f"{method_name}_{var_name}",
                        'method_name': method_name,
                        'variable_name': var_name,
                        'sql_content': cleaned,
                        'query_type': self._detect_query_type(cleaned),
                    })

            return queries
        except Exception as e:
            handle_error(e, f"Java query extraction failed: {method_name}")
            return []

    def _extract_jpa_queries(self, method_content: str, method_name: str) -> List[Dict]:
        """Extract @Query("...") fragments and join them."""
        try:
            queries: List[Dict] = []
            for m in re.finditer(r'@Query\s*\(\s*([\s\S]+?)\s*\)', method_content, re.DOTALL | re.IGNORECASE):
                annotation = m.group(1)
                parts = re.findall(r'"([^"\\]*(?:\\.[^"\\]*)*)"', annotation, re.DOTALL)
                if not parts:
                    continue
                full = re.sub(r'\s+', ' ', ' '.join(p.strip() for p in parts).strip())
                if self._is_sql_query(full):
                    queries.append({
                        'query_id': method_name,
                        'method_name': method_name,
                        'variable_name': method_name,
                        'sql_content': full,
                        'query_type': self._detect_query_type(full),
                    })
            return queries
        except Exception as e:
            handle_error(e, f"JPA query extraction failed: {method_name}")
            return []

    # ===== Helpers =====

    def _is_sql_query(self, s: str) -> bool:
        head = (s or '').lstrip().upper()
        return any(head.startswith(k) for k in self.sql_start_patterns)

    def _detect_query_type(self, s: str) -> str:
        u = (s or '').lstrip().upper()
        if u.startswith('SELECT'):
            return 'SQL_SELECT'
        if u.startswith('INSERT'):
            return 'SQL_INSERT'
        if u.startswith('UPDATE'):
            return 'SQL_UPDATE'
        if u.startswith('DELETE'):
            return 'SQL_DELETE'
        return 'SQL_MERGE'

