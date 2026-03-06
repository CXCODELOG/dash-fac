# src/database/sql_db/dao/dao_sqlserver.py
from database.sql_db.conn import sqlserver_db
from peewee import Model, CharField, DateTimeField

# 定义 SQL Server 专属模型（与原有模型隔离）
class SQLServerBaseModel(Model):
    class Meta:
        database = sqlserver_db()  # 绑定 SQL Server 连接

# 示例：SQL Server 表模型
class BigDataTable(SQLServerBaseModel):
    id = CharField(primary_key=True, max_length=64)
    data = CharField(max_length=255)
    create_time = DateTimeField()

    class Meta:
        table_name = 'big_data_table'  # SQL Server 中的表名

# 示例：查询 SQL Server 数据
def query_sqlserver_data():
    db_instance = sqlserver_db()
    with db_instance.connection_context():  # 手动管理连接（可选）
        data = [item for item in BigDataTable.select()]
    return data