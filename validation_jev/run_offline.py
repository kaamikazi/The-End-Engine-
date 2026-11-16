"""Offline validation entry point. Raises on any attempted runtime network access.

Run from the repository root with Python 3.11+: python -B validation_jev/run_offline.py
Only the Engine unittest suite is discovered; no benchmark/replay CLI is launched.
"""
import importlib.util
import json
import os
from pathlib import Path
import socket
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
os.chdir(ROOT)
os.environ.pop("TYPESAFE_API_KEY",None)  # Process-local only; never retain or print its value.
attempts=[]


def forbidden(*args,**kwargs):
    attempts.append("blocked_network_attempt")
    raise AssertionError("Offline validation forbids network access")


if __name__ == "__main__":
    with patch.object(socket.socket,"connect",forbidden), patch.object(socket.socket,"connect_ex",forbidden), \
         patch.object(socket,"create_connection",forbidden), patch.object(socket,"getaddrinfo",forbidden), \
         patch.object(socket.socket,"sendto",forbidden):
        suite=unittest.defaultTestLoader.discover(str(ROOT/"tests"),top_level_dir=str(ROOT))
        with (ROOT/"validation_jev"/"engine-tests-after.txt").open("w",encoding="utf-8") as log:
            result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    summary={"tests":result.testsRun,"failures":len(result.failures),"errors":len(result.errors),
             "runtime_network_calls":len(attempts),"live_model_calls":0,
             "typesafe_sdk_installed":importlib.util.find_spec("typesafe_sdk") is not None,
             "typesafe_sdk_imported": "typesafe_sdk" in sys.modules,
             "jev_default": "disabled", "benchmark_executed":False}
    (ROOT/"validation_jev"/"test-summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))
    raise SystemExit(0 if result.wasSuccessful() and not attempts else 1)
