class Client(object):

    def __init__(self, **kwargs):
        self.sock = None
        self.name = None
        self.last_message = None
        self.__dict__.update(kwargs)

    def __repr__(self):
        return '{"name": "'+str(self.name)+'", "last_message": "'+str(self.last_message)+'"}'