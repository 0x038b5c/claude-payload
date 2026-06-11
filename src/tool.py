from pathlib import Path

import click
import subprocess

def run(cmd, successcode=0, **kwargs):
    result = subprocess.run(
        cmd,
        shell=True,
        check=True,
        text=True,
        capture_output=True,
        **kwargs
    )

    success = result.returncode == successcode

    if not success:
        print("ERROR Running:", cmd)
        print("stderr:")
        print(result.stderr)
        print("stdout:")
        print(result.stdout)

    return result, success


@click.group()
def main():
    ...

@main.group()
def project():
    ...

@project.command()
@click.argument("name")
def new(name):
    import json

    project_dir = Path(f"/home/claude/{name}")

    _, success = run(f"gh repo create {name} --public")
    if not success:
        return

    project_dir.mkdir()
    (project_dir / ".claude").mkdir()
    (project_dir / ".claude" / "notes").mkdir()

    (project_dir / "CLAUDE.md").write_text(f"# {name}\n\n## Structure\n\n## Notes\n")
    (project_dir / ".claude" / "todo.md").write_text(
        "## What I was doing\n\n"
        "## What's done\n\n"
        "## What's in flight\n\n"
        "## What's next\n"
    )

    run("git init -b main", cwd=project_dir)
    run(f"git remote add origin https://github.com/0x038b5c/{name}.git", cwd=project_dir)
    run("git add -A", cwd=project_dir)
    run("git commit -S -m 'init'", cwd=project_dir)
    run("git push -u origin main", cwd=project_dir)

    state = {
        "active": True,
        "project": {
            "name": name,
            "repo": f"https://github.com/0x038b5c/{name}.git",
            "handoff": f"projects/{name}.md",
        }
    }
    state_dir = Path("/opt/state")
    (state_dir / "state.json").write_text(json.dumps(state, indent=4))
    (state_dir / "active.md").write_text(
        f"## What I was doing\nInitialized project {name}\n\n"
        "## What's done\n- Created repository and scaffolded project structure\n\n"
        "## What's in flight\n\n"
        "## What's next\n"
    )
    (state_dir / "projects" / f"{name}.md").write_text(
        f"## {name}\n\nProject initialized.\n"
    )
    run("git add -A", cwd=state_dir)
    run(f"git commit -S -m 'init project state: {name}'", cwd=state_dir)
    run("git push", cwd=state_dir)

    print(f"Project created at: {project_dir}")

if __name__ == "__main__":
    main()
