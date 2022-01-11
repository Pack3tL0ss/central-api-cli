# Python script for the Python Demo Service

if __name__ == '__main__':
    import time
    import systemd.daemon
    from . import wh_proxy

    print('Starting up ...')
    time.sleep(10)
    print('Startup complete')
    # Tell systemd that our service is ready
    systemd.daemon.notify('READY=1')

    while True:
        print('Hello from the Python Demo Service')
        time.sleep(5)
