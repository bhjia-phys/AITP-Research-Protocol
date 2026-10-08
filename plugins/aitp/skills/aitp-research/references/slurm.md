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

## Estimate resources before submitting

Estimate memory and time for an expensive run by scaling the closest comparable completed
run with the method's scaling and the implementation's distribution; the field's
[domain methods](../SKILL.md#domain-methods) give known scalings. Compare the estimate with any recorded failure: agreement
supports both the estimate and that reading of the failure. Record what each measurement
covers: step, task or node scope, units and parallel layout. `MaxRSS` is the largest
single task's resident memory, not a multi-task node peak, and it excludes GPU memory;
with one task per node it is the largest node's resident memory for that step. Use node
or device measurements where available, account for replicated allocations, and treat
missing accounting as unknown. A question about a measurement's scope qualifies an
estimate; it does not replace it. When unsure, run a pilot that exercises the suspected
peak allocation at the target settings. Record the estimate and the measurement in the
run report, so that an overrun corrects the next estimate.

When a report that the current decision relies on is shown to be ambiguous or misread,
by its layout or another measurement, add a dated note beside it; do not reword the
original record. A caveat that is only suspected, or that applies to several reports,
goes in the reply or the plan rather than into each report.

## Many jobs, several sites

Keep each job's run directory and report, so that a status request can assemble them;
no separate tracking file is needed. Record the site, the job or array identity and the
run directory in the report at submission. Site profiles, such as accounts, partitions, GPU
or CPU nodes, memory per node and queue habits, belong in the workspace's environment
instructions.

## Restart, resubmit or change resources

Before resubmitting, read the failed job's first causal error and check for a
checkpoint. Resume from a checkpoint when the code supports it and the inputs are
unchanged. Moving between GPU and CPU or changing the parallel layout requires
confirming that the code supports the target and that a small case agrees; record the
change in the run report.

## Record state changes

An unchanged poll requires no memory edit when the account remains usable.
A failure that changes the diagnosis or a first consequential result belongs in
the relevant research argument, even while the job is unfinished. Link its evidence
and retain the observation time, provisional scope and remaining checks; under
read-only scope, identify the pending integration without editing. Inspect an
existing job after lost observation before considering another submission.
Apply cancellation only to the specifically
authorized jobs. No cluster commands were executed to author this guide.
