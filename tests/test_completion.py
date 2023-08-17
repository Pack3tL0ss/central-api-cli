import subprocess
from typing import List, Union

from cli import app  # type: ignore # NoQA
from typer.testing import CliRunner
from centralcli import cache

runner = CliRunner()

# TODO make this work
# work in progress based on https://stackoverflow.com/questions/9137245/unit-test-for-bash-completion-script
# need to see of typer command runner has a function to test completion

# NEVER GOT THIS TO WORK TEST COMPLETION DIRECT TO THE CACHE COMPLETION FUNCS
# completion_function = r"""
# _cencli_completion() {
#     local IFS=$'
# '
#     COMPREPLY=( $( env COMP_WORDS="${COMP_WORDS[*]}" \
#                    COMP_CWORD=$COMP_CWORD \
#                    _CENCLI_COMPLETE=complete_bash $1 ) )
#     return 0
# }

# complete -o default -F _cencli_completion cencli

# """


# def test_caas_send_cmds_completion(cmd_base: Union[str, List[str]] = ["cencli", "caas", "send-cmds", "group"], incomplete: str = "Bra"):
#     # result = runner.invoke(app, [
#     #     "caas",
#     #     "send-cmds",
#     #     "group",
#     #     "Br",
#     #     "-Y"
#     #     ])
#     # assert result.exit_code == 0
#     # assert "Success" in result.stdout
#     cmd_base = cmd_base if isinstance(cmd_base, list) else cmd_base.split()
#     completion_file="~/.bash_completions/cencli.sh"
#     cmd = cmd_base + [incomplete]
#     cmdline = ' '.join(cmd)
#     print(f"Sending command: {cmdline}")
#     # full_cmdline=r'source {comp_file};COMP_LINE="{cmdline}"; COMP_WORDS=({cmdline}) COMP_CWORD={cword} COMP_POINT={cmdlen}; $(complete -p {program} | sed "s/.*-F \\([^ ]*\\) .*/\\1/") && echo ${{COMPREPLY[*]}}'.format(
#     full_cmdline=r'source {comp_file};COMP_LINE="{cmdline}"; COMP_WORDS=({cmdline}); COMP_CWORD={cword}; COMP_POINT={cmdlen}; $(complete -p {program}) && echo ${{COMPREPLY[*]}}'.format(
#         comp_file=completion_file,
#         completion_function=completion_function,
#         cmdline=cmdline,
#         cmdlen=len(cmdline),
#         program=cmd[0],
#         cword=cmd.index(incomplete)
#     )
#     print(f"Instructions being sent to shell:\n{full_cmdline}")

#     out = subprocess.Popen(['bash', '-i', '-c', full_cmdline], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#     stdout, stderr = out.communicate()
#     _ = [print(line) for line in [*stdout.decode("utf-8").split(), *stderr.decode("utf-8").split()]]
#     pass
#     # self.assertEqual(stdout, "Branch1\n")

# test_caas_send_cmds_completion()

        # r'{completion_function} COMP_LINE="{cmdline}" COMP_WORDS=({cmdline}) COMP_CWORD={cword} COMP_POINT={cmdlen} $(complete -p {cmd} | sed "s/.*-F \\([^ ]*\\) .*/\\1/") && echo ${{COMPREPLY[*]}}'.format(
        #     completion_function=completion_function, cmdline=cmdline, cmdlen=len(cmdline), cmd=cmd[0], cword=cmd.index(incomplete)
        #     )

        # r'source {completion_file}; COMP_LINE="{cmdline}" COMP_WORDS=({cmdline}) COMP_CWORD={cword} COMP_POINT={cmdlen} $(complete -p {cmd} | sed "s/.*-F \\([^ ]*\\) .*/\\1/") && echo ${{COMPREPLY[*]}}'.format(
            # completion_file=completion_file, cmdline=cmdline, cmdlen=len(cmdline), cmd=cmd[0], cword=cmd.index(partial_word)

    # full_cmdline=r'{completion_function}COMP_LINE="{cmdline}"; COMP_WORDS=({cmdline}) COMP_CWORD={cword} COMP_POINT={cmdlen}; $(complete -p {program} | sed "s/.*-F \\([^ ]*\\) .*/\\1/") && echo ${{COMPREPLY[*]}}'.format(

# full commands variables replaced with values for direct testing in bash to see if we can get this working
# source ~/.bash_completions/cencli.sh;COMP_LINE="cencli caas send-cmds group Bra"; COMP_WORDS=(cencli caas send-cmds group Bra); COMP_CWORD=4; COMP_POINT=31; $(complete -p cencli) && echo ${COMPREPLY[*]}

# this relies on one of my aliases showvars
# source ~/.bash_completions/cencli.sh;export COMP_LINE="cencli caas send-cmds group Bra";export COMP_WORDS=(cencli caas send-cmds group Bra);export COMP_CWORD=4;export COMP_POINT=31;$(complete -p cencli) ; showvars | grep COMP

# TODO dynamically get available devices
def test_dev_completion(incomplete: str = "bsmt"):
    result = [c for c in cache.dev_completion(incomplete)]
    assert len(result) > 0
    assert all(incomplete in c if isinstance(c, str) else c[0] for c in result)

def test_dev_completion_case_insensitive(incomplete: str = "BSmT"):
    result = [c for c in cache.dev_completion(incomplete)]
    assert len(result) > 0
    assert all([m.lower().startswith(incomplete.lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])

def test_dev_ap_gw_completion(incomplete: str = "ant"):
    result = [c for c in cache.dev_ap_gw_completion(incomplete, ["show", "overlay", "summary"])]
    assert len(result) > 0
    assert all([m.lower().startswith(incomplete.lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])

def test_group_completion(incomplete: str = ""):
    result = [c for c in cache.group_completion(incomplete)]
    assert len(result) > 0
    assert all(incomplete in c if isinstance(c, str) else c[0] for c in result)

def test_group_completion_case_insensitive(incomplete: str = "w"):
    result = [c for c in cache.group_completion(incomplete)]
    assert len(result) > 0
    assert all([m.lower().startswith(incomplete.lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])

def test_dev_site_completion(incomplete: str = ""):
    result = [c for c in cache.dev_site_completion(incomplete, ("show", "vlans",))]
    assert len(result) > 0
    assert all([m.lower().startswith(incomplete.lower()) for m in [c if isinstance(c, str) else c[0] for c in result]])