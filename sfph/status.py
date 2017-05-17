# Copyright (c) 2017 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.
#
#
# def is_active(status):
#     for gid, s in status.items():
#         if s > manage.JobStatus.inactive:
#             return True
#     return False
#
#
# def draw_progressbar(value, total, width=40):
#     n = int(value / total * width)
#     return '|' + ''.join(['#'] * n) + ''.join(['-'] * (width - n)) + '|'
#
#
# def abbreviate(x, a):
#     if x == a:
#         return x
#     else:
#         abbreviate.table[a] = x
#         return a
# abbreviate.table = dict()  # noqa
#
#
# def shorten(x, max_length=None):
#     if max_length is None:
#         return x
#     else:
#         return abbreviate(x, x[:max_length])
#
#     @classmethod
#     def _tr(cls, x):
#         "Use name translation table for x."
#         return cls.NAMES.get(x, x)
#
#     ALIASES = dict(
#         status='S',
#         unknown='U',
#         registered='R',
#         queued='Q',
#         active='A',
#         inactive='I',
#         requires_attention='!'
#     )
#
#     @classmethod
#     def _alias(cls, x):
#         "Use alias if specified."
#         return abbreviate(x, cls.ALIASES.get(x, x))
#
#     @classmethod
#     def update_aliases(cls, aliases):
#         "Update the ALIASES table for this class."
#         cls.ALIASES.update(aliases)
#
#     def print_overview(self, stati, max_lines=None, file=sys.stdout):
#         "Print the project's status overview."
#         progress = defaultdict(int)
#         for status in stati:
#             for label in status['labels']:
#                 progress[label] += 1
#         progress_sorted = islice(sorted(
#             progress.items(), key=lambda x: (x[1], x[0]), reverse=True), max_lines)
#         table_header = ['label', 'progress']
#         rows = ([label, '{} {:0.2f}%'.format(
#             draw_progressbar(num, len(stati)), 100 * num / len(stati))]
#             for label, num in progress_sorted)
#         print("{} {}".format(self._tr("Total # of jobs:"), len(stati)), file=file)
#         print(util.tabulate.tabulate(rows, headers=table_header), file=file)
#         if max_lines is not None:
#             lines_skipped = len(progress) - max_lines
#             if lines_skipped:
#                 print("{} {}".format(self._tr("Lines omitted:"), lines_skipped), file=file)
#
#     def format_row(self, status, statepoint=None, max_width=None):
#         "Format each row in the detailed status output."
#         row = [
#             status['job_id'],
#             ', '.join((self._alias(s) for s in status['submission_status'])),
#             status['operation'],
#             ', '.join(status.get('labels', [])),
#         ]
#         if statepoint:
#             sps = self.open_job(id=status['job_id']).statepoint()
#
#             def get(k, m):
#                 if m is None:
#                     return
#                 t = k.split('.')
#                 if len(t) > 1:
#                     return get('.'.join(t[1:]), m.get(t[0]))
#                 else:
#                     return m.get(k)
#
#             for i, k in enumerate(statepoint):
#                 v = self._alias(get(k, sps))
#                 row.insert(i + 3, None if v is None else shorten(str(v), max_width))
#         if status['operation'] and not status['active']:
#             row[1] += ' ' + self._alias('requires_attention')
#         return row
#
#     def print_detailed(self, stati, parameters=None,
#                        skip_active=False, param_max_width=None,
#                        file=sys.stdout):
#         "Print the project's detailed status."
#         table_header = [self._tr(self._alias(s))
#                         for s in ('job_id', 'status', 'next_operation', 'labels')]
#         if parameters:
#             for i, value in enumerate(parameters):
#                 table_header.insert(i + 3, shorten(self._alias(str(value)), param_max_width))
#         rows = (self.format_row(status, parameters, param_max_width)
#                 for status in stati if not (skip_active and status['active']))
#         print(util.tabulate.tabulate(rows, headers=table_header), file=file)
#         if abbreviate.table:
#             print(file=file)
#             print(self._tr("Abbreviations used:"), file=file)
#             for a in sorted(abbreviate.table):
#                 print('{}: {}'.format(a, abbreviate.table[a]), file=file)
#     def print_status(self, scheduler=None, job_filter=None,
#                      overview=True, overview_max_lines=None,
#                      detailed=False, parameters=None, skip_active=False,
#                      param_max_width=None,
#                      file=sys.stdout, err=sys.stderr,
#                      pool=None):
#         """Print the status of the project.
#
#         :param scheduler: The scheduler instance used to fetch the job stati.
#         :type scheduler: :class:`~.manage.Scheduler`
#         :param job_filter: A JSON encoded filter,
#             that all jobs to be submitted need to match.
#         :param detailed: Print a detailed status of each job.
#         :type detailed: bool
#         :param parameters: Print the value of the specified parameters.
#         :type parameters: list of str
#         :param skip_active: Only print jobs that are currently inactive.
#         :type skip_active: bool
#         :param file: Print all output to this file,
#             defaults to sys.stdout
#         :param err: Print all error output to this file,
#             defaults to sys.stderr
#         :param pool: A multiprocessing or threading pool. Providing a pool
#             parallelizes this method."""
#         if job_filter is not None and isinstance(job_filter, str):
#             job_filter = json.loads(job_filter)
#         jobs = list(self.find_jobs(job_filter))
#         if scheduler is not None:
#             self.update_stati(scheduler, jobs, file=err, pool=pool)
#         print(self._tr("Generate output..."), file=err)
#         if pool is None:
#             stati = [self.get_job_status(job) for job in jobs]
#         else:
#             stati = pool.map(self.get_job_status, jobs)
#         title = "{} '{}':".format(self._tr("Status project"), self)
#         print('\n' + title, file=file)
#         if overview:
#             self.print_overview(stati, max_lines=overview_max_lines, file=file)
#         if detailed:
#             print(file=file)
#             print(self._tr("Detailed view:"), file=file)
#             self.print_detailed(stati, parameters, skip_active,
#                                 param_max_width, file)
#
#     @classmethod
#     def add_print_status_args(cls, parser):
#         "Add arguments to parser for the :meth:`~.print_status` method."
#         parser.add_argument(
#             '-f', '--filter',
#             dest='job_filter',
#             type=str,
#             help="Filter jobs.")
#         parser.add_argument(
#             '--no-overview',
#             action='store_false',
#             dest='overview',
#             help="Do not print an overview.")
#         parser.add_argument(
#             '-m', '--overview-max-lines',
#             type=int,
#             help="Limit the number of lines in the overview.")
#         parser.add_argument(
#             '-d', '--detailed',
#             action='store_true',
#             help="Display a detailed view of the job stati.")
#         parser.add_argument(
#             '-p', '--parameters',
#             type=str,
#             nargs='*',
#             help="Display select parameters of the job's "
#                  "statepoint with the detailed view.")
#         parser.add_argument(
#             '--param-max-width',
#             type=int,
#             help="Limit the width of each parameter row.")
#         parser.add_argument(
#             '--skip-active',
#             action='store_true',
#             help="Display only jobs, which are currently not active.")
#
#
#
class Status(object):
    pass

def status():
    pass
