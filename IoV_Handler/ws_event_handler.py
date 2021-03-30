import json
import time
from typing import List

'''
// server to car
#define UNLOCK_READY 		0		// 租车请求
#define HASH_PUSH			1		// 同步密钥/生物识别信息
#define RTN_CAR				2		// 归还车辆
// car to server
#define LOG_SYNC			3		// 车辆同步日志
// both
#define STATUS_SYNC			4		// 车辆和服务器同步状态
#define REPLY_MSG			5		// 回应消息
// #define UNEXPECTED_DATA	6	    // 数据错误(不要把这个回给服务器，自己处理)

server: 0
car:    5
server: 1
car:    5

car:    3
server: 5
(要是没发出去就忽略掉x)

server: 2
car:    5
'''

UNLOCK_READY = 0
PUSH_HASH = 1
RTN_CAR = 2
LOG_SYNC = 3
REPLY_MSG = 4
STATUS_SYNC = 5
UNEXPECTED_DATA = 6


def decrypt(data, *args):
    # 解密部分
    return data


def encrypt(data, *args):
    # 加密部分
    return data


def json_data_constructor(event: int, data: str, timestamp: int) -> dict:
    # 构造json
    return {
        "event": event,
        "data": data,
        "timestamp:": timestamp
    }


def json_parser(data: str) -> List:
    # 处理接受的数据
    try:
        data = decrypt(data)
        json_data = json.loads(data)
        return [json_data["event"], json_data["data"], json_data["timestamp"]]
    except json.JSONDecodeError as e:
        return [UNEXPECTED_DATA, "Unexpected data format!", int(time.time())]
    except KeyError as e:
        return [UNEXPECTED_DATA, "Missing Value", int(time.time())]


def event_handler(data: str) -> str:
    # 事件处理
    # 1. producer方法通过websocket接收到服务器端发送的消息，存入message_queue队列中。
    # 2. processor按照顺序读取message_queue中的数据，发送到这里处理。
    # 3. 这里处理完了生成数据发送回去，交由consumer进行发送等操作。
    [event, dat, timestamp] = json_parser(data)

    msg = ""
    data_to_diliver={'signal':None,'data_to_send':None}
    if event == UNLOCK_READY:
        # function for rent the car
        msg = "i'm ok!"
        reply_id = REPLY_MSG
        data_to_diliver['data_to_send'] = encrypt(json.dumps(json_data_constructor(reply_id, msg, int(timestamp))))

    elif event == PUSH_HASH:
        # recv feature data
        reply_id = REPLY_MSG
        data_to_diliver['signal']='PREPARE_FOR_BLUETOOTH'

    elif event == RTN_CAR:
        # return the car
        reply_id = REPLY_MSG

    elif event == STATUS_SYNC:
        # sync status / send heart beat pkgs
        reply_id = STATUS_SYNC

    elif event == LOG_SYNC:
        # sync logs
        reply_id = LOG_SYNC

    elif event == 'PREPARE_FOR_BLUETOOTH':
        # sync
        data_to_diliver['signal']='UNLOCKED'

    elif event== 'SS':
        reply_id = LOG_SYNC
        msg='' #the right face or not

    else:  # UNEXPECTED STATUS
        # other situations
        reply_id = REPLY_MSG

    return data_to_diliver


def initialize_process(handler) -> None:
    handler.set_time_task("log_sync", 3, 10, "sync data")
