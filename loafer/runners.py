import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging
import os
import signal

logger = logging.getLogger(__name__)


class LoaferRunner:

    def __init__(self, loop=None, max_workers=None, on_stop_callback=None):
        self._on_stop_callback = on_stop_callback
        self._loop = loop or asyncio.get_event_loop()

        # XXX: See https://github.com/python/asyncio/issues/258
        # The minimum value depends on the number of cores in the machine
        # See https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ThreadPoolExecutor
        self._executor = ThreadPoolExecutor(max_workers)
        self._loop.set_default_executor(self._executor)

    def start(self, future=None, run_forever=True):
        start = 'Starting Loafer - (pid={} / run_forever={}) ...'
        logger.info(start.format(os.getpid(), run_forever))

        self._loop.add_signal_handler(signal.SIGINT, self.stop)
        self._loop.add_signal_handler(signal.SIGTERM, self.stop)

        try:
            if run_forever:
                self._loop.run_forever()
            else:
                self._loop.run_until_complete(future)
        finally:
            self._loop.close()

    def stop(self, *args, **kwargs):
        logger.info('Stopping Loafer ...')
        if callable(self._on_stop_callback):
            self._on_stop_callback()

        self._executor.shutdown(wait=True)
        if self._loop.is_running():
            self._loop.stop()
