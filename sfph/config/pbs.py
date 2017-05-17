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

def parse_node_item(node):
    """
    {<node_count> | <hostname>} [:ppn=<ppn>][:gpus=<gpu>][:<property>[:<property>]...] [+ ...]
    nodes=2:blue:ppn=2+red:ib:ppn=3+b1014
    [
        {
            'count': 2
            'name': None
            'ppn': 2
            'gpus': None
            'features':['blue']
        },
        {
            'count': 1
            'name': None
            'ppn': 3
            'gpus': None
            'features': ['blue', 'red']
        },
        {
            'count': None
            'name': 'b1014'
            'ppn': None # default is 1?
            'gpus': None
            'features': []
        }
    ]
    """
    assert 'nodes=' == node[:6];
    node_specs = node.lstrip('nodes=').split('+');
    specs = [];
    for spec in node_specs:
        data = dict(count=None, name=None, ppn=None, gpus=None, features=None);
        sp = spec.split(':');
        assert len(sp) > 0
        if sp[0].isnumeric():
            data['count'] = int(sp[0]);
        else:
            data['name'] = sp[0];
        if len(sp) > 1:
            for s in sp[1:]:
                if 'ppn=' == s[:4] or 'gpus=' == s[:5]:
                    n = s.split('=')
                    assert len(n) == 2
                    assert n[0] in data.keys()
                    data[n[0]] = int(n[1]);
                else:
                    if data['features'] is None:
                        data['features'] = [];
                    data['features'].append(s);
        specs.append(data);
    return specs;


def parse_resource_list(resources):
    """
    Assumes that resources is a list of the form ["nodes=1:ppn=2,walltime=05:00:00", "qos=fluxoe", ...]
    """
    resource_map = dict() if len(resources) !=0 else None;
    for options in resources:
        for ops in options.split(','):
            if 'nodes=' == ops[:6]:
                resource_map['nodes'] = parse_node_item(ops);
            else:
                namevalue = ops.split('=');
                assert len(namevalue) == 2;
                resource_map[namevalue[0]] = namevalue[1];
    return resource_map

def dump_node_spec(nodelist):
    """
    Returns a list of resources of the form ["nodes=1:ppn=2,walltime=05:00:00", "qos=fluxoe", ...]
    """
    specstr = [];
    for spec in nodelist:
        strs = []
        if spec['count'] is not None:
            strs.append(str(spec['count']));
        else:
            assert spec['name'] is not None
            strs.append(spec['name']);
        if spec['ppn'] is not None:
            strs.append("ppn={}".format(spec['ppn']));
        if spec['gpus'] is not None:
            strs.append("gpus={}".format(spec['gpus']));
        if spec['features'] is not None:
            strs = strs + spec['features'];
        specstr.append(':'.join(strs));
    return '+'.join(specstr)


