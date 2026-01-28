import logging
import re

import mysql


def check_table_exists(cursor, table_name):
    """检查表是否存在"""
    cursor.execute("SHOW TABLES LIKE %s", (table_name,))
    return cursor.fetchone() is not None


def check_table_has_data(cursor, table_name):
    """检查表是否有数据"""
    cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
    count = cursor.fetchone()[0]
    return count > 0


def truncate_table(cursor, table_name):
    """清空表数据"""
    try:
        cursor.execute(f"TRUNCATE TABLE `{table_name}`")
        logging.info(f"表 `{table_name}` 已被清空。")
        return True
    except mysql.connector.Error as err:
        logging.error(f"清空表 `{table_name}` 时发生错误: {err}")
        return False



def generate_drop_table_sql(table_name):
    return f"drop table if exists `{table_name}`;"

def generate_create_table_sql(table_name, df):
    """根据DataFrame生成创建表的SQL"""
    columns = df.columns
    columns1 = []
    column_mapping = generate_column_mapping(columns)

    # 准备列名，替换空格为下划线并映射到数据库列名
    mapped_columns = [column_mapping.get(col, col) for col in columns]

    # 过滤无效列或不需要插入的列
    filtered_columns = [col for col in mapped_columns if col in column_mapping.values()]

    if not filtered_columns:
        raise ValueError("字段列表为空 或者 检查字段是否存在特殊符号，无法生成 CREATE TABLE 语句。")
    # 计算列数
    num_columns = len(filtered_columns)
    logging.info(f"字段共有: {num_columns}个\n")

    # MySQL行大小限制(65535字节)，预留20%空间给行开销和主键
    max_total_size = 65535 * 0.8  # 约52428字节可用

    # 计算每列平均可分配的大小(utf8mb4每个字符最多占4字节)
    avg_length = int(max_total_size / (num_columns * 4)) if num_columns > 0 else 100
    # 设置合理的上下限 (50-1000)
    field_length = max(100, min(1000, avg_length))

    logging.info(f"计算出的动态字段长度: {field_length} (基于{num_columns}列)")

    for col in filtered_columns:
        columns1.append(f"`{col}` VARCHAR({field_length})")
        # columns1.append(f"`{col}` VARCHAR(150)")
    columns1.append("`id` INT AUTO_INCREMENT PRIMARY KEY")
    columns_sql = ', '.join(columns1)
    return f"CREATE TABLE `{table_name}` ({columns_sql}) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;"

def replace_pattern(s):
    return re.sub(r'\((\d+)\)', r'_\1', s)
    # return re.sub(r'\((.*?)\)', r'_\1', s)

if __name__ == '__main__':
    replace_pattern(1)

def generate_column_mapping(columns):
    """根据列名生成映射表，删除括号及特殊字符，替换空格为下划线，并移除无效字段"""
    column_mapping = {}
    for col in columns:
        # handle_str = replace_pattern(str(col)).replace('\n', '')
        # 将 \n 及之后的所有内容替换为空字符串
        handle_str = re.sub(r'\n.*', '', replace_pattern(str(col)))
        cleaned_col = re.sub(r'\(.*?\)|[?？]', '', handle_str).strip()  # 删除括号及特殊符号
        mapped_col = cleaned_col.replace('  ', '_').replace(' ', '_').replace('-', '_').replace('.', '').replace('/', '').replace('%','').replace('___','_').replace('__','_').replace(')', '')
        # if mapped_col:  # 确保字段名非空
        #     print(col, mapped_col)
        #     column_mapping[col] = mapped_col

        # 检查mapped_col是否已经存在于column_mapping的值中
        counter = 90
        original_mapped_col = mapped_col
        while mapped_col in column_mapping.values():
            mapped_col = f"{original_mapped_col}_{counter}"
            counter += 1

        if mapped_col:  # 确保字段名非空
            # print(col, mapped_col)
            column_mapping[col] = mapped_col
    return column_mapping


# if __name__ == "__main__":
#     col = "Product Family (UCS/ BBI/CloudPND (Private Network Data)/ Cloud/ China Business/ Wholesales/EMS)"
#     print(replace_pattern(col))

