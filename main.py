import requests
import os
import openai
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

token = os.getenv("PR_REVIEW_BOT_TOKEN")
user = os.getenv("PR_REVIEW_BOT_OWNER")
repo = os.getenv("PR_REVIEW_BOT_REPO_NAME")
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_type = os.getenv("OPENAI_API_TYPE")
openai.api_version = os.getenv("OPENAI_API_VERSION")
openai.api_base = os.getenv("OPENAI_API_BASE")

headers = {
    'Authorization': f'token {token}',
    'Accept': 'application/vnd.github+json'
}

url = f'https://api.github.com/repos/{user}/{repo}/pulls'
response = requests.get(url, headers=headers)

if response.status_code == 200:
    data = response.json()
    if data:
        last_processed_pr = max(pull_request['number'] for pull_request in data)
        print(f"Last Processed Pull Request Number: {last_processed_pr}")
        
        # Fetching diff for the first pull request
        if 'diff_url' in data[0]:
            diff_url = data[0]['diff_url']
            diff_response = requests.get(diff_url, headers=headers)
            if diff_response.status_code == 200:
                diff = diff_response.text 

                messages = [
                        {"role": "system", "content": "You are github PR reviwer assistant. "},
                        {"role": "user", "content": f"Analyze this pull request text and provide a review and check if there is an error in the code:\n\n{diff}"}
                    ]

                response = openai.ChatCompletion.create(
                        engine="gpt-4",
                        messages=messages,
                    )

                review = response.choices[0].message['content'].strip()
                review = f"Review from GPT \n\n{review}"

                print(diff)

                comment_url = f'https://api.github.com/repos/{user}/{repo}/issues/{last_processed_pr}/comments'

                comment_data = {
                    'body': review,
                    'user': "PR-Reviewer-Bot"
                }

                comment_response = requests.post(comment_url, json=comment_data, headers=headers)

                if comment_response.status_code == 201:
                    print("Review successfully posted on GitHub.")
                else:
                    print(f"Failed to post review. Status code: {comment_response.status_code}")
                    print(f"Response: {comment_response.json()}")
            else:
                print(f"Failed to fetch diff for PR: {diff_response.status_code}")
        else:
            print("No diff_url found for the first pull request")
    else:
        print("No Pull Requests Found")
else:
    print("Failed to fetch pull requests")