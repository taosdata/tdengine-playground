import os

import numpy as np
import pandas as pd
from tqdm import tqdm

file_list = []
data_list = []

for dirname, _, filenames in os.walk('./archive_data'):
    for filename in filenames:
        file_list.append(os.path.join(dirname, filename))
        print(os.path.join(dirname, filename))

for i in file_list:
    df1 = pd.read_csv(i, delimiter=',', header=None)
    data_list.append(df1)
    print(df1)

import taos
from datetime import datetime


# note: lines have already been sorted by table name
# lines = [('d1001', '2018-10-03 14:38:05.000', 10.30000, 219, 0.31000, 'California.SanFrancisco', 2),
#          ('d1001', '2018-10-03 14:38:15.000', 12.60000, 218, 0.33000, 'California.SanFrancisco', 2)]


def get_ts(ts: str):
    # dt = datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
    dt = datetime.strptime(ts, '%Y-%m-%dT%H:%M:%S.%f')  # 存档数据需要 同步数据不需要
    return int(dt.timestamp() * 1000)


# sensor_id,lat,lon,timestamp,pressure,temperature,humidity

def create_stable():
    conn = taos.connect()
    try:
        conn.execute("CREATE DATABASE transport")
        conn.execute(
            "CREATE STABLE transport.gps (ts TIMESTAMP, type nchar(10), latitude float, longitude float, vehicle_id int) "
            "TAGS (line_number nchar(10))")
    finally:
        conn.close()


# !!!note: lines have already been sorted by table name
def bind_row_by_row(stmt: taos.TaosStmt):
    tb_name = None
    for row in tqdm(df1.values.tolist()[:100000]):  # todo 最多一次十万t
        if tb_name != 'd' + str(row[2]):
            tb_name = 'd' + str(row[2])
            tags: taos.TaosBind = taos.new_bind_params(1)
            tags[0].nchar(row[2])  # line_number
            stmt.set_tbname_tags(tb_name, tags)
        values: taos.TaosBind = taos.new_bind_params(5)
        values[0].timestamp(get_ts(row[6]))
        values[1].nchar(row[3])
        values[2].float(row[4])
        values[3].float(row[5])
        values[4].int(row[1])
        stmt.bind_param(values)


def insert_data():
    conn = taos.connect(database="transport")
    try:
        stmt = conn.statement("INSERT INTO ? USING gps TAGS(?) VALUES(?, ?, ?, ?,?)")
        bind_row_by_row(stmt)
        stmt.execute()
        stmt.close()
    finally:
        conn.close()


if __name__ == '__main__':
    # create_stable()
    dataset = pd.concat(data_list, ignore_index=False)
    dataset.sort_values(by=2, axis=0, inplace=True)
    insert_data()
