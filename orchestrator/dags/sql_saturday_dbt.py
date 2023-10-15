from datetime import datetime
import re
import uuid

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import task, PythonOperator
import requests


def get_dbt(url: str, route: str):
    complete_url = url + '/' + route
    r = requests.get(url=complete_url)
    execution_success = list()
    execution_fail = list()
    
    for execution in r.json():
        if execution["status"] in {"success", "pass"}:
            execution_success.append(execution["name"])
        else:
            execution_fail.append(execution["name"])
    
    print("The following execution could be concluded: " + ", ".join(execution_success))
    
    if len(execution_fail) > 0:
        failed_execution_names = [execution["name"] for execution in execution_fail]
        raise RuntimeError("The following executions could not be conclued: " + ", ".join(failed_execution_names))


with DAG("sql-saturday-dbt",
         description="The DBT project used as an example in the SQL Saturday Event",
         start_date=datetime(2023, 1, 1),
         catchup=False) as dag:
    
    generate_container_name_tsk = PythonOperator(task_id='generate_container_name',
                                                 python_callable= lambda: "sql-saturday-" + str(uuid.uuid4()))
    
    start_container_cmd = ("docker run "
                           "-e DBT_TOKEN=$token "
                           "-e DBT_HOST=$host "
                           "-e DBT_PATH=$path "
                           "-p 5000:5000 "
                           "--name {{ task_instance.xcom_pull(task_ids='generate_container_name', key='return_value') }} "
                           "-d sql-saturday; sleep 5s")
    
    start_container_tsk = BashOperator(
        task_id="start_container",
        bash_command=start_container_cmd,
        env={"token": "{{ var.value.DBT_DATABRICKS_TOKEN }}", 
             "host": "{{ var.value.DBT_DATABRICKS_HOST }}",
             "path": "{{ var.value.DBT_DATABRICKS_PATH }}"}
        )

    dbt_run = PythonOperator(task_id="dbt_run", python_callable=lambda: get_dbt("http://localhost:5000", "run"))
    
    dbt_test = PythonOperator(task_id="dbt_test", python_callable=lambda: get_dbt("http://localhost:5000", "test"))
    
    stop_container_tsk = BashOperator(
        task_id="stop_container",
        bash_command="docker container stop {{ task_instance.xcom_pull(task_ids='generate_container_name', key='return_value') }}") 

    
    generate_container_name_tsk >> start_container_tsk >> dbt_run >> dbt_test >> stop_container_tsk 
    
