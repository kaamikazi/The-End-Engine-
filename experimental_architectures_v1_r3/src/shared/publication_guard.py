"""F01 local Windows publication pins, not hostile-host or power-loss security.

Read handles deny write/delete sharing through the exclusive-link syscall.
The existing run lock and OS owner lease still serialize cooperating writers.
Directory inventories are checked at the native publication seam; arbitrary
namespace creation by hostile host code is outside this trust model.
"""
import ctypes
from ctypes import wintypes
import os
import threading
from pathlib import Path

_CURRENT = threading.local()


class EvidencePin:
    def __init__(self, pub, pending, anchor, raw, prepared):
        self.pub = pub
        self.pending = Path(pending)
        self.anchor = Path(anchor)
        self.raw = raw
        self.prepared = prepared
        self.handles = []

    def inventory(self):
        p = self.pub
        paths = {p.ledger.path.resolve(), p.ledger.path.with_suffix('.closed.json').resolve(),
                 p.owner_path, p.meta / 'IDENTITY.json', self.pending, self.anchor}
        for directory, pattern in ((p.directory / 'wire', '*.jsonl'),
                                   (p.meta / 'attempts', '*.json')):
            paths.update(directory.glob(pattern))
        return frozenset(paths)

    def pin(self, path):
        from .publication import ArtifactIntegrity, PublicationFailure
        if os.name != 'nt':
            raise PublicationFailure('F01_WRITE_DENY_PUBLICATION_PINS_REQUIRE_WINDOWS')
        if path.is_symlink():
            raise ArtifactIntegrity('F01_SYMLINK_EVIDENCE_NOT_PINNED')
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        create = kernel.CreateFileW
        create.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                           wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
        create.restype = wintypes.HANDLE
        # GENERIC_READ, FILE_SHARE_READ only, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL.
        # A writer already holding incompatible access also prevents admission.
        handle = create(str(path), 0x80000000, 1, None, 3, 0x80, None)
        if handle == wintypes.HANDLE(-1).value:
            error = ctypes.WinError(ctypes.get_last_error())
            raise ArtifactIntegrity('F01_EVIDENCE_PIN_NOT_ACQUIRED:' + path.name) from error
        self.handles.append(handle)

    def check(self):
        from .publication import ArtifactIntegrity, StaleOwner
        from .strict_json import read
        if self.inventory() != self.paths:
            raise ArtifactIntegrity('F01_EVIDENCE_INVENTORY_CHANGED_BEFORE_LINK')
        if self.pending.read_bytes() != self.raw or read(self.anchor) != self.prepared:
            raise ArtifactIntegrity('F01_PREPARED_PUBLICATION_CHANGED')
        owner = self.pub._owner()
        if self.pub.fd is None or self.pub.detached or owner['token'] != self.pub.token or owner['fence'] != self.pub.fence:
            raise StaleOwner('F01_OWNER_CHANGED_BEFORE_LINK')

    def __enter__(self):
        from .publication import ArtifactIntegrity
        try:
            self.paths = self.inventory()
            for path in sorted(self.paths):
                self.pin(path)
            self.check()
            _CURRENT.pin = self
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def __exit__(self, *args):
        if getattr(_CURRENT, 'pin', None) is self:
            del _CURRENT.pin
        if self.handles:
            kernel = ctypes.WinDLL('kernel32', use_last_error=True)
            close = kernel.CloseHandle
            close.argtypes = [wintypes.HANDLE]
            close.restype = wintypes.BOOL
            for handle in reversed(self.handles):
                close(handle)
            self.handles.clear()


def before_exclusive_link(pending, final):
    pin = getattr(_CURRENT, 'pin', None)
    if pin is not None:
        from .publication import ArtifactIntegrity
        if Path(pending) != pin.pending or Path(final) != pin.pub.final:
            raise ArtifactIntegrity('F01_PUBLICATION_TARGET_CHANGED')
        pin.check()


def denied_evidence_write(error, pin):
    """A denied mutation is an integrity failure, not a successful publication."""
    filename = getattr(error, 'filename', None)
    return filename is not None and Path(filename).resolve() in pin.paths
