## PYTHON.NET
## WINDOWS ONLY!

from Deadline.Events import DeadlineEventListener
from Deadline.Jobs import Job

import sys
import socket
import re
import subprocess

PROC_TASKS = R"C:\Windows\System32\tasklist.exe"
DLINE = R"C:\Program Files\Thinkbox\Deadline10\bin\deadlinecommand.exe"
PROC_NV = R"C:\Windows\System32\nvidia-smi.exe"
PROC_KILL = R"C:\Windows\System32\taskkill"

def get_process_running(process: str) -> bool:
    result = subprocess.run(PROC_TASKS,capture_output=True,text=True)
    text_out = result.stdout
    return process in text_out


def kill_process(process: str):
    # force kill
    subprocess.run(f"{PROC_KILL} /f /im \"{process}\"")


def get_gpu_util() -> int:
    args = "--format=csv --query-gpu=utilization.gpu"
    out = subprocess.run(f"{PROC_NV} {args}",capture_output=True,text=True)
    value = (out.stdout.split("\n")[1]).split(" ")[0]
    return int(value)


def get_worker(worker_name):
    p = subprocess.run(f"{DLINE} -GetSlave {worker_name}", capture_output=True,text=True)
    stdout = p.stdout
    return stdout


def get_job_task(job_id, task_id):
    p = subprocess.run(f"{DLINE} -GetJobTask {job_id} {task_id}", capture_output=True,text=True)
    stdout = p.stdout
    return stdout


def get_render_task():
    host = socket.gethostname()
    jobid = None
    taskids = None
    
    worker_info = get_worker(host)
    match_job = re.search(r'^CurrentJobId=([0-9a-z]*)\s*$', worker_info, flags=re.M)
    match_task = re.search(r'^CurrentTaskIds=([\d,]*)\s*$', worker_info, flags=re.M)
    if match_job and match_task:
        jobid = match_job.group(1) or None
        taskids = match_task.group(1).split(',')
        
        if jobid and taskids:
            return jobid, taskids[0]
        
    return None, None


class ProcessManagerEvent(DeadlineEventListener):
    def __init__(self):
        super().__init__()
        self.OnSlaveStartingJobCallback += self.OnSlaveStartingJob

    def OnSlaveStartingJob(self, string, job: Job):
        if sys.platform != "win32":
            self.LogStdout("INTERCEPT_PROCESS: NOT RUNNING ON WINDOWS")
            return
        
        self.LogStdout("TASK START: CHECKING PROCESS PRESENCE")
        job_id, task_id = get_render_task()
        if job_id is None:
            job_id = job.JobId
            task_id = 0

        settings = self.get_configs()

        self.LogStdout(f"[JOB : TASK] {job_id} : {task_id}")
        if (job_id, task_id) != (None, None):
            if get_process_running(settings['proc']):
                self.LogStdout(f"DETECTED {settings['proc']}! @ {socket.gethostname()}")
                
                if settings['action'] == "Bounce":
                    # if set to kill on higher priority task, handle that first.
                    if settings['killonprio']:
                        if job.JobPriority > settings['priotresh']:
                            self.LogStdout(f"DETECTED ACTIVE {settings['proc']} JOB, INCOMING JOB HAS HIGHER PRIORITY, KILLING PROCESS!")
                            kill_process(settings["proc"])
                            return
                    
                    # bounce job if GPU utilization exceeds limit
                    if get_gpu_util() > settings['gpulimit']:
                        self.LogStdout(f"DETECTED ACTIVE {settings['proc']} JOB, REQUEUEING TASK!")
                        subprocess.run(f"{DLINE} -RequeueJobTask {job_id} {task_id}")
                     
                elif settings['action'] == "Kill":
                    # if default action is to kill the process no matter what, kill it. No mercy.
                    kill_process(settings["proc"])

    def Cleanup(self):
        del self.OnSlaveStartingJobCallback

    def get_configs(self):
        Process = self.GetConfigEntry("Process")
        GPU_limit = int(self.GetConfigEntryWithDefault("GPU_limit",40))
        KillOnPriority = bool(self.GetConfigEntry("KillOnPriority"))
        Priority_threshold = int(self.GetConfigEntry("Priority_threshold"))
        Action = self.GetConfigEntryWithDefault("Action","Bounce") # Either "Bounce" or "Kill"
        return {"proc" : Process, 
                "gpulimit" : GPU_limit,
                "killonprio": KillOnPriority,
                "priotresh" : Priority_threshold,
                "action" : Action}
        
    
def GetDeadlineEventListener():
    return ProcessManagerEvent()

def CleanupDeadlineEventListener(deadlinePlugin: ProcessManagerEvent):
    deadlinePlugin.Cleanup()        