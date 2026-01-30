import logging
import time
import csv

from constants import MESSAGES
from config import mysql_config
from dao import excelImportDao
import mysql.connector
from utils import sqlUtils, sysUtils

def csv_file():
    logging.info(MESSAGES.CSV_IMPORT_INFO)
    time.sleep(0.1)
    # 查找CSV文件
    csv_files = []
    for file in sysUtils.list_files():
        if file.lower().endswith('.csv'):
            csv_files.append(file)
    
    if not csv_files:
        logging.error("未找到任何CSV文件")
        return None
    
    print("找到以下CSV文件:")
    for i, file in enumerate(csv_files, 1):
        print(f"{i}. {file}")
    
    while True:
        try:
            choice = int(input(">>> 请选择要导入的CSV文件(输入序号): "))
            if 1 <= choice <= len(csv_files):
                return csv_files[choice-1]
            print("输入无效，请重新输入")
        except ValueError:
            print("请输入有效数字")

def load_csv_data(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader)
            data = list(reader)
        return headers, data
    except Exception as e:
        logging.error(f"加载CSV文件失败: {e}")
        return None, None

def csv_to_mysql():
    file_path = csv_file()
    if not file_path:
        return
    
    headers, data = load_csv_data(file_path)
    if not headers or not data:
        return
    
    conn = mysql_config.get_mysql_connection()
    cursor = conn.cursor()

    # 获取表名
    while True:
        table_name = input(MESSAGES.INPUT_MYSQL_TABLE).strip()
        if table_name:
            break
        print("表名不能为空，请重新输入。")

    # 检查表是否已存在
    if excelImportDao.check_table_exists(cursor, table_name):
        drop_table_flag = input(f"表 `{table_name}` 已存在，是否删除原表? (yes or y / no or n):")
        if drop_table_flag.lower() in ['no', 'n']:
            print(f"表 `{table_name}` 已存在，程序将退出。\n")
            cursor.close()
            conn.close()
            return

    # 生成并执行删除表 SQL
    drop_sql = excelImportDao.generate_drop_table_sql(table_name)
    logging.info(f"生成的 DROP TABLE SQL:\n{drop_sql}\n")

    # 生成创建表SQL
    create_sql = f"CREATE TABLE {table_name} ("
    for header in headers:
        create_sql += f"\n    {header} VARCHAR(255),"
    create_sql = create_sql.rstrip(',') + "\n);"
    
    print(f"create table >>> \n{create_sql}\n")
    create_sql = sqlUtils.input_create_table(table_name, create_sql)

    try:
        cursor.execute(drop_sql)
        cursor.execute(create_sql)
        logging.info(f"表 `{table_name}` 创建成功！\n")
        time.sleep(0.1)
    except mysql.connector.Error as err:
        logging.error(f"创建表时发生错误: {err}\n")
        cursor.close()
        conn.close()
        return

    # 导入数据
    try:
        placeholders = ', '.join(['%s'] * len(headers))
        insert_sql = f"INSERT INTO {table_name} VALUES ({placeholders})"
        cursor.executemany(insert_sql, data)
        conn.commit()
        logging.info(f"成功导入 {len(data)} 条数据到表 `{table_name}`")
    except mysql.connector.Error as err:
        logging.error(f"导入数据时发生错误: {err}")
        conn.rollback()
    
    cursor.close()
    conn.close()
    time.sleep(0.1)
