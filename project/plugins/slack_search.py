import json
import requests
import re

from taskweaver.plugin import Plugin, register_plugin

@register_plugin
class SlackSearcher(Plugin):
    def __call__(self, query: str):
        api_token = self.config.get("api_token")
        if not api_token:
            raise ValueError("API token not found in config file")
        base_url = "https://slack.com/api"
        headers = {"Authorization": f"Bearer {api_token}"}
        channel_names = self.config.get("channel_names", ["general", "random"])

        query_with_channels = self.build_query_with_channels(query, channel_names)
        search_url = f"{base_url}/search.messages"
        params = {"query": query_with_channels}
        response = requests.get(search_url, headers=headers, params=params)

        if response.status_code != 200:
            return f"Error: Received status code {response.status_code}\n{response.text}"

        try:
            data = response.json()
            if not data['ok']:
                return f"Error: {data['error']}"

            simplified_output = []
            for message in data['messages']['matches']:
                simplified_message = {
                    "user": message['user'],
                    "text": message['text'],
                    "permalink": message['permalink']
                }
                thread_ts = self.extract_thread_ts(message['permalink'])
                if thread_ts:
                    thread_messages = self.get_thread_messages(message['channel']['id'], thread_ts, base_url, headers)
                    simplified_message['thread'] = thread_messages
                simplified_output.append(simplified_message)
            return json.dumps(simplified_output, indent=4)  # Pretty-printing
        except ValueError as e:
            return f"Error parsing JSON: {e}\nResponse text: {response.text}"

    def build_query_with_channels(self, query, channel_names):
        channel_queries = [f"in:{channel}" for channel in channel_names]
        return f"{query} {' '.join(channel_queries)}"

    def extract_thread_ts(self, permalink):
        match = re.search(r"thread_ts=([0-9.]+)", permalink)
        return match.group(1) if match else None

    def get_thread_messages(self, channel_id, thread_ts, base_url, headers):
        thread_url = f"{base_url}/conversations.replies"
        params = {"channel": channel_id, "ts": thread_ts}
        response = requests.get(thread_url, headers=headers, params=params)

        if response.status_code != 200 or not response.json()['ok']:
            return f"Error fetching thread messages: {response.text}"

        thread_messages = []
        for message in response.json()['messages']:
            if message['ts'] != thread_ts:  # Exclude the parent message
                thread_messages.append({
                    "user": message['user'],
                    "text": message['text']
                })
        return thread_messages
