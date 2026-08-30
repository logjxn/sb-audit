import sys

from .render import render
from .snapshot import SnapshotError, read_snapshot
from .walker import walk_boot_path, walk_checklist


def main() -> int:
    try:
        snapshot = read_snapshot()
    except SnapshotError as exc:
        print(exc, file=sys.stderr)
        return 1
    print(render(walk_boot_path(snapshot), walk_checklist(snapshot)))
    return 0


if __name__ == "__main__":
    sys.exit(main())