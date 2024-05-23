
#/usr/bin/python2.7
# -*- coding: utf-8 -*-
# Date: 2024.5.13

from socket import *
from time import ctime
import threading
import json

global HOST
global PORT
global BUFSIZ
global ADDR
global ADDR_V

class client():
    def __init__(self, address, tcpconnenct):
        self.address = address
        self.tcpconnenct = tcpconnenct

voice_socket = socket(AF_INET, SOCK_STREAM)
voice_list = []
clients = {
    'client1': 'passwd1',
    'client2': 'passwd2',
    'client3': 'passwd3',
    'client4': 'passwd4',
    'client5': 'passwd5',
    'admin': 'adminpasswd'
}

class client_get():
    clientnames = {}

    def __init__(self, client):
        self.client = client
    @staticmethod
    def getclient(clientname):
        def getKey(list, value):
            return [k for k,v in d.items() if v == value][0]
        return getKey(client_get.clientnames, clientname)

    @staticmethod
    def delclientname(clientname):
        try:
            client = client_get.getclient(clientname)
            client_get.delclient(client)
        except:
            pass

    @staticmethod
    def delclient(client):
        try:
            client_get.clientnames.pop(client)
        except Exception as e:
            print(e)

    @staticmethod
    def all_send(clientList, data):
        json_Data = json.dumps(data)
        for client in clientList:
            client.tcpconnenct.send(json_Data.encode())
        print ("__sendToAll__" + json_Data)

    @staticmethod
    def send_to_clientnames(clientnameList, data):
        def getKeys(list, valueList):
            return [k for k,v in list.items() if v in valueList]
        clientList = getKeys(client_get.clientnames, clientnameList)
        client_get.all_send(clientList, data)

    def send_to_me(self, data):
        json_Data = json.dumps(data)
        json_Data = json_Data
        self.client.tcpconnenct.send(json_Data.encode())
        print ('__send__' + json_Data)

    def login(self, data):
        if self.client in client_get.clientnames.keys():
            data['status'] = False
            data['info'] = "您已登录"
        elif data['clientname'] in client_get.clientnames.values():
            data['status'] = False
            data['info'] = "用户名已存在"
        elif data['clientname'] not in clients or data['passwd'] != clients[data['clientname']]:
            data['status'] = False
            data['info'] = "密码错误"
        else:
            data['status'] = True
            client_get.clientnames[self.client] = data['clientname']
        self.send_to_me(data)

    def ping(self, data):
        """ping pong!"""
        data = {'type': 'pong'}
        self.send_to_me(data)

    def list(self, data):
        nameList = client_get.clientnames.values()
        data['list'] = list(nameList)
        self.send_to_me(data)

    def singleChat(self, data):
        toclientname = data['to']
        self.send_to_clientnames([toclientname], data)

    def groupChat(self, data):
        clientList = [client for client in client_get.clientnames]
        self.all_send(clientList, data)

    def logout(self, data):
        print ("用户"+ client_get.clientnames[self.client] +"登出")
        client_get.delclient(self.client)

    def voice(self, data):
        print("begin to talk!")
        # while True:
        #     try:
        #         c, addr = voice_socket.accept()
        #         voice_list.append(c)
        #         threading.Thread(target=self.client_get_client, args=(c, addr)).start()
        #         break
        #     except:
        #         print("Couldn't bind to that port")
    # def broadcast(self, sock, data):
    #     for client in voice_list:
    #         if client != voice_socket and client != sock:
    #             try:
    #                 client.send(data)
    #             except:
    #                 pass
    #
    # def client_get_client(self, c, addr):
    #
    #     while 1:
    #         try:
    #             data = c.recv(1024)
    #             # print(data)
    #             self.broadcast(c, data)
    #         except Exception as e:
    #             print(e)

    def __main__(self, data):
        type = data['type']
        switch = {
                "login": self.login,
                "ping": self.ping,
                "list": self.list,
                "singleChat": self.singleChat,
                "groupChat": self.groupChat,
                "logout": self.logout,
                "voice": self.voice
                }
        try:
            return switch[type](data)
        except Exception as e:
            print (e)
            data['status'] = False
            data['info'] = "未知错误"
            return data

class Client_Thread(threading.Thread):
    def __init__(self, client):
        threading.Thread.__init__(self)
        self.client = client

    def run(self):
        client_get = client_get(self.client)
        while True:

            json_Data = self.client.tcpconnenct.recv(BUFSIZ)
            json_Data = json_Data.decode()
            data = json.loads(json_Data)
            print(data)
            print ("___receive___" + json_Data)
            if data['type'] == 'logout':
                break
            else:
                client_get.__main__(data)

    def stop(self):
        try:
            self.client.tcpconnenct.shutdown(2)
            self.client.tcpconnenct.close()
        except:
            pass

class server_setup():
    def __main__(self):
        socket_tcp = socket(AF_INET, SOCK_STREAM)
        socket_tcp.bind(ADDR)
        socket_tcp.listen(5)

        threads = []

        while True:
            try:
                print ('Waiting for connection...')
                tcpconnenct, addr = socket_tcp.accept()
                print ('...connected from:', addr)

                client = client(addr, tcpconnenct)
                client_Thread = Client_Thread(client)
                threads += [client_Thread]
                client_Thread.start()
            except KeyboardInterrupt:
                print ('KeyboardInterrupt:')
                for t in threads:
                    t.stop()
                break

        socket_tcp.close()


if __name__ == '__main__':
    HOST = '172.21.191.236'
    PORT = 8945
    PORT_V = 9808
    PORT_F = 9809
    BUFSIZ = 4096
    ADDR = (HOST, PORT)
    ADDR_V = (HOST, PORT_V)
    ADDR_F = (HOST, PORT_F)

    voice_socket = socket(AF_INET, SOCK_STREAM)
    voice_socket.bind(ADDR_V)
    voice_socket.listen(10)
    voice_list = []
    def broadcast(sock, data, list, server_setup_socket):
        for client in list:
            if client != server_setup_socket and client != sock:
                try:
                    client.send(data)
                except:
                    pass

    def client_get_client(c, list, server_setup_socket):
        while 1:
            try:
                data = c.recv(4096)
                broadcast(c, data, list, server_setup_socket)

            except error:
                c.close()

    def voice_thread():
        while True:
            c, addr = voice_socket.accept()
            print("c", c)
            voice_list.append(c)
            threading.Thread(target=client_get_client, args=(c,voice_list, voice_socket )).start()

    threading.Thread(target=voice_thread).start()


    file_socket = socket(AF_INET, SOCK_STREAM)
    file_socket.bind(ADDR_F)
    file_socket.listen(10)
    file_list = []
    def file_thread():
        while True:
            c, addr = file_socket.accept()
            print("c", c)
            file_list.append(c)
            threading.Thread(target=client_get_client, args=(c,file_list, file_socket)).start()

    threading.Thread(target=file_thread).start()


    server_setup = server_setup()
    server_setup.__main__()

