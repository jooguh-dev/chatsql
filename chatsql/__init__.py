import pymysql

# 让 PyMySQL 伪装成 MySQLdb，这样 Django 就可以使用 PyMySQL 了
pymysql.install_as_MySQLdb()

# 修复版本检查问题：Django 4.2+ 需要 mysqlclient 2.2.1+
# 在 install_as_MySQLdb() 之后，MySQLdb 模块已经被创建，我们需要修改它的版本信息
try:
    import MySQLdb
    # 设置版本号以满足 Django 4.2+ 的要求
    MySQLdb.version_info = (2, 2, 1, 'final', 0)
    MySQLdb.__version__ = '2.2.1'
except ImportError:
    pass

