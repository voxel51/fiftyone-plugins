import fiftyone.operators as foo
import fiftyone.operators.types as types
import fiftyone as fo
import fiftyone.brain as fob
import requests
from requests.auth import HTTPBasicAuth
import os
import fiftyone.zoo as foz

AIRFLOW_USERNAME = os.environ.get('AIRFLOW_USERNAME')
AIRFLOW_PASSWORD = os.environ.get('AIRFLOW_PASSWORD')

airflow_auth = HTTPBasicAuth(AIRFLOW_USERNAME, AIRFLOW_PASSWORD)

class MyAirflowTriggerOperator(foo.Operator):
    def execute(self, ctx):
        # NOTE: the folowing params are available, but are just passed along to the airflow api
        # dataset_name = ctx.params.get('fiftyone_dataset_name')
        # embeddings_field = ctx.params.get('fiftyone_embeddings_field')
        # vis_brain_key = ctx.params.get('fiftyone_vis_brain_key')
        # sim_model = ctx.params.get('fiftyone_sim_model')
        # emb_model = ctx.params.get('fiftyone_emb_model')
        view_param = {'fiftyone_view_stages': ctx.view._serialize(), 'fiftyone_dataset_name': ctx.dataset_name}
        airflow_params = {**view_param, **ctx.params}

        # trigger the "my-example-dag: defined in airflow.py
        r = requests.post('http://localhost:8080/api/v1/dags/my-fiftyone-compute-similarity/dagRuns',
            json={
                "conf": airflow_params
            },
            auth=airflow_auth)

        result = r.json()

        ctx.save()

        print(result)
        return {
          'dag_run_id': result['dag_run_id'],
        }

class MyAirflowStatusOperator(foo.Operator):
    def execute(self, ctx):
        dag_run_id = ctx.params.get('dag_run_id')
        r = requests.get(f'http://localhost:8080/api/v1/dags/my-fiftyone-compute-similarity/dagRuns/{dag_run_id}',
            auth=airflow_auth)
        result = r.json()
        return {
          'dag_run_id': result['dag_run_id'],
          'state': result['state'],
        }

trigger = None
status = None

def register():
    trigger = MyAirflowTriggerOperator(
        "trigger-compute-embeddings",
        "Trigger Compute Similarity Airflow DAG",
    )

    model_names = foz.list_zoo_models()

    trigger.inputs.define_property('fiftyone_sim_brain_key', types.String())
    trigger.inputs.define_property('fiftyone_sim_model', types.Enum(model_names))
    
    trigger.outputs.define_property('dag_run_id', types.String())

    status = MyAirflowStatusOperator(
        "my-airflow-status-operator",
        "My Airflow Status Operator",
    )

    status.inputs.define_property('dag_run_id', types.String())
    status.outputs.define_property('state', types.Enum(["queued", "running", "success", "failed"]))

    foo.register_operator(trigger)
    foo.register_operator(status)


def unregister():
    foo.unregister_operator(trigger)
    foo.unregister_operator(status)