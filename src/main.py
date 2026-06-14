from pathlib import Path

import json
import shutil

import click

from src.utils import run


@click.command()
@click.argument("github_username")
def main(github_username: str):
    # provisioning logs wrapped so they read as a distinct block
    print("<provisioning>")

    run("apt-get update || true")
    packages = ["gh", "age", "openssh-client"]
    run(f"apt-get install -y {' '.join(packages)}")
    print("Packages:", ", ".join(packages))

    shutil.copy2("/opt/payload/bin/tool", "/usr/local/bin/tool")
    print("Binary: tool")

    run(f"git clone https://github.com/{github_username}/claude-secrets /opt/secrets --depth 1")
    run("age -d -i /opt/age.key -o /opt/secrets/github-token /opt/secrets/github-token.age")
    run("age -d -i /opt/age.key -o /opt/secrets/signing-key /opt/secrets/signing-key.age")
    Path("/opt/secrets/signing-key").chmod(0o600)

    run("git config --global user.name Claude")
    run("git config --global user.email claude@anthropic.com")
    run("git config --global user.signingkey /opt/secrets/signing-key")
    run("git config --global gpg.format ssh")
    print("Git: user.name, user.email, user.signingkey, gpg.format configured")

    shutil.copy("/opt/payload/bash_profile.sh", "/opt/bash_profile")
    Path("/bin/sh").unlink()
    shutil.copy("/opt/payload/shell_wrapper.sh", "/bin/sh")

    # Write github_username so tool.py can read it without re-parsing argv
    Path("/opt/github_username").write_text(github_username)

    run(f"git clone https://github.com/{github_username}/claude-state /opt/state --depth 1")
    Path("/opt/state/projects").mkdir(exist_ok=True)
    print("State repository: /opt/state")
    print(f"GitHub username: {github_username}")

    print("</provisioning>")
    print()

    # static context
    print(open("/opt/payload/context.md").read())

    # dynamic context
    print("<dynamic_context>")

    if (
        (state_file := Path("/opt/state/state.json")).exists()
        and (state := json.loads(state_file.read_text())).get("active")
    ):
        if (project := state.get("project")) is not None:
            print("<active_project>")
            print("name:", project["name"])
            print("repo:", project["repo"])
            print("handoff:", f"/opt/state/{project['handoff']}")
            print("</active_project>")
            print()

        print("<active_task>")
        print(open("/opt/state/active.md").read())
        print("</active_task>")
    else:
        print("No active task.")

    print("</dynamic_context>")


if __name__ == "__main__":
    main()
