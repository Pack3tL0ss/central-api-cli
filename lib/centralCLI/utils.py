#!/usr/bin/env python3

import string
import subprocess
import shlex
import time
import os
import sys
import yaml
# import stat
# import grp
import json
# import threading
import socket
from io import StringIO
from halo import Halo
from tabulate import tabulate
from pygments import highlight, lexers, formatters

try:
    loc_user = os.getlogin()
except Exception:
    loc_user = os.getenv("SUDO_USER", os.getenv("USER"))

# removed from output and placed at top (provided with each item returned)
CUST_KEYS = ["customer_id", "customer_name"]


class Convert:
    def __init__(self, mac):
        self.orig = mac
        if not mac:
            mac = '0'
        self.clean = ''.join([c for c in list(mac) if c in string.hexdigits])
        self.ok = True if len(self.clean) == 12 else False
        self.cols = ':'.join(self.clean[i:i+2] for i in range(0, 12, 2))
        self.dashes = '-'.join(self.clean[i:i+2] for i in range(0, 12, 2))
        self.dots = '.'.join(self.clean[i:i+4] for i in range(0, 12, 4))
        self.tag = f"ztp-{self.clean[-4:]}"
        self.dec = int(self.clean, 16) if self.ok else 0


class Mac(Convert):
    def __init__(self, mac):
        super().__init__(mac)
        oobm = hex(self.dec + 1).lstrip('0x')
        self.oobm = Convert(oobm)


