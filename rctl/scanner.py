import os
import heapq
import fnmatch
from typing import Iterator, List, Tuple, Optional


def scan_files(
    root_dir: str,
    strategy: str = "bfs_name",
    include: Optional[List[str]] = None,
    exclude: Optional[List[str]] = None,
) -> Iterator[str]:
    """
    指定したディレクトリを再帰的にスキャンし、ファイルを指定の順序で返す。

    :param root_dir: スキャンするルートディレクトリ
    :param strategy: ファイルの順序戦略 ('bfs', 'dfs', 'name', 'mtime', 'bfs_name')
    :param include: 含めるファイルのワイルドカードパターン
    :param exclude: 除外するファイルのワイルドカードパターン
    :return: ファイルパスのイテレータ
    """
    if strategy == "bfs":
        return bfs_scan(root_dir, include, exclude)
    elif strategy == "dfs":
        return dfs_scan(root_dir, include, exclude)
    elif strategy == "name":
        return sorted_scan(root_dir, include, exclude)
    elif strategy == "mtime":
        return mtime_scan(root_dir, include, exclude)
    elif strategy == "bfs_name":
        return bfs_sorted_scan(root_dir, include, exclude)
    else:
        raise ValueError(
            "Invalid strategy. Choose from 'bfs', 'dfs', 'name', 'mtime', 'bfs_name'"
        )


def should_include(
    file_path: str, include: Optional[List[str]], exclude: Optional[List[str]]
) -> bool:
    """ファイルが含まれるべきかどうかをワイルドカードで判定"""
    if exclude and any(fnmatch.fnmatch(file_path, ex) for ex in exclude):
        return False
    if include and not any(fnmatch.fnmatch(file_path, inc) for inc in include):
        return False
    return True


def bfs_scan(
    root_dir: str, include: Optional[List[str]], exclude: Optional[List[str]]
) -> Iterator[str]:
    """幅優先探索でファイルをスキャン"""
    queue = [root_dir]
    while queue:
        current_dir = queue.pop(0)
        with os.scandir(current_dir) as entries:
            dirs = []
            files = []
            for entry in entries:
                if entry.is_file() and should_include(entry.path, include, exclude):
                    files.append(entry.path)
                elif entry.is_dir():
                    dirs.append(entry.path)

            for file in sorted(files):
                yield file

            queue.extend(sorted(dirs))


def dfs_scan(
    root_dir: str, include: Optional[List[str]], exclude: Optional[List[str]]
) -> Iterator[str]:
    """深さ優先探索でファイルをスキャン"""
    stack = [root_dir]
    while stack:
        current_dir = stack.pop()
        with os.scandir(current_dir) as entries:
            for entry in entries:
                if entry.is_file() and should_include(entry.path, include, exclude):
                    yield entry.path
                elif entry.is_dir():
                    stack.append(entry.path)


def sorted_scan(
    root_dir: str, include: Optional[List[str]], exclude: Optional[List[str]]
) -> Iterator[str]:
    """名前順にソートしてファイルをスキャン"""
    files = []
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if should_include(filepath, include, exclude):
                files.append(filepath)
    yield from sorted(files)


def mtime_scan(
    root_dir: str, include: Optional[List[str]], exclude: Optional[List[str]]
) -> Iterator[str]:
    """更新時刻順にソートしてファイルをスキャン"""
    files: List[Tuple[float, str]] = []
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if should_include(filepath, include, exclude):
                mtime = os.path.getmtime(filepath)
                heapq.heappush(files, (-mtime, filepath))  # 最新のものを優先

    while files:
        _, filepath = heapq.heappop(files)
        yield filepath


def bfs_sorted_scan(
    root_dir: str, include: Optional[List[str]], exclude: Optional[List[str]]
) -> Iterator[str]:
    """幅優先探索 + アルファベット順でスキャン"""
    queue = [root_dir]
    while queue:
        current_dir = queue.pop(0)
        with os.scandir(current_dir) as entries:
            dirs = []
            files = []
            for entry in entries:
                if entry.is_file() and should_include(entry.path, include, exclude):
                    files.append(entry.path)
                elif entry.is_dir():
                    dirs.append(entry.path)

            for file in sorted(files):
                yield file

            queue.extend(sorted(dirs))


# 使用例
if __name__ == "__main__":
    root_directory = "./your_directory_here"
    includes = ["*.txt", "*.log"]  # 例: テキストファイルとログファイルのみ
    excludes = ["*.tmp", "ignore/*"]  # 例: 一時ファイルや特定のディレクトリを除外

    for file_path in scan_files(
        root_directory, strategy="bfs_name", include=includes, exclude=excludes
    ):
        print(file_path)
