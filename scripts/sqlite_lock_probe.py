"""Probe SQLite's expected exclusive-write locking behavior."""

from __future__ import annotations

import sqlite3
import tempfile
from threading import Thread


def main() -> None:
    directory = tempfile.TemporaryDirectory()
    path = f"{directory.name}/probe.sqlite3"
    first = sqlite3.connect(path, timeout=1, check_same_thread=False)
    second = sqlite3.connect(path, timeout=0.1, check_same_thread=False)
    result: list[str] = []

    try:
        first.execute("create table probe (id integer primary key)")
        first.commit()
        first.execute("begin exclusive")
        first.execute("insert into probe default values")

        def attempt_write() -> None:
            try:
                second.execute("insert into probe default values")
                second.commit()
                result.append("unexpected-success")
            except sqlite3.OperationalError:
                result.append("blocked-as-expected")

        worker = Thread(target=attempt_write)
        worker.start()
        worker.join()
        print(result[0])
    finally:
        first.rollback()
        first.close()
        second.close()
        directory.cleanup()


if __name__ == "__main__":
    main()
