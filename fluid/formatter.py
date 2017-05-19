# Copyright (c) 2017 The Regents of the University of Michigan
# All rights reserved.
# This software is licensed under the BSD 3-Clause License.

class ScriptFormatter(object):
    #TODO: think if we can remove the header + script and just have a single entry.
    # def format_header(self, header, host, submitconf, project, operation, nprocs=None, **kwargs):
    #     """
    #     formats script based on the host configuration, submitconf requests,
    #     operation name, job and other keyword arguments passed from the command line.
    #
    #     TODO:
    #
    #     list of names:
    #         * operation: name of the operation
    #         * mpicmd: the mpi command from the host configuration if nprocs > 1 otherwise an empty string
    #         * nprocs: the number of procs requested
    #         * ngpus: the number of gpus requested
    #         * memory: the amount memory in MB requested
    #         * walltime: the amount of time in seconds requested
    #     """
    #     #* parameters: the parameters defined by the project. you can access specific parameters
    #     np = submitconf.nprocs if nprocs is None else nprocs
    #     ng = submitconf.ngpus
    #     mem = submitconf.memory
    #     walltime = submitconf.walltime
    #     mpi=""
    #     if np > 0:
    #         mpi = host.get_mpi_cmd(nprocs=np);
    #
    #     fparams = dict(
    #         project_root=project.root_directory(),
    #         operation=operation.name,
    #         mpicmd=mpi,
    #         nprocs=np,
    #         ngpus=ng,
    #         memory=mem,
    #         walltime=walltime
    #     );
    #     return header.format(**fparams, **kwargs)

    # here we have already converted from the submit configuration to the relevant parameters.
    # or we have just passed them in.
    def format( self,
                script,
                project,
                operation,
                job,
                nprocs=None,
                ngpus=None,
                walltime=None,
                memory=None,
                mpicmd=None,
                **kwargs):
        """
        formats script based on the host configuration, submitconf requests,
        operation name, job and other keyword arguments passed from the command line.

        TODO:

        list of names:
            * operation: name of the operation
            * job: handle to the job. {job} will print the job id, you can access *atributes* of the job class by {job.attribute_name}
            * workspace: the path to the workspace directory.
            * statepoint: the statepoint paramters of the job. e.g. you could access the 'pressure' by {statepoint[pressure]}
            * mpicmd: the mpi command from the host configuration if nprocs > 1 otherwise an empty string
            * nprocs: the number of procs requested
            * ngpus: the number of gpus requested
            * memory: the amount memory in MB requested
            * walltime: the amount of time in seconds requested
        """
        #* parameters: the parameters defined by the project. you can access specific parameters
        np = 0 if nprocs is None else nprocs
        ng = 0 if ngpus is None else ngpus
        mem = 0 if memory is None else memory
        walltime = 0 if walltime is None else walltime
        mpi = "" if mpicmd is None else mpicmd.format(nprocs=np);

        fparams = dict(
            project_root=project.root_directory(),
            operation=operation.name,
            job=job,
            workspace=job.workspace(),
            statepoint=job.statepoint(),
            mpicmd=mpi,
            nprocs=np,
            ngpus=ng,
            memory=mem,
            walltime=walltime
        );
        return script.format(**fparams, **kwargs)

# TODO: move this into the project template as an example of how to add
class HoomdScriptFormatter(ScriptFormatter):

    def format(self, script, host, submitconf, operation, job, **kwargs):
        """
        hoomd_mode: --mode={hoomd_mode} where mode is either 'cpu' or 'gpu'
        """
        ng = submitconf.ngpus
        assert ng is not None
        mode='cpu' if ng == 0 else 'gpu'
        return super().format(script.format(hoomd_mode=mode), host, submitconf, operation, job, **kwargs)
