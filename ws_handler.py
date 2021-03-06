import asyncio
import json
import time

import websockets

from IoV_Handler import ws_event_handler


class ws_handler():
    '''
    websockets 通信类
    '''
    def __init__(self, url):
        '''
        构造类
        :param url: 连接的服务器url
        '''
        self.__message_queue = []  # 接收的消息队列
        self.__send_queue = []  # 发送的消息队列
        self.__websocket = None  # 用来操作的websocketsClientProtocol对象
        self.__running_list = {}  # 定时任务队列
        self.__url = url  # 服务器url
        self.__occupiedState = False  # 被占用状态，用于本地和服务器的同步状态确定
        self.__connection_state = False
        try:
            with open("session_key", "r") as key_file:
                data = key_file.read()
                self.__CAR_ID = data.split('\n')[0]
                self.__CAR_PRIVATE_SESSION_KEY = data.split('\n')[1]
                print("on start:\nid:{}\nprivate_session_key:{}".format(self.__CAR_ID,self.__CAR_PRIVATE_SESSION_KEY))
        except FileNotFoundError:  # 极端情况，估计不会发生……
            print()
            exit

    async def __producer_handler(self) -> None:
        '''
        生产者，接收消息，放入消息队列__message_queue
        :return:
        '''
        msg = await self.__websocket.recv()
        print("recv msg" + msg)
        self.__message_queue.append(msg)

    async def __processor_handler(self) -> None:
        '''
        加工者，从消息队列__message_queue中抓取最早的信息，进行处理之后放入待发送队列__send_queue
        :return:
        '''
        if not self.__message_queue:
            return
        msg = ws_event_handler.event_handler(self, self.__message_queue[0])  # 这里是调用消息处理的函数
        self.__message_queue.remove(self.__message_queue[0])
        self.__send_queue.append(msg)

    async def __consumer_handler(self) -> None:
        '''
        消费者，从待发送队列中抓取信息发送给服务器。
        :return:
        '''
        for msg in self.__send_queue:
            try:
                data = json.dumps(dict(
                    id=self.__CAR_ID,
                    data=msg
                ))
                await self.__websocket.send(data)
            except Exception as e:
                print("An exception occurred when processing the msg to be send\n{}".format(e))
                return  # 万一没发送成功，那就不remove消息队列里面的东西了
                # 不过有一说一，我感觉这句话没啥用
            self.__send_queue.remove(msg)
            print("send_msg: " + str(msg) + "at" + str(time.time()))

    async def __handler(self) -> None:
        '''
        内部类，调用生产、加工、消费
        :return:
        '''
        # print("entering handler")
        consumer_task = asyncio.ensure_future(
            self.__producer_handler()
        )
        processor_task = asyncio.ensure_future(
            self.__processor_handler()
        )
        producer_task = asyncio.ensure_future(
            self.__consumer_handler()
        )
        _, pending = await asyncio.wait(
            [consumer_task, processor_task, producer_task],
            return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()

    def checkOccupationState(self) -> bool:
        return self.__occupiedState

    async def start(self, interval_time = 1) -> None:
        '''
        开始client的ws交互操作。
        1、开启连接（如果失败就重试
        2、处理定时任务
        3、收发消息
        :param interval_time: 每次接受消息，发送消息清空队列之间的时间间隔，如果性能吃不消的话稍微提高一点。
        :return:
        '''
        for i in self.__running_list:
            self.__running_list[i]["timestamp"] = time.time()  # 每次启动的时候开始更新定时任务
        while True:
            try:
                self.__websocket = await  websockets.connect(self.__url)
                break
            except ConnectionError:
                await asyncio.sleep(1)
        while True:
            if self.__send_queue!=[]:
                print(self.__send_queue)
            if self.__message_queue!=[]:
                print(self.__message_queue)
            for tasks in self.__running_list:
                # 笨方法
                if time.time() - self.__running_list[tasks]["timestamp"] > self.__running_list[tasks]["interval"]:
                    self.add_msg_queue(
                        {
                            "event": self.__running_list[tasks]["msg_type"],
                            "data": self.__running_list[tasks]["data"],
                            "status_code": 0,
                            "timestamp": time.time()
                        })
                    self.__running_list[tasks]["timestamp"] = time.time()
            # start main #
            try:
                await asyncio.sleep(interval_time)
                await self.__websocket.ensure_open()
                await self.__handler()
            #  end  main #
            except websockets.ConnectionClosed:
                print("unexpected websocket close!")
                await self.__processor_handler()
                await asyncio.sleep(1)
                try:
                    self.__websocket = await websockets.connect(self.__url)
                except:
                    pass

    async def close(self):
        '''
        关闭socket连接（客户端应该没必要整这些
        :return:
        '''
        await self.__websocket.close()

    def add_msg_queue(self, msg):
        '''
        向消息队列中添加数据
        :param msg: 字符串或者字典格式的消息
        :return:
        '''
        print("add msg to queue" + str(msg))
        if type(msg) == str:
            self.__message_queue.append(msg)
        elif type(msg) == dict:
            self.__message_queue.append(json.dumps(msg))
        else:
            raise TypeError

    def set_time_task(self, ID, msg_type, interval, data=""):
        '''
        设定定时任务，这里把定时任务数据也直接加进了消息队列，和服务器发过来的指令一样去处理。
        :param ID: 任务名称（唯一表示
        :param msg_type: 任务类型：数字，见ws_event_handler
        :param interval: 任务触发的时间间隔
        :param data: 数据（没有必要）
        :return:
        '''
        self.__running_list[ID] = {
            "msg_type": msg_type,
            "interval": interval,
            "data": data,
            "timestamp": 0
        }

    def delete_time_task(self, ID):
        """
        根据事件ID删除定时任务，若ID不存在，则忽略。
        :param ID: 任务ID（唯一标识
        :return: None
        """
        try:
            self.__running_list.remove(ID)
        except IndexError:
            pass

    def clear_time_task(self):
        """
        清除定时任务队列。
        :return: None
        """
        self.__running_list = {}

    def get_car_id(self) -> int:
        """
        返回对应的车辆id
        """
        return self.__CAR_ID

    def get_session_key(self) -> str:
        """
        返回车辆对应的session key。。。
        """
        return self.__CAR_PRIVATE_SESSION_KEY

    def set_status_occupied(self) -> None:
        """
        设置本地状态为借出。
        """
        self.__occupiedState = True

    def set_status_idle(self) -> None:
        """
        设置本地状态为可用。
        """
        self.__occupiedState = False