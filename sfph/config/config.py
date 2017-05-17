# Copyright (c) 2017 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.
import platform
import logging
import re
import argparse
import datetime
import socket
import signac
from signac.common.six import with_metaclass
import signac.common.config
from signac.common.config import Config

logger = logging.getLogger("flow.{}".format(__name__));

def load_config(root=None, local=False):
    logger.debug("loading flow config")
    return FlowConfig(config=signac.common.config.load_config(root, local))

def read_config_file(filename):
    logger.debug("reading flow config file")
    return FlowConfig(config=signac.common.config.read_config_file(filename));

def get_config(infile=None, configspec=None, * args, **kwargs):
    logger.debug("getting flow config")
    return FlowConfig(config=signac.common.config.get_config(infile, configspec, *args, **kwargs));


# TODO: Error Handling. There are many asserts in the code, we need to handle the errors.

class SubmitConfigType(type):

    def __init__(cls, name, bases, dct):
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

        return super(SubmitConfigType, cls).__init__(name, bases, dct)

# Here is the internal model of how a submission on a compute environment
# works. All of the assumptions are contained on this class and the derivative
# classes (PBS, SLURM). If this model does not work for a given compute resource
# a new config class will need to be written, see how PBS and SLURM config classes
# have been done for an example of how to do this.
class SubmitConfig(with_metaclass(SubmitConfigType)):

    def _get_nodes(self):
        if self._nodes:
            return [node['count'] for node in self._nodes]
        return None;

    def _get_procs_per_node(self):
        if self._nodes:
            return [node['ppn'] for node in self._nodes]
        return None;

    def _get_gpus_per_node(self):
        if self._nodes:
            return [node['gpus'] for node in self._nodes]
        return None;

    def _get_walltime(self):
        return int(self._walltime.total_seconds()) if self._walltime else 0;

    def _get_memory_per_proc(self):
        return self._memory_per_proc;

    def _get_memory(self):
        raise NotImplementedError("The mem property is not implemented")

    def _get_nprocs(self):
        if self._nodes is not None:
            nl = self._get_nodes();
            nl = [n if n is not None else 1 for n in nl]; # assumption!
            pl = self._get_procs_per_node();
            pl = [p if p is not None else 1 for p in pl]; # assumption!
            return sum([n*p for n,p in zip(nl,pl)]);
        return None

    def _get_ngpus(self):
        if self._gpus is not None and self._nodes is not None:
            return sum(self._get_nodes())*self._gpus # assumption!
        elif self._nodes is not None:
            nl = self._get_nodes();
            nl = [n if n is not None else 1 for n in nl]; # assumption!
            gl = self._get_gpus_per_node();
            gl = [g if g is not None else 0 for g in gl]; # assumption!
            return sum([n*g for n,g in zip(nl,gl)]);
        return None

    def _get_remainder(self):
        return self._remainder

    nodes = property(fget=_get_nodes, fset=None, fdel=None, doc="The number of nodes requested.")
    ppn = property(fget=_get_procs_per_node, fset=None, fdel=None, doc="The number of processes per node requested.")
    walltime = property(fget=_get_walltime, fset=None, fdel=None, doc="The total walltime requested in seconds.")
    pmem = property(fget=_get_memory_per_proc, fset=None, fdel=None, doc="The amount of memory per processes requested.")
    # mem = property(fget=_get_memory, fset=None, fdel=None, doc="The total amount requested in KB.")
    nprocs = property(fget=_get_nprocs, fset=None, fdel=None, doc="The total number of procs requested.")
    gpn = property(fget=_get_gpus_per_node, fset=None, fdel=None, doc="The number of gpus per node requested.")
    ngpus = property(fget=_get_ngpus, fset=None, fdel=None, doc="The total number of gpus requested.")
    remainder = property(fget=_get_remainder, fset=None, fdel=None, doc="Extra arguments to be passed to the qsub command")

    def __init__(self, host, name, default=None):
        self._host = host;
        self._name = name;
        if default is None:
            default = dict();
        self._default = default;
        self._config = dict(default);
        self._remainder = "";
        self._nodes=None;
        self._walltime=None;
        self._memory_per_proc=None;
        self._gpus=None;

    def is_valid(self):
        return False;

    def parse_args(self, args):
        return;

    def forward_args(self):
        return self._remainder.split();

    def get_config(self):
        return self._config;

    @staticmethod
    def _rupdate(src, update):
        """
        recursively update a dictionary
        """
        for key in update:
            if key in src.keys():
                if isinstance(src[key], dict) and isinstance(update[key], dict):
                    SubmitConfig._rupdate(src[key], update[key]);
                else:
                    src[key] = update[key];
            else:
                src[key] = update[key];


class ComputeEnvironmentType(type):

    def __init__(cls, name, bases, dct):
        if not hasattr(cls, 'registry'):
            cls.registry = dict()
        else:
            cls.registry[name] = cls
        if hasattr(cls, 'alias'):
            if cls.alias in cls.registry:
                logger.warning('ComputeEnvironmentType with alias {:r} has already been registered. Overriding definition'.format(cls.alias))
            cls.registry[cls.alias] = cls
        return super(ComputeEnvironmentType, cls).__init__(name, bases, dct)

class ComputeEnvironment(with_metaclass(ComputeEnvironmentType)):
    alias='default'
    def __init__(self, alias, conf):
        # alias, pattern, mpicmd, scheduler_type, submit_schemes
        self.hostname_pattern = conf["pattern"]
        self.alias = alias
        self.mpi_cmd = conf["mpicmd"]
        self.scheduler_type = conf["type"]
        if conf["type"] == 'None':
            self.scheduler_type = None
        self.submit_config = None
        if 'submitconf' in conf: # optional
            self.submit_config = conf["submitconf"]

    def is_present(self):
        if self.hostname_pattern is None:
            return False
        else:
            return re.match(
                self.hostname_pattern, socket.gethostname()) is not None

    def get_submission_config(self, name):
        if self.scheduler_type is None or self.submit_config is None: # TODO: should this be an error?
            logger.debug("scheduler type and/or submitconf is None")
            return None;
        conf_cls = SubmitConfig.registry[self.scheduler_type];
        if name in self.submit_config:
            return conf_cls(host=self._alias, name=name, default=self.submit_config[name])
        else:
            raise KeyError("submission configuration named {} is not found".format(name))

    def get_mpi_cmd(self, nprocs): # I think we may want to move this to the handler.
        return self.mpi_cmd.format(nprocs=nprocs);

# FlowConfig in flow is meant to match the signac config as much as posible.
class FlowConfig(Config):

    def __init__(self, config=None, *args, **kwargs):
        if config is not None:
            Config.__init__(self, config);
        else:
            Config.__init__(self, *args, **kwargs);
        self._envs = list()
        self._valid = 'flow' in self;
        if self._valid:
            if 'environment' in self['flow']:
                for alias in self['flow']['environment'].keys():
                    name = self['flow']['environment'][alias]['class']
                    ComputeEnvironmentClass = ComputeEnvironment.registry[name]
                    self._envs.append(ComputeEnvironmentClass(alias, self['flow']['environment'][alias]))
        else:
            logger.debug("signac-flow has not been configured, using default definitions")

    def get_environment(self, alias=None):
        for env in self._envs:
            if alias is not None:
                if env.alias == alias:
                    return env;
            elif env.is_present():
                return env
        return None

    def get_modules(self):
        if self._valid:
            return self['flow'].get('modules', list());
        return list();
