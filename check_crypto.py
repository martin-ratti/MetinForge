import sys
print(f"Python executable: {sys.executable}")
try:
    import cryptography
    print(f"Cryptography version: {cryptography.__version__}")
    print(f"Cryptography file: {cryptography.__file__}")
except ImportError as e:
    print(f"Failed to import cryptography: {e}")

try:
    import pymysql
    print(f"PyMySQL version: {pymysql.__version__}")
except ImportError as e:
    print(f"Failed to import pymysql: {e}")
