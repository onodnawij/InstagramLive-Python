from http.server import BaseHTTPRequestHandler
import json

hostName = ""
hostPort = 80

PAGE = """<html>
<head>
    <meta content="text/html;charset=utf-8" http-equiv="Content-Type">
    <meta content="utf-8" http-equiv="encoding">
    <script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jquery/1.6.2/jquery.min.js"></script>
    <style type="text/css">

    @font-face {
        font-family: Andro;
        src: url(http://www.font-face.com/fonts/delicious/Delicious-Roman.otf);
        font-weight:400;
    }

    #thisDiv {
      border: 1px solid gray;
      width: 480px;
      height: 200px;
      overflow: scroll;
    }
    .chat-title {
    margin: 0;
    padding: .3rem;
    background-color: #eee;
    font: 1rem 'Andro', sans-serif;
    }

    .chat-title > h1,
    .chats {
        margin: .5rem;
        padding: .3rem;
        font-size: 1.2rem;
    }

    .chats {
        background: right/contain content-box border-box no-repeat white;
    }

    .chats > h2,
    .chats > p {
        margin: .2rem;
        font-size: 1rem;
    }

  </style>
</head>

<body>
    <script>
        var chats = [];
        function delok() {
            $.getJSON('http://localhost:4132/chat', function(data) {
                if (data.hasOwnProperty('id')){
                    var n = chats.includes(data.id);
                    if (n){
                    }else{
                        chats.push(data.id);
                        var tix = `<article class="chats">
                                       <h2>@${data.user.username}</h2>
                                       <p><font size=1> ${data.time}</font></p>
                                       <p>${data.text}</p>
                                   </article>`
                                $(".container").prepend(tix);
                    };
                }else{
                };
            });
        };
    setInterval(delok, 1500)
    delok();
</script>
    <div id="thisDiv">
    <article class="chat-title">
        <h1>Live Chat</h1>
        <div class="container">
        </div>
    </article>
  </div>
</body>
</html>
"""

GARBAGE = []
BIASA = bool
response = None

class ChatServer(BaseHTTPRequestHandler):

    def do_GET(self):
        global BIASA
        global GARBAGE
        global response

        if self.path == '/':
            response = bytes(PAGE, "utf-8")
            types = 'text/html'
            BIASA = True

        elif self.path == '/chat':
            garbage = GARBAGE
            if len(garbage):
                this = garbage[len(garbage) - 1]
            else:
                this = GARBAGE
            response = bytes(json.dumps(this), "utf-8")
            types = 'application/json'
            BIASA = True
        elif self.path == '/Fonts/OpenSans-Regular.ttf':
            types = 'application/octet-stream'
        else:
            BIASA = False

        self.send_response(200)
        if BIASA:
            self.send_header('Content-Type', types)
            if types == 'application/json':
                self.send_header('Content-Length', str(len(response)))
            self.end_headers()
            self.wfile.write(response)
        else:
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'no')

    def do_POST(self):
        self.send_response(200)
    
    def log_message(self, format, *args):
        return
