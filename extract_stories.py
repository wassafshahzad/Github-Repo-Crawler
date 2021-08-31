import os
from github import Github
import re
from dotenv import load_dotenv
from threading import Thread
import pandas as pd

load_dotenv()

g= Github(os.getenv("ACCESS_TOKEN"))
repo = g.get_repo(os.getenv("GITHUB_REPO_NAME"))


class Extarctor:
    def __init__(self,filters):
        self.filters = filters
        self.data = [[], [], [], []]

    def issues_by_filter(self):
        return self._save_to_dict(repo.get_issues(**self.filters))

    def _save_to_dict(self,issues):
        for issue in issues:
            self.data[
                pd.Timestamp(issue.closed_at).quarter % 4].append(
                    {"Assignee": issue.assignee.login if issue.assignee else "", 
                        "URL": issue.html_url if issue.html_url else "",
                        "Title": issue.title if issue.title else "",
                        "Created At":issue.created_at.strftime("%d-%m-%Y"),
                        "Closed At":issue.closed_at.strftime("%d-%m-%Y"),
                        })
        
        return self.data

class ThreadMerger:
    
    @staticmethod
    def start_worker(name,data):
        try:
            result = Extarctor({"state":"closed", "assignee": name}).issues_by_filter()
            for i in range(len(result)):
                data[i].extend(result[i])
        except Exception as e:
            print(e)

    @staticmethod
    def save_to_excel(data):
        with pd.ExcelWriter(f"{os.getenv('FILE_NAME')}.xlsx") as writer:
            for i,quarter in enumerate(data):
                if data:
                    df = pd.DataFrame.from_dict(quarter)
                    df.to_excel(writer,sheet_name=f"Quarter {i+1}")
        
    @staticmethod
    def start():
        threads= []
        result= [[],[],[],[]]
        for i in os.getenv("USERS").split(","):
            process= Thread(target= ThreadMerger.start_worker,
                args= [i,result],
                daemon= True)
            process.start()
            threads.append(process)
        
        for process in threads:
            process.join()
        ThreadMerger.save_to_excel(result)


ThreadMerger.start()