class Utils:
    def __init__(self):
        self.Mac = Mac

    def user_input_bool(self, question):
        """Ask User Y/N Question require Y/N answer

        Error and reprompt if user's response is not valid
        Appends '? (y/n): ' to question/prompt provided

        Params:
            question:str, The Question to ask
        Returns:
            answer:bool, Users Response yes=True
        """
        valid_answer = ["yes", "y", "no", "n"]
        try:
            answer = input(question + "? (y/n): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("")  # prevents header printing on same line when in debug
            return False
        while answer.lower() not in valid_answer:
            if answer != "":
                print(
                    f" \033[1;33m!!\033[0m Invalid Response '{answer}' Valid Responses: {valid_answer}"
                )
            answer = input(question + "? (y/n): ").strip()
        if answer[0].lower() == "y":
            return True
        else:
            return False

    def error_handler(self, cmd, stderr, user=loc_user):
        if isinstance(cmd, str):
            cmd = shlex.split(cmd)
        if stderr and "FATAL: cannot lock /dev/" not in stderr:
            # Handle key change Error
            if "WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!" in stderr:
                print(
                    "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n"
                    "@    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @\n"
                    "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n"
                    "IT IS POSSIBLE THAT SOMEONE IS DOING SOMETHING NASTY!\n"
                    "Someone could be eavesdropping on you right now (man-in-the-middle attack)!\n"
                    "It is also possible that a host key has just been changed."
                )
                while True:
                    choice = ""
                    try:
                        choice = input(
                            "\nDo you want to remove the old host key and re-attempt the connection (y/n)? "
                        )
                        if choice.lower() in ["y", "yes"]:
                            _cmd = shlex.split(
                                stderr.replace("\r", "")
                                .split("remove with:\n")[1]
                                .split("\n")[0]
                                .replace("ERROR:   ", "")
                            )  # NoQA
                            _cmd = shlex.split("sudo -u {}".format(user)) + _cmd
                            subprocess.run(_cmd)
                            print("\n")
                            subprocess.run(cmd)
                            break
                        elif choice.lower() in ["n", "no"]:
                            break
                        else:
                            print(
                                "\n!!! Invalid selection {} please try again.\n".format(
                                    choice
                                )
                            )
                    except (KeyboardInterrupt, EOFError):
                        print("")
                        return "Aborted last command based on user input"
                    except ValueError:
                        print(
                            f"\n!! Invalid selection {choice} please try again.\n")
            elif (
                "All keys were skipped because they already exist on the remote system"
                in stderr
            ):
                return "Skipped - key already exists"
            elif "/usr/bin/ssh-copy-id: INFO:" in stderr:
                if "sh: 1:" in stderr:
                    return "".join(stderr.split("sh: 1:")[1:]).strip()
            # ssh cipher suite errors
            elif "no matching cipher found. Their offer:" in stderr:
                print("Connection Error: {}\n".format(stderr))
                cipher = stderr.split("offer:")[1].strip().split(",")
                aes_cipher = [c for c in cipher if "aes" in c]
                if aes_cipher:
                    cipher = aes_cipher[-1]
                else:
                    cipher = cipher[-1]
                cmd += ["-c", cipher]

                print("Reattempting Connection using cipher {}".format(cipher))
                r = subprocess.run(cmd)
                if r.returncode:
                    return "Error on Retry Attempt"  # TODO better way... handle banners... paramiko?
            else:
                return stderr  # return value that was passed in

        # Handle hung sessions always returncode=1 doesn't always present stderr
        elif cmd[0] == "picocom":
            if self.kill_hung_session(cmd[1]):
                subprocess.run(cmd)
            else:
                return "User Abort or Failure to kill existing session to {}".format(
                    cmd[1].replace("/dev/", "")
                )

    def shell_output_cleaner(self, output):
        strip_words = ["/usr/bin/ssh-copy-id: "]
        return "".join(
            [x.replace(i, "") for x in self.listify(output) for i in strip_words]
        )

    def do_shell_cmd(
        self,
        cmd,
        do_print=False,
        handle_errors=True,
        return_stdout=False,
        tee_stderr=False,
        timeout=5,
        shell=False,
        **kwargs,
    ):
        """Runs shell cmd (i.e. ssh) returns stderr if any by default

        Arguments:
            cmd {str|list} -- commands/args sent to subprocess

        Keyword Arguments:
            do_print {bool} -- Print stderr after cmd completes (default: {False})
            handle_errors {bool} -- Send stderr to error_handler (default: {True})
            return_stdout {bool} -- run with shell and return tuple returncode, stdout, stderr (default: {False})
            tee_stderr {bool} -- stderr is displayed and captured (default: {False})
            timeout {int} -- subprocess timeout (default: {5})
            shell {bool} -- run cmd as shell (default: {True})

        Returns:
            {str|tuple} -- By default there is no return unless there is an error.
            return_stdout=True will return tuple returncode, stdout, stderr
        """
        if return_stdout:
            res = subprocess.run(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                **kwargs,
            )
            return res.returncode, res.stdout.strip(), res.stderr.strip()
        elif shell:
            res = subprocess.run(
                cmd,
                shell=True,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                **kwargs,
            )
            if res.stderr:
                return (
                    res.stderr
                    if not handle_errors
                    else self.error_handler(cmd, res.stderr)
                )

        else:
            if isinstance(cmd, str):
                cmd = shlex.split(cmd)

            if tee_stderr:
                s = subprocess
                start_time = time.time()
                with s.Popen(
                    cmd, stderr=s.PIPE, bufsize=1, universal_newlines=True, **kwargs
                ) as p, StringIO() as buf1, StringIO() as buf2:
                    for line in p.stderr:
                        print(line, end="")
                        # handles login banners which are returned via stderr
                        if time.time() - start_time < timeout + 5:
                            buf1.write(line)
                        else:
                            buf2.write(line)

                    early_error = buf1.getvalue()
                    late_error = buf2.getvalue()

                # if connections lasted 20 secs past timeout assume the early stuff was innocuous
                if time.time() - start_time > timeout + 10:
                    error = late_error
                else:
                    error = early_error

                if handle_errors and error and p.returncode != 0:
                    error = self.error_handler(cmd, error)
                else:
                    error = None
                return error
            else:
                proc = subprocess.Popen(
                    cmd, stderr=subprocess.PIPE, universal_newlines=True, **kwargs
                )
                err = proc.communicate(timeout=timeout)[1]
                if err is not None and do_print:
                    print(self.shell_output_cleaner(err), file=sys.stdout)
                # if proc.returncode != 0 and handle_errors:
                if err and handle_errors:
                    err = self.error_handler(cmd, err)

                proc.wait()
                return err

    def json_print(self, obj):
        print(json.dumps(obj, indent=4, sort_keys=True))

    def get_tty_size(self):
        size = subprocess.run(["stty", "size"], stdout=subprocess.PIPE)
        rows, cols = size.stdout.decode("UTF-8").split()
        return int(rows), int(cols)

    # TODO check if using kwarg sort added to fix re-order of error_msgs
    def unique(self, _list, sort=False):
        out = []
        [out.append(i) for i in _list if i not in out and i is not None]
        return out if not sort else sorted(out)

    def is_reachable(self, host, port, timeout=3, silent=False):
        s = socket.socket()
        try:
            s.settimeout(timeout)
            s.connect((host, port))
            _reachable = True
        except Exception as e:
            if not silent:
                print("something's wrong with %s:%d. Exception is %s" % (host, port, e))
            _reachable = False
        finally:
            s.close()
        return _reachable

    def valid_file(self, filepath):
        return os.path.isfile(filepath) and os.stat(filepath).st_size > 0

    def listify(self, var):
        return var if isinstance(var, list) or var is None else [var]

    @staticmethod
    def read_yaml(filename):
        """Read variables from local yaml file

        :param filename: local yaml file, defaults to 'vars.yaml'
        :type filename: str
        :return: Required variables
        :rtype: Python dictionary
        """
        filename = os.path.abspath(os.path.join(os.path.dirname(__file__), filename))
        with open(filename, "r") as input_file:
            data = yaml.load(input_file, Loader=yaml.FullLoader)
        return data

    @staticmethod
    def get_host_short(host):
        """Extract hostname from fqdn

        Arguments:
            host {str} -- hostname. If ip address is provided it's returned as is

        Returns:
            str -- host_short (lab1.example.com becomes lab1)
        """
        return (
            host.split(".")[0]
            if "." in host and not host.split(".")[0].isdigit()
            else host
        )

    @staticmethod
    def spinner(spin_txt, function, *args, **kwargs):
        spinner = kwargs.get("spinner", "dots")
        if sys.stdin.isatty():
            with Halo(text=spin_txt, spinner=spinner):
                return function(*args, **kwargs)

    def output(self, outdata, tablefmt):
        # log.debugv(f"data passed to output():\n{pprint(outdata, indent=4)}")
        if tablefmt == "json":
            # from pygments import highlight, lexers, formatters
            json_data = json.dumps(outdata, sort_keys=True, indent=2)
            table_data = highlight(bytes(json_data, 'UTF-8'),
                                   lexers.JsonLexer(),
                                   formatters.Terminal256Formatter(style='solarized-dark')
                                   )
        elif tablefmt == "csv":
            table_data = "\n".join(
                            [
                                ",".join(
                                    [
                                        k if outdata.index(d) == 0 else str(v)
                                        for k, v in d.items()
                                        if k not in CUST_KEYS
                                    ])
                                for d in outdata
                            ])
        elif tablefmt in ["yml", "yaml"]:
            table_data = highlight(bytes(yaml.dump(outdata, sort_keys=True, ), 'UTF-8'),
                                   lexers.YamlLexer(),
                                   formatters.Terminal256Formatter(style='solarized-dark')
                                   )
        else:
            customer_id = customer_name = ""
            outdata = self.listify(outdata)
            if outdata and isinstance(outdata, list) and isinstance(outdata[0], dict):
                customer_id = outdata[0].get("customer_id", "")
                customer_name = outdata[0].get("customer_name", "")
            outdata = [{k: v for k, v in d.items() if k not in CUST_KEYS} for d in outdata]
            table_data = tabulate(outdata, headers="keys", tablefmt=tablefmt)
            table_data = f"--\n{'Customer ID:':15}{customer_id}\n{'Customer Name:':15} {customer_name}\n--\n{table_data}"

        return table_data
