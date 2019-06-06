import socket
import time
import sys

class packet:
    def __init__(self, packNumber, time, pType, data):
        self.packNum = packNumber
        self.time = time
        self.pType = pType
        self.data = data
    def __str__(self):
        rS = str(self.packNum) + ", " + str(self.time) + "\n"
        rS+= self.data
        return rS
    def sendStr(self, conNum):
        rS = str(conNum) + ", " + str(self.pType) + ", " + str(self.packNum) + "\n"
        rS+= self.data
        return rS

def makeAPacket(packNum):
    rS = ""
    for x in range(100):
        rS+= "a"
    temp = packet(packNum, 0, "DA", rS)
    return temp

class senderConnection:
    def __init__(self, currSocket, serverAddr, startCW, connectionNum = 0,):
        self.sock = currSocket
        self.Addr = serverAddr
        self.CWSize = startCW
        self.connNum = connectionNum
        self.packAck = 0
        self.currPacket = 0
        self.packetBuf = []
    def __str__(self):
        rS = "Connection\n"
        rS += "con #: " + str(self.connNum) + " CWSize: " + str(self.CWSize) \
              + " pAck: " + str(self.packAck) + " pSend: " + str(self.packSen)
        for x in range(len(self.packetBuf)):
            rS += "\n" + str(x) + "---\n" + str(self.packetBuf[x])
        return rS
    def packSend(self, bufNum):
        self.sock.sendto(bytes(self.packetBuf[bufNum].sendStr(self.connNum), "utf-8"), self.Addr)
        self.packetBuf[bufNum].time = time.time()
        tTime = time.localtime(self.packetBuf[bufNum].time)
        tString = str(tTime.tm_hour) + ":" + str(tTime.tm_min) + ":" + str(tTime.tm_sec)
        print("Sender sent packet: Seq= ", self.packetBuf[bufNum].packNum, " Time= ", tString, " CW= ", self.CWSize)
    def isSpace(self):
        while True:
            if self.CWSize > len(self.packetBuf):
                temp = makeAPacket(self.packAck + len(self.packetBuf))
                self.packetBuf.append(temp)
            else:
                break
    def sendUnsent(self):
        while True:
            if self.currPacket < len(self.packetBuf) and self.currPacket != self.CWSize:
                self.packSend(self.currPacket)
                self.currPacket += 1
            else:
                break
    def anyAck(self):
        while True:
            try:
                data, server = self.sock.recvfrom(4096)
                data = data.decode("utf-8")
                splitData = data.split("\n")
                header = splitData[0].split(",")
                for x in range(len(header)):
                    header[x] = header[x].strip()
                header[0] = int(header[0])
                header[2] = int(header[2])
                if header[0] == self.connNum:
                    tTime = time.localtime()
                    tString = str(tTime.tm_hour) + ":" + str(tTime.tm_min) + ":" + str(tTime.tm_sec)
                    print("Sender received ACK: Seq#= ", str(header[2]), " Time= ", tString, " Exp#= ", self.packAck)
                    if header[2] < self.packAck: #This means a packet was lost and receiver is discarding packets and trying to quick retransmit
                        self.CWSize = 1
                        self.currPacket = 0
                        while True: # Clear all ACKs which should be the same thing
                            try:
                                data, server = self.sock.recvfrom(4096)
                            except socket.error:
                                break
                        break
                    elif header[2] == self.packAck: #Everything appears correct
                        self.packAck += 1
                        if self.CWSize < 8:
                            self.CWSize += 1
                        del(self.packetBuf[0])
                        self.currPacket -= 1
                    else: #Got a higher packet number, an ACK from receiver was lost, everything should still be fine
                        while self.packAck <= header[2]:
                            self.packAck += 1
                            if self.CWSize < 8:
                                self.CWSize += 1
                            del(self.packetBuf[0])
                            self.currPacket -= 1
                        
            except socket.error:
                break
    def anyTimeOut(self):
        tTime = time.time()
        for x in range(len(self.packetBuf)):
            if x == self.currPacket:
                break
            if tTime - self.packetBuf[x].time > 2:
                #Timeout has occured, need to resend packet
                print("Timeout on ", self.packetBuf[x].packNum)
                self.CWSize = 1
                self.currPacket = 0
                break 
    def sendingLoop(self):
        if self.packAck > 100:
            return False
        else:
            self.isSpace()
            self.sendUnsent()
            self.anyAck()
            self.anyTimeOut()
            return True


#socket.gethostbyname("ubuntu") #"192.168.18.129"
if len(sys.argv) != 3:
    print("fileName.py udpIP udpPort")
    exit()
udpIP = sys.argv[1]
udpPort = int(sys.argv[2])

print ("UDP target IP:", udpIP)
print ("UDP target port:", udpPort, "\n")

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
serverAddr = (udpIP, udpPort)
sock.setblocking(0)

conn = senderConnection(sock, serverAddr, 1)

while conn.sendingLoop():
    pass
    #print(conn.CWSize, " ", conn.packAck, " ", conn.currPacket, " ", len(conn.packetBuf))
    #time.sleep(1)


sock.close()

