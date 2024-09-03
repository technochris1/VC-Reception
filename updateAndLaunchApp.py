import os
import requests
import logging

from diff_parser import Diff

from os import environ as env

from dotenv import load_dotenv


logging.basicConfig(filename="./updater.log", level=logging.INFO)


class Updater:
    def __init__(self) -> None:
        print(__file__)
        load_dotenv()

        print('API_KEY:  {}'.format(env['API_KEY']))
        print('HOSTNAME: {}'.format(env['HOSTNAME']))
        print('PORT:     {}'.format(env['PORT']))


        logging.info("Checking for Updates.")
        repo, version = ""#data.splitlines()

        GITHUB_REPO_URL=f"https://github.com/{repo.strip()}" 
        VERSION=version.strip()

        print(f"Checking for updates in {repo} version {VERSION}")

        LATEST_RELEASES_URL=f"{GITHUB_REPO_URL}/releases/latest"

        

        LATEST_VERSION = requests.head(LATEST_RELEASES_URL).headers['location'].split("/")[-1]

        print(f"Latest version: {LATEST_VERSION}")

        DIFF_URL=f"{GITHUB_REPO_URL}/compare/{VERSION}...{LATEST_VERSION}.diff"
        RAW_GITHUB_URL=f"https://raw.githubusercontent.com/{repo.strip()}"
        
        UPTODATE = VERSION == LATEST_VERSION

        if UPTODATE:
            logging.info("No updates found.")
            return
        
        # comapring diffs
        resp = requests.get(DIFF_URL)
        diff = Diff(resp.content.decode())

        print(f"Updating from {VERSION} to {LATEST_VERSION}")


        # downloading and installing updates
        for d in diff:
            if d.type != 'deleted':
                print(f"WRITING: .{d.filepath}")
                with open(f'.{d.filepath}', 'wb') as file:
                    resp = requests.get(f"{RAW_GITHUB_URL}/{LATEST_VERSION}{d.filepath}")
                    file.write(resp.content)
            elif os.path.exists(f".{d.filepath}"):
                print(f"DELETING: .{d.filepath}")
                os.remove(f".{d.filepath}")

    def setup_auto_run():
        # to be implemented
        pass



if __name__ == "__main__":
    updater = Updater()