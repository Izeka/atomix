from sys import stdout
from twisted.python import log
from twisted.web.server import Site
from twisted.web.static import File
from twisted.internet import reactor
from autobahn.twisted.websocket import WebSocketServerFactory, WebSocketServerProtocol
from autobahn.twisted.resource import WebSocketResource
from starpy.manager import AMIFactory, AMIProtocol
import json

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

    def connect(self):

        def onloginsuccess(ami):
            log.msg("Server %s :: AMI connected..." % (self.servername))
            return ami

        def onloginfailure(ami):
            log.msg("connection to %s failed " % (self.servername))
            return ami

        df = self.login(ip=self.servername)
        df.addCallbacks(onloginsuccess, onloginfailure)
        return df

    def clientConnectionLost(self, connector, reason):
        log.msg("Server %s :: Lost connection to AMI: %s" % (self.servername, reason.value))

    def clientConnectionFailed(self, connector, reason):
        log.msg("Server %s :: Failed to connected to AMI: %s" % (self.servername, reason.value))

class Atomix:

    def __init__(self, sock, servername, username, secret):
        self.sock = sock
        self.servername = servername
        self.username = username
        self.secret = secret
        self.start()

    def start(self):
        ami = AtomixAMIFactory(self.servername, self.username, self.secret)
        df = ami.connect()
        df.addCallback(self.getContacts, self.sock)
     #   df.addCallback(self.getEvent)
        return df

    def getContacts(self, ami, sock):

        def list(result):
            c = [contact.split()[1][:3] for contact in result[2:]]
            d = {"Event":"Contacts", "Data":c}
            payload = json.dumps(d, ensure_ascii=False).encode('utf8')
            sock.sendMessage(payload, isBinary=False)
            return result

        df = ami.command('pjsip show contacts')
        df.addCallback(list)
        return ami

    def getEvent(self, ami):

        def onEvent(ami, event):
            caller = event.get('calleridnum')
            dest = event.get('exten')
            channel = event.get('channel')
            if event.get('event') == 'Newchannel':
                if caller == "<unknown>":
                    log.msg("New external call in line %s" % channel)
                else:
                    log.msg("%s is calling extention %s" % (caller, dest))
            elif event.get('event') == 'Hangup':
                if event.get('channelstatedesc') == 'Ring':
                    log.msg("%s Hangup" % (caller))
            elif event.get('event') == 'DialBegin':
                log.msg("%s is calling extention %s" % (channel, dest))

        df = ami.registerEvent(None, onEvent)
        return ami

def RunAtomix():
    log.startLogging(stdout)

    factory = WebSocketServerFactory(u"ws://127.0.0.1:8080")
    factory.protocol = WebServerProtocol

    resource = WebSocketResource(factory)
    site = Site(resource)

    reactor.listenTCP(8080, site)
    reactor.run()

if __name__ == '__main__':
    RunAtomix()
