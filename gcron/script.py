import os
import tempfile
import subprocess

class Script (object):
    def __init__ (self, fd=None, text=None):
        self.fd = tempfile.NamedTemporaryFile()
        if fd:
            self.fd.write(fd.read())
        elif text:
            self.fd.write(text)

        self.fd.seek(0)
        os.chmod(self.fd.name, 0755)

    def run(self):
        subprocess.call(['/bin/sh', self.fd.name])

