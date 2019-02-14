
import os
import mitogen.master
import mitogen.utils


def main():
    mitogen.utils.log_to_file(level='IO')
    broker = mitogen.master.Broker(threadless=True, install_watcher=False)
    router = mitogen.master.Router(broker)
    context = router.ssh(hostname='k3')
    print context
    print context.call(os.getpid)


if __name__ == '__main__':
    main()
