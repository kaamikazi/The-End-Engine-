# Run re-executed after a server connection reset (original preserved)

BA-003.T2.DIRECT failed at 2026-09-30T21:15Z with `transport_error: [WinError 10054] An existing connection was
forcibly closed by the remote host` on its only call. The live process stopped at the same moment (the controlling
session ended), so this is an infrastructure interruption, not a property of the DIRECT condition. It is the only run
with a transport error. This record is exactly as written; the run was executed again with unchanged settings.
