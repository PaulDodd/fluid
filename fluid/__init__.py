
from .bundler import Bundler
from .formatter import ScriptFormatter
from .parameter import FluidParams
from .project import FluidProject, FluidOperation
from .scheduler import Scheduler
from . import config
from . import ipython
import argparse


__all__ = ['Bundler', 'ScriptFormatter', 'FlowParams', 'FlowProject', 'FlowOperation', 'Scheduler', 'run', 'ipython']


# class operation(object):
#     """Decorate a function to be a operation function.
#
#     The operation() method as part of FlowProject iterates over all
#     methods decorated with this label and yields the method's name
#     or the provided name.
#
#     For example:
#
#     .. code::
#
#         class MyProject(FlowProject):
#
#             @label()
#             def foo(self, job):
#                 return True
#
#             @label()
#             def bar(self, job):
#                 return 'a' in job.statepoint()
#
#         >>> for label in MyProject().labels(job):
#         ...     print(label)
#
#     The code segment above will always print the label 'foo',
#     but the label 'bar' only if 'a' is part of a job's state point.
#
#     This enables the user to quickly write classification functions
#     and use them for labeling, for example in the classify() method.
#     """
#
#     def __init__(self, name=None):
#         self.name = name
#
#     def __call__(self, func):
#         func._label = True
#         if self.name is not None:
#             func._label_name = self.name
#         return func
#
#
# class runner:
#
#     def __init__(self, parser=True):
#         self._parser = argparse.ArgumentParser()
#         if parser:
#             self.setup_parser();
#
#     def add_args(self):
#         self._parser.add_argument(
#             'operation',
#             type=str,
#             choices=list(_get_operations()),
#             help="The operation to execute.")
#         self._parser.add_argument(
#             'jobid',
#             type=str,
#             nargs='*',
#             help="The job ids, as registered in the signac project. "
#                  "Omit to default to all statepoints.")
#         self._parser.add_argument(
#             '--np',
#             type=int,
#             help="Specify the number of cores to parallelize to. The "
#                  "default value of 0 means as many cores as are available.")
#         self._parser.add_argument(
#             '-t', '--timeout',
#             type=int,
#             help="A timeout in seconds after which the parallel execution "
#                  "of operations is canceled.")
#         self._parser.add_argument(
#             '--progress',
#             action='store_true',
#             help="Display a progress bar during execution.")
#
#     @property
#     def parser(self):
#         return self._parser;
#
#     def __call__(self):
#         args = self._parser.parse_args()
#         project = get_project()
#         if len(args.jobid):
#             try:
#                 jobs = [project.open_job(_id=jid) for jid in args.jobid]
#             except (KeyError, LookupError) as e:
#                 print(e, file=sys.stderr)
#                 sys.exit(1)
#         else:
#             jobs = project
#
#         module = inspect.getmodule(inspect.currentframe().f_back)
#         try:
#             operation = getattr(module, args.operation)
#         except AttributeError:
#             raise KeyError("Unknown operation '{}'.".format(args.operation))
#
#         # Serial execution
#         if args.np == 1:
#             for job in tqdm(jobs) if args.progress else jobs:
#                 operation(job)
#
#         # Parallel execution
#         elif six.PY2:
#             # Due to Python 2.7 issue #8296 (http://bugs.python.org/issue8296) we
#             # always need to provide a timeout to avoid issues with "hanging"
#             # processing pools.
#             timeout = sys.maxint if args.timeout is None else args.timeout
#             pool = Pool(args.np)
#             result = pool.imap_unordered(operation, jobs)
#             for _ in tqdm(jobs) if args.progress else jobs:
#                 result.next(timeout)
#         else:
#             with Pool(args.np) as pool:
#                 result = pool.imap_unordered(operation, jobs)
#                 for _ in tqdm(jobs) if args.progress else jobs:
#                     result.next(args.timeout)
#
#
#
# run = runner(True);
