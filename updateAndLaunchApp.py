import os
import requests
import logging
from diff_parser import Diff
from os import environ as env
from dotenv import load_dotenv


#logging.basicConfig(filename="./updater.log", level=logging.INFO)


class Updater:
    def __init__(self) -> None:
        print(__file__)
        load_dotenv()


        #logging.info("Checking for Updates.")
        repo = env['SERVER_REPO']
        version = env['APP_VERSION']

        GITHUB_REPO_URL=f"https://github.com/{repo.strip()}" 
        VERSION=version.strip()

        print(f"Checking for updates in {repo}, Current version {VERSION}")

        LATEST_RELEASES_URL=f"{GITHUB_REPO_URL}/releases/latest"


        LATEST_VERSION = None

        try:
            LATEST_VERSION = requests.head(LATEST_RELEASES_URL).headers['location'].split("/")[-1]
            print(f"Latest version: {LATEST_VERSION}")

            DIFF_URL=f"{GITHUB_REPO_URL}/compare/{VERSION}...{LATEST_VERSION}.diff"
            #print(f"DIFF URL: {DIFF_URL}")

            RAW_GITHUB_URL=f"https://raw.githubusercontent.com/{repo.strip()}"
            #print(f"RAW GITHUB URL: {RAW_GITHUB_URL}")
            
            UPTODATE = VERSION == LATEST_VERSION

            if UPTODATE:
                print("No updates found.")
                return
            else:
                print(f"Updating from {VERSION} to {LATEST_VERSION}")
                

            
            # comapring diffs
            resp = requests.get(DIFF_URL)
            #print(f"DIFF STATUS: {resp.status_code} - {resp.content}")

            if(resp.content == b''):
                print("No differences found.")
                return
            else:

                diff = Diff(resp.content.decode())
                print(f"DIFF: {diff}")

                


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


        except requests.exceptions.ConnectionError:
            print("Not able to Reach Server, Skipping Update")
            pass
            
        # except Exception as e:
        #     if hasattr(e, 'message'):
        #         print(e.message)
        #     else:
        #         print(e)

        
        print("START APP")
        #os.system('python app.py')



       

        
    def setup_auto_run():
        # to be implemented
        pass



if __name__ == "__main__":
    updater = Updater()