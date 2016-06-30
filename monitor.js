var sock = null;
var ellog = null;
window.onload = function() {
    ellog = document.getElementById('log');
    var wsuri;
 /*   wsuri = "ws://" + window.location.hostname + ":8080";*/
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
            log("Connected to " + wsuri);
        }
        sock.onclose = function(e) {
            log("Connection closed (wasClean = " + e.wasClean + ", code = " + e.code + ", reason = '" + e.reason + "')");
            sock = null;
        }
        sock.onmessage = function(e) {
            var obj = JSON.parse(e.data);
            switch (obj.Event) {
               case "Auths":
                   la=obj.Data.length;
                   for(var i=0; i<la; ++i){
                       PJSipContact(obj.Data[i]);
                   }
                   break;
               case "Contacts":
                   la=obj.Data.length;
                   for(var i=0; i<la; ++i){
                       ContactActive(obj.Data[i]);
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
              }
          }
      }
  }

  function DahdiContact(line) {
      //creates DIV Element, and assign ID
      var div = document.createElement("DIV");
      div.setAttribute("id", line.dahdichannel );
      //creates DIV Title Element, tehn assins class and text
      var title = document.createElement("DIV")
      title.setAttribute("class", "contact-title" );
      title.innerText= "DAHDI/"+line.dahdichannel;
      //creates DIV alarm Element, then assigns id and text
      var alarm = document.createElement("TEXT")
      alarm.setAttribute("id", line.dahdichannel+"Status" );
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
      div.appendChild(title);
      div.appendChild(alarm);
      document.getElementById("dahdi").appendChild(div);
  }

  function PJSipContact(id) {
      //create DIV element, then asigns text, id and class
      var btn = document.createElement("DIV");
      btn.setAttribute("id", id );
      btn.setAttribute("class", "btn btn-default" );
      var title = document.createElement("DIV")
      title.setAttribute("class", "contact-title" );
      title.innerText= id;
      //creates DIV alarm Element, then assigns id and text
      var alarm = document.createElement("TEXT")
      alarm.setAttribute("id", id+"Status" );
      alarm.innerText= "No Registered";
      btn.appendChild(title);
      btn.appendChild(alarm);

      document.getElementById("pjsip").appendChild(btn);
  }

  function Newchannel(chan) {
      //active caller contact
      ContactUp(chan.calleridnum);
      //create row link
      var link = document.getElementById(chan.linkedid);
      var call = document.getElementById("call"+chan.linkedid);
      if (link == null){
        var  link = document.createElement("DIV");
        link.setAttribute("id", chan.linkedid );
        link.setAttribute("class", "row" );
        var  title = document.createElement("DIV");
        title.setAttribute("class", "row" );
        var src = document.createElement("DIV");
        src.setAttribute("class", "col-md-5 link-title " );
        src.innerText = "SRC channel";
        var dst = document.createElement("DIV");
        dst.setAttribute("class", "col-md-5 link-title " );
        dst.innerText = "DST channel";
        var call = document.createElement("DIV");
        call.setAttribute("class", "row" );
        call.setAttribute("id", "call"+chan.linkedid );

        title.appendChild(src);
        title.appendChild(dst);
        link.appendChild(title);
        link.appendChild(call);
      }
      //create channel button
      var btn = document.createElement("DIV");
      btn.innerText = chan.channel+" "+chan.channelstatedesc;
      btn.setAttribute("id",chan.channel)

      //set class by status
      switch (chan.channelstatedesc) {
      case "Ringing":
         btn.setAttribute("class", "col-md-offset-2 col-md-5 alert alert-danger blink" );
         break;
      case  "Up":
         //update destination contact status
         btn.setAttribute("class", "col-md-5 alert alert-info" );
         ch = chan.channel.substring(0,5);
         //check if destination contact is DAHDI
         if (ch == "DAHDI") {
           ContactUp(chan.channel.substring(6,7));
          }
          else {
           ContactUp(chan.channel.substring(6,9));
          }
         break;
      default:
         btn.setAttribute("class", "col-md-5 alert alert-warning" );
         break;
      }

      //append button to call row
      call.appendChild(btn);
      document.getElementById("channels").appendChild(link);
  }

  function Updatechannel(chan) {
      //get chan from likedid and change status
      var btn= document.getElementById(chan.channel);
      btn.innerText = chan.channel+ " "+chan.channelstatedesc;
      // change class by status
      switch (chan.channelstatedesc) {
        case "Ringing":
          btn.setAttribute("class", "col-md-5 alert alert-danger blink" );
          break;
        case  "Up":
          //update contact status
          btn.setAttribute("class", "col-md-5 alert alert-info" );
          ch = chan.channel.substring(0,5);
         //check if destination contact is DAHDI
          if (ch == "DAHDI") {
            ContactUp(chan.channel.substring(6,7)); //gets character[7] from string
          }
          else {
            ContactUp(chan.channel.substring(6,9)); //gets character[7:9] from string
          }
         break;
      }
  }

  function Destroychannel(chan) {
     //get chan from likedid and change status
     var link = document.getElementById(chan.linkedid);
    //update contact status
     ContactActive(chan.calleridnum);
     ch = chan.channel.substring(0,5);
     //check if destination contact is DAHDI
     if (ch == "DAHDI") {
         ContactActive(chan.channel.substring(6,7));
     }
     else {
         ContactActive(chan.channel.substring(6,9));
     }
     //remove link div
     if(!!link){
       link.remove();
     }
  }

function ContactActive(id) {
    //get contact by id
    var btn=document.getElementById(id);
    //get alarm div by id
    var alarm = document.getElementById(id+'Status');
    //set classes to contact button and alarm div
    if (!!btn) {
        btn.setAttribute("class", "btn btn-success" );
    }
    if (!!alarm){
      //check if contact is dahdi
       if (id.length <=2 ){
        alarm.innerText="No Alarm";
       }
       else {
        alarm.innerText="Registered";
       }
    }
}

function ContactUp(id) {
    //get contact by id
    var btn = document.getElementById(id);
    //get alarm div by id
    var alarm = document.getElementById(id+'Status');
    //set classes to contact button and alarm div
    if(!!btn){
        btn.setAttribute("class", "btn btn-info" );
    }
    if (!!alarm){
        alarm.innerText="Up";
    }

}

function log(m) {
ellog.innerHTML += m + '\n';
ellog.scrollTop = ellog.scrollHeight;
}
