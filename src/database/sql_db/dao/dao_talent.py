from typing import Any, Dict, List, Optional, Sequence

from database.sql_db.conn import talent_db


def _cursor_to_dicts(cursor) -> List[Dict[str, Any]]:
    columns = [column[0] for column in cursor.description or []]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def select_all(sql: str, params: Optional[Sequence[Any]] = None) -> List[Dict[str, Any]]:
    database = talent_db()
    with database.connection_context():
        cursor = database.execute_sql(sql, params or ())
        return _cursor_to_dicts(cursor)


def select_one(sql: str, params: Optional[Sequence[Any]] = None) -> Optional[Dict[str, Any]]:
    rows = select_all(sql, params)
    return rows[0] if rows else None


def execute(sql: str, params: Optional[Sequence[Any]] = None) -> int:
    database = talent_db()
    with database.connection_context():
        cursor = database.execute_sql(sql, params or ())
        return cursor.rowcount


def test_connection() -> Dict[str, Any]:
    return select_one('SELECT DATABASE() AS database_name, VERSION() AS version')
