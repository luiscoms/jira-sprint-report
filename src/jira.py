#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import current_app as app, g
import logging
import re
import requests
import sys
import yaml

logging.basicConfig(
    stream=sys.stdout,
    # level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s:%(name)s:%(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

logger.debug('install')

try:
    config = yaml.load(open('config.yml'))
except Exception as e:
    logger.error(e, exc_info=True)
    config = {}

BASE_URL = config.get('jira_url')
# if not BASE_URL:
#     BASE_URL = input("Jira URL: ")


def get_headers():
    try:
        jira_username = g.get('username')
        jira_password = g.get('password')
        logger.debug('Login with (%s:%s)', jira_username, jira_password)
        auth = requests.auth.HTTPBasicAuth(jira_username, jira_password)
        headers = {
            "Content-Type": "application/json"
        }
    except Exception as e:
        logger.error(e, exc_info=True)
        return {}

    return {
        'auth': auth,
        'headers': headers
    }


def get_boards():
    headers = get_headers()
    # logger.debug(headers)

    try:
        boards = requests.get(BASE_URL + "/rest/agile/1.0/board", **headers).json()['values']
        # board_names = [b['name'] for b in boards]
        logger.debug(boards)
    except Exception as e:
        logger.error(e, exc_info=True)
        return []

    return boards


def get_board(board_name, boards):
    if not board_name:
        logger.warning('No board name')
        return
    # boards = get_boards()
    if not boards:
        return

    board = list(filter(lambda x: x['name'] == board_name, boards))
    board = board[0] if board else None
    return board


def get_sprints(board):
    if not board:
        logger.warning('No board')
        return []
    headers = get_headers()

    board_sprints = requests.get(board['self']+"/sprint", **headers).json()['values']

    return board_sprints


def get_sprint(sprint_name, sprints):
    if not sprint_name:
        return
    if not sprints:
        logger.warning('No sprints')
        return []
    sprint_names = [s['name'] for s in sprints]

    active_sprint = list(filter(lambda x: x['state'] == 'active', sprints))
    if active_sprint:
        active_sprint = active_sprint[0]

    future_sprint = list(filter(lambda x: x['state'] == 'future', sprints))
    if future_sprint:
        future_sprint = future_sprint[0]

    default_sprint = active_sprint or future_sprint

    sprint = list(filter(lambda x: x['name'] == sprint_name, sprints))
    sprint = sprint[0] if sprint else default_sprint

    return sprint


def get_issues(sprint):
    if not sprint:
        logger.warning('No sprints')
        return []
    headers = get_headers()
    sprint_issues = requests.get(sprint['self']+"/issue?maxResults=1000", **headers).json()['issues']
    # logger.debug(sprint_issues)

    return sprint_issues


def get_types(sprint_issues):
    types = []
    if not sprint_issues:
        return types
    remaining_hours = {}
    spent_hours = {}

    for issue in sorted(sprint_issues, key=lambda i: '{}{:030d}'.format(
                i.get('fields', {}).get('summary')[:3],
                i.get('fields', {}).get('timetracking', {}).get('remainingEstimateSeconds', 0))):
        _type = re.match('\[([^\]]*)\].*', issue.get('fields', {}).get('summary'))
        spent_seconds = issue.get('fields', {}).get('timetracking', {}).get('timeSpentSeconds', 0)
        remaining_seconds = issue.get('fields', {}).get('timetracking', {}).get('remainingEstimateSeconds', 0)
        _remaining_hours = remaining_seconds/60/60
        _spent_hours = spent_seconds/60/60
        if not _type and remaining_seconds:
            logger.debug("Issue {} has no type.".format(issue['key']))
        if _type and (remaining_seconds or spent_seconds):
            _type = _type.groups()[0]
            _type = _type.upper()
            hours = remaining_hours.get(_type, 0)
            hours += _remaining_hours
            remaining_hours[_type] = hours
            hours = spent_hours.get(_type, 0)
            hours += _spent_hours
            spent_hours[_type] = hours
            logger.debug("{:5.1f} | {:4.1f} - {:6s} - {}".format(_remaining_hours, _spent_hours, issue['key'], issue.get('fields', {}).get('summary')))

    for key, value in sorted(remaining_hours.items(), key=lambda x:x[0]):
        logger.debug('. {} - ({} remaining) ({} spent)'.format(key, value, spent_hours.get(key)))
        t = {
            "name": key,
            "remainig": value,
            "spent": spent_hours.get(key),
        }
        types += [t]

    logger.debug('Total: {} ({})'.format(sum(remaining_hours.values()), sum(spent_hours.values())))

    return types
