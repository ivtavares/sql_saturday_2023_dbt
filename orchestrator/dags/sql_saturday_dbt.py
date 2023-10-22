from datetime import datetime
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
        raise RuntimeError("The following executions could not be conclued: " + ", ".join(execution_fail))
    
    return "Success"


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
                           "-d sql-saturday; sleep 15s")
    
    start_container_tsk = BashOperator(
        task_id="start_container",
        bash_command=start_container_cmd,
        env={"token": "{{ var.value.DBT_DATABRICKS_TOKEN }}", 
             "host": "{{ var.value.DBT_DATABRICKS_HOST }}",
             "path": "{{ var.value.DBT_DATABRICKS_PATH }}"}
        )

    dbt_run_tsk = PythonOperator(task_id="dbt_run", python_callable=lambda: get_dbt("http://localhost:5000", "run"))
    
    dbt_test_tsk = PythonOperator(task_id="dbt_test", python_callable=lambda: get_dbt("http://localhost:5000", "test"))
    
    stop_container_tsk = BashOperator(
        task_id="stop_container",
        bash_command="docker container stop {{ task_instance.xcom_pull(task_ids='generate_container_name', key='return_value') }}",
        trigger_rule="all_done") 

    @task(task_id="test_dbt_status")
    def test_dbt_status(**context):
        dbt_run_success = context['ti'].xcom_pull(key="return_value", task_ids="dbt_run")
        dbt_test_success = context['ti'].xcom_pull(key="return_value", task_ids="dbt_test")
        
        assert dbt_run_success == "Success", "dbt_run task did not succeed"
        assert dbt_test_success == "Success", "dbt_test task did not succeed"
        
    test_dbt_status_tsk = test_dbt_status()
    
    generate_container_name_tsk >> start_container_tsk >> dbt_run_tsk >> dbt_test_tsk  >> stop_container_tsk >> test_dbt_status_tsk
    dbt_run_tsk >> stop_container_tsk >> test_dbt_status_tsk
