import csv
import datetime

import requests

res = requests.get('https://api.luftdaten.info/static/v2/data.temp.min.json')
# https://api.luftdaten.info/static/v2/data.dust.min.json #pm数据

res = res.json()
res_data = []
for i in res:
    temp_dict = {j['value_type']: j['value'] for j in i['sensordatavalues']}
    # res_data.append({
    #     'sensor_id': i['sensor']['id'],
    #     'location': i['location']['id'],
    #     'lat': i['location']['latitude'],
    #     'lon': i['location']['longitude'],
    #     'timestamp': i['timestamp'],
    #     'pressure': temp_dict.get('pressure'),
    #     'temperature': temp_dict.get('temperature'),
    #     'humidity': temp_dict.get('humidity'),
    #     # 'P1': temp_dict.get('P1'),
    #     # 'P2': temp_dict.get('P2')
    # })
    res_data.append([
        i['sensor']['id'],
        # i['location']['id'],
        i['location']['latitude'],
        i['location']['longitude'],
        i['timestamp'],
        temp_dict.get('pressure'),
        temp_dict.get('temperature'),
        temp_dict.get('humidity')
    ])
pass

with open('./sync_data/'+datetime.datetime.now().strftime('%Y-%m-%d-%H:%M:%S') + '.csv', 'w+', newline='') as f:
    writer = csv.writer(f)
    writer.writerows(res_data)
