import time
#import MySQLdb
import pymysql
import serial
import struct
from ctypes import *

def fletcher16(data):
    c0 = 0
    c1 = 0
    c = list(map(ord, data))
    for i in range(len(c)):
        c0 = (c0 + c[i]) % 255
        c1 = (c0 + c1) %255 
    return ((c1 << 8) | c0)

def main():
    t1 = "Starting XBEEllo"
    print(t1[:-3])
    database_connection = None
    lastIndex = -1
    while True:
        try:
            s = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
            
            database_connection = pymysql.connect(host='localhost', user='user', passwd='123456', db='data_sync')
            cur = database_connection.cursor()
            statement = "insert into `serial_data` values (null, %s, 0, %s)"
            dataList = []
            #print(database_connection.port())
            #print(database_connection.get_autocommit())
            #print(database_connection.get_server_info())
            try:
                #print(database_connection.ping())
                #print("database_connection.ping()")
                database_connection.ping()
            except:
                print("DB is unreachable")
                database_connection.reconnect()
                
            while s.inWaiting:
                line = s.readline()
                #print(line)
                if line is not None and len(line) > 1:
                    #line = line.replace("\n", "")
                    #line = line[:-1]
                    print(len(line))
                    dataList.append(line)

                readin = ""
                for i in reversed(dataList):
                    readIndex = -2
                    readin = str(i).strip('b').strip('"') + readin
                    print(":readin:")
                    print(readin)
                    print(readin[:-5])
                    checkSum = fletcher16(readin[:-5])
                    print(checkSum)
                    print("checkSum: " + str(checkSum))
                    print(":")

                    #crcBytes = bytes(readin[-4:])
                    #crc = struct.unpack('H'*(len(crcBytes)/2), crcBytes)
                    try:
                        print("Reached try")
                        print(readin[-4:])
                        crc = int(readin[-4:].strip('"'), 16)
                        print("crc: ")
                        print(crc)
                        print("(crc): ")
                        print((crc))
                        #readIndex = int(readin[-5].strip('"'), 16)
                        #print("readin[-5]:" + str(readin[-5]))
                        #print("readIndex:")
                        #print(readIndex)
                        readIndex = int(str(readin[:-5])[str(readin[:-5]).rfind(":")+1:])
                        print("readIndex:")
                        print(readIndex)
                        print("lastIndex:")
                        print(lastIndex)
                        #print (readin[-6])
                        if readIndex == lastIndex:
                            print("Data written to DB already")
                    except:
                        continue            
                    if len(readin) > 0:
                        print(":After Try Except:")
                        print(readin[:-5])
                        print(checkSum)
                        print((crc))
                    
                        if checkSum == (crc):
                            s.write(bytes("OK",'utf-8'))
                            #print(readin[:-1])
                            
                            if readIndex != lastIndex:
                                print("write to server (db actually)<<<<<<<<<<<<<<<<<<<<<<<<<")
                                cur.execute(statement, [str(readin[:-5]), int(time.time())])
                                database_connection.commit()
                                lastIndex = readIndex
                            dataList[:] = []
                            break 

                    #data = data.replace("\n", "")
                    #cur.execute(statement, [data, int(time.time())])
                    
                    
                    
                    #s.write("OK")
                    #print("writing")   
                    #print(fletcher16(data[0]))
                if len(dataList) > 20:
                    dataList[:] = []
        except:
            import traceback
            print("Something wrong!! ")
            traceback.print_exc()
            pass
main()
