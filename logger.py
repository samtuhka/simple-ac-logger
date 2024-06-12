# -*- coding: utf-8 -*-

import socket
import time
import struct
import sys
import os
import logging
import json


from base64 import b64encode
from threading import Thread
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

def make_logfiles(root = "./log", info = ""):
    now = datetime.now()
    folder = now.strftime("%d-%m-%Y--%H-%M-%S-%f")

    directory = os.path.join(root, folder)
    raw_path = os.path.join(directory, "raw.csv")
    parsed_path = os.path.join(directory, "parsed.csv")
    
    info_path = os.path.join(directory, "info.json")
    
    if not os.path.exists(directory):
        os.makedirs(directory)
        raw_file = open(raw_path, "w")
        parsed_file = open(parsed_path, "w")
        
        if len(info) > 0:
            _, parsed = parse_message(info)  
            
            info_file = open(info_path, "w")
            log_ts = time.time()

            r = b64encode(info)
            info_string = b64encode(info).decode('utf-8')

            info_dict = {"log_ts": log_ts, "car":parsed[0], "user": parsed[1], "identifier": parsed[2], "version": parsed[3], "track": parsed[4], "track_config": parsed[5], "raw_info": info_string}
            json.dump(info_dict, info_file)
        
        var_names = "time,speedKmh,speedMph,speedMs,"\
            "isAbsEnabled,isAbsInAction,isTcInAction,isTcEnabled,isInPit,isEngineLimiterOn,"\
            "accGVertical,accGHorizontal,accGFrontal,lapTime,lastLap,bestLap,lapCount,gas,brake,clutch,engineRPM,steer,gear,cgHeight,"\
            "wheelAngularSpeed1,wheelAngularSpeed2,wheelAngularSpeed3,wheelAngularSpeed4, slipAngle1,slipAngle2,slipAngle3,slipAngle4,"\
            "slipAngleContactPatch1,slipAngleContactPatch2,slipAngleContactPatch3,slipAngleContactPatch4,"\
            "slipRatio1,slipRatio2,slipRatio3,slipRatio4,tyreSlip1,tyreSlip2,tyreSlip3,tyreSlip4,ndSlip1,ndSlip2,ndSlip3,ndSlip4,"\
            "load1,load2,load3,load4,Dy1,Dy2,Dy3,Dy4,Mz1,Mz2,Mz3,Mz4,tyreDirtyLevel1,tyreDirtyLevel2,tyreDirtyLevel3,tyreDirtyLevel4,"\
            "camberRAD1,camberRAD2,camberRAD3,camberRAD4,tyreRadius1,tyreRadius2,tyreRadius3,tyreRadius4,"\
            "tyreLoadedRadius1,tyreLoadedRadius2,tyreLoadedRadius3,tyreLoadedRadius4,"\
            "suspensionHeight1,suspensionHeight2,suspensionHeight3,suspensionHeight4,"\
            "carPositionNormalized,carSlope,carCoordinatesX,carCoordinatesY,carCoordinatesZ"

        
        parsed_file.write(var_names + "\n")
    else:
        raw_file = open(raw_path, "a")
        parsed_file = open(parsed_path, "a")

    return raw_file, parsed_file
    
def parse_message(msg):
    size = len(msg)
    if size == 328:        
        msg_fmt = '< 8x 3f 6b 2x 3f 4i 5f i f 4f 4f 4f 4f 4f 4f 4f 4f 4f 4f 4f 4f 4f 4f f f 3f'
        parsed_msg = struct.unpack(msg_fmt, msg)
        return 328, parsed_msg
    elif size == 408:
        msg_fmt = '< 100s 100s 2i 100s 100s'
        parsed_msg = struct.unpack(msg_fmt, msg)
        decode = lambda x: x.decode('utf-16', errors='ignore').split("%")[0] if type(x) == bytes else x
        parsed_msg = tuple(decode, parsed_msg))
        return 408, parsed_msg    
    else:
        logging.info(f"Unexpected msg size at: {size} (expected 328)")
        return 0, None     

class AC_Socket():

    def __init__(self, ip_address, port):
        self.ip_address = ip_address
        self.port = port
        self.info = ""

        self.make_socket()
        
    def make_socket(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setblocking(1)
        self.socket.settimeout(2.0)
        
    def send_message(self, operation):
        message = struct.pack('iii', 1, 1, operation)
        self.socket.sendto(message, (self.ip_address, self.port))

    def handshake(self):
        self.send_message(0)

    def subscribe_update(self):
        self.send_message(1)

    # not entirely what this does
    def subscribe_spot(self):
        self.send_message(2)

    def dismiss(self):
        self.send_message(3)
                             
    def start(self):    
        try:
            logging.info("Trying to connect")
            self.handshake()
            
            msg, rinfo = self.socket.recvfrom(1024)
            
            if len(msg) == 408:
                self.info = msg
            
            self.subscribe_update()
            self.subscribe_spot()
            
            logging.info("Connected")
        except Exception as e:
            logging.error(e)
            time.sleep(5)
            self.restart()
                    
    def restart(self):
        self.stop()        
        self.make_socket()
        self.start()
            
    def stop(self):
        try:
            self.dismiss()
        except Exception as e:
            logging.error(e)
            
        self.socket.close()
            
def run(ip_address = '127.0.0.1', port = 9996):

    ac = AC_Socket(ip_address, port)
    ac.start()
    
    raw_f, parsed_f = make_logfiles(info = ac.info)
        
    while True:
        try:
            ts = time.time()
        
            msg, rinfo = ac.socket.recvfrom(1024)
            
            msg_string = b64encode(msg).decode('utf-8')
            raw_f.write(f"{ts},{msg_string}\n")

            size, parsed = parse_message(msg)

            if size == 328:
                parsed = ",".join(map(str, parsed))
                parsed_f.write(f"{ts},{parsed}\n")          
        except KeyboardInterrupt:
            ac.stop()
            break          
        except Exception as e:
            logging.error(e)
            logging.info("Restarting everything")
            run()              
                   
if __name__ == '__main__':

    add, port = '127.0.0.1', 9996
    if len(sys.argv) > 1:
        add = sys.argv[1]
    if len(sys.argv) > 2:
        port = int(sys.argv[2])

    run(add, port)

