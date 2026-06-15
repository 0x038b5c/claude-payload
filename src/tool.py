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
def new(name):
    project_dir = Path(f"/home/claude/{name}")

    _, success = run(f"gh repo create {name} --public")
    if not success:
        return

    project_dir.mkdir()

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

if __name__ == "__main__":
    main()

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
