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

class HelloWorldOperator(foo.Operator):
    def execute(self, ctx):
        return {
            "message": ctx.params.get("message") + " World!"
        }

class KitchenSinkOperator(foo.Operator):
    def execute(self, ctx):
        return ctx.params

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
        r = requests.post('http://localhost:8080/api/v1/dags/my-fiftyone-compute-embeddings/dagRuns',
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

# An operator that prints the status of an airflow workflow
class MyAirflowStatusOperator(foo.Operator):
    def execute(self, ctx):
        dag_run_id = ctx.params.get('dag_run_id')
        r = requests.get(f'http://localhost:8080/api/v1/dags/my-fiftyone-compute-embeddings/dagRuns/{dag_run_id}',
            auth=airflow_auth)
        result = r.json()
        return {
          'dag_run_id': result['dag_run_id'],
          'state': result['state'],
        }

class CreateSampleFromFileOperator(foo.Operator):
    def resolveInput(self, ctx):
        requests("http://localhost:8080/api/v1/dags/my-fiftyone-compute-embeddings/dagRuns")
        inputs = types.ObjectType()

    def execute(self, ctx):
        dataset = ctx.dataset
        filepath = ctx.params.get("filepath", None)
        sample = fo.Sample(filepath=filepath)
        # add a sample to the dataset
        dataset.add_sample(sample)

        return {
          # return the sample ids
          # this will be passed as the input to the select samples operator
          "samples": {
            "sample_ids": [sample.id]
          }
        }

def register():
    operator = HelloWorldOperator(
        "hello-world",
        "Hello World Operator",
    )
    operator.inputs.define_property("message", types.String())
    operator.outputs.define_property("message", types.String())
    foo.register_operator(operator)

    # kso = KitchenSinkOperator(
    #     "kitchen-sink",
    #     "Kitchen Sink Operator",
    # )
    # kso.inputs.define_property("string", types.String())
    # kso.inputs.define_property("number", types.Number())
    # kso.inputs.define_property("boolean", types.Boolean())
    # kso.inputs.define_property("enum", types.Enum(["a", "b", "c"]))
    # kso.inputs.define_property("list", types.List(types.String()))

    # kso.outputs.define_property("string", types.String())
    # kso.outputs.define_property("number", types.Number())
    # kso.outputs.define_property("boolean", types.Boolean())
    # kso.outputs.define_property("enum", types.Enum(["a", "b", "c"]))
    # kso.outputs.define_property("list", types.List(types.String()))


    # foo.register_operator(kso)

    # trigger = MyAirflowTriggerOperator(
    #     "trigger-compute-embeddings",
    #     "Trigger Compute Embeddings Airflow DAG",
    # )

    # model_names = foz.list_zoo_models()

    # # trigger.inputs.define_property('fiftyone_dataset_name', types.Dataset())
    # # trigger.inputs.define_property('fiftyone_embeddings_field', types.String())
    # # trigger.inputs.define_property('fiftyone_emb_model', types.Enum(model_names))
    # vis_key = trigger.inputs.define_property('fiftyone_vis_brain_key', types.String())
    # trigger.inputs.define_property('fiftyone_sim_brain_key', types.String())
    # trigger.inputs.define_property('fiftyone_sim_model', types.Enum(model_names))
    
    # trigger.outputs.define_property('dag_run_id', types.String())

    # status = MyAirflowStatusOperator(
    #     "my-airflow-status-operator",
    #     "My Airflow Status Operator",
    # )

    # status.inputs.define_property('dag_run_id', types.String())
    # status.outputs.define_property('state', types.Enum(["queued", "running", "success", "failed"]))

    # foo.register_operator(trigger)
    # foo.register_operator(status)

    fileOp = CreateSampleFromFileOperator('create_sample_from_file', 'Create Sample From File')
    # add a parameter to the operator which will be displayed in the UI
    fileOp.inputs.define_property('filepath', types.String())
    #fileOp.allowed_roles =[fo.roles.Admin]
    # add an output property to the operator which tells the UI to execute this operator with the output value
    foo.register_operator(fileOp)

def unregister():
    pass
    # foo.unregister_operator(operator)