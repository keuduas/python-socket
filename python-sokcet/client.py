#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
# Date: 2024.05.13

from socket import *
import json
from tkinter import *
import threading
import ctypes
import inspect
import sys
import struct
import pyaudio
from importlib import reload
reload(sys)
# sys.getdefaultencoding('utf-8')

class R():
    SENDERPORT = 1501
    MYPORT = 1234
    MYGROUP = '224.1.1.1'

class client_setup():
    def __init__(self):
        self.connected = False

    def connect(self):
        if not self.connected:
            self.socket_tcp = socket(AF_INET, SOCK_STREAM)
            self.socket_tcp.connect(ADDR)
            self.connected = True
            print ("连接成功")
        else:
            print ("已经连接，不再重新连接")

    def disconnected(self):
        self.socket_tcp.close()

    def show_error(self, text):
        error_window = Tk()
        error_window.geometry('200x120')
        error_window.title("Error!")
        Label(error_window, text = text).pack(padx = 5, pady = 20, fill = 'x')
        bt = Button(error_window, text = "确定", command = error_window.destroy).pack()
        error_window.mainloop()

    class Login():
        def __init__(self, origin):
            self.origin = origin

        def login_setup(self, entry_1,entry_2, loginWindow):
            username = entry_1.get()
            passwd= entry_2.get()
            self.origin.username = username
            self.origin.passwd=passwd
            data = {"type": "login", "username": username , "passwd": passwd }
            json_data = json.dumps(data)
            try:
                self.origin.connect()
            except Exception as e:
                print (e)
                self.origin.show_error("网络连接异常，无法连接服务器")
                return False
            else:
                socket = self.origin.socket_tcp
                socket.send(json_data.encode())
                recv_json_data = socket.recv(BUFSIZ)
                recv_data = json.loads(recv_json_data)
                if recv_data["type"] == "login" and \
                        recv_data["username"] == username and \
                        recv_data["status"] == True:
                    print ("login success")
                    main_window = self.origin.main_window(self.origin)
                    loginWindow.destroy()
                    main_window.__main__()
                else:
                    if recv_data["text"]:
                        self.origin.show_error(recv_data["text"])
                    else:
                        self.origin.show_error("未知登录错误")

        def window(self):
            tk = Tk()
            tk.geometry('400x200')
            tk.title('登录界面')
            frame = Frame(tk)
            frame.pack(expand = YES, fill = BOTH)
            Label(frame, font = ("Arial, 10"),
                    text = "请输入用户名和密码：", anchor = 'w').pack(padx = 10,
                            pady = 15, fill = 'x')
            entry_1 = Entry(frame)
            entry_1.pack(padx = 10, fill = 'x')
            entry_2 = Entry(frame)
            entry_2.pack(padx = 10, fill = 'x')
            button = Button(frame, text = "登录",
                    command = lambda : self.login_setup(entry_1,entry_2, tk))
            button.pack()

            tk.mainloop()

        def __main__(self):
            self.window()

    class main_window():
        def __init__(self, origin):
            self.origin = origin
            self.socket = origin.socket_tcp 
            self.client_one_end = None
            self.client_two_end = None

        class ListenThread(threading.Thread):
            def __init__(self, socket, origin):
                threading.Thread.__init__(self)
                self.origin = origin
                self.socket = socket

            def run(self):
                while True:
                    try:
                        json_data = self.socket.recv(BUFSIZ).decode()
                        data = json.loads(json_data)
                    except:
                        break
                    print ("__receive__" + json_data)
                    switch = {
                            "list": self.list,
                            "singleChat": self.chat,
                            "groupChat": self.chat,
                            "pong": self.pong
                            }
                    switch[data['type']](data)
                print ("结束监听")

            def list(self, data):
                listbox = self.origin.listbox
                list = ['群聊', '组播']
                list += data['list']
                listbox.delete(0, END) 
                for l in list:
                    listbox.insert(END, l) 

            def chat(self, data):
                textArea = self.origin.textArea
                text = ('[群聊]' if data['type'] == 'groupChat' else '') + \
                        data['from'] + ': ' + data['msg'] + '\n'
                textArea.insert(END, text)

            def pong(self, data):
                """ping pong!"""
                text = '[Server]pong\n'
                textArea.insert(END, text)

        class BroadListenThread(threading.Thread):
            def __init__(self, origin):
                threading.Thread.__init__(self)
                self.origin = origin

            def run(self):
                print ('开始监听组播')
                self.alive = True
                sock = self.origin.client_one_end
                while self.alive:
                    try:
                        json_data, addr = sock.recvfrom(BUFSIZ)
                        data = json.loads(json_data)
                    except Exception as e:
                        pass
                    else:
                        textArea = self.origin.textArea
                        text = "[组播]" + data['from'] + ': ' + data['msg'] + '\n'
                        textArea.insert(END, text)
                        print ("__receiveBroad__" + json_data)
                print ('组播监听循环结束')

            def stop(self):
                self.alive = False

        class Window():
            def __init__(self, origin):
                self.origin = origin

            def refresh(self, socket):
                data = {"type": "list"}
                json_data = json.dumps(data)
                socket.send(json_data.encode())

            def changeAddr(self):
                def setAddr(entry1, entry2, entry3, self, tk):
                    if self.origin.client_one_end:
                        self.origin.broadListenThread.stop()
                        self.origin.client_two_end = None.sendto("", (R.MYGROUP, R.MYPORT))
                        print ('停止之前的地址')

                    try:
                        R.MYGROUP = entry1.get()
                        R.MYPORT = int(entry2.get())
                        R.SENDERPORT = int(entry3.get())
                        s = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
                        s.bind((HOST, R.SENDERPORT))
                        ttl_bin = struct.pack('@i', MYTTL)
                        s.setsockopt(IPPROTO_IP, IP_MULTICAST_TTL, ttl_bin)
                        status = s.setsockopt(IPPROTO_IP, IP_ADD_MEMBERSHIP,
                                inet_aton(R.MYGROUP) +
                                inet_aton(HOST))
                        self.origin.client_two_end = None = s

                        so = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
                        so.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
                        so.bind((HOST, R.MYPORT))
                        status = so.setsockopt(IPPROTO_IP,
                                IP_ADD_MEMBERSHIP,
                                inet_aton(R.MYGROUP) +
                                inet_aton(HOST))
                        so.setblocking(0)
                        self.origin.client_one_end = so

                    except Exception as e:
                        print (e)
                        self.origin.origin.show_error("该地址不可使用")
                    else:
                        broadListenThread = self.origin.BroadListenThread( \
                                self.origin)
                        broadListenThread.start()
                        self.origin.broadListenThread = broadListenThread
                        tk.destroy()

                def isset(v):
                    try:
                        type(eval(v))
                    except:
                        return False
                    else:
                        return True

                tk = Tk()
                tk.geometry('270x120')
                tk.title('请修改组播设置')
                Label(tk, text = "组播地址: ").grid(row = 0, column = 0)
                Label(tk, text = "监听端口: ").grid(row = 1, column = 0)
                Label(tk, text = "本地端口: ").grid(row = 2, column = 0)
                entry1 = Entry(tk)
                entry1.grid(row = 0, column = 1)
                entry1.insert(END, R.MYGROUP)
                entry2 = Entry(tk)
                entry2.grid(row = 1, column = 1)
                entry2.insert(END, R.MYPORT)
                entry3 = Entry(tk)
                entry3.grid(row = 2, column = 1)
                entry3.insert(END, R.SENDERPORT)
                bt = Button(tk, text = "确定",
                        command = lambda : setAddr(entry1, entry2, entry3,
                            self, tk)).grid(row = 3, column = 0, columnspan = 2)

                tk.mainloop()

            def sendBroad(self, msg, data_set_to_send, username):
                client_two_end = Noneself.origin.client_two_end = None
                if not client_two_end = None:
                    self.changeAddr()
                else:
                    data = {'type': 'broadChat', 'msg': msg, 'from': username}
                    json_data = json.dumps(data)
                    print (R.MYGROUP, R.MYPORT)
                    client_two_end = None.sendto(json_data, (R.MYGROUP, R.MYPORT))
                    print ('__sendBroad__' + json_data)

                    # 清空输入框
                    data_set_to_send.delete(0, END)

            def send(self, socket, talking_target, data_set_to_send, voice=False):
                text = data_set_to_send.get()
                toName = talking_target['text']
                username = self.origin.origin.username
                print (toName)
                if voice == True:
                    data = {'type': 'voice', 'msg': text,
                            'to': toName, 'from': username}
                    textArea = self.origin.textArea
                    t = "[->" + toName + ']' + text + '\n'
                    textArea.insert(END, t)
                elif toName == '群聊':
                    data = {'type': 'groupChat', 'msg': text, 'from': username}
                elif toName == '组播':
                    self.sendBroad(text, data_set_to_send, username)
                    return
                else:
                    data = {'type': 'singleChat', 'msg': text,
                            'to': toName, 'from': username}
                    textArea = self.origin.textArea
                    t = "[->" + toName + ']' + text + '\n'
                    textArea.insert(END, t)
                json_data = json.dumps(data)
                socket.send(json_data.encode())
                print ('__send__' + json_data)
                data_set_to_send.delete(0, END)

            def button_twice(self, listbox, talking_target):
                try:
                    talking_target['text'] = listbox.get(listbox.curselection())
                except:
                    pass 

            def voice_thread(self, origin_socket,talking_target, data_set_to_send):
                print("start threading")
                threading.Thread(target=self.voice(origin_socket,talking_target, data_set_to_send)).start()
                print("started threading")

            def file_thread(self, origin_socket, talking_target, data_set_to_send):
                print("start threading")
                threading.Thread(target=self.file_recv_and_send, args=(origin_socket, talking_target, data_set_to_send)).start()
                print("started threading")

            def file_recv_and_send(self, origin_socket, talking_target, data_set_to_send):
                s_file = socket(AF_INET, SOCK_STREAM)
                while 1:
                    try:
                        s_file.connect((HOST, PORT_F))
                        break
                    except:
                        print("Couldn't connect to server")
                threading.Thread(target=self.send_file,args=(s_file, data_set_to_send)).start()
                threading.Thread(target=self.recv_file,args=(s_file,)).start()

            def send_file(self,sock, data_set_to_send):
                filename = data_set_to_send.get()
                if filename == "" :
                    return
                data_set_to_send.delete(0, END)
                with open(filename, 'rb') as f:
                    while True:
                        data = f.read(4096)
                        if not data:
                            data = b'FILE_TRANSFER_DONE'
                            sock.sendall(data)
                            break
                        sock.sendall(data)

            def recv_file(self, sock):
                with open("test.jpg", 'wb') as f:
                    received_size = 0
                    while True:
                        data = sock.recv(4096)
                        if data.endswith(b'FILE_TRANSFER_DONE'):
                            f.write(data[:-len(b'FILE_TRANSFER_DONE')])
                            break
                        f.write(data)
                        received_size += len(data)
                        print(f"Received: {received_size / (1024 * 1024):.2f} MB")

                print("writing finish")
                sock.close()

            def voice(self,origin_socket,talking_target, data_set_to_send):
                self.send(origin_socket,talking_target, data_set_to_send, voice=True)
                self.s = socket(AF_INET, SOCK_STREAM)
                while 1:
                    try:
                        self.target_ip = HOST
                        self.target_port = PORT_V
                        self.s.connect((self.target_ip, self.target_port))

                        break
                    except:
                        print("Couldn't connect to server")

                chunk_size = 1024 
                audio_format = pyaudio.paInt16
                channels = 1
                rate = 20000
                self.p = pyaudio.PyAudio()
                self.playing_stream = self.p.open(format=audio_format, channels=channels, rate=rate, output=True,
                                          frames_per_buffer=chunk_size)
                self.recording_stream = self.p.open(format=audio_format, channels=channels, rate=rate, input=True,
                                            frames_per_buffer=chunk_size)

                print("Connected to Server")

                threading.Thread(target=self.receive_server_data).start()
                threading.Thread(target=self.send_data_to_server).start()

            def receive_server_data(self):
                while True:
                    try:
                        data = self.s.recv(1024)
                        self.playing_stream.write(data)
                    except:
                        pass

            def send_data_to_server(self):
                while True:
                    try:
                        data = self.recording_stream.read(1024)
                        self.s.sendall(data)
                    except:
                        pass

            def __main__(self):
                origin = self.origin
                tk = Tk()
                tk.geometry('600x400')
                tk.title('Chatroom')

                f = Frame(tk, bg='#EEEEEE', width=600, height=400)
                f.place(x=0, y=0)
                textArea = Text(f, bg='#FFFFFF', width=50,
                                height=22,
                                # state = DISABLED,
                                bd=0)
                textArea.place(x=100, y=10, anchor=NW)
                textArea.bind("<KeyPress>", lambda x: "break")
                origin.textArea = textArea
                textArea.focus_set()
                Label(f, text="双击选择发送对象:", bg="#EEEEEE").place(
                    x=500, y=10, anchor=NW)
                listbox = Listbox(f, width=10, height=4, bg='#FFFFFF')
                listbox.place(x=500, y=35, anchor=NW)
                origin.listbox = listbox
                refresh_button = Button(f, text="刷新列表",
                                    command=lambda: self.refresh(origin.socket))
                refresh_button.place(x=43, y=250, anchor=CENTER)
                addr_change_button = Button(f, text="组播地址",
                                       command=self.changeAddr)
                addr_change_button.place(x=44, y=200, anchor=CENTER)
                clear_button = Button(f, text="清屏",
                                  command=lambda: textArea.delete(0.0, END))
                clear_button.place(x=35, y=50, anchor=CENTER)
                talking_target = Label(f, text="群聊", bg='#FFFFFF', width=8)
                talking_target.place(x=12, y=360)
                listbox.bind('<Double-Button-1>',
                             lambda x: self.button_twice(listbox, talking_target))
                self.talking_target = talking_target
                data_set_to_send = Entry(f, width=37)
                data_set_to_send.place(x=90, y=358)
                self.data_set_to_send = data_set_to_send
                send_button = Button(f, text="ENTER",
                                 command=lambda: self.send(origin.socket,
                                                           talking_target, data_set_to_send))
                send_button.place(x=400, y=371, anchor=CENTER)

                voice_send = Button(f, text="VOICE",
                                    command=lambda: self.voice_thread(origin.socket,
                            talking_target, data_set_to_send))
                voice_send.place(x=40, y=100, anchor=CENTER)
                file_send = Button(f, text="FILE",
                                   command=lambda: self.file_thread(origin.socket,
                            talking_target, data_set_to_send))
                file_send.place(x=33, y=150, anchor=CENTER)
                self.refresh(origin.socket)

                tk.mainloop()

                origin.socket.shutdown(2)
                print('Socket 断开')
                try:
                    origin.broadListenThread.stop()
                    origin.client_two_end = None.sendto("", (R.MYGROUP, R.MYPORT))
                except:
                    pass
                print('client_one_end 断开')

        def __main__(self):
            listenThread = self.ListenThread(self.socket, self)
            listenThread.start()
            self.listenThread = listenThread
            window = self.Window(self)
            window.__main__()
            self.window = window

    def __main__(self):
        #pass
        login = client_setup.Login(self)
        login.__main__()

if __name__ == '__main__':
    global HOST
    global PORT
    global BUFSIZ
    global ADDR

    HOST = '39.107.253.34'
    PORT = 8945
    PORT_V = 9808
    PORT_F = 9809
    BUFSIZ = 1024
    ADDR = (HOST, PORT)
    MYTTL = 255

    client_setup = client_setup()
    client_setup.__main__()
