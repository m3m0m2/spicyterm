#!/usr/bin/python

"""
  This is intended ONLY as a 1st of April Joke to a friend using ssh/bash
  the maxim goes: jokes can be fun as long as they are not over done

  This script will update the active terminals of a user to some random colors 
  every 5 seconds.

  # optional setproctitle used to disguise the process name
  sudo -H pip install -r requirements.txt
  or alternatively
  sudo -H pip install setproctitle

  run interctively as:
  # ./spicyterm.py -u <user1> [-u <user2>]
  Ctrl-C when bored should reset term to default state

  alternatively can be detached like:
  sudo bash
  # ./spicyterm.py -u <user> > /dev/null
  ctrl-z
  bg
  jobs
  # take note of <job#>, usually will be 1
  disown -h %<job#>
  exit

  later clean stop with:
  sudo kill -INT <PID>
"""

import subprocess
import random
import time
import sys
import signal
import argparse
import os


running = True

def signal_handler(sig, frame):
    global running
    running = False

# change argv[0] to disguise on ps if possible
def set_proc_name(newname):
    import setproctitle
    setproctitle.setproctitle(newname)

# change also cwd
def obfuscate():
    try:
        os.chdir('/')
        set_proc_name('linux')
    except:
        pass


# parse idle times returned by w like:
# 2days
# 10:23m
# 50.0s
def parse_time(s):
    if 'day' in s:
        s = s.split('day')[0]
        return float(s) * 24*3600
    if 's' in s:
        s = s.split('s')[0]
        return float(s)
    if 'm' in s:
        s = s.split('m')[0]
        fields = s.split(':')
        return float(fields[0])*3600 + float(fields[1])*60
    else:
        fields = s.split(':')
        return float(fields[0])*60 + float(fields[1])


def active_user_terms(users, max_idle):
    ttys = []
    process = subprocess.Popen(['w', '-sh'], stdout=subprocess.PIPE)
    (stdoutdata, stderrdata) = process.communicate()
    for line in stdoutdata.rstrip().split('\n'):
        fields = line.split()
        user, tty, idle = fields[0], fields[1], fields[3]
        if parse_time(idle) > max_idle:
            continue
        # empty users = everyone
        if len(users) > 0 and not user in users:
            continue

        print("Spicying {0}'s terminal: {1}, idle: {2}".format(user, tty, idle))
        ttys.append(tty)
    return ttys


def send_ctrl(tty, ctrls):
    if len(ctrls) == 0:
        # reset
        ctrls = [ 0 ]
    s=';'.join([str(_) for _ in ctrls])
    f = open("/dev/" + tty, "w")
    f.write("\x1B[0;{0}m".format(s))
    f.close()


def rand_ctrl(tty):
    """
    https://misc.flogisoft.com/bash/tip_colors_and_formatting

    1-8: bold, dim, underlined, blink, reverse, hidden
    30-37, 90-97 foreground
    40-47, 100-107 background
    """
    c1 = random.randint(1,8)
    c2 = random.randint(30,45)
    if c2 > 37:
        c2 += 90 - 38
    c3 = random.randint(40,55)
    if c2 > 47:
        c2 += 100 - 48

    send_ctrl(tty, [c1, c2, c3])


def run(args):
    while running:
        ttys = active_user_terms(args.users, args.idle)
        
        for tty in ttys:
            rand_ctrl(tty)

        time.sleep(5)
    send_ctrl(tty, [])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Spicy Term Colors.')
    parser.add_argument('-i', '--idle', type=int, default=1800, help='max term idle time')
    parser.add_argument('-u', '--users', action='append', default=[], help='users')
    args = parser.parse_args()
    args.users = set(args.users)

    obfuscate()
    signal.signal(signal.SIGINT, signal_handler)
    run(args)
