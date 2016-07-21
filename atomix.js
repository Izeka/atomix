var sock = null;
var ellog = null;
window.onload = function() {
    ellog = document.getElementById('log');

    var wsuri;
    if (window.location.protocol === "file:") {
       wsuri = "ws://127.0.0.1:8080/ws?a=23&foo=bar";
    } else {
       wsuri = "ws://" + window.location.hostname + ":8080/ws?a=23&foo=bar";
    }

    if ("WebSocket" in window) {
       sock = new WebSocket(wsuri);
    } else if ("MozWebSocket" in window) {
       sock = new MozWebSocket(wsuri);
    } else {
       log("Browser does not support WebSocket!");
    }

    if (sock) {
        sock.onopen = function() {
            log("CLI> Connected to " + wsuri);
        };
        sock.onclose = function(e) {
            log("CLI> Connection closed (wasClean = " + e.wasClean + ", code = " + e.code + ", reason = '" + e.reason + "')");
            sock = null;
        };
        sock.onmessage = function(e) {
            var obj = JSON.parse(e.data);
            switch (obj.Event) {
               case "Command":
                   log(obj.Data)
                 break;
               case "Peers":
                   for (var key in obj.Data){
                       PJSipContact(key);
                       if (obj.Data[key] == "OK") {
                           ContactRegistered(key);
                       }
                   }
                   break;
                 case "Dahdi":
                     DahdiContact(obj.Data);
                     break;
                 case "Newchannel":
                     Newchannel(obj.Data);
                     break;
                 case "Newstate":
                     Updatechannel(obj.Data);
                     break;
                 case "Hangup":
                     Destroychannel(obj.Data);
                     break;
                case "PeerStatus":
                     UpdatePJSipContact(obj.Data);
                     break;
                case "Alarm":
                case "AlarmClear":
                     UpdateDAHDI(obj.Data);
                     break;
                }
            }
        }
    }

    function sendCommand() {
            command = document.getElementById( "command").value
            log("CLI> "+command)
            sock.send(command);
    };

    function DahdiContact(line) {
        //creates DIV Element, and assign ID
        var div = document.createElement("DIV");
        div.setAttribute("id", line.dahdichannel );
        //creates DIV Title Element, then asigns class and  inner text
        var title = document.createElement("DIV")
        title.setAttribute("class", "contact-title" );
        title.innerText= "DAHDI/"+line.dahdichannel;
        //creates DIV alarm Element, then assigns id and innter text
        var alarm = document.createElement("TEXT")
        alarm.setAttribute("id", line.dahdichannel+"-status" );
        alarm.innerText= line.alarm;
        //set class by Alarm Status
        switch (line.alarm) {
        case "Red Alarm":
            div.setAttribute("class", "btn btn-danger" );
            break;
        case "No Alarm":
            div.setAttribute("class", "btn btn-success" );
            break;
        }
        //append div to document
        div.appendChild(title);
        div.appendChild(alarm);
        document.getElementById("dahdi").appendChild(div);
    }
    function UpdateDAHDI(line) {
        if (!!line.alarm) {
            div = document.getElementById(line.dahdichannel);
            div.setAttribute("class", "btn btn-danger" );
            text = document.getElementById(line.dahdichannel+"-status");
            text.innerText= line.alarm;
        }
        else {
            div = document.getElementById(line.channel);
            div.setAttribute("class", "btn btn-success" );
            text = document.getElementById(line.channel+"-status");
            text.innerText= "No Alarm";
        }
    }
    function PJSipContact(id) {
        //create DIV element, then asigns id
        var btn = document.createElement("DIV");
        btn.setAttribute("id", id );
        //create DIV title element, then assigns inner text and class
        var title = document.createElement("DIV")
        title.setAttribute("class", "contact-title" );
        title.innerText= id;
        //creates DIV alarm Element, then assigns id
        var alarm = document.createElement("TEXT")
        alarm.setAttribute("id", id+"-status" );
        //eppend div to document
        btn.appendChild(title);
        btn.appendChild(alarm);
        document.getElementById("pjsip").appendChild(btn);
        //set contact as Unregistered
        ContactNotRegistered(id);
    }
    function ContactNotRegistered(id){
        //gets contact btn and alarm by id, set innerText and assigns classes
        var btn = document.getElementById(id);
        var alarm = document.getElementById(id+"-status");
        alarm.innerText= "No Registered";
        btn.setAttribute("class", "btn btn-default" );
    }
    function ContactRegistered(id) {
        //gets contact btn and alarm by id, set innerText and assigns classes
        var btn=document.getElementById(id);
        var alarm = document.getElementById(id+'-status');
        //set classes to contact button and alarm div if exists
        if (!!btn) {
            btn.setAttribute("class", "btn btn-success" );
        }
        if (!!alarm){
            //check if contact is dahdi or sip
            if (id.length <=2 ){
                alarm.innerText="No Alarm";
            }
            else {
                alarm.innerText="Registered";
            }
        }
    }
    function ContactUp(id) {
          //gets contact btn and alarm by id, set innerText and assigns classes
          var btn = document.getElementById(id);
          var alarm = document.getElementById(id+'-status');
          //set classes to contact button and alarm div if exists
          if(!!btn){
              btn.setAttribute("class", "btn btn-info" );
          }
          if (!!alarm){
              alarm.innerText="Up";
          }
      }
    function UpdatePJSipContact(chan){
        //gets peer number from channel
        var id= chan.peer.substring(6,9);
        //sets contact as Registered or Unregistered
        if ( chan.peerstatus == "Unreachable") {
            ContactNotRegistered(id)
        }
        else if (chan.peerstatus == "Reachable"){
            ContactRegistered(id);
        }
    }
    function Newchannel(chan) {
        //active caller contact
        ContactUp(chan.calleridnum);
        //sets id as the last three numbers of the channel linkedid
        var id = chan.linkedid.substr(chan.linkedid.length - 4)
        //gets link, call and btn_time by id
        var link = document.getElementById(chan.linkedid);
        var call = document.getElementById("call"+chan.linkedid);
        var btn_time = document.getElementById(id);
        //if don't exists, create link call div
        if (link == null){
          var  link = document.createElement("DIV");
          link.setAttribute("id", chan.linkedid );
          link.setAttribute("class", "row" );
          var  title = document.createElement("DIV");
          title.setAttribute("class", "row" );
          var src = document.createElement("DIV");
          src.setAttribute("class", "col-md-4 link-title " );
          src.innerText = "SRC channel";
          var dst = document.createElement("DIV");
          dst.setAttribute("class", "col-md-4 link-title " );
          dst.innerText = "DST channel";
          var time = document.createElement("DIV");
          time.setAttribute("class", "col-md-2 link-title " );
          time.innerText = "Time";
          var btn_time = document.createElement("DIV");
          btn_time.innerText = "00:00:00";
          btn_time.setAttribute("id", id);
          var call = document.createElement("DIV");
          call.setAttribute("class", "row" );
          call.setAttribute("id", "call"+chan.linkedid );

          title.appendChild(time);
          title.appendChild(src);
          title.appendChild(dst);
          call.appendChild(btn_time);
          link.appendChild(title);
          link.appendChild(call);
        }
        //create channel button
        var btn = document.createElement("DIV");
        btn.innerText = chan.channel+" "+chan.channelstatedesc;
        btn.setAttribute("id",chan.channel)
        //append button to call row
        call.appendChild(btn);
        //appends call to channels div
        document.getElementById("channels").appendChild(link);

        //create Date object, if chan.seconds exists get its value if not set it to 0
        var curdate = new Date(null);
        if( !!chan.seconds){
          seconds = curdate.setTime(chan.seconds*1000);
        }
        else {
          seconds =curdate.setTime(0*1000);
        }
        //create instance of object Timer, send id and seconds
        var timer = new Timer(id,seconds);
        //call start method of Timer object
        timer.start();
        Updatechannel(chan);
    }

    function Updatechannel(chan) {
        var id = chan.linkedid.substr(chan.linkedid.length - 4)
        var btn_time = document.getElementById(id) ;
        var btn= document.getElementById(chan.channel);
        btn.innerText = chan.channel+ " "+chan.channelstatedesc;
        // change class by status
        switch (chan.channelstatedesc) {
          case "Ringing":
            btn.setAttribute("class", "col-md-4 alert alert-danger blink" );
            break;
          case  "Up":
            //update contact status
            btn.setAttribute("class", "col-md-4 alert alert-info" );
            btn_time.setAttribute("class", "col-md-2 alert alert-info" );
            ch = chan.channel.substring(0,5);
           //check if destination contact is DAHDI
            if (ch == "DAHDI") {
                ContactUp(chan.channel.substring(6,7)); //gets character[7] from string
            }
            else {
               ContactUp(chan.calleridnum); //gets character[7:9] from string
            }
           break;
         default:
           btn_time.setAttribute("class", "col-md-2 alert alert-warning" );
           btn.setAttribute("class", "col-md-4 alert alert-warning" );
           break;
        }
    }

    function Destroychannel(chan) {
       //get chan from likedid and change status
       var link = document.getElementById(chan.linkedid);
      //update contact status
       ContactRegistered(chan.calleridnum);
       ch = chan.channel.substring(0,5);
       //check if destination contact is DAHDI
       if (ch == "DAHDI") {
           ContactRegistered(chan.channel.substring(6,7));
       }
       else {
           ContactRegistered(chan.calleridnum);
       }
       //remove link div
       if(!!link){
         link.remove();
       }
    }
function ShowPanel(id){
     var div = document.getElementById(id+"-panel");
     var btn= document.getElementById(id+"-btn");
     if (div.style.display !== 'none') {
         div.style.display = 'none';
         btn.setAttribute("class","btn")
     }
     else {
         div.style.display = 'block';
         btn.setAttribute("class","btn btn-primary")
     }
  }
function log(m) {
ellog.innerHTML += m + '\n';
ellog.scrollTop = ellog.scrollHeight;
}
//declare funcion class Timer
var Timer = function startTime(id,seconds) {
    //saves this to variable me
    var me = this;
    //gets time div of current channel
    var btn_timer = document.getElementById(id);
    //get starting time
    inicio = new Date().getTime();
    //function that changes value of btn_timer every second
    this.start = function(){
        this.actual = new Date().getTime();
        this.diff=new Date(this.actual -inicio+seconds);
        this.result=LeadingZero(this.diff.getUTCHours())+":"+LeadingZero(this.diff.getUTCMinutes())+":"+LeadingZero(this.diff.getUTCSeconds());
        btn_timer.innerHTML = this.result;
        setTimeout(function() {me.start(id)}, 1000);
    }
}
function LeadingZero(Time) {
  return (Time < 10) ? "0" + Time : + Time;
}
