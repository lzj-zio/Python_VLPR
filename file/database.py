# -*- coding: utf-8 -*-
"""
数据库模块 - SQLite 持久化识别记录
数据库文件: ./vlpr_records.db（与 main_VLPR.py 同目录）
"""
import sqlite3
import os
import threading
import time

# 数据库文件路径（项目根目录）
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "vlpr_records.db")
# 确保路径是绝对路径
DB_PATH = os.path.abspath(DB_PATH)

_lock = threading.Lock()

# ---------------------------------------------------------------------------
# 连接管理
# ---------------------------------------------------------------------------

def _get_conn():
    """获取数据库连接（线程安全）"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _execute(sql, args=(), commit=True):
    """执行 SQL（自动提交）"""
    with _lock:
        conn = _get_conn()
        try:
            cur = conn.cursor()
            cur.execute(sql, args)
            if commit:
                conn.commit()
            return cur
        finally:
            conn.close()


def _query(sql, args=()):
    """查询 SQL（不自动提交）"""
    with _lock:
        conn = _get_conn()
        try:
            cur = conn.cursor()
            cur.execute(sql, args)
            rows = cur.fetchall()
            return rows
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# 初始化
# ---------------------------------------------------------------------------

def init_db():
    """初始化数据库和表（如不存在则创建）"""
    _execute("""
        CREATE TABLE IF NOT EXISTS recognition_records (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            plate       TEXT    NOT NULL,
            province    TEXT    NOT NULL DEFAULT '',
            color       TEXT    NOT NULL DEFAULT '',
            channel     TEXT    NOT NULL DEFAULT '',
            confidence  REAL    NOT NULL DEFAULT 0.0,
            captured_at TEXT    NOT NULL,
            created_at  TEXT    NOT NULL
        )
    """, commit=True)
    # 索引：按时间倒序查询
    _execute("""
        CREATE INDEX IF NOT EXISTS idx_captured_at
        ON recognition_records(captured_at DESC)
    """, commit=True)
    print(f"[DB] 初始化完成，数据库路径: {DB_PATH}")


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

def add_record(plate, color, channel, confidence, captured_at):
    """
    新增一条识别记录
    参数:
        plate:      车牌号字符串（如 "川AA662F"）
        color:      颜色中文（如 "蓝牌"）
        channel:    识别通道（如 "形状定位"）
        confidence: 置信度（0.0 ~ 1.0）
        captured_at: 识别时间字符串（YYYY-MM-DD HH:MM:SS）
    返回:
        新记录 id
    """
    province = plate[0] if plate else ""
    created_at = time.strftime("%Y-%m-%d %H:%M:%S")
    cur = _execute(
        """
        INSERT INTO recognition_records
            (plate, province, color, channel, confidence, captured_at, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (plate, province, color, channel, confidence, captured_at, created_at),
    )
    return cur.lastrowid


def get_records(limit=100, offset=0):
    """
    获取识别记录列表（倒序，最新的在前）
    参数:
        limit:  返回条数，默认 100
        offset:  跳过条数，用于分页
    返回:
        list[dict]，每条记录含所有字段
    """
    rows = _query(
        """
        SELECT id, plate, province, color, channel, confidence,
               captured_at, created_at
        FROM recognition_records
        ORDER BY captured_at DESC, id DESC
        LIMIT ? OFFSET ?
        """,
        (limit, offset),
    )
    return [dict(row) for row in rows]


def get_total_count():
    """获取总记录数"""
    rows = _query("SELECT COUNT(*) AS cnt FROM recognition_records")
    return rows[0]["cnt"] if rows else 0


def get_today_count():
    """获取今日记录数"""
    today = time.strftime("%Y-%m-%d")
    rows = _query(
        "SELECT COUNT(*) AS cnt FROM recognition_records WHERE captured_at LIKE ?",
        (today + "%",),
    )
    return rows[0]["cnt"] if rows else 0


def get_stats_by_color():
    """按颜色统计数量"""
    rows = _query(
        """
        SELECT color, COUNT(*) AS cnt
        FROM recognition_records
        GROUP BY color
        """
    )
    result = {}
    for row in rows:
        key = {"蓝牌": "blue", "黄牌": "yello", "绿牌": "green"}.get(row["color"], "unknown")
        result[key] = row["cnt"]
    return result


def get_stats_by_channel():
    """按识别通道统计数量"""
    rows = _query(
        """
        SELECT channel, COUNT(*) AS cnt
        FROM recognition_records
        GROUP BY channel
        """
    )
    result = {}
    for row in rows:
        key = {"形状定位": "shape", "颜色定位": "color"}.get(row["channel"], "unknown")
        result[key] = row["cnt"]
    return result


def get_stats_by_province(limit=20):
    """按省份统计数量（返回前 N 名）"""
    rows = _query(
        """
        SELECT province, COUNT(*) AS cnt
        FROM recognition_records
        WHERE province != ''
        GROUP BY province
        ORDER BY cnt DESC
        LIMIT ?
        """,
        (limit,),
    )
    return {row["province"]: row["cnt"] for row in rows}


def clear_records():
    """清空所有记录（谨慎使用）"""
    _execute("DELETE FROM recognition_records", commit=True)


if __name__ == "__main__":
    init_db()
    print("数据库模块测试:")
    print("  总记录数:", get_total_count())
    print("  今日记录:", get_today_count())
    print("  颜色统计:", get_stats_by_color())
    print("  通道统计:", get_stats_by_channel())
    print("  省份统计:", get_stats_by_province())
