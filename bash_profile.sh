# sourced every invocation of bash_tool
export GH_TOKEN=$(cat /opt/secrets/github-token)
export GIT_TERMINAL_PROMPT=0
export GIT_ASKPASS=/opt/payload/git_askpass.sh
