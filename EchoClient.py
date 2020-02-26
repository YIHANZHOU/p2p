#!/usr/bin/env python3

# Yihan Zhou April 21
# this file create the Server as a class, who has three main function
# 1、setup_socket(), once its initilize, it run as a server and open a server_socket thread waiting for others to connect,this connection is always open
# 2、register(), once it receive commad from user it connect to meta_server first and get a new referred number, close this connection and then finally get to connect to its P2P Server,this connection continues to open
# 3、Download_file(), after it register(), it is able to download file through its two connections as a client and as a server
import socket
from argparse import ArgumentParser
import sys
from threading import Thread
import time
import os


meta_server_ip = '127.0.0.1'
meta_server_port = 9000
BUFSIZE = 4096

def stop_thread(thread):
   _async_raise(thread.ident, SystemExit)
class Server:
  def __init__(self, server_ip, server_port,meta_server_ip,meta_server_port):
    print('the address of server is host:{} port:{}'.format(host,port))
    self.host = server_ip
    self.port = server_port
    self.meta_host=meta_server_ip
    self.meta_port=meta_server_port
    self.id=None
    self.thpool=[]

    self.assign=None     #assigned port number will be received from the Meta-server
    self.refer=None       # it will received the refered port number fot the server port to connect to another server p2p
    self.connection=[]    #store the port number of connected server
    self.conid=[]    #store the id of connected server
    self.idmap=dict() # store the id and port of connected server
    self.rerurnconnection=0 # initially is 0, once its connet to a server as client, it becomes 1 ,only for s1, it is 0,for other server, it is 1.
    #s4 instead of s1 to s5
    self.isfirst=False   # indicate thether it is the first server in the p2p only s1's isfirst is true
    self.con=dict() #store the socket id match with socket connection of each connect received by server, only s1 has 2, other server has only one client connect to him
    self.searchpath=None
    self.setup_socket()

    while True:
      choice=input('Please choose \n1 : Add server to the P2P network \n2 : Download a file\n3 : View the current P2P network topology\n4 : EXIT,Close the connection\n')
      if not choice.isdigit():
          print("please input number")
          continue     
      choice=int(choice)
      if choice==1 :
          self.register()
      if choice==2 :
          self.download_file()
      if choice==3:
          topo=input(" input the flag view the current P2P network topology\n")
          if topo=="TOPO":
              self.topology()
          continue
      if choice==4:
          break
    self.sock.shutdown(socket.SHUT_RDWR)
    self.sock.close()
    if self.isfirst==False:
        self.meta_socket.shutdown(socket.SHUT_RDWR)
        self.meta_socket.close()
    print('connection closed.')

  def setup_socket(self):
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.sock.bind((self.host,self.port))
    self.sock.listen(5)
    print("the server is ready")
    th = Thread(target=self.run_server, args=())
    th.start()
    self.thpool.append(th)
  def run_server(self):
    while True:
      (connectsocket, address) = self.sock.accept()
      print('Connection  establish: ' + str(address))
      data = connectsocket.recv(BUFSIZE).decode('utf-8')
      # if receive a temporal connection to transfer a file
      if data.startswith("['TRANSFER"):
        temp=data.split(",")
        connect_id=temp[1]
        connect_id=connect_id.strip(']')
        connect_id=connect_id.strip(" ")
        connect_id=connect_id.strip("'")
        print("Find file at",connect_id)
        if not os.path.exists(self.searchpath):    # eg s4 want to downloads 1.txt which both s3 and s5 have, you need to prevent redownload it twice     
           connectsocket.send(str("Ready to download file").encode())
           data = ''.join(connectsocket.recv(1024).decode())
           with open(self.searchpath, 'w') as f:
                   f.write(data)
           print('File download complete')
           connectsocket.close()
        else:
           connectsocket.send(str("HAVE").encode())
           print('Already download the file, so no extra downloads')
           connectsocket.close()


      else:
        print('***Connected to{} ***'.format(data))
        temp=data.split(",")
        connect_id=temp[0]
        connect_id=connect_id.strip('[')
        connect_id=connect_id.strip("'")      
        port_number=temp[1]
        port_number=port_number.strip(' ')
        assign_number=temp[2]
        assign_number=assign_number.strip(']')
        if(len(self.connection)<2):
            self.connection.append(int(port_number))
            self.conid.append(connect_id)
            self.idmap.update({int(port_number):connect_id})
            self.con.update({connect_id:connectsocket})
            connectsocket.send(str(["success connected!",self.id]).encode())
            # the connection is establish, and continue to receive data from
            # p2p client as a server
            th = Thread(target=self.server_command, args=(connectsocket,))
            th.start()
            self.thpool.append(th)


                 
        else:
            connectsocket.send(str(self.connection[self.rerurnconnection]).encode())
            connectsocket.close()
            print('Connection Rejected: ' + str(address))
           # close this thread if no connection
              
          
  # for each one acting like a server in the p2p network, after it make a desicion on who is his client,
  # it will have a distingush thread to handle things and command from this client          
  def server_command(self,connectsocket):
    while True:
 #####handle TOPO signal from connected client, dfirst print its own neighbors. Then
      #if it is not s1, it has a metasocktet, parse it to metasocket.
      #if it is s1,it has two client, he sennd to send another client
      data = connectsocket.recv(BUFSIZE).decode('utf-8')
      if data.startswith("['TOPO"):
         print("Receive signal TOPO")
         print(self.id,":",end=' ')
         print(self.conid)
         data=data.strip('[')
         data=data.strip(']')
         temp=data.split(',')
         send_id=temp[1]
         send_id=send_id.replace("'","")
         send_id=send_id.strip()
         if self.isfirst==False:
            self.meta_socket.send(str(["TOPO",self.id]).encode())
         else:
            for key in self.con:
              if not key==send_id:
                 self.con[key].send(str("TOPO").encode())
 #####handle search file from connected client
