# Fluid
Helper functions and class for signac-flow projects.

Signac-Flow the hackable workflow module.

The goal of isn't to 'fix' what isn't 'broken', but hopefully we can improve the flexibility, usability and extensibility. Here are a list of the modules and the purpose for each one:

Project -- Manage the sequence of operations on the data space and the state of each job.
    * Brings together the signac project and the Flow/Operation/Conditions
    * Manages state of eligibility for each job.

Status -- Report the current state of the project and data space.
    * Brings together the Project and the Formatter.

Config -- Specify the configurations of hosts and submissions. Manage/create/modify the environment specific data.
    * Yaml/json/configobj to write out the config
    * CLI to config hosts and alias submissions
    * Should be easy to overload from submit.py command line.

Scheduler -- Provide an interface to the job scheduling environment for both submissions and status queries.
    * Performs the scheduler queries
    * Bring together the Filter, Bundler, Config, Formatters
    * There will be logic here but it will be flexible
    * Remainder for all other command line options

Bundler -- Provide an interface to bundle jobs on to a set of resources.
    * Provide a default bundler that will work for single line job scripts.
    * User can provide a new

Formatter -- Provide an interface to format job scripts (Handler submission or otherwise) and the status output (Formatter).
    * each operation could have a different submission configuration.
    * each user will want to view the job status in a different way.
    * may need to format different commands differently.

Filter -- Provide an interface to filter jobs based on eligibility, parameters, scheduler state, status, include/exclude, labels and have set operations.
    * the filters should be easily combined using the +, * ,^,-,/, operators.
    * a --force option should be able to override these filters.
    * Many different objects know/manage state a Filter will be the way to combine that information.

If these concepts are implemented then I think that we could have a lightweight command line interface to flow. The commands can be overloaded (of course)
* config
* status
* submit
flow config add host flux --pattern flux --type pbs --mpi mpirun
flow config add host {alias} --pattern {pattern} --type {pbs|slurm} --mpi {cmd}
flow config add submit flux.cpu -A sglotzer_fluxoe . . . -V
flow config add submit flux.gpu -A sglotzer1_fluxoe . . . -V
flow config add submit {host_alias}.{sub_alias} [ list of submit arguments ]
flow status --detailed [other options]
flow submit --cpu # this is now required.

The current status:
* Project logic is pretty well flushed out from before combining with my project.
* Status is fine it just needs to be moved out of project into its own module.
* needs to be combined with the Formatter.
* Scheduler has a good start from before needs to be flushed out more fully.
* Bundler is new
* Formatter is new
* Filter is new



Design details still to figure out.
1. how to overload a couple of things like filters and other things

There can be more than one flow project per signac project. classes and commands should be overloadable on the command-line argument level, flow-project level, the signac project level, and global level.

This may seem like a lot but we want to have the most flexibility as possible.

The lookup order will be:
1. global config (maybe later)
2. signac-project config
3. FlowProject class
4. command-line

API thoughts
There is an implicit project sub-command i.e. a command name that is the alias of the flow project. If we have a project named 'example' we can exectute the command,
```
flow example submit . . .
```
This will submit jobs associated with that project based on the eligibility criteria defined in the workflow.

Another syntax is:
```
flow submit -p example . . .
```

Omission will iterate over all projects submitting eligible jobs accordingly.
```
flow submit . . .
```
I think the latter will be easier to implement and there is no reason to make it too much harder on ourselves.


# Go with the flow
here is a brief tutorial example of how I imagine the signac workflow going.

### Creating a project
To start we always assume that any flow project is contained in a signac project. Therefore to start we must initialize the signac project.

```
$ mkdir -p projects/tutorial
$ cd projects/tutorial
$ signac init tutorial && flow init
```

now we have a signac project and a flow project.

```
$ ls
signac.rc tutorial
```
note you can have more than one flow project per signac project.

```
$ flow init another
$ ls
another   signac.rc tutorial
```
Now we have to configure the environment that we want to run on. on a desktop computer this is as simple as making a simple alias for this environment.

```
$ flow config environment desktop
```
You will get a warning that the hostname was used as the pattern. The pattern is a regular expression used to identify the environment configuration. On cluster environments you may want to put "name*" so the same environment is used on any login node.

Aside: this could be done automatically when running flow init. Also this could be done on the global level (not implemented yet) so you can configure the environment on a global level. You can always overload the local configuration later on.

### using flow to execute jobs.
At this point we are ready to create some jobs and run them.
Since we have two projects we must use the ```-p``` option. We can remove this requirement if all of the operations are uniquely named, or cycle through all projects and run that operation if it exists.

```
$ flow run -p tutorial  hello 1a32d14d04eada835d73d898614fcbdf

hello from signac job 1a32d14d04eada835d73d898614fcbdf!
my operation is called 'hello'
my workspace directory is /Users/Paul/Code/test/flow/projects/tutorial/workspace/1a32d14d04eada835d73d898614fcbdf
the value of 'seed' in this statepoint is 42
goodbye!
```

or from the signac project template.

```
$ flow run -p another initialize 1a32d14d04eada835d73d898614fcbdf
```

### submit to cluster environments with flow.
Say we want to submit to a cluster environment here we will just set up *flow* for flux. we start by configuring the enviroment
```
$ flow config environment flux --pattern (nyx|flux).*.umich.edu --mpicmd "mpirun --bind-to none -n {nprocs}" --type pbs
```
It will often times be convenient to setup submission configurations. For example if we just want to run on a single cpu we may define an alias for that submission configuration. The enviroment flux has type pbs so we use the qsub options at the end of the command (if it we slurm we would use sbatch options).

```
flow config submit flux serialCPU -l nodes=1,walltime=24:00:00 -A sglotzer_fluxoe -l gres=cpuslots -l qos=flux -q fluxoe -V
```

Any of the options specified can be changed later by adding the override to the submit command.

```
$ flow submit serialCPU # use the default
```

or

```
$ flow submit serialCPU -l walltime=48:00:00 # jobs need more time.
```


# Goals

1. easy set up.
2. not more than one file.
3. set up submission config 1 cmd
4. hackable submission process.
6. status cmd.

5. run from cmd not required


signac init && flow init
vim projec.py
