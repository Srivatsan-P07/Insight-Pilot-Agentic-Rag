"""GCP Authentication utilities — uses Application Default Credentials (ADC).

Run `gcloud auth application-default login` once on your machine; this module
picks up those credentials automatically for all GCP API calls.
"""
from __future__ import annotations

from typing import Optional

import google.auth
import google.auth.exceptions


def get_credentials():
    """Return (credentials, project_id) from ADC."""
    try:
        credentials, project = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        return credentials, project
    except google.auth.exceptions.DefaultCredentialsError:
        return None, None


def get_current_project() -> Optional[str]:
    """Return the default project ID set in ADC."""
    _, project = get_credentials()
    return project


def list_projects() -> list[dict]:
    """
    List all active GCP projects accessible via ADC.

    Falls back to the single ADC default project when the Resource Manager
    API is unavailable or returns no results.
    """
    try:
        from google.cloud import resourcemanager_v3

        client = resourcemanager_v3.ProjectsClient()
        projects: list[dict] = []
        for p in client.search_projects(query="state:ACTIVE"):
            projects.append(
                {
                    "project_id": p.project_id,
                    "display_name": p.display_name or p.project_id,
                    "name": p.name,
                    "state": p.state.name,
                }
            )
        if projects:
            return sorted(projects, key=lambda x: x["display_name"].lower())
    except Exception:
        pass

    # Fallback: single project from ADC environment
    _, project_id = get_credentials()
    if project_id:
        return [
            {
                "project_id": project_id,
                "display_name": project_id,
                "name": f"projects/{project_id}",
                "state": "ACTIVE",
            }
        ]
    return []
