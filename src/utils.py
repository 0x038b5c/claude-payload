import subprocess
import tomllib


def run(cmd, successcode=0, **kwargs):
    result = subprocess.run(
        cmd,
        shell=True,
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

def get_settings():
    with open("/mnt/skills/user/settings/SKILL.md") as f:
        lines = f.readlines()

    # remove frontmatter
    lines.reverse()
    lines.pop()
    while lines.pop().strip() != "---":
        pass
    lines.reverse()

    return tomllib.loads("".join(lines))
