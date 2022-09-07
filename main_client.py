
#Copyright (c) 2022 Tomato Lycoris

from pythonosc import udp_client
from lib.OscClockServer import * 
from lib.OscClockClient import * 


if __name__ == "__main__":
    server = OscClockServer("127.0.0.1",9001)
    client = OscClockClient("127.0.0.1",9000,server)

    client.MoveThreading()
    
    server.SetServer()
    try:
        server.server.serve_forever()
    except KeyboardInterrupt:
        client.MOVE_THREADING = False
        client.thread.join(1)
