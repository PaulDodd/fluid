# TODO: Remove from project
_params_warned_once = False
class FluidParams(dict):
    defaults = dict() # the default values of the parameters
    def __init__(self, job, readonly=None):
        dict.__init__(self)
        try:
            # TODO: this may not really be the right case.
            from mpi4py import MPI
            self._comm = MPI.COMM_WORLD
            rank = comm.Get_rank()
        except ImportError as err:
            #TODO:handle error.
            if not _params_warned_once:
                logger.warning("Could not import mpi4py. parameters will default to read only.")
                _params_warned_once = True
            if readonly is None:
                readonly = True

        if readonly is None or type(readonly) is not bool:
            readonly = (rank != 0)
        self.__dict__.update(dict(_job=job, defaults=self.defaults, _readonly=readonly))
        self.load()

    def load(self):
        for key in self.defaults:
            self[key] = self._job.document.get(key, self.defaults[key])

    def save(self):
        if _comm: _comm.Barrier() # ensure all ranks are not accessing the data.
        ret = False
        if not self._readonly:
            for key in self.keys():
                self._job.document[key] = self[key]
            ret = True
        if _comm: _comm.Barrier() # ensure all ranks are not accessing the data.
        return True

    def __getitem__(self, key):
        return super(FlowParams, self).__getitem__(key)

    def __setattr__(self, name, value):
        if not hasattr(self.defaults, name):
            raise AttributeError('{} instance has no attribute {!r}'.format(type(self).__name__, name))
        super(FlowParams, self).__setattr__(name, value)

    @classmethod
    def get_value(cls, job, name):
        return job.document.get(name, cls.defaults[name])

    def update(self, src):
        extra, override = self.extract(src)
        super(FlowParams, self).update(override)

    @classmethod
    def extract(cls, src):
        unused = dict()
        params = dict()
        for key in src:
            if key in cls.defaults.keys():
                params[key] = src[key]
            else:
                unused[key] = src[key]
        return params, unused
