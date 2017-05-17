# Copyright (c) 2017 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.
from . import scheduler

# the logical clases are for internal use only.
# TODO: could also be applied to the FlowCondition's

class _and:
    def __init__(self, f1, f2):
        self._f1 = f1
        self._f2 = f2

    def __call__(self, job, op):
        return self._f1(job, op) and self._f2(job, op)

class _or:
    def __init__(self, f1, f2):
        self._f1 = f1
        self._f2 = f2

    def __call__(self, job, op):
        return self._f1(job, op) or self._f2(job, op)

class _not:
    def __init__(self, f1):
        self._f1 = f1

    def __call__(self, job, op):
        return not self._f1(job, op)

class _xor:
    def __init__(self, f1, f2):
        self._f1 = f1
        self._f2 = f2

    def __call__(self, job, op):
        return self._f1(job, op) != self._f2(job, op)


class JobFilter(object):

    def __init__(self, callback=None):
        self._callback = callback

    def __and__(self, other):
        """
        filter3 = filter1 & filter2
        filter3 will be the intersecion of filter1 and filter2
        """
        return JobFilter(callback=_and(self._callback, other._callback));

    def __or__(self, other):
        """
        filter3 = filter1 | filter2
        filter3 will be the union of filter1 and filter2
        """
        return JobFilter(callback=_or(self._callback, other._callback));

    def __invert__(self):
        """
        filter2 = ~filter1
        filter2 will be the compliment of filter1
        """
        return JobFilter(callback=_not(self._callback));

    def __xor__(self, other):
        """
        filter3 = filter1 ^ filter2
        filter3 will be the intersecion of filter1 or filter2
        """
        return JobFilter(callback=_xor(self._callback, other._callback));

    def _eval(self, job, op):
        if callback is not None:
            return bool(self._callback(job))
        return True

    def job_ops(self, iterable): # find the eligible job operation pairs
        for job,op in iterable:
            if self._eval(job,op):
                yield (job,op)

# class SignacJobFilter(JobFilter):
#
#     def __init__(self, filter_map=None):
#         self._filter_map = filter_map
#         JobFilter.__init__(self, callback=self._search)
#
#     def _search(self, job):
#         if self._filter_map is None:
#             return True
#         sp = job.statepoint()
#         for key,val in self._filter_map.items():
#             if key in sp.keys() and sp[key] != val:
#                 return False
#         return True

class EligibleOperationFilter(JobFilter):

    def __init__(self, project, operation=None):
        self._project = project
        self._op = operation
        JobFilter.__init__(self, callback=self._eligible)

    def _eligible(self, job, op):
        if self._op is None:
            return op in [o.name for o in self._project.next_operations(job)]
        return op == self._op and project.operation(self._op).eligible(job)

class StatusJobFilter(JobFilter):

    def __init__(self, project):
        self._project = str(project)
        JobFilter.__init__(self, callback=self._eligible_status)

    def _eligible_status(self, job, op):
        state = 0
        sub_name = util.make_submit_name(op, job, project)
        status = job.document.get('status',None)
        if status is not None and sub_name in status:
            state = status[sub_name]
        return state < scheduler.JobStatus.submitted
