# (c) Copyright IBM Corp. 2021
# (c) Copyright Instana Inc. 2019


import opentracing
import wrapt
import functools

from ...log import logger
from ...singletons import agent, async_tracer
from ...util.secrets import strip_secrets_from_query

try:
    import tornado

    @wrapt.patch_function_wrapper('tornado.httpclient', 'AsyncHTTPClient.fetch')
    def fetch_with_instana(wrapped, instance, argv, kwargs):
        try:
            parent_span = async_tracer.active_span

            # If we're not tracing, just return
            if (parent_span is None) or (parent_span.operation_name == "tornado-client"):
                return wrapped(*argv, **kwargs)

            request = argv[0]

            # To modify request headers, we have to preemptively create an HTTPRequest object if a
            # URL string was passed.
            if not isinstance(request, tornado.httpclient.HTTPRequest):
                request = tornado.httpclient.HTTPRequest(url=request, **kwargs)

                new_kwargs = {}
                for param in ('callback', 'raise_error'):
                    # if not in instead and pop
                    if param in kwargs:
                        new_kwargs[param] = kwargs.pop(param)
                kwargs = new_kwargs

            scope = async_tracer.start_active_span('tornado-client', child_of=parent_span)
            async_tracer.inject(scope.span.context, opentracing.Format.HTTP_HEADERS, request.headers)

            # Query param scrubbing
            parts = request.url.split('?')
            if len(parts) > 1:
                cleaned_qp = strip_secrets_from_query(parts[1], agent.options.secrets_matcher,
                                                      agent.options.secrets_list)
                scope.span.set_tag("http.params", cleaned_qp)

            scope.span.set_tag("http.url", parts[0])
            scope.span.set_tag("http.method", request.method)

            future = wrapped(request, **kwargs)

            if future is not None:
                cb = functools.partial(finish_tracing, scope=scope)
                future.add_done_callback(cb)

            return future
        except Exception:
            logger.debug("tornado fetch", exc_info=True)
            raise


    def finish_tracing(future, scope):
        try:
            response = future.result()
            scope.span.set_tag("http.status_code", response.code)
        except tornado.httpclient.HTTPClientError as e:
            scope.span.set_tag("http.status_code", e.code)
            scope.span.log_exception(e)
            raise
        finally:
            scope.close()


    logger.debug("Instrumenting tornado client")
except ImportError as err:
    logger.debug(f"ImportError: {err}")
except Exception as err:
    logger.debug(f"Unexpected {err=}, {type(err)=}")
    raise
