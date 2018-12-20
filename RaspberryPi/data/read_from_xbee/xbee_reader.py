import time
import MySQLdb
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
			database_connection = MySQLdb.connect(host='localhost', user='user', passwd='123456', db='data_sync')
			cur = database_connection.cursor()
			statement = "insert into `serial_data` values (null, %s, 0, %s)"
			dataList = []
			while s.inWaiting:
				line = s.readline()
				#print(line)
				if line is not None and len(line) > 1:
					#line = line.replace("\n", "")
					#line = line[:-1]
					#print(line)
					dataList.append(line)

				readin = ""
				for i in reversed(dataList):
					readIndex = -2
					readin = i + readin
					checkSum = fletcher16(readin[:-5])

					#crcBytes = bytes(readin[-4:])
					#crc = struct.unpack('H'*(len(crcBytes)/2), crcBytes)
					try:
						crc = int(readin[-4:].strip(), 16)
						readIndex = int(readin[-6].strip(), 16)
						print(readIndex)
						print (readin[-6])
					except:
						continue			
					if len(readin) > 0:
						print(readin[:-5])
						print(checkSum)
						print(crc)
					
						if checkSum == (crc):
							s.write("OK")
							#print(readin[:-1])
							
							if readIndex != lastIndex:
								print("write to server<<<<<<<<<<<<<<<<<<<<<<<<<")
								cur.execute(statement, [readin[:-5], int(time.time())])
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
