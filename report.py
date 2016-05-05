#!/usr/bin/env python

import re
from pprint import pprint

import requests
from getpass import getpass

AUTHOR='ricardo_gemignani'

BASE_URL = "https://gruporbs.atlassian.net"

jira_username = input("Jira Username: ")
jira_password = getpass("Jira Password: ")

auth = requests.auth.HTTPBasicAuth(jira_username, jira_password)

headers = {
    "Content-Type": "application/json"
}

boards = requests.get(BASE_URL +"/rest/agile/1.0/board", auth=auth, headers=headers).json()['values']
board_names = [b['name'] for b in boards]
board_names.sort()

board_name = None
while not board_name:
    print('BOARDS:')
    print(' . '+'\n . '.join(board_names))
    board_name = input("Jira Board Name: ")

board = list(filter(lambda x: x['name'] == board_name, boards))[0]

board_sprints = requests.get(board['self']+"/sprint", auth=auth, headers=headers).json()['values']

sprint = list(filter(lambda x: x['state'] == 'active', board_sprints))[0]

sprint_issues = requests.get(sprint['self']+"/issue?maxResults=1000", auth=auth, headers=headers).json()['issues']

remaining_hours = {}

print('\n')

for issue in sprint_issues:
    _type = re.match('\[([^\]]*)\].*', issue.get('fields', {}).get('summary'))
    remaining_seconds = issue.get('fields', {}).get('timetracking', {}).get('remainingEstimateSeconds', 0)
    _remaining_hours = remaining_seconds/60/60
    if not _type and remaining_seconds:
        print("\nWARNING: Issue '{} {}' has no type.".format(issue['key'], issue.get('fields', {}).get('summary')))
        _type = 'NO TYPE'
        hours = remaining_hours.get(_type, 0)
        hours += _remaining_hours
        remaining_hours[_type] = hours
    elif _type and remaining_seconds:
        _type = _type.groups()[0]
        _type = _type.upper()
        hours = remaining_hours.get(_type, 0)
        hours += _remaining_hours
        remaining_hours[_type] = hours
        print("{:4.1f} - {}".format(_remaining_hours, issue.get('fields', {}).get('summary')))

print('\nTypes:')

for key, value in remaining_hours.items():
    print('. {} - {} hours'.format(key, value))

print('Total: {}'.format(sum(remaining_hours.values())))
