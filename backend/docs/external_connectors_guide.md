# Universal Agentic AI — External Connectors Reference

## 1. Registered External Connectors

The system provides 15 standardized external connectors under `app.integrations.connectors`:

| Connector | Provider | Capabilities | Auth Methods |
| :--- | :--- | :--- | :--- |
| `github` | GitHub | `create_pull_request`, `review_pull_request`, `create_issue`, `merge_pull_request` | `oauth2`, `personal_access_token` |
| `gitlab` | GitLab | `list_projects`, `create_merge_request`, `trigger_pipeline` | `oauth2`, `personal_access_token` |
| `email` | Email Gateway | `draft_message`, `send_message`, `search_messages` | `oauth2`, `smtp_credentials` |
| `calendar` | Calendar Gateway | `list_events`, `find_free_time`, `create_event` | `oauth2`, `service_account` |
| `storage` | Cloud Storage | `list_files`, `upload_file`, `download_file`, `delete_file` | `aws_iam`, `gcp_sa`, `azure_sas` |
| `cloud` | Cloud Providers | `list_instances`, `get_metrics`, `query_logs` | `iam_role`, `service_account` |
| `database` | SQL / NoSQL | `execute_query`, `inspect_schema`, `begin_transaction` | `connection_string`, `iam_auth` |
| `docker` | Docker Daemon | `run_container`, `build_image`, `read_logs`, `stop_container` | `local_socket`, `tls_certs` |
| `kubernetes`| Kubernetes API | `list_pods`, `get_pod_logs`, `apply_manifest` | `kubeconfig`, `sa_token` |
| `ci_cd` | CI / CD | `trigger_pipeline`, `get_pipeline_status` | `api_token`, `webhook_secret` |
| `monitoring`| Observability | `query_logs`, `query_metrics`, `get_alert`, `create_incident` | `api_key`, `bearer_token` |
| `slack` | Slack | `read_channel`, `send_message`, `create_thread` | `oauth2`, `bot_token` |
| `discord` | Discord | `read_channel`, `send_message` | `bot_token`, `webhook_url` |
| `remote_exec`| Remote SSH | `connect_host`, `execute_command`, `disconnect_host` | `ssh_key`, `certificate` |
| `generic_api`| REST / GraphQL | `send_http_request`, `send_graphql_query` | `bearer_token`, `api_key`, `mtls` |
