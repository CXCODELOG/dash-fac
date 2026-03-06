from config.dashgo_conf import SqlDbConf, SqlServerDbConf
from playhouse.pool import PooledMySQLDatabase
from peewee import SqliteDatabase,Database
from playhouse.shortcuts import ReconnectMixin
import pyodbc  # 直接引入pyodbc，兜底原生连接

if SqlDbConf.RDB_TYPE == 'mysql':
    # 断线重连+连接池
    class ReconnectPooledMySQLDatabase(ReconnectMixin, PooledMySQLDatabase):
        _instance = None

        @classmethod
        def get_db_instance(cls):
            if not cls._instance:
                cls._instance = cls(
                    database=SqlDbConf.DATABASE,
                    max_connections=SqlDbConf.POOL_SIZE,
                    user=SqlDbConf.USER,
                    password=SqlDbConf.PASSWORD,
                    host=SqlDbConf.HOST,
                    port=SqlDbConf.PORT,
                    stale_timeout=300,
                )
            return cls._instance
elif SqlDbConf.RDB_TYPE == 'sqlite':
    sqlite_db = SqliteDatabase(SqlDbConf.SQLITE_DB_PATH, timeout=20)
else:
    raise NotImplementedError('Unsupported database type')


def db():
    if SqlDbConf.RDB_TYPE == 'mysql':
        return ReconnectPooledMySQLDatabase.get_db_instance()
    elif SqlDbConf.RDB_TYPE == 'sqlite':
        return sqlite_db
    else:
        raise NotImplementedError('Unsupported database type')


class SqlServerDB:
    """pyodbc 原生连接封装（接口与 Peewee 对齐）"""
    _instance = None

    @classmethod
    def get_db_instance(cls):
        if not cls._instance:
            # 构建 SQL Server 连接字符串
            conn_str = (
                f"DRIVER={SqlServerDbConf.DRIVER};"
                f"SERVER={SqlServerDbConf.SERVER};"
                f"DATABASE={SqlServerDbConf.DATABASE};"
                f"UID={SqlServerDbConf.USER};"
                f"PWD={SqlServerDbConf.PASSWORD};"
            )
            # 创建连接池（简单版，按需扩展）
            cls._instance = pyodbc.connect(conn_str, autocommit=True)
        return cls._instance

    # 模拟 Peewee 的 connection_context 方法（保持接口一致）
    def connection_context(self):
        return self.get_db_instance()

def sqlserver_db():
    """pyodbc 方式获取 SQL Server 连接"""
    return SqlServerDB.get_db_instance()

# 判断是否存在SysUser表，如不存在则初始化库
def create_rds_table():
    db_instance = db()
    from .entity.table_user import SysUser, SysRoleAccessMeta, SysUserRole, SysGroupUser, SysRole, SysGroupRole, SysGroup
    from .entity.table_announcement import SysAnnouncement
    from .entity.table_oauth2 import OAuth2Client, OAuth2AuthorizationCode, OAuth2Token
    from .entity.table_apscheduler import SysApschedulerResults, SysApschedulerExtractValue, SysApschedulerRunning
    from .entity.table_notify_api import SysNotifyApi
    from .entity.table_listen_api import SysListenApi
    from .entity.table_listen_task import ApschedulerJobsActiveListen

    db_instance.create_tables(
        [
            SysUser,
            SysRoleAccessMeta,
            SysUserRole,
            SysGroupUser,
            SysRole,
            SysGroupRole,
            SysGroup,
            SysAnnouncement,
            OAuth2Client,
            OAuth2AuthorizationCode,
            OAuth2Token,
            SysApschedulerResults,
            SysApschedulerExtractValue,
            SysApschedulerRunning,
            SysNotifyApi,
            SysListenApi,
            ApschedulerJobsActiveListen,
        ],
        safe=True,
    )


def init_rds_data():
    db_instance = db()
    from .entity.table_user import SysUser, SysUserRole, SysRole
    from datetime import datetime
    import hashlib

    with db_instance.atomic():
        SysRole.create(
            role_name='admin',
            role_status=True,
            update_datetime=datetime.now(),
            update_by='admin',
            create_datetime=datetime.now(),
            create_by='admin',
            role_remark='超级管理员角色',
        )
        SysUser.create(
            user_name='admin',
            user_full_name='超级管理员',
            password_sha256=hashlib.sha256('admin123'.encode('utf-8')).hexdigest(),
            user_status=True,
            user_sex='未知',
            user_email='',
            phone_number='',
            create_by='admin',
            create_datetime=datetime.now(),
            update_by='admin',
            update_datetime=datetime.now(),
            user_remark='',
            otp_secret='',
        )
        SysUserRole.create(user_name='admin', role_name='admin')
