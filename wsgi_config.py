import gnupg
import os
from app import ProductionConfig
from pathlib import Path

bind = '0.0.0.0:80'
backlog = 2048

workers = 4
worker_class = 'sync'
worker_connections = 1000
timeout = 30
keepalive = 2

spew = False

daemon = False
raw_env = []
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

errorlog = '-'
loglevel = 'info'
accesslog = '-'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

proc_name = None


def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)


def pre_fork(server, worker):
    pass


def pre_exec(server):
    server.log.info("Forked child, re-executing.")


def when_ready(server):
    server.log.info("Server is ready. Spawning workers")


def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

    ## get traceback info
    import threading, sys, traceback
    id2name = {th.ident: th.name for th in threading.enumerate()}
    code = []
    for threadId, stack in sys._current_frames().items():
        code.append("\n# Thread: %s(%d)" % (id2name.get(threadId, ""),
                                            threadId))
        for filename, lineno, name, line in traceback.extract_stack(stack):
            code.append('File: "%s", line %d, in %s' % (filename,
                                                        lineno, name))
            if line:
                code.append("  %s" % (line.strip()))
    worker.log.debug("\n".join(code))


def worker_abort(worker):
    worker.log.info("worker received SIGABRT signal")


def on_starting(server):
    Path(ProductionConfig.GPG_HOME_DIR).mkdir(parents=True, exist_ok=True)
    Path(ProductionConfig.GPG_SECRET_KEYRING).mkdir(parents=True, exist_ok=True)

    gpg = gnupg.GPG(gnupghome=ProductionConfig.GPG_HOME_DIR, keyring=ProductionConfig.GPG_SECRET_KEYRING)

    # check if there keyring contains at least one secret key
    if not len(gpg.list_keys(secret=True)):
        # import keys from keyfile.asc
        if os.path.isfile(f"{ProductionConfig.DATA_DIR}/keyfile.asc"):
            with open(f'{ProductionConfig.DATA_DIR}/keyfile.asc', 'r') as f:
                gpg.import_keys(f.read())
        else:
            # generate new key
            data = {
                'key_type': 'RSA',
                'key_length': 4096,
                'name_real': ProductionConfig.GPG_NAME,
                'name_email': ProductionConfig.GPG_EMAIL,
                'passphrase': ProductionConfig.GPG_PASSPHRASE
            }
            key = gpg.gen_key(gpg.gen_key_input(**data))

            # export the new generated key pair to keyfile.asc
            with open(f'{ProductionConfig.DATA_DIR}/keyfile.asc', 'w') as f:
                f.write(gpg.export_keys(key.fingerprint))
                f.write(gpg.export_keys(key.fingerprint, secret=True, passphrase=ProductionConfig.GPG_PASSPHRASE))

        # check again it the keyring contains at least one secret key
        if not len(gpg.list_keys(secret=True)):
            print("WARNING: pgp functionality is limited")
