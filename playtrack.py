import aislib
import time
import sys
import socket
import threading
import math
from polycircles import polycircles

# OPTIONS
mmsi=239658000
rate=0.1 
port=2001
latitude = 0.0
longitude = 0.0
radiusm = 3000
knots = 10

aisString = "!"

def compass_bearing(pointA, pointB):
    if (type(pointA) != tuple) or (type(pointB) != tuple):
        raise TypeError("Only tuples are supported as arguments")

    lat1 = math.radians(pointA[0])
    lat2 = math.radians(pointB[0])

    diffLong = math.radians(pointB[1] - pointA[1])

    x = math.sin(diffLong) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1)
            * math.cos(lat2) * math.cos(diffLong))

    initial_bearing = math.atan2(x, y)
    initial_bearing = math.degrees(initial_bearing)
    compass_bearing = (initial_bearing + 360) % 360

    return compass_bearing

def run():
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock.bind(('0.0.0.0', port))
	sock.listen(1)
	print("Listening on port %d" % port)
	while True:
		(clientsocket, address) = sock.accept()
		print("Connect from %s:%s" % (address[0],address[1]))
		c = threading.Thread(target=receive, args=(clientsocket,))
		c.start()

def receive(client):
	global aisString
	global rate
	while True:
		try:
			# Package AIS string here with CRLF etc
			client.send(str.encode(aisString+"\n"))
			time.sleep(rate)
		except:
			break
			client.close()

def main():  
	global aisString 
	serverThread = threading.Thread(target=run, args=())
	serverThread.start()

	polycircle = polycircles.Polycircle(latitude=latitude,
		                            longitude=longitude,
		                            radius=radiusm,
		                            number_of_vertices=360)

	points = polycircle.to_lat_lon()
	lastPoint = points[0]
	pos=0
	while True:
		point = points[pos]
		pos+=1
		if pos == 360:
			pos=0
		try:
			lat=float(point[0])
			lon=float(point[1])
			sog=float(knots)
			cog=float(compass_bearing(point,lastPoint))
			lastPoint=point
		except ValueError:
			print(sys.stderr,l)
			continue
		aismsg = aislib.AISPositionReportMessage(
		mmsi = mmsi, # User Id
		pa = 1,	     # Positional accuracy
		lon = int((lon)*60*10000),
		lat = int((lat)*60*10000),
		heading =int(cog),
		sog = int(sog*10), # Speed over ground
		cog = int(cog*10), # Course over ground
		status = 0, # Nav status
		ts = 60, #
		raim = 1,
		comm_state = 82419   
		)
		ais = aislib.AIS(aismsg)
		payload = ais.build_payload(False)
		print(payload)
		aisString=payload
		time.sleep(rate)
		#   print "nav status: %d" % aismsg.get_attr("status")

		aismsg2 = ais.decode(payload)
		ais2 = aislib.AIS(aismsg2)
		payload2 = ais2.build_payload(False)
if __name__ == "__main__":
	main()