#if it is not s1, it has a metasocktet, parse it to metasocket.
#if it is s1,it has two client, he sennd to send another client
      if data.startswith("['File"):
         data=data.strip('[')
         data=data.strip(']')
         temp=data.split(",")
         filename=temp[1]
         filename=filename.strip(" ")
         filename=filename.strip("'")
         print(filename)
         port=temp[2]
         port=port.strip(" ")
         port=port.strip("'")                   
         print(port)                      
         path=self.id
         path+="/"
         path+=filename
         send_id=temp[3]
         send_id=send_id.replace("'","")
         send_id=send_id.strip()
         print("***Received File:",filename,"Request Server Portnumber",port,"from Server***",send_id)
         if os.path.exists(path):
            print("the file is in this server's folder") # one server can maximinly coneect one server as a clien
            self.temporal_socket= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.temporal_socket.connect(('127.0.0.1', int(port)))
            # you need also ready \n to maintain the structure
  #             with open(path,'r') as f:
  #                   contents = f.read()
  #             return_str=str({'opt': 'TRANSFER','content': contents})
            self.temporal_socket.send(str(['TRANSFER',self.id]).encode())
            data = self.temporal_socket.recv(BUFSIZE).decode('utf-8')
            print("Receive msg from the requested port: ",data)
            if data == "HAVE":
               print("The requested port already have download, so no need to transfer")

               self.temporal_socket.close()

            else:
               with open(path,'r') as f:
                    contents = f.read()
               self.temporal_socket.send(contents.encode())
               self.temporal_socket.close()
            

         else:
           print("The file is not in this server's folder")
           if self.isfirst==False:
              self.meta_socket.send(str(["File",filename,port,self.id]).encode())
           else:
              for key in self.con:
                if not key==send_id:
                   self.con[key].send(str(["File",filename,port]).encode())
     
# this step is to register to the p2p, including connecting to metaserver first, get referred portnumber and try to
# connect to portnumber and finally success with a metaserver socket

  def register(self):
    self.meta_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("connect to host and port".format(self.meta_host, self.meta_port))
    self.meta_socket.connect((self.meta_host, self.meta_port))
    self.meta_socket.send(str([self.host, self.port]).encode())
    self.id=input("input the ID of the server\n")
    self.meta_socket.send(str(self.id).encode())
    flag=input("input flag if you want to register to P2P and wait for a response\n")
    while True:
      self.meta_socket.send(flag.encode())
      temp=''.join(self.meta_socket.recv(1024).decode())
      print(temp)
      if temp=='invalid':
        print(flag,"is not a valid flag")
        flag=input("Pleast input a valid flag")
      else:
         print(flag,"is a valid flag")
         #wait for 2 second to ensure the metaserver has enough time to send needed massage
         #as there is two sequent "receive function"
         assign_refer=temp
         assign_refer=assign_refer.strip('[')
         assign_refer=assign_refer.strip(']')
         #get assigned ip and refer ip from the server
