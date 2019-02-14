"""
Measure latency of local RPC.
"""

import time

import mitogen
import mitogen.master
import mitogen.utils
import ansible_mitogen.affinity

mitogen.utils.setup_gil()
ansible_mitogen.affinity.policy.assign_worker()

try:
    xrange
except NameError:
    xrange = range

def do_nothing():
    pass

def main():
    #mitogen.utils.log_to_file(level='DEBUG')
    threadless=True
    broker = mitogen.master.Broker(threadless=threadless)
    router = mitogen.master.Router(broker)

    f = router.local(threadless=True)
    f.call(do_nothing)
    t0 = time.time()
    for x in xrange(20000):
        f.call(do_nothing)
    print('++', int(1e6 * ((time.time() - t0) / (1.0+x))), 'usec')
    broker.shutdown()

if __name__ == '__main__':
    main()
