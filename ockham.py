import os
import time
import re
import json
import requests
from slackclient import SlackClient
from _thread import start_new_thread

class Bot:
    MENTION_REGEX = "^<@(|[WU].+?)>(.*)"
    RTM_READ_DELAY = 1
    OUT_CHANNEL = "bot"
    mp_base_url = "http://localhost:8001/"
    def __init__(self):
        super().__init__()
        channel_list = None
        self.info_channel_id = None
        self.slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
        if self.slack_client.rtm_connect(with_team_state=False, auto_reconnect=True):
            ockham_id = self.slack_client.api_call("auth.test")["user_id"]
            channel_list = self.slack_client.api_call("channels.list")
        if  channel_list and 'channels' in channel_list:
            for channel in channel_list.get('channels'):
                if channel.get('name') == 'bot':
                    self.info_channel_id = channel.get('id')
                    break

    def parse_bot_commands(self, slack_events):
        for event in slack_events:
            if event["type"] == "message" and not "subtype" in event:
                user_id, message = self.parse_direct_mention(event["text"])
                if user_id == self.ockham_id:
                    return message, event["channel"]
        return None, None

    def parse_direct_mention(self, message_text):
        matches = re.search(self.MENTION_REGEX, message_text)
        return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

    def build_url(self, path):
        return "{base}/{path}".format(base=self.mp_base_url, path=path)

    def make_json_msg(self, jsn):
        return  """```{jsn}```""".format(jsn=json.dumps(jsn, indent=4, sort_keys=True))
        
    def handle_command(self, command, channel):
        ok = False
        if command.startswith('info'):
            ok = True
            url = self.build_url('info')
            resp = requests.get(url)
            self.post(channel, self.make_json_msg(resp.json()))

        if command.startswith('path'):
            ok = True
            path = command.replace("path", "").replace(" ", "")
            url = self.build_url(path)
            resp = requests.get(url)
            self.post(channel, self.make_json_msg(resp.json()))


        if command.startswith('he'):
            ok = True
            self.post(channel, "Beside *he[lp]* further available commands are:")
            self.post(channel, "*path ssmp/path* returns the messages behind the given path,  *info* about measurement programm")
        if not ok:
            self.post(channel, "Not sure what you mean. Try *help* command.")

    def post(self, channel, msg, mrkdwn=True):
        self.slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            text=msg,
            mrkdwn=mrkdwn
            )

    def msg_in(self):
        self.ockham_id = self.slack_client.api_call("auth.test")["user_id"]
        while True:
            command, channel = self.parse_bot_commands(self.slack_client.rtm_read())
            if command:
                self.handle_command(command, channel)
            time.sleep(self.RTM_READ_DELAY)

if __name__ == "__main__":
    bot = Bot()
    bot.msg_in()