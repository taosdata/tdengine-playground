import os

import numpy as np
import pandas as pd
from tqdm import tqdm

file_list = []
data_list = []

for dirname, _, filenames in os.walk('./sync_data'):
    for filename in filenames:
        file_list.append(os.path.join(dirname, filename))
        print(os.path.join(dirname, filename))

for i in file_list:
    df1 = pd.read_csv(i, delimiter=',', header=None)
    data_list.append(df1)
    # df1.drop(labels=['Unnamed: 0', 'location'], axis=1, inplace=True)#存档数据需要 同步数据不需要
    print(df1)

import taos
from datetime import datetime


# note: lines have already been sorted by table name
# lines = [('d1001', '2018-10-03 14:38:05.000', 10.30000, 219, 0.31000, 'California.SanFrancisco', 2),
#          ('d1001', '2018-10-03 14:38:15.000', 12.60000, 218, 0.33000, 'California.SanFrancisco', 2)]


def get_ts(ts: str):
    dt = datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
    # dt = datetime.strptime(ts, '%Y-%m-%dT%H:%M:%S')#存档数据需要 同步数据不需要
    return int(dt.timestamp() * 1000)


# sensor_id,lat,lon,timestamp,pressure,temperature,humidity

def create_stable():
    conn = taos.connect()
    try:
        conn.execute("CREATE DATABASE weather")
        conn.execute("CREATE STABLE weather.sensor (ts TIMESTAMP, pressure DOUBLE,temperature float,humidity float) "
                     "TAGS (lat float, lon float)")
    finally:
        conn.close()


# !!!note: lines have already been sorted by table name
def bind_row_by_row(stmt: taos.TaosStmt):
    tb_name = None
    for row in tqdm(df1.values.tolist()[:100000]):  # todo 最多一次十万t
        if tb_name != 'd' + str(row[0]):
            tb_name = 'd' + str(row[0])
            tags: taos.TaosBind = taos.new_bind_params(2)  # 2 is count of tags
            tags[0].float(row[1])  # lat
            tags[1].float(row[2])  # lon
            stmt.set_tbname_tags(tb_name, tags)
        values: taos.TaosBind = taos.new_bind_params(4)  # 4 is count of columns
        values[0].timestamp(get_ts(row[3]))
        if np.isnan(row[4]):
            values[1].double(None)
        else:
            values[1].double(row[4])

        if np.isnan(row[5]):
            values[2].float(None)
        else:
            values[2].float(row[5])

        if np.isnan(row[6]):
            values[3].float(None)
        else:
            values[3].float(row[6])

        stmt.bind_param(values)


def insert_data():
    conn = taos.connect(database="weather")
    try:
        stmt = conn.statement("INSERT INTO ? USING sensor TAGS(?, ?) VALUES(?, ?, ?, ?)")
        bind_row_by_row(stmt)
        stmt.execute()
        stmt.close()
    finally:
        conn.close()


if __name__ == '__main__':
    # create_stable() #首次导入需要
    dataset = pd.concat(data_list, ignore_index=False)
    dataset.sort_values(by=0, axis=0, inplace=True)

    insert_data()
