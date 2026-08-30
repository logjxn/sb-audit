import sys

from .snapshot import SnapshotError, read_snapshot


def main() -> int:
    try:
        snapshot = read_snapshot()
    except SnapshotError as exc:
        print(exc, file=sys.stderr)
        return 1
    print(snapshot)
    return 0


if __name__ == "__main__":
    sys.exit(main())