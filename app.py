#!/usr/bin/env python
# -*- coding: utf-8 -*-
from src.application import app

# print(dir(src.main))
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
