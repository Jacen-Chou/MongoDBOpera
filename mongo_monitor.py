# -*- coding: UTF-8 -*-

# 连接李佳的MySQL数据库，读取数据

import pymongo
import pymysql
import datetime

'''
"ins_id": 设备号，根据设备号查找设备
"time": 监测时间
"value": 监测值
"status": 状态，暂定都为True
'''

nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 现在时间
print("========" + str(nowTime) + "========")

# 建立MySQL连接
conn = pymysql.connect(
    host="202.204.62.229",
    port=3308,
    user="root",
    password="admin",
    db="buffer",
    charset="utf8",
    autocommit=True
)

# 建立Mongodb连接
client = pymongo.MongoClient(
    "mongodb://202.204.62.229:27017/nfca_db",
    username='nfca',
    password='nfca'
)
db = client["nfca_db"]
col_1 = db["point"]
col_2 = db["gms_monitor"]
col_3 = db["warning_log"]

# 得到一个可以执行SQL语句的光标对象
cursor = conn.cursor()

# 定义要执行的SQL语句
sql_1 = "select * from gms_monitor"

# 执行SQL语句
cursor.execute(sql_1)
result = cursor.fetchall()
# 根据tag,找到对应id,再插入数据
for r in result:
    point = col_1.find_one({"opc_tag": r[1]})
    point_id = point["point_id"]
    instrument = point["instrument"]
    value_min = point["value_min"]
    value_max = point["value_max"]
    alarm = False  # 默认数据处在正常范围内
    monitoring_value = r[3]
    time = r[2]

    # 如果是泵，原始监测值会是很长一串，则将泵的原始监测值转换为0/1
    if point["instrument"] == "Valve":
        monitoring_value = (int(monitoring_value) >> 20) & 1

    if not value_min <= r[3] <= value_max:  # 数据超出正常范围就记录到报警日志表
        warning = {
            "point_id": point_id,
            "instrument": instrument,
            "time": datetime.datetime.strptime(str(time), '%Y-%m-%d %H:%M:%S'),
            "principal": 1,
            "value_min": value_min,
            "value_max": value_max,
            "Monitoring_value": monitoring_value
        }
        col_3.insert_one(warning)
        alarm = True
        print(str(r[2]) + "  数据异常，插入报警日志表.")
    # 插入数据到监测表
    monitor = {
        "point_id": point_id,
        "instrument": instrument,
        "time": datetime.datetime.strptime(str(time), '%Y-%m-%d %H:%M:%S'),
        "Monitoring_value": monitoring_value,
        "alarm": alarm
    }
    col_2.insert_one(monitor)
    sql_2 = "DELETE FROM gms_monitor WHERE id = %d" % r[0]
    cursor.execute(sql_2)
    print(str(r[2]) + "  monitor数据插入并删除成功.")

# 关闭光标对象
cursor.close()

# 关闭数据库连接
conn.close()
client.close()
