# Pre-reqs
This assumes you are ssh'd into a Raspberry Pi that already has the latest cosmobot image on it. 

# Usage
To use this code to run an experiment on a Raspberry Pi:
1. Navigate to where this repo is installed on the Pi:
```
pi@pi-cam-CF60:~ $ cd cosmobot-run-experiment/
pi@pi-cam-CF60:~/cosmobot-run-experiment $
```

2. Get the latest code (as appropriate) using git pull:
```
pi@pi-cam-CF60:~/cosmobot-run-experiment $ git pull
```

3. Install the python package:
```
sudo python3.6 setup.py install
```

(If this fails with an error about setuptools, you may need to pip install setuptools first:
    ```
    pi@pi-cam-CF60:~/cosmobot-run-experiment $ pip3.6 install setuptools
    ```
)

4. Run your experiment using the `run_experiment` console script, passing in appropriate args. To see which arguments are available:
```
pi@pi-cam-CF60:~/cosmobot-run-experiment $ run_experiment --help
```

Images will be saved in the `~/camera-sensor-output` folder and automatically synced to s3
