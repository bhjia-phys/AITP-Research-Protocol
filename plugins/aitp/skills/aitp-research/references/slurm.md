# Slurm: connect the job to the research question

Use the site's existing environment instructions and the authorization for this
task. Account, partition, QOS, launcher, modules and memory conventions are site
specific. Inspect their current values when needed; examples in old reports are
historical observations. Reading status does not authorize submission or
cancellation. Reuse existing permission rather than requesting it again.

Before a costly run, know its question, distinguishing result, approximate cost
and stopping condition. Use a new run directory within the project's established
calculation location and retain the actual input,
submission script, executable/source location and result location there. Do not
overwrite earlier outputs to reuse a familiar path. Computational work belongs
on resources allowed by the site's policy, ordinarily allocated compute nodes.

Submit the prepared script with `sbatch --parsable job.sbatch` when authorized.
Keep the returned identity (which can include a cluster suffix). Submission
means acceptance by the scheduler, not execution or scientific success.
`#SBATCH` lines are parsed by Slurm, so shell variables inside them are literal;
use valid site values or command-line options. See [sbatch](https://slurm.schedmd.com/sbatch.html).

For an actual known job ID, these read commands are useful starting points:

```sh
squeue -j JOB_ID -o '%.18i %.12T %.40R'
sacct -j JOB_ID --format=JobID,State,ExitCode,Elapsed,MaxRSS
```

Replace `JOB_ID` with the obtained identity. Inspect array tasks and job steps
when a parent state does not explain the calculation. `squeue` describes queued
jobs; accounting availability and retention depend on the site. Consult the
current [squeue](https://slurm.schedmd.com/squeue.html) and
[sacct](https://slurm.schedmd.com/sacct.html) manuals for the needed fields.

Match job, run directory, physical system, configuration and output before
diagnosing. Read the first causal error and relevant numerical summary. Separate
queue/resource limits, input errors, implementation failures, numerical failure
and physical disagreement. A successful exit does not establish convergence.
Do not lower a meaningful tolerance merely to obtain a pass.

An unchanged poll requires no memory edit when the account remains usable.
A failure that changes the diagnosis or a first consequential result belongs in
the relevant research argument, even while the job is unfinished. Link its evidence
and retain the observation time, provisional scope and remaining checks; under
read-only scope, identify the pending integration without editing. Inspect an
existing job after lost observation before considering another submission.
Apply cancellation only to the specifically
authorized jobs. No cluster commands were executed to author this guide.
