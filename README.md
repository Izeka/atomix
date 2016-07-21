# Atomix

Asterisk monitoring web panel made in Python (Twisted + Autobahn + Starpy) and Javascript

#Configuration

 -
    -Sample ::

    [monitor]
    secret=monitor_secret
    writetimeout=100
    read=system,call,log,verbose,command,agent,user,config,originate,reporting
    write=system,call,log,verbose,command,agent,user,config,originate,reporting

 Configure asterisk manager ::

    from extra_views import ModelFormSetView


    class ItemFormSetView(ModelFormSetView):
        model = Item
        template_name = 'item_formset.html'
        
 - Modify atomix.conf with your asterisk pbx host, manager user, secret and port
    -Sample ::

      [hostnameorip]
      username= monitor
      secret = monitor_secret
      port = 5038

 - Run atomix.py:
    # cd atomix

    # ./atomix.py

 - Point your browser to:  http://server_addr:8080


