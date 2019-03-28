from getpass import getpass
from InstagramAPI import InstagramAPI
import json
import threading
import time
from InstagramAPI.exceptions import SentryBlockException
import subprocess

class Main:
    
    def __init__(self):
        IG_NAME = input('Username: ')
        IG_PASS = getpass('Password: ')
        self.api = InstagramAPI(IG_NAME, IG_PASS)
        self.api.USER_AGENT = self.api.USER_AGENT.replace('10.26.0', '10.34.0')
        self.broadcast_id = 0
        self.chat_thread = threading.Thread(target=self.chat_job, daemon=True)
        self.isRunning = True
    
    def chat_job(self):
        with open('output', 'w') as fd:
            garbage = []
            p = subprocess.Popen(["gnome-terminal", "--hide-menubar", "--title='Live Chat'", "--","tail", "-f", "output"])
            while self.isRunning:
                time.sleep(2)
                a = self.SendRequest(f'live/{self.broadcast_id}/get_comment/', last=False)
                try:
                    if a['comments']:
                        for comment in a['comments']:
                            comment_user = (comment['user']['username'], comment['user_id'])
                            timestamp = time.gmtime(comment['created_at_utc'])
                            comment_time = time.strftime('%H:%M:%S %d/%m/%Y', timestamp)
                            comment_text = comment['text']
                            comment_id = comment['pk']
                            chat = {
                                'id': comment_id,
                                'user': comment_user,
                                'text': comment_text,
                                'time': comment_time
                                }
                            if chat not in garbage:
                                chatter = chat['user'][0]
                                chatter = 'Me' if chatter == self.api.username else chatter
                                fd.write(f"[{chat['id']}]{chat['time']} {chatter}: {chat['text']}\n")
                                fd.flush()
                                garbage.append(chat)
                except:
                    pass
            p.kill()
            print('Comment Thread Stopped')

    def create_live(self, msg=''):
        data = json.dumps({
            '_uuid': self.api.uuid,
            '_csrftoken': self.api.token,
            'preview_height': 1280,
            'preview_width': 720,
            'broadcast_message': msg
            })
        self.api.SendRequest('live/create/', self.api.generateSignature(data))
        broadcast_id, live_url, stream_key = (self.api.LastJson['broadcast_id'], self.api.LastJson['upload_url'][:43], self.api.LastJson['upload_url'][43:])

        print(f'[*]Broadcast ID: {broadcast_id}\n')
        print(f'[*]Live Upload URL: {live_url}\n')
        print(f'[*]Stream Key:\n{stream_key}\n\n')

        self.broadcast_id = broadcast_id

        return True

    def start_live(self):
        notify = True

        data = json.dumps({
            '_uuid': self.api.uuid,
            '_csrftoken': self.api.token,
            'should_send_notifications': notify
            })
        self.api.SendRequest(f'live/{self.broadcast_id}/start/', self.api.generateSignature(data))
        return True

    def end_live(self):
        data = json.dumps({
            '_uid': self.api.username_id,
            '_uuid': self.api.uuid,
            '_csrftoken': self.api.token,
            'end_after_copyright_warning': False
            })

        return self.api.SendRequest(f'live/{self.broadcast_id}/end_broadcast/', self.api.generateSignature(data))

    def save_post_live(self):
        trial = 3
        posted = bool
        while trial:
            trial -= 1
            data = json.dumps({
                '_uid': self.api.username_id,
                '_uuid': self.api.uuid,
                '_csrftoken': self.api.token
                })
            self.api.SendRequest(f'live/{self.broadcast_id}/add_to_post_live', self.api.generateSignature(data))

            if self.api.LastResponse.status_code == 200:
                print('Live Posted to Story!')
                posted = True
                break
        if not posted:
            print('Vailed to post live to story!')

    def delete_post_live(self):
        data = json.dumps({
            '_uid': self.api.username_id,
            '_uuid': self.api.uuid,
            '_csrftoken': self.api.token
            })
        return self.api.SendRequest(f'live/{self.broadcast_id}/delete_post_live', self.api.generateSignature(data))

    def pin_comment(self, comment_id):
        data = json.dumps({
            'offset_to_video_start': 0,
            'comment_id': comment_id,
            '_uid': self.api.username_id,
            '_uuid': self.api.uuid,
            '_csrftoken': self.api.token
            })
        return self.api.SendRequest(f'live/{self.broadcast_id}/pin_comment', self.api.generateSignature(data))

    def unpin_comment(self, comment_id):
        data = json.dumps({
            'offset_to_video_start': 0,
            'comment_id': comment_id,
            '_uid': self.api.username_id,
            '_uuid': self.api.uuid,
            '_csrftoken': self.api.token
            })
        return self.api.SendRequest(f'live/{self.broadcast_id}/unpin_comment', self.api.generateSignature(data))

    def SendRequest(self, endpoint, post=None, login=False, last=True):
        verify = False  # don't show request warning
        if not last:
            if (not self.api.isLoggedIn and not login):
                raise Exception("Not logged in!\n")

            self.api.s.headers.update({'Connection': 'close',
                                'Accept': '*/*',
                                'Content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                                'Cookie2': '$Version=1',
                                'Accept-Language': 'en-US',
                                'User-Agent': self.api.USER_AGENT})

            while True:
                try:
                    if (post is not None):
                        response = self.api.s.post(self.api.API_URL + endpoint, data=post, verify=verify)
                    else:
                        response = self.api.s.get(self.api.API_URL + endpoint, verify=verify)
                    break
                except Exception as e:
                    print('Except on SendRequest (wait 60 sec and resend): ' + str(e))
                    time.sleep(60)

            if response.status_code == 200:
                self.api.LastResponse = response
                self.api.LastJson = json.loads(response.text)
            else:
                print("Request return " + str(response.status_code) + " error!")
                # for debugging
                try:
                    self.api.LastResponse = response
                    self.api.LastJson = json.loads(response.text)
                    print(self.api.LastJson)
                    if 'error_type' in self.api.LastJson and self.api.LastJson['error_type'] == 'sentry_block':
                        raise SentryBlockException(self.api.LastJson['message'])
                except SentryBlockException:
                    raise
                except:
                    pass
            return self.api.LastJson
        else:
            return self.api.SendRequest(endpoint, post=None, login=False)
    
    def live_info(self):
        _json = self.SendRequest(f'live/{self.broadcast_id}/info/', last=False)
        dash_url = _json['dash_playback_url']
        viewer_count = _json['viewer_count']
        _id = _json['id']
        owner = _json['broadcast_owner']['username']
        status = _json['broadcast_status']

        print(f'[*]ID: {_id}')
        print(f'[*]Broadcast Owner: {owner}')
        print(f'[*]Dash URL: {dash_url}')
        print(f'[*]Viewer Count: {viewer_count}')
        print(f'[*]Status: {status}')
    
    def send_comment(self, msg):
        data = json.dumps({
            'idempotence_token': self.api.generateUUID(True),
            'comment_text': msg,
            'live_or_vod': 1,
            'offset_to_video_start': 0
        })

        _json = self.SendRequest(f'live/{self.broadcast_id}/comment/', self.api.generateSignature(data), last=False)
        if _json['status'] == 'ok':
            return True
    
    def exit(self):
        self.end_live()
        print('Save Live replay to story ? <y/n>')
        save = input('command> ')
        if save == 'y':
            self.save_post_live()
        else:
            self.delete_post_live()
        print('Exiting...')
        self.isRunning = False
        self.chat_thread.join()
        print('All process Stopped')

    def wave(self, userid):

        data = json.dumps({
            '_uid': self.api.username_id,
            '_uuid': self.api.uuid,
            '_csrftoken': self.api.token,
            'viewer_id': userid
        })

        _json = self.SendRequest(f'live/{self.broadcast_id}/wave/', self.api.generateSignature(data), last=False)
        if _json:
            return True

    def get_viewer_list(self):
        _json = self.SendRequest(f'live/{self.broadcast_id}/get_viewer_list/', last=False)
        users = []
        ids = []
        for user in _json['users']:
            users.append(f"{user['username']}")
            ids.append(f"{user['pk']}")
        
        return users, ids

    def run(self):
        print('[!]logging in...')
        if self.api.login():
            print('[*]logged in!!')
            print('[!]Generating stream upload_url and keys...\n')
            self.create_live()
            print('Now Open Broadcast Software and start streaming on given url and key')
            input('Press Enter after your Broadcast Software started streaming\n')
            self.start_live()
            self.chat_thread.start()
            
            while self.isRunning:                
                cmd = input('command> ')

                if cmd == 'stop':
                    self.exit()
                
                elif cmd == 'wave':
                    users, ids = self.get_viewer_list()
                    for i in range(len(users)):
                        print(f'{i+1}. {users[i]}')
                    print('Type number according to user e.g 1.')
                    while True:
                        cmd = input('number> ')

                        if cmd == 'back':
                            break
                        try:
                            userid = int(cmd) - 1
                            self.wave(ids[userid])
                            break
                        except:
                            print('Please type number e.g 1')

                elif cmd == 'info':
                    self.live_info()
                
                elif cmd == 'viewers':
                    users, ids = self.get_viewer_list()
                    print(users)

                elif cmd[:4] == 'chat':
                    to_send = cmd[5:]
                    if to_send:
                        self.send_comment(to_send)
                    else:
                        print('usage: chat <text to chat>')
                
                else:
                    print('Available commands:\n\t"stop"\n\t"info"\n\t"viewers"\n\t"chat"\n\t"wave"')


if __name__ == '__main__':
    main = Main()
    main.run()