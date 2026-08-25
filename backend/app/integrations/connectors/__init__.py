from app.integrations.connectors.github import github_connector
from app.integrations.connectors.gitlab import gitlab_connector
from app.integrations.connectors.email import email_connector
from app.integrations.connectors.calendar import calendar_connector
from app.integrations.connectors.storage import storage_connector
from app.integrations.connectors.cloud import cloud_connector
from app.integrations.connectors.database import database_connector
from app.integrations.connectors.docker import docker_connector
from app.integrations.connectors.kubernetes import kubernetes_connector
from app.integrations.connectors.ci_cd import ci_cd_connector
from app.integrations.connectors.monitoring import monitoring_connector
from app.integrations.connectors.slack import slack_connector
from app.integrations.connectors.discord import discord_connector
from app.integrations.connectors.remote_exec import remote_exec_connector
from app.integrations.connectors.generic_api import generic_api_gateway

ALL_CONNECTORS = [
    github_connector,
    gitlab_connector,
    email_connector,
    calendar_connector,
    storage_connector,
    cloud_connector,
    database_connector,
    docker_connector,
    kubernetes_connector,
    ci_cd_connector,
    monitoring_connector,
    slack_connector,
    discord_connector,
    remote_exec_connector,
    generic_api_gateway,
]

__all__ = [
    "github_connector",
    "gitlab_connector",
    "email_connector",
    "calendar_connector",
    "storage_connector",
    "cloud_connector",
    "database_connector",
    "docker_connector",
    "kubernetes_connector",
    "ci_cd_connector",
    "monitoring_connector",
    "slack_connector",
    "discord_connector",
    "remote_exec_connector",
    "generic_api_gateway",
    "ALL_CONNECTORS",
]
