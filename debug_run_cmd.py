import subprocess
import sys

subprocess.run(['python3','-m','pip','install','--no-cache-dir','requests'], check=True)
print('AFTER PIP')
subprocess.run(['python3','/workspace/debug_overpass_test.py'], check=True)
print('AFTER SCRIPT')
