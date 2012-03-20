import json
import threading
import tornado.ioloop
import tornado.httpserver
import tornado.web

from testify import assert_equal, setup_teardown, TestCase
from testify.test_runner import TestRunner
from testify.plugins.http_reporter import HTTPReporter

class DummyTestCase(TestCase):
	__test__ = False
	def test(self):
		pass


class HTTPReporterTestCase(TestCase):
	@setup_teardown
	def make_fake_server(self):
		self.results_reported = []

		class ResultsHandler(tornado.web.RequestHandler):
			def post(handler):
				result = json.loads(handler.request.body)
				self.results_reported.append(result)
				handler.finish("kthx")

		app = tornado.web.Application([(r"/results", ResultsHandler)])
		srv = tornado.httpserver.HTTPServer(app)
		srv.listen(0)
		portnum = srv._socket.getsockname()[1]

		iol = tornado.ioloop.IOLoop.instance()
		thread = threading.Thread(target=iol.start)
		thread.daemon = True # If for some reason, this thread gets blocked, don't prevent quitting.
		thread.start()

		self.connect_addr = "localhost:%d" % portnum

		yield

		iol.stop()
		thread.join()

	def test_http_reporter_reports(self):
		"""A simple test to make sure the HTTPReporter actually reports things."""

		runner = TestRunner(DummyTestCase, test_reporters=[HTTPReporter(None, self.connect_addr, 'runner1')])
		runner.run()

		(only_result,) = self.results_reported
		assert_equal(only_result['runner_id'], 'runner1')
		assert_equal(only_result['method']['class'], 'DummyTestCase')
		assert_equal(only_result['method']['name'], 'test')
