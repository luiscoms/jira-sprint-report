#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import abort, Blueprint, Flask, g, render_template, request
from flask.ext.httpauth import HTTPBasicAuth
from jinja2 import TemplateNotFound
from src import jira

# configuration
DEBUG = True

app = Flask(__name__)
app.config.from_object(__name__)
simple_page = Blueprint('simmple_page', __name__, template_folder='templates')


auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username, password):
    # first try to authenticate by token
    # return False
    app.logger.debug('verify_password')
    g.username = username
    g.password = password
    if jira.get_boards():
        return True
    return False


# @app.errorhandler(404)
# def page_not_found(error):
#     return render_template('page_not_found.html'), 404

@app.route('/logout')
def logout():
    g.username = None
    g.password = None
    return ('Bye', 401)


@simple_page.route('/', defaults={'page': 'index'}, methods=['GET', 'POST'])
@simple_page.route('/<page>')
@auth.login_required
def show(page):
    try:
        username = request.form.get('username', '').strip() or g.get('username')
        password = request.form.get('password', '').strip() or g.get('username')
        # with app.app_context() as ctx:
        #     # ctx.pop()
        #     g.username = username
        #     g.password = password
        #     ctx.push()

        board_name = request.form.get('board_name', '').strip()
        sprint_name = request.form.get('sprint_name', '').strip()

        boards = jira.get_boards()
        board = jira.get_board(board_name, boards)
        sprints = jira.get_sprints(board)
        sprint = jira.get_sprint(sprint_name, sprints)
        issues = jira.get_issues(sprint)

        data = {
            'username': username,
            'password': password,
            'boards': boards,
            'sprints': sprints,
            'issues': issues,
            'types': jira.get_types(issues),
            'board_name': board_name,
            'sprint_name': sprint_name,
        }
        return render_template('pages/%s.html' % page, **data)
    except TemplateNotFound:
        abort(404)

app.register_blueprint(simple_page)
