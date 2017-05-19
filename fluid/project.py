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
from signac.common.six import with_metaclass

from . import util
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

class label(object):

    def __init__(self, name=None):
        self.name = name

    def __call__(self, func):
        func._label = True
        if self.name is not None:
            func._label_name = self.name
        return func

class staticlabel(label):

    def __call__(self, func):
        return staticmethod(super(staticlabel, self).__call__(func))

class classlabel(label):

    def __call__(self, func):
        return classmethod(super(classlabel, self).__call__(func))

def _is_label_func(func):
    return getattr(getattr(func, '__func__', func), '_label', False)

class FlowCondition:

    def __init__(self, callback):
        self._callback = callback

    def __call__(self, job):
        if self._callback == None:
            return True
        return self._callback(job)

    def __hash__(self):
        return hash(self._callback)

    def __eq__(self, other):
        return self._callback == other._callback

class FlowOperation:

    def __init__(self, name, callback, prereqs, postconds, script, formatter):
        self.name = name
        self._operation = callback # the function call.

        if prereqs is None: prereqs = [ None ]
        if postconds is None: postconds = [ None ]

        self._prerequistes = [ FlowCondition(cond) for cond in prereqs ]
        self._postconditions = [ FlowCondition(cond) for cond in postconds ]
        self._script = script
        self._formatter = formatter

    def __str__(self):
        return self.name;

    def is_callable(self):
        return self._operation is not None and callable(self._operation)

    def __call__(self, *args, **kwargs):
        assert self.is_callable();
        return self._operation(*args, **kwargs)

    def eligible(self, job):
        # if preconditions are all true and at least one post condition is false.
        pre = all([cond(job) for cond in self._prerequistes])
        post = not all([cond(job) for cond in self._postconditions])
        return pre and post

    def complete(self, job):
        return all([cond(job) for cond in self._postconditions]) and all([cond(job) for cond in self._prerequistes])

    def format_script(self, project, job, nprocs=None, ngpus=None, walltime=None, memory=None, mpicmd=None, **kwargs):
        return self._formatter.format(script=self._script, project=project, operation=self, job=job, nprocs=nprocs, ngpus=ngpus, walltime=walltime, memory=memory, mpicmd=mpicmd, **kwargs)

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

class _FlowProjectClass(type):

    def __new__(metacls, name, bases, namespace, **kwrgs):
        cls = type.__new__(metacls, name, bases, dict(namespace))
        cls._labels = {func for func in namespace.values() if _is_label_func(func)}
        exclude = False;

        if not hasattr(cls, 'registry'):
            cls.registry = dict()
            exclude = True; # Cannot specify the base type.

        if not exclude:
            if hasattr(cls, 'alias'):
                if cls.alias in cls.registry:
                    logger.warning('SubmitConfigType with alias {:r} has already been registered. Overriding definition'.format(cls.alias))
                cls.registry[cls.alias] = cls
            else:
                cls.registry[name] = cls
        return cls

class FlowProject(with_metaclass(_FlowProjectClass, signac.contrib.Project)):

    def __init__(self, config=None):
        if config is None:
            logger.debug("loading config!")
            config = load_config() # must use the flow.config version now.
        signac.contrib.Project.__init__(self, config);

        self._operations = dict()

    def labels(self, job):
        for label in self._labels:
            if hasattr(label, '__func__'):
                label = getattr(self, label.__func__.__name__)
                if label(job):
                    yield getattr(label, '_label_name', label.__name__)
            elif label(self, job):
                yield getattr(label, '_label_name', label.__name__)

    def add_operation(self, name, callback=None, prereqs=None, postconds=None, script=None, formatter=ScriptFormatter()):
        assert name not in self._operations
        self._operations[name] = FlowOperation(name, callback, prereqs, postconds, script, formatter)

#
# TODO: update the doc strings below.
#
    def classify(self, job):
        """Generator function which yields labels for job.

        :param job: The signac job handle.
        :type job: :class:`~signac.contrib.job.Job`
        :yields: The labels to classify job.
        :yield type: str
        """
        for label in self.labels(job):
            yield label

    def completed_operations(self, job):
        for name, op in self._operations.items():
            if op.complete(job):
                yield op

    def next_operations(self, job):
        """Determine the next operation for job.

        You can, but don't have to use this function to simplify
        the submission process. The default method returns None.

        :param job: The signac job handle.
        :type job: :class:`~signac.contrib.job.Job`
        :returns: The name of the operation to execute next.
        :rtype: str"""
        for name, op in self._operations.items():
            if op.eligible(job):
                yield op

    def next_operation(self, job):
        """Determine the next operation for job.

        You can, but don't have to use this function to simplify
        the submission process. The default method returns None.

        :param job: The signac job handle.
        :type job: :class:`~signac.contrib.job.Job`
        :returns: The name of the operation to execute next.
        :rtype: str"""
        for op in self.next_operations(job):
            return op
        return None

    def operation(self, name):
        assert name in self._operations
        return self._operations[name]

    def get_filter(self, operation):
        return EligibleOperationFilter(project=self, operation=operation)

    @property
    def operations(self):
        return self._operations

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
