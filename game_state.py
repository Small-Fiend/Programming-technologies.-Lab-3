import client
import json
import model
import messages

END_CHARACTER = "\0"
MESSAGE_PATTERN = "{username}>{message}"
TARGET_ENCODING = "utf-8"

class Game_st(object):

    def __init__(self, **kwargs):        
        self.game = 0        
        self.counter = 0
        self.leader = client.Client()
        self.gamer = client.Client()       
        self.message = model.Message()
        self.__dict__.update(kwargs)

    def marshal(self):
        return (json.dumps(self.__dict__) + END_CHARACTER).encode(TARGET_ENCODING)