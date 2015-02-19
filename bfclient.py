import sys
import json
import socket
import time
import base64
from select import select
from threading import Thread, Timer
from copy import deepcopy
from types import *

#user commands
LINKDOWN= "LINKDOWN"
LINKUP= "LINKUP"
SHOWRT= "SHOWRT"
CLOSE= "CLOSE"
TRANSFER="TRANSFER"
SENDCHUNK='SENDCHUNK'

#tables
snode={}
files={}
chunks={}
neighbors=[]
#testcase=[['160.39.231.48','1111']]

#HOSTIP=''
updated=[]

#constants
INFINITY=float("inf")
SIZE=4096
timeout=0
file_chunk=''
file_sequence_num=0

#create a resettable Timer class 
class testTimer():
    def __init__(self, interval, func, args=None):
    	#assign values
        self.interval = interval
        self.func = func
        self.args = args
        self.task = self.create_timer()
    #will initiate the timer
    def start(self):
        self.task.start()
    #will reset the timer
    def reset(self):
        self.task.cancel()
        self.task = self.create_timer()
        self.start()
    #create function that will initiate the timer    
    def create_timer(self):
        t = Timer(self.interval, self.func, self.args)
        t.daemon = True
        return t
    #will cancel the timeout
    def cancel(self):
        self.task.cancel()

#create timer that will repeat function over and over again
class repeatFunc(Thread):
    """ thread that will call a function every interval seconds """
    def __init__(self, timeout, func):
        Thread.__init__(self)
        self.func = func
        self.timeout = timeout
        self.daemon = True
        self.stopped = False
    def run(self):
        while not self.stopped:
            time.sleep(self.timeout)
            self.func()

def handle_inputs(line):
    line=line.strip("\n")
    if len(line)<=1:
        return True
    if line==CLOSE:
        sock.close()
        print "You have closed this connection"
        sys.exit()
    
    if line==SHOWRT:
        print "----------------------------------------"
        print "Here is the current routing table"
        #print snode
        print time.strftime("<%H:%M:%S>Distance vector list is:")
            
        for client in snode:
            if snode[client]['NeighborAccessed']==None:
                print "Destination="+ str(client)+", Cost="+str(snode[client]['cost'])+", Link="+str(client)
                #print "hi"
                continue
            print "Destination="+ str(client)+", Cost="+str(snode[client]['cost'])+", Link="+str(snode[client]['NeighborAccessed'])
        print "----------------------------------------"
        return True

    line=line.split()
    if line[0]==SENDCHUNK and len(line)==4:
        if line[3] in files:
            sendchunk(line[1],line[2],line[3])
        elif line[3]==file_sequence_num:
            print "This is your chunk number. Use transport"
        else:
            print "Chunk never received"
        return True
    if line[0]==TRANSFER and len(line)==3:
        host=line[1]
        port=line[2]
        key=addr2key(host,port)
        
        if key not in snode:
            print "Unknown address!"
            return True

        #print file_chunk
        if [host,port] not in neighbors:
            sendto=snode[key]['NeighborAccessed']
            if sendto==None:
                print "Cannot send!"
                return False
            sendto=sendto.split(":")
            host=sendto[0]
            port=sendto[1]
            #print host
            #print port

        try:
            f=open(file_chunk,'rb')
        except:
            print "unable to read chunk file!"
            return True
        i=0
        #host,port=HOSTIP.split(":")
        binary_code=f.read(1024)
        while binary_code:
            #print binary_code
            sendfile=[i,base64.b64encode(binary_code),file_sequence_num,key]
            #print type(sendfile)
            #print sendfile
            #print json.dumps(base64.b64encode(binary_code))
            sock.sendto(json.dumps(sendfile),(host,int(port)))
            i+=1
            binary_code=f.read(1024)

        sendfile=[INFINITY,'',file_sequence_num,key,[HOSTIP]]
        sock.sendto(json.dumps(sendfile),(host,int(port)))
        print "Sent file to "+host+":"+str(port)
        return True

    if line[0]==LINKUP and len(line)==4:
        ipaddress=line[1]
        portnumber=line[2]
        try:
            cost=float(line[3])
        except:
            print("That is not a valid cost!")
            return False
        #print ipaddress
        #print portnumber
        #print cost
        test=addr2key(ipaddress, portnumber)
        print test
        test1=test.split(":")
        if test1 in neighbors:
            print "You are neighbors!"
            return True
        if test in snode:
            tempnode=snode[test]  
        else:
            print "Not a valid ipaddress port combination!"
            return True
        if test not in updated:
            print "You have never destroyed this link!"
            return True
        
        tempnode["direct_cost"]=str(cost)
        tempnode["cost"]=str(cost)
        if float(tempnode["cost"])>cost:
            tempnode["cost"]=str(cost)

        tempnode["neighbor_bool"]=True
        snode[test]=tempnode
        #print snode[test]
        neighbors.append(test1)

        #restart timer
        timeoutcheck = testTimer(interval = 3*timeout, func = handle_inputs,args=[test] )
        timeoutcheck.start()
        snode[test]["timeoutcheck"]=timeoutcheck
        #print neighbors
        updatebf()
        return True


    #print line
    if not line or len(line)!=3:
        return False


    if line[0]==LINKDOWN and len(line)==3:
        line[1]=addr2key(line[1],line[2])
        if line[1] not in snode:
            #print line[1]
            return False
        linkdown(line[1])
        broadcast()
        return True
    return False

