from twisted.internet import reactor
from starpy.manager import AMIFactory, AMIProtocol
import logging

class AtomixAMIFactory(AMIFactory):

    def __init__(self, servername, username, secret):
        self.servername = servername
        self.username = username
        self.secret = secret

    def connect(self):

        def onloginsuccess(ami):
            log.info("Server %s :: AMI connected..." % (self.servername))
            return ami

        def onloginfailure(ami):
            log.info("connection to %s failed " % (self.servername))
            return ami

        df = self.login(ip=self.servername)
        df.addCallbacks(onloginsuccess, onloginfailure)
        return df

    def clientConnectionLost(self, connector, reason):
        log.info("Server %s :: Lost connection to AMI: %s" % (self.servername, reason.value))

    def clientConnectionFailed(self, connector, reason):
        log.info("Server %s :: Failed to connected to AMI: %s" % (self.servername, reason.value))

class Atomix:

    def __init__(self, servername, username, secret):
        self.servername = servername
        self.username = username
        self.secret = secret
        self.start()

    def start(self):
        ami = AtomixAMIFactory(self.servername, self.username, self.secret)
        df = ami.connect()
        df.addCallback(self.getContacts)
        df.addCallback(self.getEvent)
        return df

    def getContacts(self, ami):

        def list(result):
            for contact in result[2:]:
                print contact.split()[1][:3]
            return result

        df = ami.command('pjsip show contacts')
        df.addCallback(list)
        return ami

    def getEvent(self, ami):

        def onEvent(ami, event):
            if event.get('channelstatedesc') == 'Ring':
                caller = event.get('calleridnum')
                dest = event.get('exten')
                if event.get('event') == 'Newchannel':
                    print "%s is calling extention %s" % (caller, dest)
                elif event.get('event') == 'Hangup':
                    print "%s Hangup" % (caller)

        df = ami.registerEvent(None,onEvent)
        return ami

def RunAtomix(AA):
    servername = "atomix"
    username = "monitor"
    secret = "asteriskmonit"
    global log

    log = logging.getLogger()
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
    handler.setFormatter(formatter)
    log.addHandler(handler)
    log.setLevel(logging.INFO)

    Atomix(servername, username, secret)
    reactor.run()

if __name__ == '__main__':
    RunAtomix(Atomix)