class PBSConfig(SubmitConfig):
    alias='pbs';
    submit_cmd = 'qsub';
    status_cmd = 'qstat -fx -u {user}';
    preable_prefix="#PBS";

    def is_valid(self):
        """
        opportunity to do a sanity check if needed.
        """
        return True;

    def parse_args(self, args):
        if isinstance(args, str):
            args = args.split();
        parser = argparse.ArgumentParser();
        self.add_args_to_parser(parser);
        submit_args = dict(**vars(parser.parse_args(args)));
        resources = parse_resource_list(submit_args['l']);
        submit_args['l'] = resources
        update = dict();
        for key in submit_args:
            if key == 'remainder':
                continue;
            if isinstance(submit_args[key], list):
                if len(submit_args[key]) != 0:
                    update[key] = submit_args[key];
            elif submit_args[key] is not None:
                update[key] = submit_args[key];
        self._remainder = submit_args['remainder'];
        SubmitConfig._rupdate(self._config, update);
        self._update_properties();

    def _update_properties(self):
        """
        units   multipliers
        b	w	1
        kb	kw	1024
        mb	mw	1,048,576
        gb	gw	1,073,741,824
        tb	tw	1,099,511,627,776
        """
        if 'nodes' in self._config['l'].keys():
            self._nodes = self._config['l']['nodes'];
        if 'gpus' in self._config['l'].keys():
            self._gpus = int(self._config['l']['gpus']); # the gpus can be specified as a resource.
        if 'pmem' in self._config['l'].keys():
            self._memory_per_proc = self._config['l']['pmem']; #TODO: parse the memory
        if 'walltime' in self._config['l'].keys():
            wt = self._config['l']['walltime'].split(':');
            # seconds, or [[HH:]MM:]SS
            assert len(wt) == 3 # TODO: parse time and or give a parse string i.e. HH:MM:SS
            self._walltime = datetime.timedelta(hours=int(wt[0]),minutes=int(wt[1]),seconds=int(wt[2])); #TODO: parse the memory


    @classmethod
    def add_args_to_parser(cls, parser):
        """
        Adds the qsub arguments to parser.
        The arguments defined here are available to be overloaded. All other qsub
        commands are stored in remiander and sent to
        """
        #PBS -t 1-5
        parser.add_argument(
            '-A',
            help="Defines the account string associated with the job.",
            default=None,
            type=str
        );
        parser.add_argument(
            '-N',
            help="Declares a name for the job.  The name specified may be up to "
                 "and including 15 characters in length.  It must consist of printable, "
                 "non white space  characters with the first character alphabetic.",
            default=None,
            type=str
        );
        parser.add_argument(
            '-q',
            help="Defines the destination of the job. The destination names a queue, "
                 "a server, or a queue at a server.",
            default=None,
            type=str
        );
        parser.add_argument(
            '-l',
            help="resource list for job submission. multiple resources can be specified "
                 "using a \',\' as a delimiter. example: -l nodes=1,walltime=24:00:00",
            default=[],
            type=str,
            action='append'
        );
        parser.add_argument(
            '-M',
            help="Declares the list of users to whom mail is sent by the execution "
                 "server when it sends mail about the job.",
            default=[],
            type=str,
            action='append'
        );
        parser.add_argument(
            '-m',
            help="Defines the set of conditions under which the execution server "
                 "will send a mail message about the job.  The mail_options argument "
                 "is a string which consists of either the single character \"n\" "
                 "or \"p\", or one or more of the characters \"a\", \"b\", \"e\", and \"f\".",
            default=None,
            type=str
        );
        parser.add_argument(
            '-j',
            help="Declares if the standard error stream of the job will be merged "
                 "with the standard output stream of the job.",
            default=None,
            type=str
        );
        parser.add_argument(
            '-V',
            help="Declares that all environment variables in the qsub command's "
                 "environment are to be exported to the batch job.",
            default=None,
            action='store_true'
        );
        parser.add_argument(
            '-t',
            help="Specifies the task ids of a job array. Single task arrays are allowed.",
            default=None,
            type=str
        );

        # its hard to remove defaults but one idea is:
        # parser.add_argument(
        #     '--no-V',
        #     help="Declares that all environment variables in the qsub command's "
        #          "environment are NOT exported to the batch job."
        #     dest='V'
        #     action='store_false'
        # );
        parser.add_argument(
            'remainder',
            nargs=argparse.REMAINDER
        )

    def _write_preamble_line(self, stream, option, value):
        stream.write("{prefix} {option} {value}\n".format( prefix=self.preable_prefix, option=option, value=value));

    def _write_preamble_name(self, stream, name):
        self._write_preamble_line(stream, '-N', name);

    def write_preamble(self, stream, name=None):
        """
        writes the preamble to stream. stream object must have a write method.
        """
        if name is not None: # name could be specified on command line
            self._write_preamble_name(stream, name)

        for name,val in self._config["l"].items():
            if name == 'nodes':
                val = dump_node_spec(val);
            value = "{}={}".format(name,val)
            self._write_preamble_line(stream, "-l", value)

        for key in self._config:
            if key == "l": # already processed
                continue;
            option = "-"+key;
            value=""
            if isinstance(self._config[key], list):
                value=",".join(self._config[key])
            elif isinstance(self._config[key], bool):
                if not self._config[key]: # this option has been disabled, we don't write it.
                    continue;
            else:
                value = self._config[key];
            self._write_preamble_line(stream, option, value)

    def job_status(self, result): # TODO: pull this into its own class? more flexible but then we need to store more info in the config
        tree = ET.parse(source=result)
        root = tree.getroot()
        for node in root.findall('Job'):
            job_state = self.node.find('job_state').text
            state = JobStatus.registered
            if job_state == 'R':
                state = JobStatus.active
            if job_state == 'Q':
                state = JobStatus.queued
            if job_state == 'C':
                state = JobStatus.inactive
            if job_state == 'H':
                state = JobStatus.held
            yield self.node.find('Job_Id').text, self.node.find('Job_Name').text, state
