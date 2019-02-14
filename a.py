
import os
import time
import mitogen.master
import mitogen.utils


def main():
    mitogen.utils.log_to_file(level='IO')
    broker = mitogen.master.Broker(threadless=True, install_watcher=False)
    router = mitogen.master.Router(broker)
    context = router.local(threadless=True)
    #root = router.sudo(via=context)
    print
    print
    print
    print
    print context
    print context.call(os.getpid)
    print context.call(time.sleep, 1234)
    #print context.call(os.getpid)


if __name__ == '__main__':
    main()
