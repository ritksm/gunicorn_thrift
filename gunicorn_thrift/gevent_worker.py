# -*- coding: utf-8 -*-

import logging

logger = logging.getLogger(__name__)

try:
    import thrift
except ImportError:
    raise RuntimeError("You need thrift installed to use this worker.")

from thrift.transport import TSocket
from thrift.transport import TTransport

from gunicorn.workers.ggevent import GeventWorker


class GeventThriftWorker(GeventWorker):
    def get_thrift_transports_and_protos(self, result):
        itrans = self.app.tfactory.getTransport(result)
        otrans = self.app.tfactory.getTransport(result)
        iprot = self.app.pfactory.getProtocol(itrans)
        oprot = self.app.pfactory.getProtocol(otrans)

        return (itrans, otrans), (iprot, oprot)

    def handle(self, listener, client, addr):
        self.cfg.on_connected(self, addr)
        if self.app.cfg.thrift_client_timeout is not None:
            client.settimeout(self.app.cfg.thrift_client_timeout)

        result = TSocket.TSocket()
        result.setHandle(client)

        try:
            (itrans, otrans), (iprot, oprot) = \
                self.get_thrift_transports_and_protos(result)

            try:
                while True:
                    self.app.thrift_app.process(iprot, oprot)
            except TTransport.TTransportException:
                pass
        except Exception as e:
            self.log.exception(e)
        finally:
            itrans.close()
            otrans.close()

    def handle_exit(self, sig, frame):
        ret = super(GeventThriftWorker, self).handle_exit(sig, frame)
        self.cfg.worker_term(self)
        return ret
