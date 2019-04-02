# Usage

For full setup and usage details, see the [Cosmobot Instruction Manual](https://docs.google.com/document/d/1ZYK24QlmTyvdBJlXioD8hm90TbwAEc02sMYBzOlQnoU/edit)

## Pre-reqs
This assumes you are ssh'd into a Raspberry Pi that already has the latest cosmobot image on it (with Python 3.6 already installed).

## SSH
Do this by finding the IP of the pi and ssh pi@[IP]
```
you@yourlaptop ~ $ ssh pi@[IP]
```

## Setup
Depending on what image you have, this might already be done for you.

### Clone repo
Clone git repo if it hasn't already been cloned.

Check if it has been cloned - try to cd to `~/cosmobot-run-experiment`. If it doesn't exist you will get an error like:
```
pi@pi-cam-CF60:~ $ cd ~/cosmobot-run-experiment
-bash: cd: /home/pi/cosmobot-run-experiment: No such file or directory
```

If not, clone the repo:
```
pi@pi-cam-CF60:~ $ cd ~/
pi@pi-cam-CF60:~ $ git clone git@github.com:OsmoSystems/cosmobot-run-experiment.git
```

### Install package
To use this code to run an experiment on a Raspberry Pi:
1. Navigate to where this repo is installed on the Pi:
```
pi@pi-cam-CF60:~ $ cd ~/cosmobot-run-experiment/
pi@pi-cam-CF60:~/cosmobot-run-experiment $
```

2. Get the latest code (as appropriate) using git pull:
```
pi@pi-cam-CF60:~/cosmobot-run-experiment $ git pull
```

3. Install the python package. The `-e` makes it installed "editable", which means that if you later pull new changes in to the repo, they should be automatically picked up.
```
sudo pip3.6 install -e .
```

## Run
Run your experiment using the `run_experiment` console script, passing in appropriate args (use --help to see available args).
```
pi@pi-cam-CF60:~ $ run_experiment --help
```

Images will be saved in the `~/camera-sensor-output` folder and automatically synced to s3.
