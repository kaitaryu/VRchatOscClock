
import time
import datetime
import math

from pythonosc import udp_client
from pythonosc import dispatcher

from lib.OscClockServer import * 
import threading
import sys

#0をそのまま入力するとなぜかfloatの最大が入力されるのでbinary32のイプシロンをZEROとする使う
ZERO = 1.193e-7



#OSCストップウォッチを動作させるためのクラス。
class OscStopwatch():
    def __init__(self,client,server):
        self.client = client
        self.server = server

        self.start_date = None
        self.second = 0
        self.minute = 0
        self.hour = 0
        
        self.next_state_list = [1,2,3,1,5,0]
        self.state = 0
        self.function_list = [  self.Reset,
                                self.StopwathSetting,
                                self.StopwathStandby,
                                self.StopwathStart,
                                self.StopwathStartBell,
                                self.StopwathWateBell]
    def MoveState(self):
        #start_classから立ち下がりがあったかどうか
        if self.server.start_button.GetButtonFall():
            self.state = self.next_state_list[self.state]

    def ResetSub(self):
        #取り出してリセットしておく
        self.server.start_button.GetButtonFall()
        self.second = ZERO
        self.minute = ZERO
        self.hour = ZERO
        self.state = 0
        self.client.send_message("/avatar/parameters/second", self.second)
        self.client.send_message("/avatar/parameters/minute", self.minute)
        self.client.send_message("/avatar/parameters/hour", self.hour)
        self.client.send_message("/avatar/parameters/bell", False)
  
    def Reset(self):

        self.ResetSub()
        while not((abs(self.server.second) <= ZERO) and 
                    (abs(self.server.minute) <= ZERO) and 
                    (abs(self.server.hour) <= ZERO) and 
                    (not(self.server.start_button.button_state))):
            self.ResetSub()
            time.sleep(0.1)
        self.state = 1
    def StopwathSetting(self):
        #ベルが鳴ったらfalseにしておく
        if self.server.bell_button.button_state:
            self.client.send_message("/avatar/parameters/bell", False)
        #変化があったときのみ状態を変える
        #float型だから注意
        if ((abs(self.second - self.server.second) <= ZERO) and 
            (abs(self.minute - self.server.minute) <= ZERO) and 
            (abs(self.hour - self.server.hour) <= ZERO)):
            time.sleep(0.1)
            return
        #現在の状態を取得
        self.second = self.server.second
        self.minute = self.server.minute
        self.hour = self.server.hour

        #そのままだと時分秒の関係ずれているので、直す
        self.second = math.floor(self.second * 60)/60
        if self.second + ZERO > 1:
            self.second = 1 - ZERO
        
        self.minute = (math.floor(self.minute * 60) + self.second)/60
        if self.minute + ZERO > 1:
            self.minute = 1 - ZERO

        self.hour = (math.floor(self.hour * 24) +  self.minute)/24
        if self.hour + ZERO > 1:
            self.hour = 1 - ZERO
        #直した状態を送信する。
        self.client.send_message("/avatar/parameters/second", self.second)
        self.client.send_message("/avatar/parameters/minute", self.minute)
        self.client.send_message("/avatar/parameters/hour", self.hour)

        print(self.hour,self.minute,self.second)
        #頻繁に送信すると負荷がかかるのでかかるので0.1秒待つ
        time.sleep(0.1)

    def StopwathStandby(self):
        self.start_date = datetime.datetime.now()
        self.state += 1

    def StopwathStart(self):
        dt_progress = datetime.datetime.now() - self.start_date
        try:
            dt_progress = datetime.datetime.strptime(str(dt_progress), "%H:%M:%S.%f")
        except:
            dt_progress = datetime.datetime.strptime(str(dt_progress), "%H:%M:%S")
        
        second_progress = (dt_progress.second /60) +  (dt_progress.microsecond / 60000000)
        minute_progress = (dt_progress.minute / 60) + (second_progress / 60)
        hour_progress = (dt_progress.hour/24) +  (minute_progress / 24)
        
        hour = self.hour - hour_progress if (self.hour - hour_progress) > ZERO else ZERO
        minute = (hour*24 - math.floor(hour*24))
        second = (minute * 60 - math.floor(minute*60))

        #直した状態を送信する。
        self.client.send_message("/avatar/parameters/second", second)
        self.client.send_message("/avatar/parameters/minute", minute)
        self.client.send_message("/avatar/parameters/hour", hour)
        #ベルが鳴ったらfalseにしておく
        if self.server.bell_button.button_state:
            self.client.send_message("/avatar/parameters/bell", False)
        time.sleep(0.2)
        #タイマーが時間切れになったら次の状態に移行する
        if hour <= ZERO:
            self.second = ZERO
            self.minute = ZERO
            self.hour = ZERO
            self.client.send_message("/avatar/parameters/second", self.second)
            self.client.send_message("/avatar/parameters/minute", self.minute)
            self.client.send_message("/avatar/parameters/hour", self.hour)
            self.state += 1
    def StopwathStartBell(self):
        #現在時刻を取得したのち、bellを鳴らす。
        self.start_date = datetime.datetime.now()
        #buttonがFalseだったらTrueにする
        while not(self.server.bell_button.button_state):
            self.client.send_message("/avatar/parameters/bell", True)
            time.sleep(0.1)
        self.state += 1
    def StopwathWateBell(self):
        dt_progress = datetime.datetime.now() - self.start_date
        try:
            dt_progress = datetime.datetime.strptime(str(dt_progress), "%H:%M:%S.%f")
        except:
            dt_progress = datetime.datetime.strptime(str(dt_progress), "%H:%M:%S")        
        
        #bellを鳴らすフラグが降りたら
        if (not(self.server.bell_button.button_state)) or (dt_progress.minute >= 1):
            self.state = self.next_state_list[self.state]
        time.sleep(0.2)
    def OscStopwathMain(self):
        self.MoveState()
        self.function_list[self.state]()
        

