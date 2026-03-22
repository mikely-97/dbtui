from dbt_tui.backend.cloud import DbtCloudClient, CloudConfig, CloudJob, CloudRun, STATUS_LABELS


def test_cloud_config_defaults():
    config = CloudConfig()
    assert config.base_url == 'https://cloud.getdbt.com/api/v2'
    assert config.api_token == ''


def test_cloud_job_dataclass():
    job = CloudJob(id=1, name='nightly', project_id=1, environment_id=1, state=10)
    assert job.name == 'nightly'


def test_status_labels():
    assert STATUS_LABELS[10] == 'Success'
    assert STATUS_LABELS[20] == 'Error'


def test_cloud_client_instantiates():
    client = DbtCloudClient(CloudConfig(api_token='test', account_id='123'))
    assert client.config.api_token == 'test'
