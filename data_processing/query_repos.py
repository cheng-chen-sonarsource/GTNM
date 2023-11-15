"""
This script query the GitHub repos and export repos' attributes (e.g. stars, size, latest commit...)
and export the results to a jsonl file.
"""
import json
import requests
import pathlib
import os
from tqdm import tqdm


def get_repo_info(owner: str, repo: str) -> dict | None:
    """Get the repo info via GitHub API"""

    url = f"https://api.github.com/repos/{owner}/{repo}"

    # Use GitHub personal tokens to bypass the rate limit.
    token_file_path = os.path.join(pathlib.Path.home(), ".secrets/github_pat")
    with open(token_file_path, "r") as ftoken: # noqa
        token = ftoken.read().strip()
    headers = {
        'Authorization': f'Bearer {token}'
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        response = response.json()
        dict_repo = {
            "owner": owner,
            "name": repo,
            "url": response["clone_url"],
            "stars": response["stargazers_count"],
            "size": response["size"],
        }

        # Get the latest commit id on the default branch
        default_branch = response["default_branch"]
        url_commit = f'https://api.github.com/repos/{owner}/{repo}/commits/{default_branch}'
        response = requests.get(url_commit, headers=headers)
        if response.status_code == 200:
            response = response.json()
            dict_repo["version"] = response["sha"]
            dict_repo["time"] = response["commit"]["author"]["date"]
            return dict_repo
        else:
            print(f"{owner}/{repo}: {response.status_code}, {response.text}")
    else:
        print(f"{owner}/{repo}: {response.status_code}, {response.text}")

    return None


if __name__ == "__main__":
    input_file = "../data-small/repos.txt"
    output_file = "../data-small/repos.jsonl"

    with open(input_file, "r") as fid:
        lines = fid.readlines()

    with open(output_file, "w") as fid:
        for line in tqdm(lines):
            repo_owner, repo_name = line.strip().split("/")
            dict_repo = get_repo_info(repo_owner, repo_name)
            if dict_repo is not None:
                fid.write(json.dumps(dict_repo) + "\n")