class OscClock():
    def __init__(self,client,server):
        self.client = client
        self.server = server
    def Timer(self):
        dt_now = datetime.datetime.now()
        second = (dt_now.second /60) +  (dt_now.microsecond / 60000000)
        minute = (dt_now.minute / 60) + (second / 60)
        hour  =  (dt_now.hour/24) +  (minute / 24)
        
        #ベルが鳴ったらfalseにしておく
        if self.server.bell_button.button_state:
            self.client.send_message("/avatar/parameters/bell", False)
        self.client.send_message("/avatar/parameters/second", second)
        self.client.send_message("/avatar/parameters/minute", minute)
        self.client.send_message("/avatar/parameters/hour", hour)
        print(hour,minute,second)
        #アラームを入れる予定
        
        time.sleep(0.2)

class OscClockClient():
    def __init__(self,ip_str,port_str,server):
        self.client = udp_client.SimpleUDPClient(ip_str,port_str)
        self.server = server
        
        self.osc_clock = OscClock(self.client,self.server)
        self.osc_stopwatch = OscStopwatch(self.client,self.server)

        self.thread = threading.Thread(target = self.MoveOscClock)
        
        self.MOVE_THREADING = True

        self.next_state_list = [1,2,3,0]
        self.state = 0
        self.function_list = [  self.osc_clock.Timer,
                                self.osc_stopwatch.ResetSub,
                                self.osc_stopwatch.OscStopwathMain,
                                self.osc_stopwatch.ResetSub,]
    def MoveState(self):
        #前回resetを踏んでいたら1つstateを進める。
        if self.state == 1:
            self.state = self.next_state_list[self.state]
        if self.state == 3:
            self.state = self.next_state_list[self.state]
        #server_classから立ち下がりがあったときに状態を次に進める
        if self.server.select_button.GetButtonFall():
            self.state = self.next_state_list[self.state]

    def MoveThreading(self):
        self.thread.start()

    def MoveOscClock(self):
        while self.MOVE_THREADING:
            self.OneMove()
        
    def OneMove(self):
        self.MoveState()
        self.function_list[self.state]()
        #


if __name__ == "__main__":
    test_server = OscClockServer("127.0.0.1",9001)
    test_client = OscClockClient("127.0.0.1",9000,test_server)

    test_client.MoveThreading()
    
    test_server.SetServer()
    try:
        test_server.server.serve_forever()
    except KeyboardInterrupt:
        MOVE_THREADING = False
        test_client.thread.join(2)

