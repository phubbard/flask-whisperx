#!/usr/bin/env python3
# Code to read config file and create database

from __future__ import unicode_literals
from loguru import logger as log
from config import DB_PATH
from model import make_database


if __name__ == '__main__':
    log.info(f'DB is {str(DB_PATH)}')
    make_database()