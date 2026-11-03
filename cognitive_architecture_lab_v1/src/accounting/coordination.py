"""Explicit Windows/NTFS L2 for enrolled Ledger instances, not all writers.

Bootstrap needs an existing parent and creates only a new control. Attachment
never repairs a control. No environment switch or automatic path enrollment.
"""
import ctypes
import errno
import hashlib
import json
import math
import os
import stat
import sys
import threading
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path


class CoordinationError(RuntimeError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


class CoordinationBusy(TimeoutError):
    code = 'L2_CONTENTION_DEADLINE'

    def __init__(self):
        super().__init__(self.code)


def _key(path):
    return os.path.normcase(os.path.abspath(os.fspath(path)))


def _identity(info):
    return (info.st_dev, info.st_ino)


def _safe_path(path):
    if os.name != 'nt':
        raise CoordinationError('WINDOWS_NTFS_REQUIRED')
    origin = _key(__file__)
    current = sys.modules[__name__]
    if any(module is not current and getattr(module, '__file__', None)
           and _key(module.__file__) == origin for module in tuple(sys.modules.values())):
        raise CoordinationError('DUPLICATE_COORDINATION_MODULE_ORIGIN')
    name = Path(path).name
    if (':' in name or name != name.rstrip(' .')
            or name.split('.')[0].upper() in
            {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(1, 10)),
             *(f'LPT{i}' for i in range(1, 10))}):
        raise CoordinationError('NONCANONICAL_LEDGER_NAME_UNSUPPORTED')
    path = Path(_key(path))
    if len(path.drive) != 2 or path.drive[1] != ':':
        raise CoordinationError('LOCAL_DRIVE_REQUIRED')
    for item in (path, *path.parents):
        try:
            info = item.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise CoordinationError('REPARSE_PATH_UNSUPPORTED')
    # Windows realpath resolves existing 8.3 aliases too. Reject reparse inputs
    # first, rather than silently following them during canonicalization.
    path = Path(_key(path.resolve()))
    if not path.parent.is_dir():
        raise CoordinationError('PARENT_MUST_ALREADY_EXIST')
    if path.exists():
        info = path.stat()
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise CoordinationError('LEDGER_ALIAS_OR_TYPE_UNSUPPORTED')
    return path


def _ntfs(path):
    from ctypes import wintypes as wt
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    fn = kernel.GetVolumeInformationW
    fn.argtypes = [wt.LPCWSTR, wt.LPWSTR, wt.DWORD, ctypes.POINTER(wt.DWORD),
                   ctypes.POINTER(wt.DWORD), ctypes.POINTER(wt.DWORD), wt.LPWSTR, wt.DWORD]
    fn.restype = wt.BOOL
    fs = ctypes.create_unicode_buffer(64)
    if not fn(path.drive + '\\', None, 0, None, None, None, fs, len(fs)):
        raise ctypes.WinError(ctypes.get_last_error())
    if fs.value != 'NTFS':
        raise CoordinationError('WINDOWS_NTFS_REQUIRED')


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('ascii')


def _read_control(fd):
    info = os.fstat(fd)
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or not 2 <= info.st_size <= 4096:
        raise CoordinationError('INVALID_CONTROL_FILE')
    # Metadata starts after the byte-lock range, so attachment also works while
    # another process owns L2. Byte zero is checked only by its acquired owner.
    os.lseek(fd, 1, os.SEEK_SET)
    raw = os.read(fd, 4096)
    try:
        value = json.loads(raw.decode('ascii'))
        if (type(value) is not dict or set(value) != {
                'protocol', 'ledger_path', 'parent_dev', 'parent_ino',
                'guard_dev', 'guard_ino', 'domain_id'}
                or value['protocol'] != 'ledger-l2-v1' or _canonical(value) != raw
                or type(value['ledger_path']) is not str
                or any(type(value[k]) is not int for k in
                       ('parent_dev', 'parent_ino', 'guard_dev', 'guard_ino'))
                or type(value['domain_id']) is not str or len(value['domain_id']) != 32
                or any(c not in '0123456789abcdef' for c in value['domain_id'])
                or (value['guard_dev'], value['guard_ino']) != _identity(info)):
            raise ValueError()
    except (ValueError, UnicodeError, TypeError):
        raise CoordinationError('INVALID_CONTROL_METADATA') from None
    return value, raw, info


