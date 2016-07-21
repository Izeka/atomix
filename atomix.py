import json
from sys import stdout
from twisted.python import log
from twisted.web.server import Site
from twisted.web.static import File
from ConfigParser import ConfigParser

from twisted.internet import reactor
from autobahn.twisted.websocket import WebSocketServerFactory, WebSocketServerProtocol
from autobahn.twisted.resource import WebSocketResource
from starpy.manager import AMIFactory

class Server():
    config = ConfigParser()
    config.read("atomix.conf")
    servername = config.sections()[0]
    username = config.get(servername,'username')
    secret = config.get(servername,'secret')

class WebServerProtocol(WebSocketServerProtocol):

    config=Server()
    servername = config.servername
    username = config.username
    secret = config.secret
    atom = None

    def onConnect(self, request):
        self.atom= Atomix(self, self.servername, self.username, self.secret)

    def onMessage(self,payload, isBinary):
        self.sendMessage(payload, isBinary)
        def send_result(results):
            for line in results:
                json_dic = {"Event": "Command",
                        "Data": line}
                payload = json.dumps(json_dic, ensure_ascii=False).encode('utf8')
                self.sendMessage(payload, isBinary=False)
        def execute_command(ami):
            defered = ami.command(self.command)
            defered.addCallback(send_result)
        self.command = payload.decode('utf8')
        print("Command received: {0}".format(self.command))
        defered = self.atom.ami.login(ip=self.servername)
        defered.addCallback(execute_command)

class AtomixAMIFactory(AMIFactory):

    def __init__(self, servername, username, secret):
        self.servername = servername
        self.username = username
        self.secret = secret
        self.plaintext_login = True
        self.id = None

    def clientConnectionLost(self, connector, reason):
        log.msg("Server %s :: Lost connection to AMI: %s" % (self.servername, reason.value))

    def clientConnectionFailed(self, connector, reason):
        log.msg("Server %s :: Failed to connected to AMI: %s" % (self.servername, reason.value))

class Atomix(object):
    def __init__(self, sock, servername, username, secret):
        self.sock = sock
        self.servername = servername
        self.username = username
        self.secret = secret
        self.ami = None
        self.start()

    def start(self):
        self.ami = AtomixAMIFactory(self.servername, self.username, self.secret)
        self.connect(self.ami)

    def connect(self, ami):
        def onloginsuccess(ami):
            print "Server %s :: AMI connected..." % (self.servername)
            return ami

        def onloginfailure(ami):
            print "Server %s :: Monast AMI Failed to Login, reason: %s" % (self.servername)
            return ami

        defered = ami.login(ip=self.servername)
        defered.addCallbacks(onloginsuccess, onloginfailure)
        defered.addCallback(self.connected)

    def connected(self, ami):
        self.get_contacts(ami)
        self.get_channels(ami)
        ami.registerEvent(None, self.handle_event)
        return ami

    def get_contacts(self, ami):

        def send_contacts(result, event):
            if event == "peers":
                 numbers = { i.get("objectname"): i.get("status")[0:2] for i in result[1:-1] if i.get("objectname") != None}
                 json_dic = {"Event":"Peers", "Data":numbers}
                 payload = json.dumps(json_dic, ensure_ascii=False).encode('utf8')
                 self.sock.sendMessage(payload, isBinary=False)
            if event == "dahdi":
                for dahdi_channel in result:
                    if dahdi_channel.get("event") == "DAHDIShowChannels":
                        json_dic = {"Event":"Dahdi", "Data": dahdi_channel}
                        payload = json.dumps(json_dic, ensure_ascii=False).encode('utf8')
                        self.sock.sendMessage(payload, isBinary=False)
            return result

        def error_contacts(failure):
             log.msg("DAHDI not found" )
             return

        defered = ami.sipPeers()
        defered.addCallback(send_contacts, "peers")
        defered = ami.dahdiShowChannels()
        defered.addCallback(send_contacts,"dahdi")
        defered.addErrback(error_contacts)

        return ami

    def get_channels(self, ami):

        def send_contacts(result):
            for channel in result:
                if channel.get("linkedid"):
                    json_dic = {"Event":"Newchannel",
                                "Data": channel}
                    payload = json.dumps(json_dic, ensure_ascii=False).encode('utf8')
                    self.sock.sendMessage(payload, isBinary=False)
        defered = ami.status()
        defered.addCallback(send_contacts)
        return ami

    def handle_event(self, ami, data):
        event = data.get('event')
        if event in {"Newchannel", "Newstate", "Hangup", "PeerStatus", "Alarm", "AlarmClear"}:
            if event == "Newstate":
                print "%s" % data
            json_dic = {"Event": event,
                        "Data": data}
            payload = json.dumps(json_dic, ensure_ascii=False).encode('utf8')
            self.sock.sendMessage(payload, isBinary=False)
        return ami

def runatomix():
    log.startLogging(stdout)
    factory  = WebSocketServerFactory(u"ws://127.0.0.1:8080")
    factory.protocol = WebServerProtocol
    resource = WebSocketResource(factory)
    root = File(".")
    root.putChild(u"ws", resource)
    site = Site(root)
    reactor.listenTCP(8080, site)
    reactor.run()

if __name__ == '__main__':
    runatomix()
