"""Alias-resolution fixtures exercising real Ledger and NTFS sidecar I/O.

The alias spelling is synthetic. Only Path.resolve for that spelling is
substituted. The native 8.3 identity and crash gates live in the evidence
controller and have their own outcomes.
"""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from cognitive_architecture_lab_v1.src.accounting import ledger as ledger_module
from cognitive_architecture_lab_v1.src.accounting.coordination import Coordinator
from cognitive_architecture_lab_v1.src.accounting.ledger import Ledger
from cognitive_architecture_lab_v1.src.interfaces.contracts import canonical, digest
from tests_coordination_v1.support import request


class InterruptedBeforeReplace(RuntimeError):
    pass


class AliasNamespaceTests(unittest.TestCase):
    def setUp(self):
        self.directory = Path(os.environ["LEDGER_TEST_OUTPUT"]) / self._testMethodName
        self.directory.mkdir(parents=True, exist_ok=False)
        self.long_path = self.directory / "budget-really-long.json"
        self.fixture_alias = self.directory / "BUDGET~1.JSO"
        self.coordinator = Coordinator.create(self.long_path)
        self.original = Ledger(self.long_path, coordination=self.coordinator)

    def files(self):
        return {path.name: path.read_bytes() for path in self.directory.iterdir()}

    @contextmanager
    def alias_resolution(self):
        """Map the synthetic spelling at the existing Coordinator resolve boundary."""
        resolve = type(self.fixture_alias).resolve
        def mapped(path, *args, **kwargs):
            if path == self.fixture_alias:
                return self.long_path
            return resolve(path, *args, **kwargs)
        with patch.object(type(self.fixture_alias), "resolve", mapped):
            yield

    def test_enrolled_constructor_binds_all_operations_to_one_namespace(self):
        """Open a fixture alias, mutate/read the canonical Ledger, retain scratch."""
        before = self.files()
        with self.alias_resolution():
            attached = Coordinator.attach(self.fixture_alias)
            peer = Ledger(self.fixture_alias, coordination=attached)
            self.assertEqual(attached.guard_identity, self.coordinator.guard_identity)
            self.assertEqual(peer.path, self.coordinator.ledger_path)
            self.assertEqual(self.files(), before)
            self.assertIsNone(peer.register(request("fixture")))
            attempt = peer.reserve("fixture", "alias fixture", 9, 1)
            self.assertEqual(attempt, 1)
            self.assertIsNone(peer.finish(attempt, state="SUCCEEDED", input_tokens=2,
                                          output_tokens=3, seconds=0.1))
            self.assertEqual(peer.summary("fixture"), self.original.summary("fixture"))

        after = self.files()
        self.assertEqual(set(after), set(before))
        self.assertFalse(self.fixture_alias.exists())
        self.assertEqual(after[self.coordinator.guard_path.name], before[self.coordinator.guard_path.name])
        envelope = json.loads(after[self.long_path.name])
        self.assertEqual(after[self.long_path.name], canonical(envelope))
        self.assertEqual(envelope["state_sha256"], digest(envelope["state"]))
        self.assertEqual(list(envelope["state"]["runs"]), ["fixture"])
        self.assertEqual(len(envelope["state"]["attempts"]), 1)

    def test_enrolled_nonowning_facade_leaves_one_recovery_namespace(self):
        """Interrupt after real fsync and verify canonical rejection. Retain evidence."""
        before = self.files()
        pending = self.long_path.with_suffix(".json.pending")
        with self.alias_resolution():
            facade = object.__new__(Ledger)
            facade.path = self.fixture_alias
            facade.limits = self.original.limits
            facade._coordination = Coordinator.attach(self.fixture_alias)
            self.assertEqual(self.files(), before)

            def stop_before_replace(source, target):
                self.assertEqual(source, pending)
                self.assertEqual(target, self.coordinator.ledger_path)
                self.assertTrue(pending.is_file())
                raise InterruptedBeforeReplace("Synthetic pre-replace stop after actual fsync")

            with patch.object(ledger_module.os, "replace", stop_before_replace):
                with self.assertRaises(InterruptedBeforeReplace):
                    facade.register(request("pending_alias"))
            self.assertEqual(facade.path, self.coordinator.ledger_path)

        held = self.files()
        self.assertEqual(set(held), set(before) | {pending.name})
        self.assertEqual({key: held[key] for key in before}, before)
        pending_bytes = held[pending.name]
        envelope = json.loads(pending_bytes)
        self.assertEqual(pending_bytes, canonical(envelope))
        self.assertEqual(envelope["state_sha256"], digest(envelope["state"]))
        self.assertEqual(list(envelope["state"]["runs"]), ["pending_alias"])

        retry = Ledger(self.long_path, coordination=Coordinator.attach(self.long_path))
        with self.assertRaises(FileExistsError) as stopped:
            retry.register(request("must_not_commit"))
        self.assertEqual(Path(stopped.exception.filename), pending)
        self.assertEqual(self.files(), held)
        self.assertEqual(retry.state()["runs"], {})


if __name__ == "__main__":
    unittest.main()
