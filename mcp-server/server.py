import os
import random
import string
import pymysql
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("simple-mcp", host="0.0.0.0", port=8080)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "mariadb"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("MYSQL_USER", "mcpuser"),
    "password": os.getenv("MYSQL_PASSWORD", "mcppass"),
    "database": os.getenv("MYSQL_DATABASE", "userdb"),
    "cursorclass": pymysql.cursors.DictCursor,
}

FIRST_NAMES = ["김", "이", "박", "최", "정", "강", "조", "윤", "장", "임",
               "한", "오", "서", "신", "권", "황", "안", "송", "류", "전"]
MIDDLE_NAMES = ["민", "서", "지", "수", "도", "하", "시", "현", "나", "태",
                "다", "주", "예", "건", "채", "도", "준", "윤", "아", "은"]
LAST_NAMES  = ["준", "연", "호", "아", "윤", "은", "우", "아", "우", "율",
               "이", "연", "양", "은", "서", "원", "린", "우", "원", "현"]


def get_conn():
    return pymysql.connect(**DB_CONFIG)


def random_name() -> str:
    return random.choice(FIRST_NAMES) + random.choice(MIDDLE_NAMES) + random.choice(LAST_NAMES)


def random_phone() -> str:
    middle = "".join(random.choices(string.digits, k=4))
    last   = "".join(random.choices(string.digits, k=4))
    return f"010-{middle}-{last}"


@mcp.tool()
def list_users() -> list[dict]:
    """DB에 저장된 전체 사용자 목록을 반환합니다."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, phone, age FROM users ORDER BY id")
            return cur.fetchall()


@mcp.tool()
def get_user_by_name(name: str) -> list[dict]:
    """이름(또는 일부)으로 사용자를 검색합니다."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, phone, age FROM users WHERE name LIKE %s ORDER BY id",
                (f"%{name}%",),
            )
            return cur.fetchall()


@mcp.tool()
def add_random_user() -> dict:
    """랜덤으로 이름·전화번호·나이(18~70)를 생성해 DB에 추가합니다."""
    name  = random_name()
    phone = random_phone()
    age   = random.randint(18, 70)
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (name, phone, age) VALUES (%s, %s, %s)",
                (name, phone, age),
            )
        conn.commit()
        user_id = cur.lastrowid
    return {"id": user_id, "name": name, "phone": phone, "age": age}


@mcp.tool()
def delete_user(user_id: int) -> dict:
    """ID로 사용자를 삭제합니다. 삭제 성공 여부를 반환합니다."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            affected = cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
    return {"deleted": affected > 0, "user_id": user_id}


@mcp.tool()
def get_statistics() -> dict:
    """전체 사용자 통계(총 인원, 평균/최소/최대 나이)를 반환합니다."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) AS total, AVG(age) AS avg_age, "
                "MIN(age) AS min_age, MAX(age) AS max_age FROM users"
            )
            row = cur.fetchone()
    return {
        "total": row["total"],
        "avg_age": round(float(row["avg_age"] or 0), 1),
        "min_age": row["min_age"],
        "max_age": row["max_age"],
    }


if __name__ == "__main__":
    mcp.run(transport="sse")
