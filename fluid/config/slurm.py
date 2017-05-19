# Copyright (c) 2017 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.

import platform
import logging
import re
import argparse
import datetime

from .config import SubmitConfig

logger = logging.getLogger("flow.{}".format(__name__));

class SLURMConfig(SubmitConfig):
    alias='slurm';
    def __init__(self):
        pass

    def _parse_args(self, args):
        raise NotImplementedError("SLURMConfig._parse_args is not implemented yet!");
