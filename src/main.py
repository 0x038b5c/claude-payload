"""Claude payload — provisioning entrypoint.

The loader writes exactly one of:
  /opt/account-uuid      (Mode A: fleet/config-driven)
  /opt/github-username   (Mode B: simple/single-account)

This script detects which exists, resolves all settings from config (Mode A)
or derives them from the username (Mode B), then provisions the environment.
"""
from pathlib import Path
import shutil
import tomllib

import click

from src.utils import run, get_settings

AGE_KEY       = Path("/opt/age.key")
SECRETS_DIR   = Path("/opt/secrets")

def _resolve_mode_a(uuid: str) -> dict:
    """Read /opt/claude-config/config.toml and resolve settings for this UUID."""
    config_path = Path("/opt/config/config.toml")
    if not config_path.exists():
        raise RuntimeError(
            f"Mode A: /opt/account-uuid exists but {config_path} is missing. "
            "Did the loader fail to clone claude-config?"
        )
    with open(config_path, "rb") as f:
        config = tomllib.load(f)

    g = config.get("global", {})
    acct = config.get("account", {}).get(uuid, {})

    github_username = acct.get("github_username") or g["github_username"]
    # payload_repo = acct.get("payload_repo") or g["payload_repo"]
    secrets_repo = g["secrets_repo"]
    state_repo = g["state_repo"]
    signing_enabled = acct.get("signing_enabled") if acct.get("signing_enabled") is not None else g.get("signing_enabled", False)
    git_signing_format = g.get("git_signing_format", "gpg")
    github_token_secret = g.get("github_token_secret", "github-token.age")
    signing_key_secret = g.get("signing_key_secret", "signing-key.age")
    git_author_name = g.get("git_author_name", "Claude")
    git_author_email = g.get("git_author_email", "claude@anthropic.com")

    return {
        "github_username": github_username,
        "secrets_repo": secrets_repo,
        "state_repo": state_repo,
        "signing_enabled": signing_enabled,
        "git_signing_format": git_signing_format,
        "github_token_secret": github_token_secret,
        "signing_key_secret": signing_key_secret,
        "git_author_name": git_author_name,
        "git_author_email": git_author_email,
    }


def _resolve_mode_b(github_username: str) -> dict:
    """Derive settings from the username using sensible defaults (Mode B)."""
    return {
        "github_username": github_username,
        "secrets_repo": f"{github_username}/claude-secrets",
        "state_repo": f"{github_username}/claude-state",
        "signing_enabled": False,
        "git_signing_format": "gpg",
        "github_token_secret": "github-token.age",
        "signing_key_secret": "signing-key.age",
        "git_author_name": "Claude",
        "git_author_email": "claude@anthropic.com",
    }


@click.command()
def main():
    print("<provisioning>")

    settings = get_settings()
    account_settings = settings.get("account", {})

    # Detect mode and resolve settings
    if (uuid := account_settings.get("uuid", False)):
        print(f"Mode: A (uuid={uuid})")
        config = _resolve_mode_a(uuid)
    elif (username := account_settings.get("username", False)):
        print(f"Mode: B (username={username})")
        config = _resolve_mode_b(username)
    else:
        raise RuntimeError(
            "Neither account.uuid or account.username found in settings. "
            "The loader did not run correctly."
        )

    github_username = config["github_username"]
    secrets_repo = config["secrets_repo"]
    state_repo = config["state_repo"]
    signing_enabled = config["signing_enabled"]
    git_signing_format = config["git_signing_format"]
    github_token_secret = config["github_token_secret"]
    signing_key_secret = config["signing_key_secret"]
    git_author_name = config["git_author_name"]
    git_author_email = config["git_author_email"]

    print(f"GitHub username: {github_username}")

    # Packages
    run("apt-get update || true")
    packages = ["gh", "age", "openssh-client"]
    if signing_enabled and git_signing_format == "gpg":
        packages.append("gnupg")
    run(f"apt-get install -y {' '.join(packages)}")
    print("Packages:", ", ".join(packages))

    # Python Packages
    python_packages = ["python-frontmatter", "python-slugify", "pyyaml", "pydantic"]
    run(f"pip install {' '.join(python_packages)} --break-system-packages")
    print("Python Packages:", ", ".join(python_packages))

    # Custom binaries
    for file_path in Path("/opt/payload/bin").iterdir():
        name = file_path.name
        shutil.copy2(file_path, f"/usr/local/bin/{name}")
        print(f"Binary: {name}")

    # Decrypt secrets
    run(f"git clone https://github.com/{secrets_repo} {SECRETS_DIR} --depth 1")

    token_age  = SECRETS_DIR / github_token_secret
    token_out  = SECRETS_DIR / "github-token"
    run(f"age -d -i {AGE_KEY} -o {token_out} {token_age}")
    print(f"Decrypted: {github_token_secret} → github-token")

    if signing_enabled:
        signing_age = SECRETS_DIR / signing_key_secret
        signing_out = SECRETS_DIR / "signing-key"
        run(f"age -d -i {AGE_KEY} -o {signing_out} {signing_age}")
        signing_out.chmod(0o600)
        print(f"Decrypted: {signing_key_secret} → signing-key")

    # Git config
    run(f"git config --global user.name \"{git_author_name}\"")
    run(f"git config --global user.email \"{git_author_email}\"")
    print(f"Git author: {git_author_name} <{git_author_email}>")

    if signing_enabled:
        signing_key_path = str(SECRETS_DIR / "signing-key")
        run(f"git config --global user.signingkey {signing_key_path}")
        run(f"git config --global gpg.format {git_signing_format}")
        run("git config --global commit.gpgsign true")
        print(f"Git signing: {git_signing_format}, key={signing_key_path}")

    # Write github_username for tool.py
    Path("/opt/github_username").write_text(github_username)

    # Shell wrappers
    shutil.copy("/opt/payload/bash_profile.sh", "/opt/bash_profile")
    Path("/bin/sh").unlink()
    shutil.copy("/opt/payload/shell_wrapper.sh", "/bin/sh")

    # Clone state
    run(f"git clone https://github.com/{state_repo} /opt/state --depth 1")
    Path("/opt/state/projects").mkdir(exist_ok=True)
    print("State repository: /opt/state")

    print("</provisioning>")
    print()

    # Static context
    print(open("/opt/payload/context.md").read())

    # Dynamic context
    import frontmatter

    print("<dynamic_context>")

    print("<active_sessions>")
    print("\n\n".join([
        f"Session: {(abs_session_path := str(session_path.absolute()))}\n"
        f"Description: {frontmatter.load(abs_session_path)['description']}"
        for session_path in Path("/opt/state/sessions").iterdir()
        if frontmatter.load(session_path).get("active", False)
    ]))
    print("</active_sessions>")

    print("</dynamic_context>")


if __name__ == "__main__":
    main()
