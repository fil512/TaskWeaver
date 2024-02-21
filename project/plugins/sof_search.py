import json
import requests

from taskweaver.plugin import Plugin, register_plugin, test_plugin

@register_plugin
class StackOverflowTeamsSearcher(Plugin):
    def __call__(self, query: str):
        api_key = self.config.get("api_key")
        if not api_key:
            raise ValueError("API key not found in config file")
        team_name = self.config.get("team_name")
        if not api_key:
            raise ValueError("team name not found in config file")
        base_url = "https://api.stackoverflowteams.com/2.3/search"
        headers = {"X-API-Access-Token": api_key}
        params = {"intitle": query, "team": team_name}
        response = requests.get(base_url, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            simplified_output = []
            for item in data['items']:
                question = {"question": item['title']}
                if 'accepted_answer_id' in item:
                    answer_id = item['accepted_answer_id']
                    answer_url = f"https://api.stackoverflowteams.com/2.3/answers/{answer_id}"
                    answer_params = {"team": team_name, "filter": "withbody"}
                    answer_response = requests.get(answer_url, headers=headers, params=answer_params)
                    if answer_response.status_code == 200:
                        answer_data = answer_response.json()
                        first_item = answer_data['items'][0]
                        if 'body' in first_item:
                            answer_text = first_item['body']
                            question['answer'] = answer_text
                simplified_output.append(question)
            return json.dumps(simplified_output, indent=4)
        else:
            return f"Request failed with status code {response.status_code}: {response.text}"
