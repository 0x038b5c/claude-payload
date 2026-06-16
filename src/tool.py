from pathlib import Path

import click
import frontmatter

from src.utils import run

GITHUB_USERNAME = Path("/opt/github_username").read_text().strip()


@click.group()
def main():
    ...

@main.group()
def project():
    ...

@project.command()
@click.argument("name")
@click.option("--dir", default=None)
def new(name, project_dir):
    project_dir = Path(project_dir) if project_dir else Path(f"/home/claude/{name}")

    _, success = run(f"gh repo create {name} --public")
    if not success:
        return

    project_dir.mkdir(parents=True, exist_ok=True)

    run("git init -b master", cwd=project_dir)
    run(f"git remote add origin https://github.com/{GITHUB_USERNAME}/{name}.git", cwd=project_dir)

    state_dir = Path("/opt/state")

    (state_dir / "projects" / f"{name}.md").write_text(
        f"## {name}\n\nProject initialized.\n"
    )
    run("git add -A", cwd=state_dir)
    run(f"git commit -S -m 'init project state: {name}'", cwd=state_dir)
    run("git push", cwd=state_dir)

    print(f"Project created at: {project_dir}")

@main.group()
def session():
    ...

@session.command()
def list():
    print("\n\n".join([
        f"Session: {session_file.absolute()}\n"
        f"Active: {(session := frontmatter.load(str(session_file.absolute())))["active"]}\n"
        f"Description: {session["description"]}"
        for session_file in Path("/opt/state/sessions").iterdir()
    ]))


@main.group()
def state():
    ...

@state.command()
@click.option("--repo", required=True, type=click.Path(), help="Absolute path to the repository")
@click.option("--file", "file_path", required=True, help="Path to the file, relative to repo root")
@click.option("--message", "-m", required=True, help="Commit message")
@click.argument("content", default="-", type=click.File("r"))
def atomic_write(repo, file_path, message, content):
    repo_dir = Path(repo)
    target = repo_dir / file_path

    if not repo_dir.exists():
        print("Project doesn't exist, creating")
        new(repo_dir.name, repo_dir) # new project

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content.read())

    _, add_ok = run(f"git add {file_path}", cwd=repo_dir)
    if not add_ok:
        target.unlink(missing_ok=True)
        print("ERROR: git add failed, file removed")
        return

    _, commit_ok = run(f"git commit -S -m '{message}'", cwd=repo_dir)
    if not commit_ok:
        print("ERROR: git commit failed")
        return

    _, push_ok = run("git push", cwd=repo_dir)
    if not push_ok:
        print("ERROR: git push failed — commit exists locally but was not pushed")
        return

    print(f"OK: {file_path} written, committed, and pushed")


if __name__ == "__main__":
    main()
