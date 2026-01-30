import logging
import time

from constants import MESSAGES
from config import mysql_config
from dao import excelImportDao
from utils import excelUtils

def excel_to_existing_table():
    """
    将Excel数据导入到【已存在】的MySQL表中。
    字段以Excel文件的列标题为准。
    """
    logging.info("--- 将Excel数据导入到【已存在】的MySQL表 ---")
    time.sleep(0.1)

    # 1. 选择并加载Excel文件
    excel_files = excelUtils.find_excel_file()
    if not excel_files:
        return
    file_path = excelUtils.user_choose_file(excel_files)

    df = excelUtils.load_data(file_path)
    if df is None:
        logging.error("无法加载文件数据，请检查文件格式或内容。\n")
        return
    logging.info("数据加载成功！\n")
    time.sleep(0.1)

    # 2. 获取数据库连接
    conn = mysql_config.get_mysql_connection()
    if not conn:
        logging.error("获取数据库连接失败。")
        return
    
    cursor = conn.cursor()

    # 3. 获取并验证表名
    while True:
        table_name = input(MESSAGES.INPUT_MYSQL_TABLE).strip()
        if table_name:
            if excelImportDao.check_table_exists(cursor, table_name):
                break
            else:
                logging.error(f"表 `{table_name}` 不存在，请重新输入。")
        else:
            print("表名不能为空，请重新输入。")

    logging.info(f"表 `{table_name}` 存在，准备导入数据...")

    # 4. 检查表是否有数据，并与用户交互
    if excelImportDao.check_table_has_data(cursor, table_name):
        print(f"警告：表 `{table_name}` 中已存在数据。")
        while True:
            action = input("请选择操作：[1] 清空后插入 [2] 直接追加插入 [q] 退出: ").strip().lower()
            if action == '1':
                if excelImportDao.truncate_table(cursor, table_name):
                    conn.commit()
                    break
                else:
                    # 如果清空失败，则不应继续
                    cursor.close()
                    conn.close()
                    return
            elif action == '2':
                break
            elif action == 'q':
                print("操作已取消。")
                cursor.close()
                conn.close()
                return
            else:
                print("无效输入，请重新选择。")
    
    cursor.close() # 关闭旧的cursor

    # 5. 调用现有的DAO函数导入数据
    # 这个函数会根据DataFrame的列自动生成INSERT语句
    excelImportDao.import_data_to_mysql(conn, table_name, df)

    # 6. 清理
    conn.close()
    time.sleep(0.1)