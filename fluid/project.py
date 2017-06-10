# Copyright (c) 2017 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.
from __future__ import print_function
import sys
import os
import errno
from hashlib import sha1
import logging

import signac
import flow

from .config import load_config
from .job_filter import EligibleOperationFilter
from .formatter import ScriptFormatter


logger = logging.getLogger("flow.{}".format(__name__)) # TODO: I am playing around with this style of naming

def _mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as error:
        if not (error.errno == errno.EEXIST and os.path.isdir(path)):
            raise


def _get_project(root=None, alias=None):
    assert hasattr(FlowProject, 'registry');
    registry = FlowProject.registry;
    logger.debug("FlowProject registry: {}".format(', '.join([k for k in registry.keys()])));
    clss=None;
    if alias is None:
        if len(registry) == 0: # no user definitions have been found.
            logger.error("Could not find flow project definitions.")
            raise LookupError("signac-flow project not found.");
        elif len(registry) == 1: # one unambiguous project
            print(registry)
            print(list(registry.items()));
            alias, clss = list(registry.items())[0];
        else: # ambiguous case. must supply alias.
            logger.error("More than one flow project found, must provide the class alias.")
            raise LookupError("signac-flow project is ambiguous.");
    else:
        if alias in registry:
            clss = registry[alias];
        else:
            logger.error("Could not find flow project named {!r}.".format(alias))
            raise LookupError("signac-flow project not found.");
    assert clss is not None; # should never happen at this point.
    logger.debug("Creating project from {!r}".format(alias));
    return clss() # TODO: use clss.get_project()? need to overload for flow


class FluidOperation:

    def __init__(self, prereqs, postconds, script, formatter):
        if prereqs is None: prereqs = [ None ]
        if postconds is None: postconds = [ None ]

        self._prerequistes = [ FlowCondition(cond) for cond in prereqs ]
        self._postconditions = [ FlowCondition(cond) for cond in postconds ]
        self._script = script
        self._formatter = formatter

    # def __str__(self):
    #     return self.name;
    #
    # def is_callable(self):
    #     return self._operation is not None and callable(self._operation)
    #
    # def __call__(self, *args, **kwargs):
    #     assert self.is_callable();
    #     return self._operation(*args, **kwargs)

    def eligible(self, job):
        # if preconditions are all true and at least one post condition is false.
        pre = all([cond(job) for cond in self._prerequistes])
        post = not all([cond(job) for cond in self._postconditions])
        return pre and post

    def complete(self, job):
        return all([cond(job) for cond in self._postconditions]) and all([cond(job) for cond in self._prerequistes])

    def format_script(self, project, job, nprocs=None, ngpus=None, walltime=None, memory=None, mpicmd=None, **kwargs):
        return self._formatter.format(script=self._script, project=project, operation=self, job=job, nprocs=nprocs, ngpus=ngpus, walltime=walltime, memory=memory, mpicmd=mpicmd, **kwargs)

    # TODO: Add to fluid project
    def write_script(self, project, job, nprocs=None, ngpus=None, walltime=None, memory=None, mpicmd=None, **kwargs):
        root = os.path.join(job.workspace(), '.flow');
        _mkdir_p(root);
        script = self.format_script(project, job, nprocs=nprocs, ngpus=ngpus, walltime=walltime, memory=memory, mpicmd=mpicmd, **kwargs);
        # hexcode = sha1(script.encode()).hexdigest()
        fn = os.path.join(root, "{operation}.sh".format(operation=self))
        logger.debug("writing job-operation script to: {}".format(fn));
        with open(fn, 'w') as f:
            f.write(script)
            f.write("\n");
        return fn;


class FluidProject(flow.FlowProject):
    pass


def get_project(root=None, alias=None):
    """
    Determine the next operation for job.

    You can, but don't have to use this function to simplify
    the submission process. The default method returns None.

    :param root: same as signac.
    :type str:
    :param alias: alias for the flow project
    :type str:
    :returns: a flow project
    :rtype: :class: `FlowProject`
    """
    return _get_project(root, alias);