def linkdown(tempaddress):
    #print tempaddress
    if tempaddress not in snode:
        #print snode
        return
    tempnode=snode[tempaddress]
    if tempnode["neighbor_bool"]==False:
        print "Node is not a neighbor!"
        return True
    if tempaddress not in updated:
        updated.append(tempaddress)
    tempnode["cost"]=INFINITY
    tempnode["direct_cost"]=INFINITY
    tempnode["neighbor_bool"]=False
    snode[tempaddress]=tempnode
    #print tempaddress
    del tempnode
    temp=tempaddress.split(":")
    neighbors.remove(temp)
    #print neighbors
    #print snode[line[1]]
    #print neighbors
    sendarr=[LINKDOWN,tempaddress]
    #print sendarr
    for neighbor in neighbors:
        if neighbor==HOSTIP:
            continue
        address=neighbor[0]
        port=neighbor[1]
        sock.sendto(json.dumps(sendarr),(address,int(port)))
    return True



def addr2key(host, port):
    return "{host}:{port}".format(host=host, port=port)

def takemin(newitem,directitem,item,address):
    #print directitem
    #print newitem
    if float(directitem)<=(newitem):
        return directitem
    else:
        snode[item]['NeighborAccessed']=address
        return newitem


def updatebf(data,sender):
    address=addr2key(sender[0],sender[1])
    #print address
    if address not in snode:
        snode[address]=createsnode(INFINITY,False,INFINITY,address,None)
    
    cost2sender=snode[address]['cost']

    #add all nodes to data
    for item in data:
        if item not in snode:
            snode[item]=createsnode(INFINITY,False,INFINITY,item,None)
            #print snode[item]
    costtable={ addr: node['cost'] for addr, node in snode.iteritems()}
    #print costtable
    for item in data:
        if item==address or item==HOSTIP:
            continue
        if snode[item]['NeighborAccessed']==sender:
            snode[item]['cost']=INFINITY
        tempcost=float(cost2sender)+float(data[item])
        if tempcost>snode[item]['cost']:
            continue
        snode[item]['cost']=takemin(tempcost,snode[item]['cost'],item,address)
        if float(snode[item]['cost'])>float(snode[item]['direct_cost']):
            snode[item]['cost']=float(snode[item]['direct_cost'])
            snode[item]['NeighborAccessed']=None
    #print snode