#         print(assign_refer)
         temp2=assign_refer.split(",")
         self.assign=temp2[1]
         self.refer=temp2[2]
         self.assign=int(self.assign.strip())
         self.refer=self.refer.strip()
         self.meta_socket.close()
         break
    # when there is no server in the p2p, it will receive None and no need to connect      
    if self.refer=='None':
      print("This is the first one to join the p2p")
      self.isfirst=True   #this is the s1 server
      return
    # when it recieve any port number other than None, it will need to connect to the server port returned and see whether can establish connection
    while True:
      print("\nNow try to connected to :"+ str(self.refer))
      self.refer=int(self.refer)
      self.meta_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      self.meta_socket.connect(('127.0.0.1', self.refer))
      self.meta_socket.send(str([self.id, self.port,self.assign]).encode())
      data = self.meta_socket.recv(BUFSIZE).decode('utf-8')
      data=data.strip('[')
      data=data.strip(']')
      print(data)
      if data.startswith("'success"):
        #print(data)
        temp=data.split(",")
        connect_id=temp[1]
        self.connection.append(self.refer)
        connect_id=connect_id.strip(" ")

        connect_id=connect_id.strip("'")
        self.idmap.update({self.refer:connect_id})
        self.rerurnconnection=1
        self.conid.append(connect_id)
        th = Thread(target=self.run_client, args=())
        th.start()
        self.thpool.append(th)

        break
      else:
        print("connection reject from server :"+ str(self.refer))
        self.meta_socket.close()
        self.refer=int(data)

        
  # After it finally connect to the metaserver, it will have a dinstingush and indepent thread to handle requests from this server 
  def run_client(self):
    while True:
         data = self.meta_socket.recv(BUFSIZE).decode('utf-8')
         # If a client receive "TOPO" from server, it first print its own connection neighbors and then parse this "topo" in formation to the client who connencts to it 
         if data=="TOPO":
           print("Receive signal",data)
           print(self.id,":",end=' ')
           print(self.conid)
           for key in self.con:
#             if not self.con[key]==self.meta_socket:          
               self.con[key].send(str("TOPO").encode())
        
         if data.startswith("['File"):
          # If a client receive "FIle" from server, it first find whether file exits in its path
          # and if not in its path, parse this "FIle" command to the client who connencts to it 

           data=data.strip('[')
           data=data.strip(']')
           temp=data.split(",")
           filename=temp[1]
           filename=filename.strip(" ")
           filename=filename.strip("'")
           print(filename)
           port=temp[2]
           port=port.strip(" ")
           port=port.strip("'")          
           print(port)                      
           path=self.id
           path+="/"
           path+=filename
           self.searchpath=path
           print("***Received File:",filename,"Request Server Portnumber",port,"from Server***")
           if os.path.exists(path):
              print("The file is in this server's folder") # one server can maximinly coneect one server as a clien
              self.temporal_socket= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
              self.temporal_socket.connect(('127.0.0.1', int(port)))
              self.temporal_socket.send(str(['TRANSFER',self.id]).encode())
              data = self.temporal_socket.recv(BUFSIZE).decode('utf-8')
              print("Receive msg from the requested port: ",data)
              if data == "HAVE":
                   print("The requested port already have download, so no need to transfer")
                   self.temporal_socket.close()
              else:
                 with open(path,'r') as f:
                      contents = f.read()
                 self.temporal_socket.send(contents.encode())
                 self.temporal_socket.close()

           else:
              print("The file is not in this server's folder")
##              if len(self.con)==0: #this might be the last server to search and did not fine it
##                  self.temporal_socket= socket.socket(socket.AF_INET, socket.SOCK_STREAM)
##                  self.temporal_socket.connect(('127.0.0.1', int(port)))
##                  self.temporal_socket.send(str("Failed").encode())
##                 
              for key in self.con:
                  self.con[key].send(str(["File",filename,port]).encode())
      

           
    
        
       
  def download_file(self):
    filename=input("Enter the file name you wishes to download\n")
    if not filename.islower():
      print("Please input filename withou uppercase")
      return
    path=self.id
    path+="/"
    path+=filename
    self.searchpath=path
    if os.path.exists(path):
      print("Already downloads it in the current server")
    else:
      if self.isfirst==False:   # this means the server is not S1, it has server socket and it will send msg to serversocket,you need to send your id to prevent the server to resend you again
            self.meta_socket.send(str(["File",filename,self.port,self.id]).encode())
      for key in self.con:
        # send msg to its client socket as a server
            self.con[key].send(str(["File",filename,self.port]).encode())


    

  def topology(self):
     print("The current P2P network topology\n")
     print(self.id,":",end=' ')
     print(self.conid)
    # for key in self.idmap:
#       topology_help(self,key)
    
     if self.isfirst==False:
        # send msg to its server socket as a client
        self.meta_socket.send(str(["TOPO",self.id]).encode())
     for key in self.con:
        # send msg to its client socket as a server

        self.con[key].send(str("TOPO").encode())

      



def parse_args():
  parser = ArgumentParser()
  parser.add_argument('--host', type=str, default='127.0.0.1',
                      help='specify a host to operate on (default: localhost)')
  parser.add_argument('-p', '--port', type=int, default=9001,
                      help='specify a port to operate on (default: 9002)')
  args = parser.parse_args()
  return (args.host, args.port)

if __name__ == '__main__':
  (host, port) = parse_args()
  Server(host,port,meta_server_ip,meta_server_port)

