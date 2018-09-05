# Copyright (c) Microsoft Corporation
# All rights reserved.
#
# MIT License
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and
# to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED *AS IS*, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
# BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from cleaner.runtime.executor import Executor
from cleaner.model.condition import Condition
from cleaner.model.action import Action
from cleaner.model.rule import Rule
import time
import subprocess
import multiprocessing
import logging
from logging.handlers import RotatingFileHandler

logger = multiprocessing.get_logger()


class Cleaner:
    def __init__(self, cool_down_time=2):
        self.rules = {}
        self.cool_down_time = cool_down_time

    def add_rule(self, key, rule):
        if key not in self.rules:
            logger.info("add rule with key %s.", key)
            self.rules[key] = rule

    def run(self):
        executor = Executor()
        executor.start()
        try:
            while True:
                for (key, rule) in self.rules.items():
                    executor.run_async(key, rule)
                time.sleep(self.cool_down_time)
        except:
            logger.error("cleaner interrupted and will exit.")
            executor.terminate()


def check_docker_cache(threshold):
    proc = subprocess.Popen(['/bin/bash', './scripts/reclaimable_docker_cache.sh'], stdout=subprocess.PIPE)
    out, _ = proc.communicate()
    out = out.decode("UTF-8").strip()
    logger.info("the reclaimable docker cache size is %s", out)
    try:
        size = float(out)
    except ValueError:
        size = 0
    return size > threshold


def add_docker_cache_rule(cache_cleaner):
    condition = Condition(key="docker_cache_condition",
                          input_data=1,
                          method=check_docker_cache)
    action = Action(key="docker_cache_action",
                    command="python ./scripts/clean_docker_cache.py")
    rule = Rule(key="docker_cache_rule",
                condition=condition,
                action=action)
    cache_cleaner.add_rule(rule.key, rule)


def setup_logging(filename):
    handler = RotatingFileHandler(filename, maxBytes=1024 * 1024 * 20, backupCount=10)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(filename)s:%(lineno)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


if __name__ == "__main__":
    setup_logging("/datastorage/cleaner/cleaner.log")
    cleaner = Cleaner()
    add_docker_cache_rule(cleaner)
    cleaner.run()