def broadcast():
    costtable={ addr: node['cost'] for addr, node in snode.iteritems()}
    #print costtable
    for neighbor in neighbors:
        naddr=neighbor[0]
        port=neighbor[1]
        address=addr2key(naddr,port)
        if address==HOSTIP:
            continue
        #print costtable
        cost=costtable[address]
        #create copy of dictionary
        poisoncosttable=deepcopy(costtable)
        for dest, cost in costtable.iteritems():
            #make sure not itself or hostIP
            if dest!=HOSTIP and dest!=naddr:
                if snode[dest]['NeighborAccessed']==naddr:
                    poisoncosttable[dest]=INFINITY
        dest=naddr.split(":")
        #dest=HOSTIP.split(":")
        #print int(dest[1])
        #send table to dest
        #print poisoncosttable
        #print naddr
        #print port
        sock.sendto(json.dumps(poisoncosttable),(naddr,int(port)))
        #sock.sendto(json.dumps(poisoncosttable),(testcase[0][0],int(testcase[0][1])))
    return

#creating a server
def createserver(host, port):
    #create a new socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        port=int(port)
        #bind the socket to host and port
        sock.bind((host, port))
        print "listening on {0}:{1}\n".format(host, port)
    except:
        print "An error occured trying to connect"
        sys.exit(1)
    return sock

def createsnode(cost,neighbor_bool,direct_cost=None, addr=None, NeighborAccessed=None,timeout=timeout):
	#create the node
	tempnode={}
	tempnode['cost']=cost
	tempnode['neighbor_bool']=neighbor_bool
	if direct_cost!=None:
		tempnode['direct_cost']=direct_cost
	else:
		tempnode['direct_cost']=INFINITY
	tempnode[addr]=addr
	
	tempnode['NeighborAccessed']=NeighborAccessed
	if neighbor_bool:
		timeoutcheck = testTimer(interval = 3*timeout, func = linkdown,args=[addr] )
		timeoutcheck.start()
		tempnode['timeoutcheck'] = timeoutcheck
	return tempnode

def createyoursnode(sock,host,port):
    #create snode to yourself
    myIP = "{host}:{port}".format(host=host, port=port)
    #print myIP
    snode[myIP] = createsnode(cost=0.0, neighbor_bool=False, 
        direct_cost=0,addr=myIP,NeighborAccessed=myIP)
    return str(myIP)

def readconfig(filename):
    f=open(filename,'r')
    line=f.readline()
    line=line.split()
    rest=f.read()
    rest=rest.split("\n")
    for item in rest:
        if not item:
            break
        item=item.split()
        addr=item[0]
        addr=addr.split(":")
        neighbors.append([addr[0],addr[1]])
        test=item[0].split(":")
        snode[item[0]]=createsnode(cost=item[1],neighbor_bool=True,
            direct_cost=item[1],addr=item[0],timeout=float(line[1]))
    return line

def sendchunk(desthost,destport,chunknum):
    host=desthost
    port=destport
    key=addr2key(host,port)
        
    if key not in snode:
        print "Unknown address!"
        return False

    #print file_chunk
    if [host,port] not in neighbors:
        sendto=snode[key]['NeighborAccessed']
        if sendto==None:
            print "Cannot send!"
            return False
        sendto=sendto.split(":")
        host=sendto[0]
        port=sendto[1]
            #print host
            #print port
    i=0
    #host,port=HOSTIP.split(":")
    for item in files[chunknum]:
        #print binary_code
        sendfile=[i,base64.b64encode(files[chunknum][i]),str(chunknum),key]
        #print type(sendfile)
        #print sendfile
        #print json.dumps(base64.b64encode(binary_code))
        sock.sendto(json.dumps(sendfile),(host,int(port)))
        i+=1
    sendfile=[INFINITY,'',str(chunknum),key,[HOSTIP]]
    sock.sendto(json.dumps(sendfile),(host,int(port)))
    print "Sent file to "+host+":"+str(port)
    return True

