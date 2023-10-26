"""
Small git wrapper to init, check status, add, commit and pull
"""

from __future__ import annotations
import subprocess
from typing import Optional
from pathlib import Path
from notepy.cli.base_cli import BaseCli, CliException
from shlex import split


def run_and_handle(command: str,
                   cwd=".",
                   comment="") -> subprocess.CompletedProcess:
    """
    Utility function for CalledProcessError easy handling. It calls a command
    and manages exceptions by calling GitException, together with the stderr
    of the process.

    :param command: the command to execute.
    :param cwd: the working directory of the environment for the command.
    :param comment: optional comment to add to the exception message.
    :return: the completed process obect.
    """
    split_cmd = split(command)
    process_result = subprocess.run(split_cmd,
                                    cwd=cwd,
                                    stderr=subprocess.STDOUT,
                                    stdout=subprocess.PIPE)

    process_returncode = process_result.returncode
    if process_returncode != 0:
        error_message = (f'Command "{command}" returned a non-zero exit status '
                         f"{process_returncode}. Below is the full stderr:\n\n"
                         f"{process_result.stdout.decode('utf-8')}")
        error_message = error_message + \
            f"\n\n{comment}" if comment else error_message
        raise GitException(error_message)

    return process_result


class Git(BaseCli):
    """
    Wrapper for git cli

    :param path: path to the repo
    """

    def __init__(self, path: Path):
        super().__init__('git')
        self.path = path.expanduser()
        self.git_path = self.path / ".git"
        self._is_repo()

    def _is_repo(self) -> None:
        """
        Check that the directory provided is a git repo.
        """
        if not self.path.is_dir():
            raise GitException(f"'{self.path}' is not a directory.")
        if not self.git_path.is_dir():
            raise GitException(f"'{self.path}' is not a git repository.")

    @classmethod
    def init(cls, path: Path) -> Git:
        """
        Initialize a new git repo in the directory provided.

        :param path: absolute path to the new git repo.
        :return: a Git wrapper
        """
        path = path.expanduser()
        git_path = path / ".git"

        # sanity checks
        if not path.is_dir():
            raise GitException(f"'{path}' is not a directory.")
        if git_path.is_dir():
            raise GitException(f"'{path}' is already a git repository.")

        # create gitignore
        gitignore = path / ".gitignore"
        gitignore.touch(exist_ok=True)
        ignore_objects = ['.index.db', 'scratchpad', '.last']
        with open(gitignore, "w") as f:
            for ignored in ignore_objects:
                f.write(ignored+"\n")

        process = run_and_handle("git init", cwd=path)
        process = run_and_handle("git add .", cwd=path)
        process = run_and_handle("git commit -m 'First commit'", cwd=path)
        del process

        new_repo = cls(path)

        return new_repo

    def add(self) -> None:
        """
        Add changed files to staging area.
        """
        process = run_and_handle("git add -A", cwd=self.path)
        del process

    def commit(self, msg: Optional[str] = "commit notes") -> None:
        """
        Commit the staging area.
        """
        process = run_and_handle(f"git commit -m '{msg}'")
        del process

    def push(self) -> None:
        """
        Push to origin.
        """
        if not self._origin_exists():
            raise GitException("""origin does not exist.""")

        process = run_and_handle('git push',
                                 cwd=self.path,
                                 comment="Check that origin is correct")
        del process

    def add_origin(self, origin: str) -> None:
        """
        Add remote origin.
        """
        if self._origin_exists():
            raise GitException("""origin already exists.""")

        process = run_and_handle(f'git remote add origin "{origin}"',
                                 cwd=self.path,
                                 comment="Check that origin is correct")
        process = run_and_handle("git push origin master --set-upstream",
                                 cwd=self.path,
                                 comment="Check that origin is correct")
        del process

    def _origin_exists(self) -> bool:
        """
        Check if origin is defined.
        """
        origin = subprocess.run(['git',
                                 'config',
                                 '--get',
                                 'remote.origin.url'],
                                cwd=self.path,
                                capture_output=True)

        origin_exists = True
        if origin.returncode == 1:  # error code given by this failed action
            origin_exists = False
        elif origin.returncode != 0:  # for any other: raise exception
            origin.check_returncode()

        return origin_exists

    def __repr__(self) -> str:

        return str(self.path)

    def __str__(self) -> str:
        string = f"git repository at '{self.path}'\n\n"
        string += f"{self.status}"

        return string

    @property
    def status(self):
        """
        Check status of current git repo.
        """
        process = run_and_handle("git status",
                                 cwd=self.path)
        status = process.stdout.decode('utf-8')

        return status

    @status.setter
    def status(self, value):
        raise GitException("You cannot do this operation.")

    @status.deleter
    def status(self):
        raise GitException("You cannot do this operation.")


class GitException(CliException):
    """Error raised when git is involved"""