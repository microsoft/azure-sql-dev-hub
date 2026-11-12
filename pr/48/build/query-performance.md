## Evidence first

The starter turns on IO and timing statistics so the session reports logical
reads and CPU for whatever you run next. That number is the baseline: without
it, a tuning change is a guess with confidence. Run the query, keep the output,
then look at the actual execution plan for the operator that carries the cost.

Azure SQL Database keeps history for you. Query Store records plans and
runtime stats over time, and Query Performance Insight in the portal surfaces
the top CPU and IO consumers without any setup. The
[monitoring and tuning overview](https://learn.microsoft.com/azure/azure-sql/database/monitor-tune-overview)
maps which tool answers which question, from DMVs for a live incident to
automatic tuning for recurring plan regressions.

The scenario prompt asks the agent for the smallest safe change. That framing
is deliberate: one index or one rewritten predicate you can measure beats a
handful of speculative changes you cannot attribute.
