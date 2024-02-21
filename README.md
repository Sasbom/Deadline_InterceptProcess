# Deadline - Intercept Process
Event plugin for Thinkbox Deadline that intercepts a process in various ways.
#### Big note: Currently works only on nodes that run Windows. 

To use this plugin, place the "intercept_events" folder inside [REPOSITORY]/events or [REPOSITORY]/custom/events

This event plugin was created to manage stray, unmanagable tasks in a deadline network. It can be used in a variety of ways, killing a task outright, letting it be rescheduled if a certain windows process was detected, or either killing the process/ rescheduling a task if the process has a priority set.

This plugin's reason for coming into existence was that at one point, a farm I managed had to contest with an Octane daemon network, and bounce jobs when the daemon service was active, for it was deemed to be of higher priority. I don't want, for example, a Cycles GPU or Redshift job to be submitted and go through, while Octane is also running. 

I expanded the functionality to be able to kill the specified task, but keep in mind that the plugin can NOT revive the task after it has killed it. A competing service would have to be created, seperately from deadline, to revive it if in turn Deadline is not busy.

Much love, Sas
