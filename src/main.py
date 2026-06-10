from pathlib import Path

import shutil
import subprocess

def run(cmd, **kwargs):
    return subprocess.run(
        cmd,
        shell=True,
        check=True,
        text=True,
        capture_output=True,
        **kwargs
    )

def main():
    # install binaries
    for path in Path("/opt/payload/bin").iterdir():
        if not path.is_file():
            continue

        print("Installing binary:", path.name)
        shutil.copy2(
            path,
            "/usr/local/bin",
        )

    # clone secrets
    run("git clone https://github.com/0x038b5c/claude-secrets /opt/secrets --depth 1")

    # decrypt and install github token
    gh_pat = run("rage -d -i /opt/age.key /opt/secrets/github-token.age").stdout
    with open("/opt/secrets/github-token", "w") as token:
        token.write(gh_pat)

    # install git-credentials
    with open("/root/.git-credentials", "w") as git_creds:
        git_creds.write(f"https://0x038b5c:{gh_pat}@github.com")

    # decrypt git signing key
    run("rage -d -i /opt/age.key /opt/secrets/signing-key.age -o /opt/secrets/signing-key")

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

if __name__ == "__main__":
    main()
