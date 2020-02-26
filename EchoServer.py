#!/usr/bin/env python3
# See https://docs.python.org/3.2/library/socket.html
# for a decscription of python socket and its parameters
import socket
import tty
import sys
import termios

from threading import Thread
from argparse import ArgumentParser
BUFSIZE = 4096

class MetaServer:
  def __init__(self, host, port):
    self.host = host
    self.port = port
    #the first port assigned is 3000 and the next is 3000+1, so on
    self.assign=3000
    self.first_server=None
    self.setup_socket()
    #the catch store the port number of every server that connect to this p2p network
    self.cache=[]
    # store every pair of original ip port and assigned ip port
    self.addmap=dict()
    # store every pair of original port and name
    self.namemap=dict()

    self.accept()
    print("Receive Esc key press signal to close the socket and abort the system")
    self.sock.shutdown(1)
    self.sock.close()
  def setup_socket(self):
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.sock.bind((self.host,self.port))
    self.sock.listen(128)
    print("Accept connection from server")

  def client_talk(self,client_sock, client_addr):
    #first receive the port number and ip_address from the server connected
    data = client_sock.recv(BUFSIZE).decode('utf-8')
    print('***Connected to{} ***'.format(data))
    #second receive the name of the server connected
    tempid=client_sock.recv(BUFSIZE).decode('utf-8')
    print("Name"+tempid)

    #get the port_number for later use, filter ] and , in the received data and then can get portnumber
    temp=data.split(",")
    port_number=temp[1]
    port_number=port_number.strip(']')

    #pott_number="".join(port_number.split())

    self.namemap.setdefault(tempid,port_number)


    data = client_sock.recv(BUFSIZE)
    # the the data is not None, means the user has sent flag to meta server
    while data:
      print(data.decode('utf-8'))
      flag=data.decode('utf-8')
      if flag=="P2P":
          print("***Valid Flag***")
 #         client_sock.send(str("valid").encode())
          self.addmap.setdefault(port_number,self.assign)
          self.assign=self.assign+1;
          if len(self.cache)==0:
            client_sock.send(str(["valid",self.assign,None]).encode())
            print('**First server in the p2p network is setup***')

          else:
            client_sock.send(str(["valid",self.assign,self.cache[0]]).encode())
            print('**This server will fisrt connected to the Referred Server ID***'+str(self.cache[0]))
          self.cache.append(int(port_number))
          #client_sock.send(str(self.first_server).encode())
          break
      else:
          print("***Invalid Flag***")
          client_sock.send(str("invalid").encode())
          data = client_sock.recv(BUFSIZE)
          #if the flag is invalid, the metaserver will continue to recieve new flag from server until it is valid
          
    # clean up
    client_sock.shutdown(1)
    client_sock.close()
    print("Connection Closed")
    return
  def topology(self):
    print('***the structure of the network')
    
  def accept(self):
    while True:
      (connectsocket, address) = self.sock.accept()
      print("Recieve connection from" +str(address))
      th = Thread(target=self.client_talk, args=(connectsocket, address))
      th.start()

port=9000
host='localhost'

if __name__ == '__main__':
  
  MetaServer(host, port)
  
