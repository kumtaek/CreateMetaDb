"""String.format-based SQL template extractor (safe, heuristic).
"""
from __future__ import annotations
import re
from typing import List, Dict


def extract_string_format_queries(method_content: str, method_name: str) -> List[Dict]:
    results: List[Dict] = []
    try:
        pattern = r'String\.format\s*\(\s*\"([^\"\\]*(?:\\.[^\"\\]*)*)\"\s*(,\s*[^\)]*)?\)'
        for m in re.finditer(pattern, method_content, re.DOTALL):
            fmt = m.group(1)
            args_raw = m.group(2) or ""

            # tokenize arguments by commas with simple parenthesis depth tracking
            args_list: List[str] = []
            buf: List[str] = []
            depth = 0
            for ch in args_raw:
                if ch == '(':
                    depth += 1
                elif ch == ')':
                    depth = max(0, depth - 1)
                if ch == ',' and depth == 0:
                    token = ''.join(buf).strip()
                    if token:
                        args_list.append(token)
                    buf = []
                else:
                    buf.append(ch)
            token = ''.join(buf).strip()
            if token:
                args_list.append(token)
            if args_list and args_list[0].startswith(','):
                args_list[0] = args_list[0][1:].strip()

            def ph(i: int, arg: str) -> str:
                a = (arg or '').strip().lower()
                if not a:
                    return f"arg{i+1}"
                if 'environment' in a or a == 'env':
                    return 'env'
                if 'limit' in a:
                    return 'limit'
                if 'offset' in a:
                    return 'offset'
                if 'join' in a:
                    return f"join_{i}"
                if 'entitytype' in a or 'entity_type' in a:
                    return 'entity'
                return f"arg{i+1}"

            placeholders = [ph(i, a) for i, a in enumerate(args_list)]

            spec_pattern = r'%(?:\d+\$)?[sdif]|%s|%d|%f|%\.\d+f'
            idx = 0

            def repl(_m):
                nonlocal idx
                name = placeholders[idx] if idx < len(placeholders) else f"arg{idx+1}"
                idx += 1
                return '{' + name + '}'

            templ = re.sub(spec_pattern, repl, fmt)
            templ_compact = re.sub(r'\s+', ' ', templ).strip()

            # quick SQL start detection
            head = templ_compact[:10].upper()
            if not any(head.startswith(k) for k in ("SELECT", "INSERT", "UPDATE", "DELETE", "MERGE")):
                continue

            # classify
            if head.startswith("SELECT"):
                qtype = 'SQL_SELECT'
            elif head.startswith("INSERT"):
                qtype = 'SQL_INSERT'
            elif head.startswith("UPDATE"):
                qtype = 'SQL_UPDATE'
            elif head.startswith("DELETE"):
                qtype = 'SQL_DELETE'
            else:
                qtype = 'SQL_MERGE'

            results.append({
                'query_id': f"{method_name}_FMT_{len(results)+1}",
                'method_name': method_name,
                'variable_name': f"FMT_{len(results)+1}",
                'sql_content': templ_compact,
                'query_type': qtype,
            })

    except Exception:
        # non-fatal: return what we have
        pass

    return results
