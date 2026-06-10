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
    project_dir = Path(f"/home/claude/{name}")
    _, success = run(f"gh repo create {name} --public")
    if not success:
        return

    project_dir.mkdir()
    run("git init", cwd=project_dir)
    run(f"git remote add origin https://github.com/0x038b5c/{name}.git", cwd=project_dir)
    print("Project created at:", project_dir)

if __name__ == "__main__":
    main()