def handlefile():
    #print "success"
    bytecode=''
    #print files
    for item in files:
        #print item
        if item in chunks:
            continue
        i=0
        for item1 in files[item]:
            bytecode+=files[item][i]
            i=i+1
        #print item
        chunks[item]=bytecode
        print "The size of the whole chunk was: "+str(len(bytecode)) + "bytes"
    if len(chunks)==chunknum:
        total=chunks['1']+chunks['2']
        try:
            f=open('output.jpeg', 'wb')
            f.write(total)
        except:
            print 'Error: Could not write output'
            return
        print '[%s] Assembled chunks and wrote output' % time.strftime('%H:%M:%S')

if __name__ == '__main__':
    if(len(sys.argv) < 2) :
        print 'Usage : python config-file'
        sys.exit()

    #initiate values
    hostname=socket.gethostbyname(socket.gethostname())
    
    test=readconfig(sys.argv[1])
    localport=test[0]
    timeout=float(test[1])
    file_chunk=test[2]
    file_sequence_num=test[3]
    chunknum=input("How many chunks would you like to receive?")
    chunknum=int(chunknum)

    #print snode
    #for nodes in snode:
    #    print snode.get(nodes)

    localhost=socket.gethostbyname(socket.gethostname())
    #print localhost
    #print localport
    #print neighbors
    #print testcase
    #print testcase[0][0]
    sock=createserver(localhost,localport)

    HOSTIP=createyoursnode(sock,localhost,localport)
    neighbors.append([localhost,localport])
    
    #print neighbors
    #print snode
    
    repeat=repeatFunc(timeout,broadcast)
    repeat.start()

    inputs = [sock, sys.stdin]
    running = True
    sys.stdout.write('%')
    while running:
        incomingSockets,outgoingSockets,errorSockets=select(inputs,[],[])
        for sockets in incomingSockets:
            if sockets==sys.stdin:
                #user command
                boolean=handle_inputs(sys.stdin.readline())
                if not boolean:
                    print "Input was not recognized!"
                sys.stdout.write('%')

            else:
                data, sender=sockets.recvfrom(SIZE)
                key=addr2key(sender[0],sender[1])
                data=json.loads(data)

                if type(data)==ListType:
                    if data[0]==LINKDOWN:
                        for neighbor in neighbors:
                            #neighbor=neighbor.split(":")
                            address=neighbor[0]
                            port=neighbor[1]
                            neighbor=addr2key(address,port)
                            senderkey=addr2key(sender[0],sender[1])
                            if neighbor==HOSTIP or neighbor==senderkey:
                                continue
                            senderIP=addr2key(sender[0],sender[1])
                            if data[1] not in snode:
                                continue
                            if snode[data[1]]['NeighborAccessed']==senderIP:
                                snode[data[1]]['NeighborAccessed']=None
                                snode[data[1]]['cost']=INFINITY
                            sock.sendto(json.dumps(data),(address,int(port)))
                        
                        #snode[data[1]]['cost']=INFINITY

                        continue

                    if data[3]!=HOSTIP:
                        newaddress=snode[data[3]]["NeighborAccessed"]
                        if newaddress==None:
                            newaddress=data[3]

                        if data[0]==INFINITY:
                            print "Transfering to "+newaddress
                            print data[4]
                            data[4]=data[4]+[HOSTIP]
                            print data[4]
                        newaddress=newaddress.split(":")
                        address=newaddress[0]
                        port=newaddress[1]
                        sock.sendto(json.dumps(data),(address,int(port)))
                        continue

                    if data[2] not in files:
                        files[data[2]]={}
                    if data[0]==INFINITY:
                        print "transfer ended: received chunk"
                        print time.strftime("Received at <%H:%M:%S>!")
                        print "file path was:"
                        print data[4]
                        handlefile()
                        #print files
                        sys.stdout.write('%')
                        continue
                    assert(type(data[1])==UnicodeType)
                    #print "success"
                    files[data[2]][data[0]]=base64.b64decode(data[1])
                    continue
                #print "received update from"
                #print sender
                
                snode[key]['timeoutcheck'].reset()
                #print data['160.39.231.48:1111']
                #print type(data)
                #print data
                #print sender

                updatebf(data,sender)
                #for item in data:
                 #   print data
                #sys.stdout.write('%')

    sock.close()


