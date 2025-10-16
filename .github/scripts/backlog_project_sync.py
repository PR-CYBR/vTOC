#!/usr/bin/env python3
"""Synchronize backlog entries with GitHub Projects v2."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

try:
    import yaml  # type: ignore
except ModuleNotFoundError as exc:  # pragma: no cover - handled at runtime in workflow
    print("::error::PyYAML is required to run backlog sync: {0}".format(exc), file=sys.stderr)
    sys.exit(1)


BACKLOG_FILE = "backlog/backlog.yaml"
PROJECT_TITLE = os.environ.get("PROJECT_NAME", "vTOC-Project-Board")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_API_URL = os.environ.get("GITHUB_API_URL", "https://api.github.com")
REPO = os.environ.get("GITHUB_REPOSITORY", "")
OWNER = os.environ.get("GITHUB_REPOSITORY_OWNER", "")


class SyncError(RuntimeError):
    """Raised when synchronisation cannot proceed."""


@dataclass
class BacklogEntry:
    id: str
    node: Dict[str, object]

    @property
    def project_item_id(self) -> Optional[str]:
        raw = self.node.get("project_item_id")
        if isinstance(raw, str) and raw.strip():
            return raw
        return None

    @project_item_id.setter
    def project_item_id(self, value: str) -> None:
        self.node["project_item_id"] = value

    @property
    def title(self) -> str:
        for key in ("title", "summary", "name"):
            raw = self.node.get(key)
            if isinstance(raw, str) and raw.strip():
                return raw.strip()
        return self.id

    @property
    def body(self) -> Optional[str]:
        for key in ("description", "body", "notes"):
            raw = self.node.get(key)
            if isinstance(raw, str) and raw.strip():
                return raw.strip()
        return None


@dataclass
class ProjectContext:
    project_id: str
    status_field_id: str
    backlog_option_id: str


@dataclass
class SyncReport:
    created_items: List[Tuple[str, str]]  # (backlog id, project item id)
    skipped_items: List[str]


class GraphQLClient:
    def __init__(self, token: str, api_url: str = GITHUB_API_URL) -> None:
        if not token:
            raise SyncError("Missing GitHub token; cannot call GraphQL API")
        self.api_url = api_url.rstrip("/") + "/graphql"
        self.token = token

    def query(self, query: str, variables: Optional[Dict[str, object]] = None) -> Dict[str, object]:
        payload = json.dumps({"query": query, "variables": variables or {}})
        try:
            completed = subprocess.run(
                ["curl", "-fsSL", self.api_url,
                 "-H", f"Authorization: bearer {self.token}",
                 "-H", "Content-Type: application/json"],
                input=payload.encode("utf-8"),
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as exc:
            detail = exc.stderr.decode("utf-8", errors="ignore")
            raise SyncError(f"GraphQL request failed: {detail}") from exc
        try:
            data = json.loads(completed.stdout.decode("utf-8"))
        except json.JSONDecodeError as exc:  # pragma: no cover
            raise SyncError("Invalid JSON response from GitHub GraphQL API") from exc
        if "errors" in data:
            raise SyncError(f"GitHub GraphQL error: {data['errors']}")
        return data["data"]


def load_yaml_from_ref(ref: str) -> object:
    try:
        output = subprocess.check_output(["git", "show", f"{ref}:{BACKLOG_FILE}"], text=True)
    except subprocess.CalledProcessError:
        return []
    return yaml.safe_load(output) or []


def load_yaml_from_worktree(path: str) -> object:
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or []


def collect_entries(node: object) -> List[BacklogEntry]:
    entries: List[BacklogEntry] = []

    def _visit(current: object) -> None:
        if isinstance(current, dict):
            if "id" in current and isinstance(current["id"], str):
                entries.append(BacklogEntry(id=current["id"], node=current))
            for value in current.values():
                _visit(value)
        elif isinstance(current, list):
            for value in current:
                _visit(value)

    _visit(node)
    return entries


def determine_previous_ref() -> Optional[str]:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD^"], text=True).strip()
    except subprocess.CalledProcessError:
        return None


def identify_new_entries(current: Sequence[BacklogEntry], previous: Sequence[BacklogEntry]) -> List[BacklogEntry]:
    previous_ids = {entry.id for entry in previous}
    seen: set[str] = set()
    new_entries: List[BacklogEntry] = []
    for entry in current:
        if entry.id in seen:
            continue
        seen.add(entry.id)
        if entry.id not in previous_ids:
            new_entries.append(entry)
    return new_entries


def resolve_project(client: GraphQLClient, owner: str, repo: str, title: str) -> ProjectContext:
    query = """
    query($owner: String!, $repo: String!, $title: String!) {
      organization(login: $owner) {
        projectsV2(first: 100, query: $title) {
          nodes { id title fields(first: 20) { nodes { ...Field } } }
        }
      }
      user(login: $owner) {
        projectsV2(first: 100, query: $title) {
          nodes { id title fields(first: 20) { nodes { ...Field } } }
        }
      }
      repository(owner: $owner, name: $repo) {
        projectsV2(first: 100, query: $title) {
          nodes { id title fields(first: 20) { nodes { ...Field } } }
        }
      }
    }
    fragment Field on ProjectV2FieldCommon {
      ... on ProjectV2SingleSelectField {
        id
        name
        options(first: 50) { nodes { id name } }
      }
    }
    """
    data = client.query(query, {"owner": owner, "repo": repo, "title": title})

    def _project_nodes(container: Optional[Dict[str, object]]) -> Iterable[Dict[str, object]]:
        if not container:
            return []
        nodes = container.get("projectsV2", {}).get("nodes", []) if isinstance(container, dict) else []
        if isinstance(nodes, list):
            return [node for node in nodes if isinstance(node, dict)]
        return []

    candidates: List[Dict[str, object]] = []
    candidates.extend(_project_nodes(data.get("organization")))
    candidates.extend(_project_nodes(data.get("user")))
    repo_container = data.get("repository")
    if isinstance(repo_container, dict):
        candidates.extend(_project_nodes(repo_container))

    for project in candidates:
        if project.get("title") == title and isinstance(project.get("id"), str):
            fields = project.get("fields", {}).get("nodes", []) if isinstance(project.get("fields"), dict) else []
            if not isinstance(fields, list):
                fields = []
            for field in fields:
                if not isinstance(field, dict):
                    continue
                if field.get("name") == "Status" and isinstance(field.get("id"), str):
                    options = field.get("options", {}).get("nodes", []) if isinstance(field.get("options"), dict) else []
                    if not isinstance(options, list):
                        options = []
                    for option in options:
                        if isinstance(option, dict) and option.get("name") == "Backlog" and isinstance(option.get("id"), str):
                            return ProjectContext(
                                project_id=project["id"],
                                status_field_id=field["id"],
                                backlog_option_id=option["id"],
                            )
    raise SyncError(f"Could not resolve project '{title}' or its Backlog status option")


def create_project_item(client: GraphQLClient, context: ProjectContext, entry: BacklogEntry) -> str:
    mutation = """
    mutation($project: ID!, $title: String!, $body: String) {
      createProjectV2DraftIssue(input: {projectId: $project, title: $title, body: $body}) {
        projectItem { id }
      }
    }
    """
    variables = {"project": context.project_id, "title": entry.title, "body": entry.body}
    data = client.query(mutation, variables)
    draft = data.get("createProjectV2DraftIssue")
    if not isinstance(draft, dict) or not isinstance(draft.get("projectItem"), dict):
        raise SyncError("Draft issue creation response missing project item data")
    item = draft["projectItem"]
    item_id = item.get("id")
    if not isinstance(item_id, str):
        raise SyncError("Project item id not returned from GitHub")

    set_status = """
    mutation($project: ID!, $item: ID!, $field: ID!, $option: ID!) {
      updateProjectV2ItemFieldValue(input: {
        projectId: $project,
        itemId: $item,
        fieldId: $field,
        value: { singleSelectOptionId: $option }
      }) {
        projectV2Item { id }
      }
    }
    """
    client.query(
        set_status,
        {
            "project": context.project_id,
            "item": item_id,
            "field": context.status_field_id,
            "option": context.backlog_option_id,
        },
    )
    return item_id


def run() -> SyncReport:
    if not os.path.exists(BACKLOG_FILE):
        raise SyncError(f"Backlog file '{BACKLOG_FILE}' does not exist")

    current_data = load_yaml_from_worktree(BACKLOG_FILE)
    current_entries = collect_entries(current_data)

    previous_ref = determine_previous_ref()
    if previous_ref:
        previous_data = load_yaml_from_ref(previous_ref)
        previous_entries = collect_entries(previous_data)
    else:
        previous_entries = []

    new_entries = identify_new_entries(current_entries, previous_entries)
    if not new_entries:
        return SyncReport(created_items=[], skipped_items=[])

    client = GraphQLClient(GITHUB_TOKEN or "")
    if not REPO:
        raise SyncError("GITHUB_REPOSITORY is not set")
    if not OWNER:
        raise SyncError("GITHUB_REPOSITORY_OWNER is not set")

    repo_owner, _, repo_name = REPO.partition("/")
    if not repo_name:
        repo_name = REPO
        repo_owner = OWNER

    context = resolve_project(client, owner=repo_owner or OWNER, repo=repo_name, title=PROJECT_TITLE)

    created: List[Tuple[str, str]] = []
    skipped: List[str] = []

    for entry in new_entries:
        if entry.project_item_id:
            skipped.append(entry.id)
            continue
        item_id = create_project_item(client, context, entry)
        entry.project_item_id = item_id
        created.append((entry.id, item_id))

    with open(BACKLOG_FILE, "w", encoding="utf-8") as handle:
        yaml.safe_dump(current_data, handle, sort_keys=False)

    return SyncReport(created_items=created, skipped_items=skipped)


def main() -> None:
    try:
        report = run()
    except SyncError as exc:
        print(f"::error::{exc}")
        sys.exit(1)
    except Exception as exc:  # pragma: no cover - safety net
        print(f"::error::Unexpected failure during backlog sync: {exc}")
        raise

    summary = {
        "created": report.created_items,
        "skipped": report.skipped_items,
    }
    with open(".github/scripts/backlog-sync-report.json", "w", encoding="utf-8") as handle:
        json.dump(summary, handle)

    if report.created_items:
        print(f"::notice::Created {len(report.created_items)} project items: {[item for item, _ in report.created_items]}")
    else:
        print("::notice::No new backlog entries required project items")


if __name__ == "__main__":
    main()
