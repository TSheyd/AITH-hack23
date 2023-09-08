import os
import sqlite3

from redis import Redis
from rq import Worker, Queue, Connection
from rq.job import Job
from time import time

from copy import deepcopy


from tg_bot import launch_bot, send_notification


from Main import MarkerFinder




path = f'{os.path.abspath(os.curdir)}/'


def main_loop(redis_conn, r_queue):
    with sqlite3.connect(f"{path}tg/jobs.db") as con:
        cur_jobs = set()
        j2t = {'a':'D4S0ze0DLmGda1qILCDUdA_16941326687502'}
        while True:
            cur = con.cursor()
            cur.execute(
                "SELECT job_confirmed, job_token, filename, n_obs, start_time FROM jobs WHERE job_confirmed=1 AND START_TIME IS NULL;")
            table = cur.fetchall()
            for row in table:
                _token = row[1]
                _time = int(time())
                job = r_queue.enqueue(MarkerFinder,
                                      f"./data/{_token}.csv",
                                      "condition",
                                      50,
                                      float(row[3]),
                                      100,
                                      f"./data/{_token}_stat.txt",
                                      f"./data/{_token}_hm.txt")
                cur_jobs.add(job.id)
                j2t[job.id]=_token
                cur.execute("UPDATE jobs SET start_time=? WHERE job_token=?", (_time, _token))
                con.commit()
            cur_jobs_copy = deepcopy(cur_jobs)
            for job_id in cur_jobs_copy:
                # Get the job by its ID (use the job ID printed in enqueue_job.py)
                job = Job.fetch(str(job_id), connection=redis_conn)
                _token = j2t[job_id]
                flag = True
                # Check the job status
                if job.is_finished:
                    result = job.return_value()  # Get the result of the finished job
                    print(f"Job Result: {result}")
                elif job.is_failed:
                    print("Job failed")
                else:
                    flag = False
                if not flag:
                    continue
                cur_jobs.remove(job_id)
                cur.execute("UPDATE jobs SET end_time=? WHERE job_token=?",
                            (int(time()), _token,))
                cur.execute("UPDATE jobs SET notification_sent=1 WHERE job_token=?",
                            (_token,))

                con.commit()
                # sending only one message at a time, may proof with ORDER BY id DESC LIMIT 1
                cur.execute("SELECT user_id, filename FROM jobs WHERE job_token=?",
                            (_token,))
                user_id, filename = cur.fetchone()
                send_notification(user_id, filename, _token)




if __name__ == '__main__':
    # Timer(1, open_browser).start()
    redis_conn = Redis(host='localhost', port=6379, db=0)
    ping_response = redis_conn.ping()
    print(f"Redis Ping Response: {ping_response}")
    # Create a worker for the "default" queue with the specified connection
    queue = Queue(connection=redis_conn)
    queue.enqueue(launch_bot)
    main_loop(redis_conn, queue)