class _State:
    def __init__(self):
        self.mutex = threading.RLock()
        self.depth = 0
        self.thread = None
        self.fd = None


# Internal ownership state, not a configuration or activation switch. Kernel
# identity shares one thread mutex across distinct explicit Coordinator objects.
_registry = {}
_registry_mutex = threading.Lock()
_inner = threading.local()


@contextmanager
def _inner_scope(path):
    stack = getattr(_inner, 'stack', None)
    if stack is None:
        stack = _inner.stack = []
    token = (_key(path), object())
    stack.append(token)
    try:
        yield
    finally:
        if not stack or stack[-1] is not token:
            raise CoordinationError('INNER_OWNERSHIP_STACK_CORRUPT')
        stack.pop()


@dataclass(frozen=True)
class Coordinator:
    ledger_path: Path
    guard_path: Path
    parent_identity: tuple
    guard_identity: tuple
    metadata_sha256: str
    domain_id: str
    timeout: float = 0.5

    @classmethod
    def create(cls, path, *, timeout=0.5):
        """One-time explicit bootstrap. No mkdir, overwrite or data repair."""
        path = _safe_path(path)
        _ntfs(path)
        cls._timeout(timeout)
        parent = path.parent.stat()
        guard = path.with_name(path.name + '.coordination-v1.lock')
        fd = os.open(guard, os.O_CREAT | os.O_EXCL | os.O_RDWR | os.O_BINARY, 0o600)
        try:
            info = os.fstat(fd)
            value = {'protocol': 'ledger-l2-v1', 'ledger_path': str(path),
                     'parent_dev': parent.st_dev, 'parent_ino': parent.st_ino,
                     'guard_dev': info.st_dev, 'guard_ino': info.st_ino,
                     'domain_id': uuid.uuid4().hex}
            with os.fdopen(fd, 'wb', closefd=False) as stream:
                stream.write(b'0' + _canonical(value))
                stream.flush()
                os.fsync(fd)
        finally:
            os.close(fd)
        return cls.attach(path, timeout=timeout)

    @classmethod
    def attach(cls, path, *, timeout=0.5):
        """Read preexisting control without acquiring or recreating its lock."""
        path = _safe_path(path)
        _ntfs(path)
        cls._timeout(timeout)
        guard = path.with_name(path.name + '.coordination-v1.lock')
        if guard.is_symlink() or guard.lstat().st_file_attributes & 0x400:
            raise CoordinationError('REPARSE_CONTROL_UNSUPPORTED')
        fd = os.open(guard, os.O_RDONLY | os.O_BINARY)
        try:
            value, raw, info = _read_control(fd)
        finally:
            os.close(fd)
        result = cls(path, guard, (value['parent_dev'], value['parent_ino']),
                     _identity(info), hashlib.sha256(raw).hexdigest(), value['domain_id'], timeout)
        result.validate(path)
        return result

    @staticmethod
    def _timeout(value):
        if type(value) not in (int, float) or not math.isfinite(value) or not 0 < value <= 5:
            raise CoordinationError('INVALID_L2_DEADLINE')

    def validate(self, path):
        actual = _safe_path(path)
        if actual != self.ledger_path or _identity(actual.parent.stat()) != self.parent_identity:
            raise CoordinationError('LEDGER_RESOURCE_MISMATCH')
        expected = actual.with_name(actual.name + '.coordination-v1.lock')
        if self.guard_path != expected:
            raise CoordinationError('CONTROL_PATH_MISMATCH')
        if self.guard_path.is_symlink() or self.guard_path.lstat().st_file_attributes & 0x400:
            raise CoordinationError('REPARSE_CONTROL_UNSUPPORTED')
        fd = os.open(self.guard_path, os.O_RDONLY | os.O_BINARY)
        try:
            value, raw, info = _read_control(fd)
            if (_identity(info) != self.guard_identity
                    or hashlib.sha256(raw).hexdigest() != self.metadata_sha256
                    or value['ledger_path'] != str(actual) or value['domain_id'] != self.domain_id
                    or (value['parent_dev'], value['parent_ino']) != self.parent_identity):
                raise CoordinationError('CONTROL_IDENTITY_CHANGED')
        finally:
            os.close(fd)
        self._timeout(self.timeout)

    def _state(self):
        return _registry.get((os.getpid(), *self.guard_identity))

    def _owned(self):
        state = self._state()
        if (state is None or state.depth < 1 or state.thread != threading.get_ident()
                or state.fd is None or _identity(os.fstat(state.fd)) != self.guard_identity):
            raise CoordinationError('L2_NOT_OWNED_BY_CURRENT_THREAD')
        return state

    def assert_write(self, path):
        """Check existing ownership only; no L2 acquisition under L3."""
        self._owned()
        if not getattr(_inner, 'stack', ()) or _inner.stack[-1][0] != _key(path):
            raise CoordinationError('L3_NOT_OWNED_FOR_WRITE')
        self.validate(path)

    def check_inner_entry(self, path):
        self.validate(path)
        if getattr(_inner, 'stack', ()):
            raise CoordinationError('RECURSIVE_OR_REVERSED_L3_ENTRY')

    @contextmanager
    def acquire(self):
        if getattr(_inner, 'stack', ()):
            raise CoordinationError('LOCK_ORDER_L3_TO_L2_REJECTED')
        self.validate(self.ledger_path)
        key = (os.getpid(), *self.guard_identity)
        with _registry_mutex:
            state = _registry.setdefault(key, _State())
        deadline = time.monotonic() + self.timeout
        if not state.mutex.acquire(timeout=max(0, deadline - time.monotonic())):
            raise CoordinationBusy()
        entered = False
        try:
            if state.depth:
                self._owned()
            else:
                import msvcrt
                fd = os.open(self.guard_path, os.O_RDWR | os.O_BINARY)
                locked = False
                try:
                    while True:
                        try:
                            os.lseek(fd, 0, os.SEEK_SET)
                            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                            locked = True
                            break
                        except OSError as error:
                            if error.errno not in (errno.EACCES, errno.EAGAIN):
                                raise
                            if time.monotonic() >= deadline:
                                raise CoordinationBusy() from error
                            time.sleep(min(0.01, max(0, deadline - time.monotonic())))
                    value, raw, info = _read_control(fd)
                    os.lseek(fd, 0, os.SEEK_SET)
                    if (os.read(fd, 1) != b'0' or _identity(info) != self.guard_identity
                            or _identity(self.guard_path.stat()) != self.guard_identity
                            or hashlib.sha256(raw).hexdigest() != self.metadata_sha256):
                        raise CoordinationError('CONTROL_IDENTITY_CHANGED')
                    state.fd = fd
                    state.thread = threading.get_ident()
                except BaseException:
                    try:
                        if locked:
                            os.lseek(fd, 0, os.SEEK_SET)
                            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
                    finally:
                        os.close(fd)
                    raise
            state.depth += 1
            entered = True
            yield self
        finally:
            try:
                if entered:
                    state.depth -= 1
                    if state.depth == 0:
                        fd = state.fd
                        state.fd = None
                        state.thread = None
                        try:
                            import msvcrt
                            os.lseek(fd, 0, os.SEEK_SET)
                            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
                        finally:
                            os.close(fd)
            finally:
                state.mutex.release()
