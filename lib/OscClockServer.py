
import time
import datetime
import math

from pythonosc import udp_client
from pythonosc import dispatcher
from pythonosc import osc_server

import threading
Osclock = threading.RLock()

#buttonの立ち上がり、立ち下り、現在の状態を記録するクラス。
class OscButton():
    def __init__(self):
        self.button_up = False
        self.button_fall = False
        self.button_state = False
    #立ち下がりと立ち上がりを記録して、現在のbuttonの状態を取得する。
    def SetButtonState(self, args,state):
        #bool型以外は受け付けない
        #できるだけ脆弱性をつかれないように（一応サーバーだからね）
        if (type(state) is bool):
            print("[{0}] ~ {1}".format(args, state))
            with Osclock:
                self.button_fall = True if self.button_state and (not(state)) else self.button_fall
                self.button_up = True if (not(self.button_state)) and state else self.button_up
                self.button_state = state
            
    #立ち上がりを行ったかどうかを取得後、立ち上がりのフラグをリセットする。
    def GetButtonUp(self):
        tmp = self.button_up
        with Osclock:
            self.button_up = False 
        return tmp

    #立ち下がりを行たかどうかを取得後、立下りのフラグをリセットする。
    def GetButtonFall(self):
        tmp = self.button_fall
        with Osclock:
            self.button_fall = False 
        return tmp


#VRCのクライアントからのOSCの通信を受信するサーバー
class OscClockServer():
    def __init__(self,ip_str,port_int):
        self.second = 0
        self.minute = 0
        self.hour = 0
        self.select_button = OscButton()
        self.start_button = OscButton()
        self.bell_button = OscButton()
        self.hour_bell_button = OscButton()
        self.ip_str = ip_str
        self.port_int = port_int
    def SetServer(self):
        #サーバーの準備
        dispatcher_ = dispatcher.Dispatcher()
        dispatcher_.map("/avatar/parameters/second", self.GetOscSecond)
        dispatcher_.map("/avatar/parameters/minute", self.GetOscMinute)
        dispatcher_.map("/avatar/parameters/hour", self.GetOscHour)
        dispatcher_.map("/avatar/parameters/select", self.select_button.SetButtonState)
        dispatcher_.map("/avatar/parameters/start", self.start_button.SetButtonState)
        dispatcher_.map("/avatar/parameters/bell", self.bell_button.SetButtonState)
        dispatcher_.map("/avatar/parameters/hour_bell", self.hour_bell_button.SetButtonState)
        
        self.server = osc_server.ThreadingOSCUDPServer(
            (self.ip_str , self.port_int), dispatcher_)
    #予想外の値が入力されたときに回避するため
    #できるだけ脆弱性をつかれないように（一応サーバーだからね）
    def CheckType(self,value):
        return (True if ((type(value) is float) & ((0 <= value) & (value <= 1))) else False)
    def GetOscSecond(self,args, volume):
        self.second = volume if self.CheckType(volume) else self.second
        print("[{0}] ~ {1}".format(args, volume))

    def GetOscMinute(self,args, volume):
        self.minute = volume if self.CheckType(volume) else self.minute
        print("[{0}] ~ {1}".format(args, volume))

    def GetOscHour(self,args, volume):
        self.hour = volume if self.CheckType(volume) else self.hour
        print("[{0}] ~ {1}".format(args, volume))



if __name__ == "__main__":
   test_class = OscClockServer("127.0.0.1",9001)
   test_class.SetServer()
   test_class.server.serve_forever()