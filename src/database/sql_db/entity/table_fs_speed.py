from peewee import Model, IntegerField, DateTimeField
from ..conn import sqlserver_db  # 引用新增的 SQL Server 连接方法

# 专属 SQL Server 的 BaseModel（区别于原有 MySQL/SQLite 的 BaseModel）
class SQLServerBaseModel(Model):
    class Meta:
        database = sqlserver_db()  # 绑定 SQL Server 数据库连接

class CX_fs_speed(SQLServerBaseModel):
    id = IntegerField(primary_key=True, help_text='自增ID')
    speed_1 = IntegerField(null=True, help_text='发射管1速度')
    speed_2 = IntegerField(null=True, help_text='发射管2速度')
    speed_3 = IntegerField(null=True, help_text='发射管3速度')
    speed_4 = IntegerField(null=True, help_text='发射管4速度')
    speed_5 = IntegerField(null=True, help_text='发射管5速度')
    speed_6 = IntegerField(null=True, help_text='发射管6速度')
    speed_7 = IntegerField(null=True, help_text='发射管7速度')
    speed_8 = IntegerField(null=True, help_text='发射管8速度')
    speed_9 = IntegerField(null=True, help_text='发射管9速度')
    speed_10 = IntegerField(null=True, help_text='发射管10速度')
    time = DateTimeField(help_text='采集时间')

    class Meta:
        table_name = 'CX_fs_speed'  # 对应 SQL Server 中的表名
        schema = 'dbo'  # 指定 SQL Server 的 schema