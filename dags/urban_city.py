from datetime import datetime, timedelta

from airflow import DAG
from airflow.sdk import task


from airflow.providers.microsoft.azure.operators.data_factory import (
    AzureDataFactoryRunPipelineOperator,
)

from scripts.upload_raw_data import upload_data
from scripts.transform import transform


default_args = {
    "owner": "urban_city",
    "depends_on_past": False,
    "start_date": datetime(2026, 9, 23),
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}


@task()
def extract_data_from_csv():
    api_response = upload_data()
    return api_response


@task()
def transform_data():
    cleaned_data = transform()
    return cleaned_data


run_adf_pipeline = AzureDataFactoryRunPipelineOperator(
    task_id="run_adf_pipeline",
    pipeline_name="PL_Silver_To_Gold",
    resource_group_name="data_engineering_dev",
    factory_name="urbancityADF",
    azure_data_factory_conn_id="azure_data_factory",
    wait_for_termination=True,
)


with DAG(
    dag_id="urban_city_service_request",
    catchup=False,
    schedule="@hourly",
    default_args=default_args,
) as dag:

    extract_data_from_csv() >> transform_data() >> run_adf_pipeline