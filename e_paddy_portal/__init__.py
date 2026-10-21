# Use PyMySQL as the MySQL driver (pure Python: installs on Windows, Linux and macOS
# without compiling anything). Django's MySQL backend expects the MySQLdb module name.
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass
