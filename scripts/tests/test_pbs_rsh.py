"""Check the shell-prefix protocol used by Open MPI's remote-launch agent."""
import json
import os
from pathlib import Path
import runpy
import subprocess
import tempfile
import unittest
from unittest.mock import patch


class LaunchCaptured(Exception):
    def __init__(self, argv):
        self.argv=argv


class AgentTest(unittest.TestCase):
    def test_prefixed_and_quoted_remote_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            nodes=root/'nodes';nodes.write_text('node-a\nnode-b\n')
            env=dict(PBS_NODEFILE=str(nodes),PCG_DAEMON_LOG_DIR=str(root/'logs'))
            args=['pbs_rsh.py','node-b',
                  'PCG_TEST_VALUE=works; export PCG_TEST_VALUE; /usr/bin/printf',
                  '"%s\\n"','"$PCG_TEST_VALUE with spaces"']
            def capture(path,argv):
                raise LaunchCaptured(argv)
            with patch.dict(os.environ,env),patch('sys.argv',args),patch('os.execv',capture):
                with self.assertRaises(LaunchCaptured) as result:
                    runpy.run_path(str(Path(__file__).resolve().parents[1]/'vanda/pbs_rsh.py'))
            argv=result.exception.argv
            self.assertEqual(argv[:5],['pbsdsh','-n','1','--','/usr/bin/env'])
            actual=subprocess.check_output(['/bin/bash','-c',argv[-1]],text=True)
            self.assertEqual(actual,'works with spaces\n')
            self.assertEqual(json.loads((root/'logs/daemon-node-b.json').read_text())['index'],1)


if __name__=='__main__':unittest.main()
