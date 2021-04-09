import json
import time
from typing import List, Union
from IoV_Handler.client_func import *

'''
// server to car
#define UNLOCK_READY 		0		// 租车请求
#define HASH_PUSH			1		// 同步密钥/生物识别信息
#define RTN_CAR				2		// 归还车辆
// car to server
#define LOG_SYNC			3		// 车辆同步日志
// both
#define REPLY_MSG			4		// 回应消息
// #define UNEXPECTED_DATA	5	    // 数据错误(不要把这个回给服务器，自己处理)
#define CHECK_HASH          6       // 进行生物校验，用于本地事件

server: 0
car:    4
server: 1
car:    4

car:    3
server: 5
(要是没发出去就忽略掉x)

server: 2
car:    4
'''

UNLOCK_READY = 0
PUSH_HASH = 1
RTN_CAR = 2
LOG_SYNC = 3
REPLY_MSG = 4
UNEXPECTED_DATA = 5
CHECK_HASH = 6


def decrypt(data: Union[str, bytes], *args) -> Union[str, bytes]:
    # 解密部分
    return data


def encrypt(data: Union[str, bytes], *args) -> Union[str, bytes]:
    # 加密部分
    return data


def json_data_constructor(event: int, data: str, status_code:int, timestamp: int) -> dict:
    # 构造json
    return {
        "event": event,
        "data": data,
        "status_code": status_code,
        "timestamp:": timestamp
    }


def json_parser(data: str) -> List:
    # 处理接受的数据
    try:
        data = decrypt(data)
        json_data = json.loads(data)
        return [json_data["event"], json_data["data"], json_data["status_code"], json_data["timestamp"]]
    except json.JSONDecodeError as e:
        return [UNEXPECTED_DATA, "Unexpected data format!", int(time.time())]
    except KeyError as e:
        return [UNEXPECTED_DATA, "Missing Value", int(time.time())]


def event_handler(handler, data: str) -> Union[str, bytes]:
    # 感觉降低websocket模块和这边事件处理模块的耦合挺重要的，要不然debug起来简直就是一堆大屎山
    # 每一次ws模块收到message之后，就会调用这里的函数event_handler，传入一个被加密的参数data
    # 如果需要额外发送数据的话可以直接回调handler的 *_time_tasker 方法
    # 这样子避免修改ws模块的内容（我也不想修改了）
    # 事件处理
    # 1. producer方法通过websocket接收到服务器端发送的消息，存入message_queue队列中。
    # 2. processor按照顺序读取message_queue中的数据，发送到这里处理。
    # 3. 这里处理完了生成数据发送回去，交由consumer进行发送等操作。

    # 事件ID，数据（可以为空字符串），状态码（0为正常），时间戳
    [event, dat, status_code, timestamp] = json_parser(data)

    if timestamp > time.time() or timestamp < time.time() - 60:
        # 时间戳异常
        return encrypt(json.dumps(
            json_data_constructor(
                REPLY_MSG,
                "INCORRECT_TIMESTAMP",
                1,
                time.time()
            )
        ))

    msg = ""
    status_code = 0
    if event == UNLOCK_READY:
        if handler.checkOccupationState():  # 如果已经被占用，那多半是这边或者数据库挂了
            msg = "vehicle already occupied? check database status?"
            status_code = 1
            reply_id = REPLY_MSG
        else:   # 正常分支
            # function for rent the car
            msg = "set status unlock successfully"
            handler.set_status_occupied()
            reply_id = REPLY_MSG
        
    elif event == PUSH_HASH:
        msg = "recv hash info successfully"
        # recv feature data
        set_bio_hash(data)
        reply_id = REPLY_MSG
        handler.set_time_task("bio check", CHECK_HASH, 30, "")

    elif event == RTN_CAR:
        if handler.checkOccupationState():
            msg = "set status lock successfully"
            clear_local_data()
            handler.set_status_idle()
            handler.delete_time_task("bio check")
            status_code = 0
        else:
            msg = "vehicle not rented yet? check database status?"
            status_code = 1
        # return the car
        reply_id = REPLY_MSG

    elif event == LOG_SYNC:
        # sync logs
        reply_id = LOG_SYNC
        msg = send_log_data()
        status_code = 0
        
    elif event = CHECK_HASH:
        reply_id = REPLY_MSG
        msg = "doing bio hash check"
        status_code = 0
        check_hash()

    else:  # UNEXPECTED STATUS
        # other situations
        msg = "UNEXPECTED_STATUS"
        status_code = 1
        reply_id = REPLY_MSG

    # 返回值
    # 所有返回值都是 encrypt({事件ID，消息，时间戳})的格式
    return encrypt(
        json.dumps(
            json_data_constructor(
                reply_id, 
                msg,
                status_code, 
                time.time()
                )
            )
        )
    # 然后在ws模块中再加以处理成 {车辆id，加密的payload} 格式发送给服务器


def initialize_process(handler) -> None:
    handler.set_time_task("log_sync", 3, 10, "sync data")
