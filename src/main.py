from pathlib import Path

import json
import shutil
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

def main():
    print("Provisioning Claude's environment")

    # install packages
    packages = ["gh", "age", "openssh-client"]
    run(f"apt-get install -y {' '.join(packages)}")
    print("Installing packages:", ", ".join(packages))

    # install tool
    shutil.copy2("/opt/payload/bin/tool", "/usr/local/bin/tool")
    print("Installing binary: tool")

    # clone secrets
    run("git clone https://github.com/0x038b5c/claude-secrets /opt/secrets --depth 1")

    # decrypt github token
    run("age -d -i /opt/age.key -o /opt/secrets/github-token /opt/secrets/github-token.age")

    # decrypt git signing key
    run("age -d -i /opt/age.key -o /opt/secrets/signing-key /opt/secrets/signing-key.age")
    Path("/opt/secrets/signing-key").chmod(0o600)

    # configure git
    run("git config --global user.name Claude")
    run("git config --global user.email claude@anthropic.com")
    run("git config --global user.signingkey /opt/secrets/signing-key")
    run("git config --global gpg.format ssh")
    print(
        "git's user.name, "
        "user.email, "
        "user.signingkey, "
        "and gpg.format, "
        "have been set."
    )

    # install bash_profile
    shutil.copy(
        "/opt/payload/bash_profile.sh",
        "/opt/bash_profile",
    )

    # install bash wrapper
    Path("/bin/sh").unlink()
    shutil.copy(
        "/opt/payload/shell_wrapper.sh",
        "/bin/sh",
    )

    # clone state
    run("git clone https://github.com/0x038b5c/claude-state /opt/state --depth 1")
    print("Your state repository is stored at /opt/state")

    # tell claude its github name
    print("Your GitHub account username is: 0x038b5c")

    # inject static context
    print("Static context:")
    print(open("/opt/payload/context.md").read())
    print()

    print("Dynamic context:")

    # inject active task context
    if (
        (state_file := Path("/opt/state/state.json")).exists()
        and (state := json.loads(state_file.read_text())).get("active")
    ):
        if (project := state.get("project")) is not None:
            print("The previously active task was using a project")
            print("Project name:", project["name"])
            print("Project repository:", project["repo"])
            print("Project handoff file:", f"/opt/state/{project["handoff"]}")
            print()

        print("Previously active task context (active.md):")
        print(open("/opt/state/active.md").read())
    else:
        print("No active task")

if __name__ == "__main__":
    main()
