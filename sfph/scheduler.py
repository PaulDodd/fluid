# Copyright (c) 2017 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.

import logging
import enum
import time
import getpass

from . import config
from . import bundler as bund
from . import job_filter
# from . import project as proj


def format_timedelta(delta):
    hours, r = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(r, 60)
    hours += delta.days * 24
    return "{:0>2}:{:0>2}:{:0>2}".format(hours, minutes, seconds)

class JobStatus(enum.IntEnum):
    """Classifies the job's execution status.

    The stati are ordered by the significance
    of the execution status.
    This enables easy comparison, such as

    .. code-block: python

        if status < JobStatus.submitted:
            submit()

    which prevents a submission of a job,
    which is already submitted, queued, active
    or in an error state."""
    unknown = 1
    registered = 2
    inactive = 3
    submitted = 4
    held = 5
    queued = 6
    active = 7
    error = 8
# User stati are >= 128.
    user = 128

class ClusterJob(object):

    def __init__(self, jobid, name, status):
        self._id = jobid
        self._name = name
        self._status = status

    def __str__(self):
        return str(self._job_id())

    def name(self):
        return self._name

    def id(self):
        return self._id

    def status(self):
        return self._status

class Scheduler(object):
    _last_query = None
    _dos_timeout = 10

    def __init__(self, conf):
        self._config = conf;
        # self._users = set([]+users)

    @classmethod
    def _prevent_dos(cls):
        if cls._last_query is not None:
            if time.time() - cls._last_query < cls._dos_timeout:
                raise RuntimeError(
                    "Too many scheduler requests within a short time!")
        cls._last_query = time.time()

    def submit(self, script, pretend=False, remainder=None):
        submit_cmd = [self._config.submit_cmd]
        if remainder is not None:
            remainder = remainder.split()
        else:
            remainder = []
        if pretend:
            print("# Submit command: {}".format(' '.join(submit_cmd+remainder)))
            print(script.read())
            print()
        else:
            with tempfile.NamedTemporaryFile() as tmp_submit_script:
                tmp_submit_script.write(script.read().encode('utf-8'))
                tmp_submit_script.flush()
                output = subprocess.check_output(
                    submit_cmd + [tmp_submit_script.name])
            jobsid = output.decode('utf-8').strip()
            return jobsid

    def jobs(user=None):
        self._prevent_dos();
        if user is None:
            user = getpass.getuser()
        cmd = status_cmd.format(user=user)
        try:
            result = io.BytesIO(subprocess.check_output(cmd.split()))
        except FileNotFoundError:
            raise RuntimeError("{} not available.".format(cmd.split()[0]));
        return [ClusterJob(i,n,s) for i,n,s in self._config.parse_status(result)] # TODO: fix this later
