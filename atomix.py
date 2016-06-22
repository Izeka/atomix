from sys import stdout
from twisted.python import log
from twisted.web.server import Site
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
        self.events = {
                        'Newchannel'          : self.EventNewchannel,
                        'Newstate'            : self.EventNewstate,
                        'Hangup'              : self.EventHangup,
                      }
        self.start()

    def start(self):
        ami = AtomixAMIFactory(self.servername, self.username, self.secret)
        self.connect(ami)

    def connect(self,ami):
        def onloginsuccess(ami):
            print "Server %s :: AMI connected..." % (self.servername)
            return ami

        def onloginfailure(ami):
            print "Server %s :: Monast AMI Failed to Login, reason: %s" % (self.servername)
            return ami

        df = ami.login(ip=self.servername)
        df.addCallbacks(onloginsuccess, onloginfailure)
        df.addCallback(self.connected)

    def connected(self,ami):
      self.getContacts(ami)
      for event, function in self.events.items():
          ami.registerEvent(event,function)


    def getContacts(self, ami):

        def list(result,event):
             if event =="contacts":
                 c = [contact.split()[1][:3] for contact in result[2:]]
                 d = {"Event":"Contacts", "Data":c}
             if event =="auths":
                 c = [contact.split()[1][:3] for contact in result[2:]]
                 d = {"Event":"Auths", "Data":c}
             if event =="dahdi":
                 c= ["DAHDI/%s" % line.get('dahdichannel') for line in result]
                 d = {"Event":"Dahdi", "Data":c}
             payload = json.dumps(d, ensure_ascii=False).encode('utf8')
             self.sock.sendMessage(payload, isBinary=False)
             return result

        df=ami.command('pjsip show auths')
        df.addCallback(list,"auths")
        df=ami.command('pjsip show contacts')
        df.addCallback(list,"contacts")
        df=ami.DAHDIShowChannels()
        df.addCallback(list,"dahdi")

        return ami

    def EventNewstate(self, ami, event):
        state = event.get('channelstatedesc')
        channel = event.get('channel')
        caller= event.get('calleridnum')
        dest = event.get('exten')
        c= [channel, caller, dest]
        d = {"Event":"Newstate",
             "State": state,
             "Channel": channel,
             "Caller": caller,
             "Dest": dest}
        payload = json.dumps(d, ensure_ascii=False).encode('utf8')
        self.sock.sendMessage(payload, isBinary=False)

    def EventNewchannel(self, ami, event):
        state = event.get('channelstatedesc')
        channel = event.get('channel')
        caller = event.get('calleridnum')
        dest = event.get('exten')
        c = [channel, caller, dest]
        d = {"Event":"Newchannel",
             "State": state,
             "Channel": channel,
             "Caller": caller,
             "Dest": dest}
        payload = json.dumps(d, ensure_ascii=False).encode('utf8')
        self.sock.sendMessage(payload, isBinary=False)

    def EventHangup(self, ami, event):
        state = event.get('channelstatedesc')
        channel = event.get('channel')
        caller = event.get('calleridnum')
        dest = event.get('exten')
        d = {"Event":"Hangup",
             "State": state,
             "Channel": channel,
             "Caller": caller,
             "Dest": dest}
        payload = json.dumps(d, ensure_ascii=False).encode('utf8')
        self.sock.sendMessage(payload, isBinary=False)

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
