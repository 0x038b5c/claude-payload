from pathlib import Path

import json
import shutil

from src.utils import run

def main():
    # provisioning logs wrapped so they read as a distinct block
    print("<provisioning>")

    run("apt-get update || true")
    packages = ["gh", "age", "openssh-client"]
    run(f"apt-get install -y {' '.join(packages)}")
    print("Packages:", ", ".join(packages))

    shutil.copy2("/opt/payload/bin/tool", "/usr/local/bin/tool")
    print("Binary: tool")

    run("git clone https://github.com/0x038b5c/claude-secrets /opt/secrets --depth 1")
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

    run("git clone https://github.com/0x038b5c/claude-state /opt/state --depth 1")
    Path("/opt/state/projects").mkdir(exist_ok=True)
    print("State repository: /opt/state")
    print("GitHub username: 0x038b5c")

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
