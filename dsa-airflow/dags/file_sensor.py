import os
from datetime import datetime
import pandas as pd
import statistics
from statistics import mode
from airflow import DAG
from airflow.decorators import dag, task
from airflow.sensors.filesystem import FileSensor
from airflow.hooks.filesystem import FSHook


# global variable for votes file name
VOTES_FILE_NAME = 'votes.csv'


@task
def filter_valid_votes():
    """
    read votes file from a CSV, filters valid votes, and returns a list

    This function uses an Airflow FileSystem Connection called "data_fs" as the root folder
    to look for the votes file. Make sure this FileSystem connection exists
    """
    # get the data_fs filesystem root path
    data_fs = FSHook(conn_id='data_fs')     # get airflow connection for data_fs
    data_dir = data_fs.get_path()           # get its root path
    print(f"data_fs root path: {data_dir}")

    # create the full path to the votes file
    file_path = os.path.join(data_dir, VOTES_FILE_NAME)
    print(f"reading file: {file_path}")

    # read csv
    votes = pd.read_csv(file_path)
    valid_votes_df = votes[votes.isin(["lemon", "vanilla", "chocolate", "pistachio", "strawberry", "confetti", "caramel", "pumpkin", "rose"])].dropna()
    valid_votes = valid_votes_df['votes'].tolist()
    
    return valid_votes

@task
def class_choice(votes: list):
    """
    takes a list of ice cream flavors and prints the flavor that is chosen the most.
    """
    print(mode(votes))


@dag(
    schedule_interval="@once",
    start_date=datetime.utcnow(),
    catchup=False,
    default_view='graph',
    is_paused_upon_creation=True,
    tags=['dsa', 'dsa-example'],
)
def favorite_ice_cream():
    """Example of using FileSensors and FileSystem Connections"""

    # define the file sensor...
    # wait for the votes file in the "data_fs" filesystem connection
    wait_for_file = FileSensor(
        task_id='wait_for_file',
        poke_interval=15,                   # check every 15 seconds
        timeout=(30 * 60),                  # timeout after 30 minutes
        mode='poke',                        # mode: poke, reschedule
        filepath=VOTES_FILE_NAME,        # file path to check (relative to fs_conn)
        fs_conn_id='data_fs',               # file system connection (root path)
    )

    # read the file
    valid_votes_task = filter_valid_votes()

    #print the class choice
    class_choice__task = class_choice(valid_votes_task)
    
    # orchestrate tasks
    wait_for_file >> valid_votes_task >> class_choice__task


# create the dag
dag = favorite_ice_cream()