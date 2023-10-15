from functools import partial

from dbt.cli.main import dbtRunner, dbtRunnerResult
from flask import Flask

# initialize
# https://docs.getdbt.com/docs/core/connect-data-platform/postgres-setup
# https://docs.getdbt.com/reference/programmatic-invocations


def dbt_run_args(*cli_args: str):
    dbt = dbtRunner()

    # create CLI args as a list of strings
    cli_args = list(cli_args)
    res: dbtRunnerResult = dbt.invoke(cli_args)

    # # return the results
    return [{"name": r.node.name, "status": r.status} for r in res.result] 


app = Flask(__name__)

dbt_endpoint_list = [
    {"route": "/", "cmd": lambda: "<p>Hello, SQL Saturday!!</p>"},
    {"route": "/run", "cmd": lambda: dbt_run_args("run")},
    {"route": "/build", "cmd": lambda: dbt_run_args("build")},
    {"route": "/seed", "cmd": lambda: dbt_run_args("seed")},
    {"route": "/test", "cmd": lambda: dbt_run_args("test")},
    ]
    
for dbt_endpoint in dbt_endpoint_list:
    app.add_url_rule(dbt_endpoint["route"], endpoint=dbt_endpoint["route"], view_func=dbt_endpoint["cmd"])
