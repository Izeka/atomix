import json
from sys import stdout
from twisted.python import log
from twisted.web.server import Site
from twisted.web.static import File

from twisted.internet import reactor
from autobahn.twisted.websocket import WebSocketServerFactory, WebSocketServerProtocol
from autobahn.twisted.resource import WebSocketResource
from starpy.manager import AMIFactory

class WebServerProtocol(WebSocketServerProtocol):
    servername = "atomix"
    username = "monitor"
    secret = "asteriskmonit"

    def onConnect(self, request):
        Atomix(self, self.servername, self.username, self.secret)

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
        self.start()

    def start(self):
        ami = AtomixAMIFactory(self.servername, self.username, self.secret)
        self.connect(ami)

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

    def get_contacts(self, ami):

        def send_contacts(result, event):
            if event == "contacts":
                numbers = [contact.split()[1][:3] for contact in result[2:]]
                json_dic = {"Event":"Contacts", "Data":numbers}
                payload = json.dumps(json_dic, ensure_ascii=False).encode('utf8')
                self.sock.sendMessage(payload, isBinary=False)
            if event == "auths":
                numbers = [contact.split()[1][:3] for contact in result[2:]]
                json_dic = {"Event":"Auths", "Data":numbers}
                payload = json.dumps(json_dic, ensure_ascii=False).encode('utf8')
                self.sock.sendMessage(payload, isBinary=False)
            if event == "dahdi":
                for dahdi_channel in result:
                    if dahdi_channel.get("event") == "DAHDIShowChannels":
                        json_dic = {"Event":"Dahdi", "Data": dahdi_channel}
                        payload = json.dumps(json_dic, ensure_ascii=False).encode('utf8')
                        self.sock.sendMessage(payload, isBinary=False)
            return result

        defered = ami.command('pjsip show auths')
        defered.addCallback(send_contacts, "auths")
        defered = ami.command('pjsip show contacts')
        defered.addCallback(send_contacts, "contacts")
        defered = ami.dahdiShowChannels()
        defered.addCallback(send_contacts, "dahdi")

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
        if event in {"Newchannel", "Newstate", "Hangup"}:
            json_dic = {"Event": event,
                        "Data": data}
            payload = json.dumps(json_dic, ensure_ascii=False).encode('utf8')
            self.sock.sendMessage(payload, isBinary=False)
        return ami

def runatomix():
    log.startLogging(stdout)

    factory = WebSocketServerFactory(u"ws://127.0.0.1:8080")
    factory.protocol = WebServerProtocol

    resource = WebSocketResource(factory)
    root = File(".")

    # and our WebSocket server under "/ws"
    root.putChild(u"ws", resource)

    site = Site(root)

    reactor.listenTCP(8080, site)
    reactor.run()

if __name__ == '__main__':
    runatomix()
