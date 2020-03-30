import pathlib
import typing

import pygit2


def switch(repo: pygit2.Repository, ref: pygit2.Reference) -> None:
    stashed = False
    if [
        code
        for code in repo.status().values()
        if (code ^ (code & pygit2.GIT_STATUS_WT_NEW))
    ]:
        repo.stash(stasher=repo.default_signature)
        stashed = True

    repo.checkout(refname=ref)

    if stashed:
        repo.stash_pop()


def commit(
    repo: pygit2.Repository,
    message: str,
    pathspecs: typing.Optional[typing.List[typing.Union[str, pathlib.Path]]] = None,
) -> None:
    if pathspecs is None:
        pathspecs = []

    pathspecs = [
        (
            str(
                pathspec.relative_to(repo.workdir)
                if pathspec.is_absolute()
                else pathspec
            )
            if isinstance(pathspec, pathlib.Path)
            else pathspec
        )
        for pathspec in pathspecs
    ]

    repo.index.add_all(pathspecs=pathspecs)
    repo.index.write()
    tree = repo.index.write_tree()

    try:
        parent, ref = repo.resolve_refish(refish=repo.head.name)
    except pygit2.GitError:
        parents = []
        ref_name = 'refs/heads/master'
    else:
        parents = [parent.oid]
        ref_name = ref.name

    repo.create_commit(
        ref_name, repo.default_signature, repo.default_signature, message, tree, parents
    )


def push(repo: pygit2.Repository, branch_name: str) -> None:
    branch = repo.branches.local[branch_name]
    if not branch.is_head():
        raise ValueError(branch)

    try:
        remote = repo.remotes['origin']
    except KeyError:
        return

    remote.push(specs=[branch.name])