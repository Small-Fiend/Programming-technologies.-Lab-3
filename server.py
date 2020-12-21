# -*- coding: utf-8 -*-
import json
import socket
import sys
import threading
import model
import client
import time
import messages
import game_state


BUFFER_SIZE = 2 ** 10
CLOSING = "Application closing..."
CONNECTION_ABORTED = "Connection aborted"
CONNECTED_PATTERN = "Client connected: {}:{}"
ERROR_ARGUMENTS = "Provide port number as the first command line argument"
ERROR_OCCURRED = "Error Occurred"
EXIT = "exit"
JOIN_PATTERN = "{username} has joined"
LOGOUT_PATTERN = "{username} has left the game"
CHANGE_ROLE = "Now {username1} lead, {username2} play"
RUNNING = "Server is running..."
SHUTDOWN_MESSAGE = "shutdown"
TYPE_EXIT = "Type 'exit' to exit>"


class Server(object):

    def __init__(self, argv):
        self.clients = set()
        self.listen_thread = None
        self.port = None
        self.sock = None
        self.parse_args(argv)
        #self.message = model.Message()
        self.server_message = model.Message() 
        self.server_message.username = messages.SERVER
        #self.action_message.message = model.Action()

        self.game_state = game_state.Game_st()
        self.stop = False

        '''self.game_state.leader = client.Client()
        self.game_state.gamer = client.Client()
        self.game = 0        
        self.counter = 0'''


    def listen(self):
        self.sock.listen(1)
        while True:
            try:
                client, address = self.sock.accept()
            except OSError:
                print(CONNECTION_ABORTED)
                return
            print(CONNECTED_PATTERN.format(*address))
            if len(self.clients) < 2:
                self.clients.add(client)       
            else:
                self.server_message.message = messages.SERVER_OVERFLOW
                client.sendall(self.server_message.marshal())
                client.close()
            threading.Thread(target=self.handle, args=(client,)).start()

    def handle(self, client):
        while True:

            try:
                message = model.Message(**json.loads(self.receive(client)))
            except (ConnectionAbortedError, ConnectionResetError):
                print(CONNECTION_ABORTED)
                return
            if  message.quit:
                client.close()
                self.clients.remove(client)

                if (self.game_state.leader.name == message.username and self.game_state.gamer.name is None) \
                        or (self.game_state.gamer.name == message.username and self.game_state.leader.name is None):
                    self.game_state.gamer.name = None
                    self.game_state.leader.name = None
                elif self.game_state.leader.name == message.username:
                    self.game_state.leader.name = self.game_state.gamer.name
                    self.game_state.gamer.name = None
                    self.server_message.message = LOGOUT_PATTERN.format(username='Leader')
                elif self.game_state.gamer.name == message.username:
                    self.game_state.gamer.name = None
                    self.server_message.message = LOGOUT_PATTERN.format(username='Gamer')
                self.broadcast(self.server_message)
                if self.game_state.leader.name is not None:
                    self.start_game()
                self.game = 0
                return
            print(str(message))
            if SHUTDOWN_MESSAGE.lower() == message.message.lower():
                self.exit()
                if self.game_state.leader.name == message.username:
                    self.game_state.leader.name = None
                else:
                    self.game_state.gamer.name = None
                return
            if not self.check(message): #проверка состояния
                self.start_game()
                continue

            if message.username == self.game_state.leader.name:
                self.game_state.leader.last_message = message.message
            else:
                self.game_state.gamer.last_message = message.message
            self.broadcast(message)

            if message.username == self.game_state.leader.name:
                for i in range(0, 7):
                    if not self.stop:
                        if i==0:
                            time.sleep(0.1)
                        else:
                            time.sleep(0.9)
                        self.counter += 1
                        self.server_message.message = str(7 - self.counter)
                        self.broadcast(self.server_message)
                    else:
                        break
                if self.stop:
                    continue
            else:
                self.stop = True

            if self.stop:
                self.finish(False)
            else:
                self.finish(True)
            self.start_game()




    def start_game(self):
        self.counter = 0
        self.game_state.game = 0
        self.game_state.leader.last_message = None
        self.game_state.gamer.last_message = None
        self.stop = False
        if len(self.clients) == 1:
            self.server_message.message = messages.WAITING_USER
        elif len(self.clients) == 2:
            self.server_message.message = CHANGE_ROLE.format(username1=self.game_state.leader.name, username2=self.game_state.gamer.name)
        else:
            return
        self.broadcast(self.server_message)

    def finish(self, is_time_over):
        if is_time_over:
            self.server_message.message = self.game_state.leader.name + " is a winner!"
        else:
            if self.game_state.leader.last_message == self.game_state.gamer.last_message:
                self.server_message.message = self.game_state.gamer.name + " is a winner!"
            else:
                self.server_message.message = self.game_state.leader.name + " is a winner!"
        print(self.server_message.message)
        self.broadcast(self.server_message)

        temp = self.game_state.leader
        self.game_state.leader = self.game_state.gamer
        self.game_state.gamer = temp

        time.sleep(1)

    #true - значит сообщение от пользователя, а не программное

    def check(self, message):
        if self.game_state.leader.name is None:
            self.game_state.leader.name = message.username
            return False
        elif self.game_state.gamer.name is None:
            self.game_state.gamer.name = message.username
            return False
        return True

    def broadcast(self, message):
        for client in self.clients:
            client.sendall(message.marshal())

    def receive(self, client):
        buffer = ""
        while not buffer.endswith(model.END_CHARACTER):
            buffer += client.recv(BUFFER_SIZE).decode(model.TARGET_ENCODING)
        return buffer[:-1]

    def run(self):
        print(RUNNING)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(("", self.port))
        self.listen_thread = threading.Thread(target=self.listen)
        self.listen_thread.start()

    def parse_args(self, argv):
        #if len(argv) != 2:
        #    raise RuntimeError(ERROR_ARGUMENTS)
        try:
            self.port = 3030
        except ValueError:
            raise RuntimeError(ERROR_ARGUMENTS)

    def exit(self):
        self.sock.close()
        for client in self.clients:
            client.close()
        print(CLOSING)


if __name__ == "__main__":
    try:
        Server(sys.argv).run()
    except RuntimeError as error:
        print(ERROR_OCCURRED)
        print(str(error))
