# Copyright (c) 2017 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.
import itertools
from . import scheduler
from signac.common.six import with_metaclass
import uuid

# def _fn_bundle(self, bundle_id):
#     return os.path.join(self.root_directory(), '.bundles', bundle_id)
#
# def _store_bundled(self, operations):
#     """Store all job session ids part of one bundle.
#
#     The job session ids are stored in a text file in the project's
#     root directory. This is necessary to be able to identify each
#     job's individual status from the bundle id."""
#     if len(operations) == 1:
#         return operations[0].get_id()
#     else:
#         h = '.'.join(op.get_id() for op in operations)
#         bid = '{}-bundle-{}'.format(self, sha1(h.encode('utf-8')).hexdigest())
#         fn_bundle = self._fn_bundle(bid)
#         _mkdir_p(os.path.dirname(fn_bundle))
#         with open(fn_bundle, 'w') as file:
#             for operation in operations:
#                 file.write(operation.get_id() + '\n')
#         return bid
#
# def _expand_bundled_jobs(self, scheduler_jobs):
#     "Expand jobs which were submitted as part of a bundle."
#     for job in scheduler_jobs:
#         if job.name().startswith('{}-bundle-'.format(self)):
#             with open(self._fn_bundle(job.name())) as file:
#                 for line in file:
#                     yield manage.ClusterJob(line.strip(), job.status())
#         else:
#             yield job

class JobBundle(object):

    def __init__(self, jobops, procs_per_job=None):
        self._job_ops = list(jobops)
        self._name = None;
        self._job_names = [];
        self._ppj = procs_per_job;

    def _submit_name(self, project):
        if len(self._job_ops) == 1:
            op, job = self._job_ops[0]
            return "{}-{}-{}".format(job, op, project);
        else:
            uid = uuid.uuid4();
            return "{}-bundle-{}".format(uid, project);

    def dump(self, stream, hostconf, submitconf, project, **kwargs):
        assert len(self._job_ops) > 0
        if len(self._job_ops) == 1: # just one job so we just write the operation script.
            job, op = self._job_ops[0]
            self._name = self._make_submit_name(op, job, project)
            submitconf.write_preamble(stream, self._name)
            stream.write(op.format_header(hostconf, submitconf, project, **kwargs))
            stream.write('\n')
            stream.write(op.format_script(host, submission, project, job, **kwargs))
            stream.write('\n')
        else:
            self._name = "{project}-bundle-{hex}".format(project, hex)
            submitconf.write_preamble(stream, self._name)
            _, op = self._job_ops[0];
            stream.write(op.format_header(hostconf, submitconf, project, nprocs=self._ppj, **kwargs)) #TODO: fix this.
            stream.write('\n')
            for job, operation in self._job_ops:
                self._job_names(scheduler.make_submit_name(operation, job, project))
                stream.write(op.format_script(host, submission, project, job, nprocs=self.procs_per_job, **kwargs).strip())
                stream.write(' &\n');

    def dumps(self, hostconf, submitconf, project, **kwargs):
        stream = io.StringIO()
        self.dump(stream, hostconf, submitconf, project, **kwargs);
        stream.seek(0)
        return stream.read();

    def jobops(self):
        return self._job_ops

    def job_names(self):
        return self._job_names

    def name(self):
        return self._name

    def save(self):
        pass

    def load(self):
        pass


class BundlerType(type):

    def __init__(cls, name, bases, dct):
        if not hasattr(cls, 'registry'):
            cls.registry = dict()
        else:
            cls.registry[name] = cls
        return super(BundlerType, cls).__init__(name, bases, dct)

class Bundler(with_metaclass(BundlerType)):

    def __init__(self, size):
        self._size = size

    def bundle(self, hostconf, submitconf, jobops, **kwargs):
        jobops = list(jobops);
        total_size = len(jobops);
        assert total_size % self._size == 0
        for i in range(total_size/self._size):
            yield JobBundle(itertools.islice(jobops, start=i*self._size, stop=(i+1)*self._size), procs_per_job=(submitconf.nprocs/self._size))
