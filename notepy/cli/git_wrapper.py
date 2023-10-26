"""
Small git wrapper to init, check status, add, commit and pull
"""

from __future__ import annotations
import subprocess
from typing import Optional
from pathlib import Path
from notepy.cli.base_cli import BaseCli, CliException, run_and_handle


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

        # initialize repository
        process = run_and_handle("git init", exception=GitException, cwd=path)
        process = run_and_handle("git add .", exception=GitException, cwd=path)
        process = run_and_handle("git commit -m 'First commit'",
                                 exception=GitException,
                                 cwd=path)
        del process

        new_repo = cls(path)

        return new_repo

    def add(self) -> None:
        """
        Add changed files to staging area.
        """
        process = run_and_handle("git add -A",
                                 exception=GitException,
                                 cwd=self.path)
        del process

    def commit(self, msg: Optional[str] = "commit notes") -> None:
        """
        Commit the staging area.
        """
        process = run_and_handle(f"git commit -m '{msg}'",
                                 exception=GitException,
                                 cwd=self.path)
        del process

    def push(self) -> None:
        """
        Push to origin.
        """
        if not self._origin_exists():
            raise GitException("""origin does not exist.""")

        process = run_and_handle('git push',
                                 exception=GitException,
                                 cwd=self.path,
                                 comment="Check that origin is correct")
        del process

    def pull(self) -> None:
        """
        Pull from origin
        """
        if not self._origin_exists():
            raise GitException("""origin does not exist.""")

        process = run_and_handle('git pull',
                                 exception=GitException,
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
                                 exception=GitException,
                                 cwd=self.path,
                                 comment="Check that origin is correct")
        process = run_and_handle("git pull origin master --set-upstream",
                                 exception=GitException,
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
                                 exception=GitException,
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
