"""
TrustLens AI - Configuration Database
数据库连接管理
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from pathlib import Path
from typing import Generator
from .models import Base


class Database:
    """数据库管理类"""

    def __init__(self, database_url: str = "sqlite:///./trustlens.db"):
        """
        初始化数据库连接

        Args:
            database_url: 数据库连接 URL
        """
        self.database_url = database_url
        self.engine = None
        self.SessionLocal = None

    def connect(self):
        """建立数据库连接"""
        # 确保数据目录存在
        if self.database_url.startswith("sqlite:///"):
            db_path = self.database_url.replace("sqlite:///", "")
            if db_path and db_path != "./trustlens.db":
                Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # 创建引擎
        self.engine = create_engine(
            self.database_url,
            echo=False,  # 设置为 True 可查看 SQL 日志
            pool_pre_ping=True,  # 连接池预检查
        )

        # 创建 Session 工厂
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

        # 创建所有表
        Base.metadata.create_all(bind=self.engine)

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        获取数据库会话（上下文管理器）

        Usage:
            with db.get_session() as session:
                # 使用 session
                pass
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def disconnect(self):
        """关闭数据库连接"""
        if self.engine:
            self.engine.dispose()
            self.engine = None
            self.SessionLocal = None


# 全局数据库实例
_db: Database = None


def get_database() -> Database:
    """获取全局数据库实例"""
    global _db
    if _db is None:
        _db = Database()
        _db.connect()
    return _db


def init_db(database_url: str = "sqlite:///./trustlens.db") -> Database:
    """初始化数据库"""
    global _db
    _db = Database(database_url)
    _db.connect()
    return _db