def import_data_to_mysql(conn, table_name, df, batch_size=1000):
    """将数据批量导入MySQL表中，自动生成列名映射"""
    cursor = conn.cursor()

    # 将NaN值替换为空字符串
    df = df.where(df.notnull(), None)
    # 将文本格式的 'NULL' 替换为 None
    df = df.replace(['NULL', 'Null', 'null'], None)

    # 检查第一列是否存在空值，如果有则抛出异常
    if df.iloc[:, 0].isnull().any():
        print(" 错误：第一列存在空值，导入失败。\n")
        return

    # 自动生成列名映射
    columns = df.columns
    column_mapping = generate_column_mapping(columns)

    # 准备列名，替换空格为下划线并映射到数据库列名
    mapped_columns = [column_mapping.get(col, col) for col in columns]

    # 过滤无效列或不需要插入的列
    filtered_columns = [col for col in mapped_columns if col in column_mapping.values()]

    # 生成 SQL 插入语句的占位符
    placeholders = ', '.join(['%s'] * len(filtered_columns))
    # insert_sql = f"INSERT INTO `{table_name}` ({', '.join(filtered_columns)}) VALUES ({placeholders})"
    insert_sql = f"INSERT INTO `{table_name}` ({', '.join([f'`{col}`' for col in filtered_columns])}) VALUES ({placeholders})"

    print(f"🔄 准备插入数据到表 `{table_name}`。\n生成的 SQL:\n{insert_sql}\n")

    # 将DataFrame转换为适合批量插入的格式
    rows_to_insert = df[columns].values.tolist()

    try:
        # 批量插入数据，按批次分割
        for i in range(0, len(rows_to_insert), batch_size):
            batch = rows_to_insert[i:i + batch_size]
            cursor.executemany(insert_sql, batch)
            conn.commit()  # 每次提交一个批次
            print(f" 已导入 {i + len(batch)} / {len(rows_to_insert)} 条数据...\n")

        print(f"🎉 数据已成功批量导入到表 `{table_name}` 中！\n")

    except mysql.connector.Error as err:
        print(f" 导入数据时发生错误: {err}\n")
        conn.rollback()  # 如果出现错误，回滚事务
    finally:
        cursor.close()


def import_data_to_mysql_V2(conn, table_name, df, batch_size=1000):
    """将数据批量导入MySQL表中，自动生成列名映射"""
    cursor = conn.cursor()

    # 将NaN值替换为空字符串
    df = df.where(df.notnull(), None)
    # 将文本格式的 'NULL' 替换为 None
    df = df.replace(['NULL', 'Null', 'null'], None)

    # 检查第一列是否存在空值，如果有则抛出异常
    if df.iloc[:, 0].isnull().any():
        logging.ERROR(" 错误：第一列存在空值，导入失败。\n")
        return

    # 自动生成列名映射
    columns = df.columns
    column_mapping = generate_column_mapping(columns)

    # 准备列名，替换空格为下划线并映射到数据库列名
    mapped_columns = [column_mapping.get(col, col) for col in columns]

    # 过滤无效列或不需要插入的列
    filtered_columns = [col for col in mapped_columns if col in column_mapping.values()]

    # 生成 SQL 插入语句的占位符
    placeholders = ', '.join(['%s'] * len(filtered_columns))
    # insert_sql = f"INSERT INTO `{table_name}` ({', '.join(filtered_columns)}) VALUES ({placeholders})"
    insert_sql = f"INSERT INTO `{table_name}` ({', '.join([f'`{col}`' for col in filtered_columns])}) VALUES ({placeholders})"
    logging.info(f"准备插入数据到表 `{table_name}`。")
    # 将DataFrame转换为适合批量插入的格式
    rows_to_insert = df[columns].values.tolist()

    try:
        # 批量插入数据，按批次分割
        for i in range(0, len(rows_to_insert), batch_size):
            batch = rows_to_insert[i:i + batch_size]
            cursor.executemany(insert_sql, batch)
            conn.commit()  # 每次提交一个批次
            logging.info(f" 已导入 {i + len(batch)} / {len(rows_to_insert)} 条数据...\n")

        logging.info(f"数据已成功批量导入到表 `{table_name}` 中！\n")

    except mysql.connector.Error as err:
        logging.error(f" 回滚插入。导入数据时发生错误: {err}\n")
        conn.rollback()  # 如果出现错误，回滚事务
    finally:
        cursor.close()