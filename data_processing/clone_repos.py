"""
This script clones repositories listed in a jsonl file.
"""

import glob
import json
import logging
import os
import sys
import shutil
import threading
from typing import TypedDict
from typing_extensions import Required
import subprocess


class Repository(TypedDict):
    """
    A repository
    """
    owner: Required[str]
    name: Required[str]
    url: str
    version: str
    stars: int


class RepoCloner:
    """
    A class implementing cloning multiple repositories in a multi-thread way.
    """

    def __init__(self,
                 output_root_dir: str,
                 n_worker: int = 4,
                 delete_history: bool = True,
                 delete_hidden_files: bool = True,
                 keep_files_pattern: str = "*"):
        if not os.path.isdir(output_root_dir):
            os.mkdir(output_root_dir)
        self._root_dir = output_root_dir
        self._delete_history = delete_history
        self._delete_hidden_files = delete_hidden_files
        self._n_worker = n_worker
        self._keep_files_pattern = keep_files_pattern

    def clone_repos(self, repos: list[Repository]) -> None:
        threads = [threading.Thread(target=self._clone_repos_thread, args=(repos, worker_id))
                   for worker_id in range(self._n_worker)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

    def _clone_repos_thread(self, repos: list[Repository], worker_id: int) -> None:
        logging.info(f"[{worker_id}] started thread {worker_id}")
        while True:
            lock = threading.Lock()
            with lock:
                if len(repos) == 0:
                    return
                repo = repos.pop()
                try:
                    self.clone_repo(repo, worker_id)
                except Exception as ex:
                    owner, name = repo["owner"], repo["name"]
                    logging.error(f"[{worker_id}] {owner}/{name}: clone failed. {str(ex)}")
                    target_dir = os.path.join(self._root_dir, owner, name)
                    shutil.rmtree(target_dir)

    def clone_repo(self, repo: Repository, worker_id: int) -> None:
        owner, name = repo["owner"], repo["name"]
        if "url" in repo.keys():
            url = repo["url"]
        else:
            url = f"https://github.com/{owner}/{name}.git"
        target_dir = os.path.join(self._root_dir, owner, name)
        logging.info(f"[{worker_id}] {owner}/{name}: start cloning.")
        # if target dir to write repo exists, skip
        if os.path.isdir(target_dir):
            logging.info(f"[{worker_id}] {owner}/{name}: dir already exist, skip.")
            return

        # clone repo
        command = ["git", "clone", url, target_dir]
        process = subprocess.run(command, capture_output=True)
        return_code = process.returncode
        if return_code != 0:
            err_msg = process.stderr.decode("utf-8")
            logging.error(f"[{worker_id}] {owner}/{name}: clone failed with code {return_code}. {err_msg}")
            shutil.rmtree(target_dir)
            return

        # check out version if requested
        if "version" in repo.keys():
            version = repo["version"]
            process = subprocess.run(f"cd {target_dir} && git checkout {version}", capture_output=True, shell=True)
            return_code = process.returncode
            if return_code != 0:
                err_msg = process.stderr.decode("utf-8")
                logging.error(f"[{worker_id}] {owner}/{name}: failed to checkout version {version[:5]}. "
                              f"Repo ignored. {err_msg}")
                shutil.rmtree(target_dir)
                return

        # delete history if requested
        if self._delete_history:
            shutil.rmtree(os.path.join(target_dir, ".git"))

        # remove hidden files and dirs if requested
        hidden_files: list[str] = glob.glob(f"{target_dir}/**/.*", recursive=True)
        for file in hidden_files:
            if os.path.isfile(file):
                os.remove(file)

        # only keep relevant files
        keep_files: list[str] = glob.glob(f"{target_dir}/**/{self._keep_files_pattern}", recursive=True)
        keep_files = [file for file in keep_files if os.path.isfile(file)]
        all_files: list[str] = glob.glob(f"{target_dir}/**", recursive=True)
        all_files = [file for file in all_files if os.path.isfile(file)]
        delete_files: set[str] = set(all_files) - set(keep_files)
        for file in delete_files:
            if os.path.isfile(file):
                os.remove(file)

        logging.info(f"[{worker_id}] {owner}/{name}: finished cloning. {len(keep_files)} files.")


# main entry
if __name__ == "__main__":

    n = len(sys.argv)
    if n <= 2:
        print("Usage: clone_repo <repo_list_file> <clone_root_dir>")
        sys.exit(1)

    repo_list_file, target_root_dir = sys.argv[1], sys.argv[2]
    logging_file = os.path.join(target_root_dir, "clone-repo.log")
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s : %(message)s',  # noqa
                        datefmt='%Y/%m/%d %H:%M:%S',
                        handlers=[
                            logging.FileHandler(logging_file),
                            logging.StreamHandler(sys.stdout)
                        ])
    logging.info(f"Logging started. Cloning repos listed in {repo_list_file} to folder {target_root_dir}")

    cloner = RepoCloner(target_root_dir, n_worker=8, keep_files_pattern="*.java",
                        delete_history=True, delete_hidden_files=True)

    list_repos: list[Repository] = []
    with open(repo_list_file, "r") as fid:
        for line in fid:
            js: Repository = json.loads(line)
            list_repos.append(js)

    cloner.clone_repos(list_repos)