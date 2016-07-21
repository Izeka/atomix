# Atomix

Asterisk monitoring web panel made in Python (Twisted + Autobahn + Starpy) and Javascript

#Configuration

Configure asterisk manager :

    [monitor]
    secret=monitor_secret
    writetimeout=100
    read=system,call,log,verbose,command,agent,user,config,originate,reporting
    write=system,call,log,verbose,command,agent,user,config,originate,reporting

Modify atomix.conf with your asterisk pbx host, manager user, secret and port :
 
    [hostnameorip]
    username= monitor
    secret = monitor_secret
    port = 5038

Run atomix.py ::

    # cd atomix
    # ./atomix.py

Point your browser to :

    http://server_addr:8080


