import socket
import time
import random
import sys

class packet:
    def __init__(self, packNumber, time, pType, data):
        self.packNum = packNumber
        self.time = time
        self.pType = pType
        self.data = data
    def __str__(self):
        rS = str(self.packNum) + ", " + str(self.pType) + ", " + str(self.time) + "\n"
        rS+= self.data
        return rS
    def sendStr(self, conNum):
        rS = str(conNum) + ", " + str(self.pType) + ", " + str(self.packNum) + "\n"
        rS+= self.data
        return rS

class recConnection:
    def __init__(self, currSocket):
        self.packNum = 0 #The packet/sequence number the object is expecting, the next in order packet
        self.connNum = 0
        self.sock = currSocket
    def gotPacket(self, packData, addr):
        splitData = packData.split("\n")
        header = splitData[0].split(",")
        for x in range(len(header)):
            header[x] = header[x].strip()
        header[0] = int(header[0])
        header[2] = int(header[2])
        '''
        ranNum = random.randint(1, 5)
        if ranNum == 5:
            print("Packet Lost ", header[2])
            return
        if ranNum == 1:
            self.packNum += 1
            print("Accepted Packet ", header[2], " but ACK gets lost")
            return
        '''
        if header[0] == self.connNum:
            tTime = time.localtime()
            tString = str(tTime.tm_hour) + ":" + str(tTime.tm_min) + ":" + str(tTime.tm_sec)
            if header[2] < self.packNum: #The sender did not receive an ACK and so is retransmitting old packets send ACK like if accepted
                temp = packet(header[2], 0, "AK", "")
                self.sock.sendto(bytes(temp.sendStr(self.connNum), "utf-8"), addr)
                print("Rcvr received packet: Seq#= ", str(header[2]), " Time= ", tString,  " Exp#= ", self.packNum, " Discarded")
                print("Rcvr sent ACK: Seq#= ", str(header[2]), " Time= ", tString)
            elif header[2] == self.packNum: #The sender sent the packet the object is expecting, accept packet and send ACK
                temp = packet(self.packNum, 0, "AK", "")
                self.sock.sendto(bytes(temp.sendStr(self.connNum), "utf-8"), addr)
                print("Rcvr received packet: Seq#= ", str(header[2]), " Time= ", tString, " Exp#= ", self.packNum, " Accepted")
                print("Rcvr sent ACK: Seq#= ", self.packNum, " Time= ", tString)
                self.packNum += 1
            else : #A higher packet number than what was expected, a packet must have been lost, send ACK for last accepted packet (cumulative ACKs)
                temp = packet(self.packNum - 1, 0, "AK", "")
                self.sock.sendto(bytes(temp.sendStr(self.connNum), "utf-8"), addr)
                print("Rcvr received packet: Seq#= ", str(header[2]), " Time= ", tString, " Exp#= ", self.packNum, " Discarded")
                print("Rcvr sent ACK: Seq#= ", self.packNum - 1, " Time= ", tString)
                  

#socket.gethostbyname("ubuntu") #"192.168.18.129"
if len(sys.argv) != 3:
    print("fileName.py udpIP udpPort")
    exit()
udpIP = sys.argv[1]
udpPort = int(sys.argv[2])

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind( (udpIP, udpPort) )
conn = recConnection(sock)


while True:
    data, addr = sock.recvfrom(4096)
    data = data.decode("utf-8")
    #print ("\n", "received packet:\n", data)
    conn.gotPacket(data, addr)
    '''
    if data:
        sock.sendto(bytes("ACK1", "utf-8"), addr )
        print("-sent ACK")
    '''
