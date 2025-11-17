"""Utilities for summarizing commits and optionally posting discussions.

Exit codes:
    0: Success.
    2: Unable to gather git metadata or diffs.
    3: Failed to read repository context files.
    4: Code/Codex CLI invocation failed.
    5: Unable to normalize CLI response.
    6: Failed to write summary output file.
    7: Discussion posting failed.

The script is designed for GitHub Actions automation. It runs a Code/Codex CLI
prompt using repository context and the base/head commits, saving the output for
subsequent workflow steps.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

try:
    import requests
except ImportError:  # pragma: no cover - requests should be available, but fallback to urllib
    requests = None
    import urllib.request
    import urllib.error


DEFAULT_CONTEXT_FILES = ["README.md", "docs/IMPLEMENTATION_SUMMARY.md"]
DEFAULT_MAX_PROMPT_CHARS = 12000
DEFAULT_OUTPUT_FILE = "summary.md"
DEFAULT_MODEL = "gpt-4.1"


@dataclass
class GitMetadata:
    commits: str
    diff: str


def run_git_command(args: Sequence[str]) -> str:
    """Run a git command and return stdout or raise on failure."""
    try:
        completed = subprocess.run(
            ["git", *args],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as exc:  # pragma: no cover - passthrough
        sys.stderr.write(f"Git command failed: {' '.join(exc.cmd)}\n{exc.stderr}\n")
        raise
    return completed.stdout.strip()


def gather_git_metadata(base: str, head: str, max_diff_chars: int) -> GitMetadata:
    """Collect commit metadata and diff information between base and head."""
    try:
        log_output = run_git_command(
            [
                "log",
                "--format=%H%x1f%an%x1f%ae%x1f%ad%x1f%s",
                f"{base}..{head}",
            ]
        )
        diff_output = run_git_command(
            ["diff", "--unified=0", f"{base}..{head}"]
        )
    except subprocess.CalledProcessError as exc:
        raise SystemExit(2) from exc

    commits = []
    if log_output:
        for line in log_output.splitlines():
            parts = line.split("\x1f")
            if len(parts) != 5:
                continue
            commit_sha, author, email, date, subject = parts
            commits.append(
                f"- {subject} ({commit_sha[:7]}) by {author} <{email}> on {date}"
            )
    commit_section = "\n".join(commits) if commits else "- No new commits detected."

    trimmed_diff = trim_text(diff_output, max_diff_chars)
    return GitMetadata(commits=commit_section, diff=trimmed_diff)


def trim_text(text: str, max_chars: int) -> str:
    """Trim text to fit within a character limit while preserving chunk boundaries."""
    if len(text) <= max_chars:
        return text
    segments: List[str] = []
    current = 0
    while current < len(text) and len("\n\n".join(segments)) < max_chars:
        chunk = text[current : current + 1000]
        segments.append(chunk)
        current += 1000
        if len("".join(segments)) >= max_chars:
            break
    trimmed = "".join(segments)
    remaining = len(text) - len(trimmed)
    return f"{trimmed}\n...\n[diff truncated, {remaining} additional characters omitted]"


def read_context_files(context_files: Iterable[str]) -> str:
    contents: List[str] = []
    for file_path in context_files:
        path = Path(file_path)
        if not path.exists():
            continue
        try:
            contents.append(f"# {path}\n{path.read_text()}\n")
        except OSError as exc:
            sys.stderr.write(f"Unable to read context file {path}: {exc}\n")
            raise SystemExit(3) from exc
    return "\n".join(contents)


def build_prompt(
    repo: str,
    base: str,
    head: str,
    metadata: GitMetadata,
    context: str,
) -> str:
    prompt_sections = [
        "You are assisting with generating a pull request discussion summary.",
        f"Repository: {repo}",
        f"Base Commit: {base}",
        f"Head Commit: {head}",
        "\n## Repository Context\n",
        context or "(No additional context provided.)",
        "\n## Commit Summary\n",
        metadata.commits,
        "\n## Diff (trimmed)\n",
        metadata.diff or "(No diff available.)",
        "\nPlease provide:\n",
        "1. Overview of the changes.\n2. Key files touched.\n3. Potential follow-up tasks.",
    ]
    return "\n".join(section.strip("\n") for section in prompt_sections)


def determine_cli_path() -> str:
    env = os.environ
    path = env.get("CODEX_BIN") or env.get("code") or "codex"
    return path


def invoke_cli(cli_path: str, model: str, prompt: str) -> str:
    env = os.environ.copy()
    api_key = env.get("CODEX_API_KEY")
    if api_key:
        env.setdefault("CODEX_API_KEY", api_key)

    try:
        completed = subprocess.run(
            [cli_path, "chat", "--model", model, "--input", prompt],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
    except FileNotFoundError as exc:
        sys.stderr.write(f"Code/Codex CLI not found at {cli_path}: {exc}\n")
        raise SystemExit(4) from exc
    except subprocess.CalledProcessError as exc:
        sys.stderr.write(
            "Code/Codex CLI failed with exit code "
            f"{exc.returncode}: {exc.stderr}\n"
        )
        raise SystemExit(4) from exc
    return completed.stdout.strip()


def normalize_cli_output(cli_response: str) -> str:
    if not cli_response:
        raise SystemExit(5)

    sections = {"Overview": [], "Key Files": [], "Follow-ups": []}
    current_key = None

    for line in cli_response.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            heading = stripped[3:].strip()
            if heading.lower().startswith("overview"):
                current_key = "Overview"
            elif heading.lower().startswith("key"):
                current_key = "Key Files"
            elif "follow" in heading.lower():
                current_key = "Follow-ups"
            else:
                current_key = None
            continue
        if current_key:
            sections[current_key].append(stripped)
        else:
            sections["Overview"].append(stripped)

    normalized_lines: List[str] = []
    for heading, lines in sections.items():
        normalized_lines.append(f"## {heading}")
        content = "\n".join(line for line in lines if line)
        normalized_lines.append(content or "(No details provided.)")
        normalized_lines.append("")

    normalized_text = "\n".join(normalized_lines).strip()
    if not normalized_text:
        raise SystemExit(5)
    return normalized_text


def write_summary(output_path: str, content: str) -> None:
    try:
        Path(output_path).write_text(content)
    except OSError as exc:
        sys.stderr.write(f"Failed to write summary output: {exc}\n")
        raise SystemExit(6) from exc


def post_discussion(
    repo: str,
    discussion_category_id: str,
    title: str,
    body: str,
) -> str:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.stderr.write("GITHUB_TOKEN is required when --post is set.\n")
        raise SystemExit(7)

    try:
        owner, name = repo.split("/", 1)
    except ValueError as exc:
        sys.stderr.write(
            "Repository must be provided as 'owner/name' when --post is set.\n"
        )
        raise SystemExit(7) from exc
    headers = {
        "Authorization": f"bearer {token}",
        "Content-Type": "application/json",
    }

    if requests:
        session = requests.Session()
        graphql_url = "https://api.github.com/graphql"

        repo_query = {
            "query": "query($owner:String!, $name:String!){repository(owner:$owner,name:$name){id}}",
            "variables": {"owner": owner, "name": name},
        }
        repo_response = session.post(
            graphql_url, headers=headers, data=json.dumps(repo_query)
        )
        if repo_response.status_code != 200:
            sys.stderr.write(
                f"Failed to fetch repository id: {repo_response.status_code} "
                f"{repo_response.text}\n"
            )
            raise SystemExit(7)
        repo_json = repo_response.json()
        repo_id = repo_json.get("data", {}).get("repository", {}).get("id")
        if not repo_id:
            sys.stderr.write(
                f"Repository ID not found in response: {repo_response.text}\n"
            )
            raise SystemExit(7)

        mutation = {
            "query": (
                "mutation($repoId:ID!,$catId:ID!,$title:String!,$body:String!)"
                "{createDiscussion(input:{repositoryId:$repoId,categoryId:$catId,"
                "title:$title,body:$body}){discussion{id url}}}"
            ),
            "variables": {
                "repoId": repo_id,
                "catId": discussion_category_id,
                "title": title,
                "body": body,
            },
        }
        mutation_response = session.post(
            graphql_url, headers=headers, data=json.dumps(mutation)
        )
        if mutation_response.status_code != 200:
            sys.stderr.write(
                "Failed to create discussion: "
                f"{mutation_response.status_code} {mutation_response.text}\n"
            )
            raise SystemExit(7)
        mutation_json = mutation_response.json()
        discussion = mutation_json.get("data", {}).get("createDiscussion", {}).get(
            "discussion", {}
        )
        if not discussion:
            sys.stderr.write(
                f"Discussion creation failed: {mutation_response.text}\n"
            )
            raise SystemExit(7)
        return discussion.get("url", "")

    # Fallback using urllib
    graphql_url = "https://api.github.com/graphql"
    payload = json.dumps(
        {
            "query": "query($owner:String!, $name:String!){repository(owner:$owner,name:$name){id}}",
            "variables": {"owner": owner, "name": name},
        }
    ).encode()
    request = urllib.request.Request(graphql_url, data=payload, headers=headers)
    try:
        with urllib.request.urlopen(request) as response:
            repo_json = json.loads(response.read().decode())
    except urllib.error.URLError as exc:  # pragma: no cover
        sys.stderr.write(f"Failed to fetch repository id: {exc}\n")
        raise SystemExit(7) from exc
    repo_id = repo_json.get("data", {}).get("repository", {}).get("id")
    if not repo_id:
        sys.stderr.write(f"Repository ID missing in response: {repo_json}\n")
        raise SystemExit(7)

    mutation_payload = json.dumps(
        {
            "query": (
                "mutation($repoId:ID!,$catId:ID!,$title:String!,$body:String!)"
                "{createDiscussion(input:{repositoryId:$repoId,categoryId:$catId,"
                "title:$title,body:$body}){discussion{id url}}}"
            ),
            "variables": {
                "repoId": repo_id,
                "catId": discussion_category_id,
                "title": title,
                "body": body,
            },
        }
    ).encode()
    mutation_request = urllib.request.Request(
        graphql_url, data=mutation_payload, headers=headers
    )
    try:
        with urllib.request.urlopen(mutation_request) as response:
            mutation_json = json.loads(response.read().decode())
    except urllib.error.URLError as exc:  # pragma: no cover
        sys.stderr.write(f"Failed to create discussion: {exc}\n")
        raise SystemExit(7) from exc
    discussion = mutation_json.get("data", {}).get("createDiscussion", {}).get(
        "discussion", {}
    )
    if not discussion:
        sys.stderr.write(f"Discussion creation failed: {mutation_json}\n")
        raise SystemExit(7)
    return discussion.get("url", "")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate commit summary prompts")
    parser.add_argument("--base", required=True, help="Base commit SHA or ref")
    parser.add_argument("--head", required=True, help="Head commit SHA or ref")
    parser.add_argument("--repo", required=True, help="Repository in owner/name form")
    parser.add_argument(
        "--discussion-category-id",
        required=True,
        help="GitHub discussion category identifier",
    )
    parser.add_argument(
        "--context-file",
        action="append",
        default=[],
        help="Additional context files to include in the prompt",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Model name for the Code/Codex CLI",
    )
    parser.add_argument(
        "--max-prompt-chars",
        type=int,
        default=DEFAULT_MAX_PROMPT_CHARS,
        help="Maximum characters allowed for diff context in the prompt",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT_FILE,
        help="File path to write the normalized summary",
    )
    parser.add_argument(
        "--title",
        default="Automated Change Summary",
        help="Title for the generated discussion",
    )
    parser.add_argument(
        "--post",
        action="store_true",
        help="Post the summary directly to GitHub discussions",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])

    context_files = DEFAULT_CONTEXT_FILES + args.context_file
    context = read_context_files(context_files)

    metadata = gather_git_metadata(args.base, args.head, args.max_prompt_chars)

    prompt = build_prompt(args.repo, args.base, args.head, metadata, context)

    cli_path = determine_cli_path()
    cli_response = invoke_cli(cli_path, args.model, prompt)

    normalized = normalize_cli_output(cli_response)

    write_summary(args.output, normalized)

    print(normalized)

    if args.post:
        url = post_discussion(
            repo=args.repo,
            discussion_category_id=args.discussion_category_id,
            title=args.title,
            body=normalized,
        )
        if url:
            print(f"Discussion created: {url}")

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
