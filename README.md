Jira Sprint Report
==================

A python application that prints sprint report on console:

Exaple:

    ./report.py

    3.0 - [BE] Task 1
    5.5 - [FE] Task 2
    4.8 - [BE] Task 3

    Types:
    . BE - 7.8 hours
    . FE - 5.5 hours
    Total: 13.3

## Usage

* Configure vars on `condig.yml`
* (Optional) Create a virtual environment with `virtualenv -p python3 jira-sprint-report`
    * Activate the virtual environment `source jira-sprint-report/bin/activate`
* Install dependencies with `pip install -r requirements.txt`
* Run the report `./report.py`
