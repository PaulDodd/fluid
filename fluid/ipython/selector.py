from ipywidgets import IntSlider, Dropdown
from IPython.display import display

def _get_value(d, keys, i=0):
    if type(d) != dict:
        return d;
    if type(keys) == str:
        ks = keys.split('.');
    else:
        ks = keys;
    if i == len(keys):
        return d;
    assert ks[i] in d;
    return _get_value(d[ks[i]], ks, i+1)

def __get_keys(d):
    keys = set();
    for k in d:
        if type(d[k]) == dict:
            nested = __get_keys(d[k]);
            for _k in nested:
                keys.add(k + '.' + _k);
        else:
            keys.add(k);
    return keys;

def _get_statepoint_keys(project, n=10, job_filter=None):
    ct=0;
    keys = set();
    for job in project.find_jobs(job_filter):
        statepoint = job.statepoint();
        if n > 0 and ct < n:
            keys.update(__get_keys(statepoint));
        else:
            break;
        ct+=1;
    return keys;

def _get_statepoint_options(project, keys, job_filter=None):
    ct=0;
    options = dict();
    for k in keys:
        options[k] = set();
    for job in project.find_jobs(job_filter):
        statepoint = job.statepoint();
        for k in keys:
            options[k].add(_get_value(statepoint, k))
    return options;

def _expand_keys(d):
    _d = dict();
    for k in d:
        s = k.split('.');
        if len(s)==1:
            _d[k] = d[k];
        else:
            __d = dict();
            value = d[k];
            for i,_k in enumerate(s[::-1]):
                __d = {_k : value};
                value = __d;
            _d.update(__d);
    return _d;


class Selector:

    def __init__(self, project, select, job_filter=None, n=1, **kwargs):

        avail = _get_statepoint_keys(project, n, job_filter);
        self._value = None;
        self._dropdowns = [];
        self._filter = job_filter if job_filter is not None else dict();
        self._project = project;

        for s in select:
            if not s in avail: # now we can add a drop down.
                raise RuntimeError("Error! The key {} is not found in the statepoint. \nOptions are: {}".format(s, ', '.join(avail)))

        opts = _get_statepoint_options(project, select, job_filter)
        for opt in opts:
            self._dropdowns.append(
                Dropdown(
                    options = sorted(list(opts[opt])),
                    description = opt,
                    button_style = ''
                )
            )

    def display(self):
        for d in self._dropdowns:
            display(d)

    def _get_filter(self):
        job_filter = dict(**self._filter);
        opts = dict();
        for d in self._dropdowns:
            opts.update({d.description : d.value});
        job_filter.update(_expand_keys(opts));
        return job_filter;

    @property
    def value(self):
        return list(self._project.find_jobs(filter=self._get_filter()));


# s = Selector(project, select = ['shape_data.short_name', 'shape_move'])
# s.display()
