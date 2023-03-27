# -*- coding: utf-8 -*-
import argparse
from github import Github
import os
from glob import glob
import json
import codecs
from tqdm import tqdm
import dataclasses


@dataclasses.dataclass
class Report:
    link: str = ""
    created_at: str = ""
    labels: str = ""
    body: str = ""
    title: str = ""


class Parser:
    parse = True

    def __init__(self):
        self._parser = argparse.ArgumentParser(
            description="Скрипт по поиску прецедентов бага", add_help=False)
        self._parser.add_argument("--parse",
                                  action="store_const",
                                  default=not self.parse,
                                  const=self.parse,
                                  help="Флаг для парсинга аргументов")
        self._parser.add_argument("--search", type=str, default=None, metavar="", help='Что ищем')
        self._parser.add_argument("--token", type=str, default=None, metavar="", help='Токен гита')

    def get_arguments(self):
        my_namespace = self._parser.parse_args()
        _args = {"parse": my_namespace.parse, "search": my_namespace.search, "token": my_namespace.token}
        return _args


def pull_issues_from_github(name, token):
    if token:
        github = Github(token)
    else:
        github = Github()
    base_url = "https://github.com"
    user = github.get_user(name)
    reports = []
    for repo in tqdm(user.get_repos(), f"Ищем репозитории на {name}"):
        if "findings" in str(repo):
            for issue in repo.get_issues(state="all"):
                report = Report()
                report.labels = str(issue.labels)
                report.created_at = issue.created_at.strftime("%d/%m/%Y, %H:%M:%S")
                report.body = issue.body
                report.title = issue.title
                report.link = base_url + f"/{repo.full_name}" + "/issues" + f"/{issue.number}"
                reports.append(report)
    return reports


def create_reports_dir(start_dir):
    reports_dir = os.path.join(start_dir, "reports")
    if not os.path.exists(reports_dir):
        os.mkdir(reports_dir)
    return reports_dir


def get_reports(token):
    code4arena_reports = pull_issues_from_github("code-423n4", token)
    sherlock_reports = pull_issues_from_github("sherlock-audit", token)
    full_reports = code4arena_reports + sherlock_reports
    start_dir = os.getcwd()
    reports_dir = create_reports_dir(start_dir)
    for report in full_reports:
        json_issue = json.dumps(dataclasses.asdict(report))
        filename = os.path.join(reports_dir, f"{report.title.replace(' ', '_').replace('/', '_')[0:100]}.json")
        with open(filename, "wb") as outfile:
            json.dump(json_issue, codecs.getwriter("utf-8")(outfile), ensure_ascii=False)


def get_downloaded_reports():
    files = []
    start_dir = os.getcwd()
    reports_dir = os.path.join(start_dir, "reports")
    pattern = "*.json"
    for directory, _, _ in os.walk(reports_dir):
        files.extend(glob(os.path.join(directory, pattern)))
    return files


def search_in_file(search, file):
    with open(file) as json_file:
        data = json.load(json_file)
        data = json.loads(data)
        if search.lower() in data["body"].lower():
            print_log(data, search)


def search_in_reports(search):
    files = get_downloaded_reports()
    for file in files:
        search_in_file(search, file)


def print_log(data, search):
    log = f"""
        ==============================
        Report URL: {data['link']}
        Report Title: {data['title']}
        Report labels: {data['labels']}
        Report created: {data['created_at']}
        SEARCH: {search}
        ==============================
          """
    print(log)


def main():
    parser = Parser()
    _args = parser.get_arguments()
    if _args["parse"]:
        get_reports(_args["token"])
    if _args["search"]:
        search_in_reports(_args["search"])


if __name__ == "__main__":
    main()
