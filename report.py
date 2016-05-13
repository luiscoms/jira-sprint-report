#!/usr/bin/env python

from pprint import pprint
import re
import yaml

import requests
from getpass import getpass

try:
    config = yaml.load(open('config.yml'))
except:
    config = {}

AUTHOR = 'ricardo_gemignani'

BASE_URL = config.get('jira_url')
if not BASE_URL:
    BASE_URL = input("Jira URL: ")

jira_username = config.get('jira_username')
if not jira_username:
    jira_username = input("Jira Username: ")
jira_password = config.get('jira_password')
if not jira_password:
    jira_password = getpass("Jira Password for {}: ".format(jira_username))

auth = requests.auth.HTTPBasicAuth(jira_username, jira_password)

headers = {
    "Content-Type": "application/json"
}

boards = requests.get(BASE_URL +"/rest/agile/1.0/board", auth=auth, headers=headers).json()['values']
board_names = [b['name'] for b in boards]

board_name = config.get('jira_board_name')
board = None
while board_name not in board_names:
    print('BOARDS:')
    print(' . '+'\n . '.join(board_names))
    board_name = input("Jira Board Name: ")

board = list(filter(lambda x: x['name'] == board_name, boards))[0]

board_sprints = requests.get(board['self']+"/sprint", auth=auth, headers=headers).json()['values']

active_sprint = list(filter(lambda x: x['state'] == 'active', board_sprints))
if active_sprint:
    active_sprint = active_sprint[0]

future_sprint = list(filter(lambda x: x['state'] == 'future', board_sprints))
if future_sprint:
    future_sprint = future_sprint[0]

default_sprint = active_sprint or future_sprint

sprint_names = [s['name'] for s in board_sprints]

sprint_name = config.get('jira_sprint_name', '')
while sprint_name not in sprint_names:
    print('SPRINTS:')
    print(' . '+'\n . '.join('{} ({})'.format(s['name'], s['state']) for s in board_sprints))
    if default_sprint:
        sprint_name = input("Jira Sprint Name [{}]: ".format(default_sprint['name']))
        if not sprint_name:
            sprint_name = default_sprint['name']
    else:
        sprint_name = input("Jira Sprint Name: ")

sprint = list(filter(lambda x: x['name'] == sprint_name, board_sprints))[0]

sprint_issues = requests.get(sprint['self']+"/issue?maxResults=1000", auth=auth, headers=headers).json()['issues']

remaining_hours = {}

for issue in sorted(sprint_issues, key=lambda i: '{}{:030d}'.format(
            i.get('fields', {}).get('summary')[:3],
            i.get('fields', {}).get('timetracking', {}).get('remainingEstimateSeconds', 0))):
    _type = re.match('\[([^\]]*)\].*', issue.get('fields', {}).get('summary'))
    remaining_seconds = issue.get('fields', {}).get('timetracking', {}).get('remainingEstimateSeconds', 0)
    _remaining_hours = remaining_seconds/60/60
    if not _type and remaining_seconds:
        print("Issue {} has no type.".format(issue['key']))
    elif _type and remaining_seconds:
        _type = _type.groups()[0]
        _type = _type.upper()
        hours = remaining_hours.get(_type, 0)
        hours += _remaining_hours
        remaining_hours[_type] = hours
        print("{:5.1f} - {}".format(_remaining_hours, issue.get('fields', {}).get('summary')))

print('\nTypes:')

for key, value in sorted(remaining_hours.items(), key=lambda x:x[0]):
    print('. {} - {} hours'.format(key, value))

print('Total: {}'.format(sum(remaining_hours.values())))
