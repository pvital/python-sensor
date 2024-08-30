# (c) Copyright IBM Corp. 2021
# (c) Copyright Instana Inc. 2018


import re
from operator import attrgetter

from ..log import logger
from ..util.traceutils import get_tracer_tuple, tracing_is_off

try:
    import sqlalchemy
    from sqlalchemy import event
    from sqlalchemy.engine import Engine

    url_regexp = re.compile(r"\/\/(\S+@)")


    @event.listens_for(Engine, 'before_cursor_execute', named=True)
    def receive_before_cursor_execute(**kw):
        try:
            # If we're not tracing, just return
            if tracing_is_off():
                return

            tracer, parent_span, _ = get_tracer_tuple()
            scope = tracer.start_active_span("sqlalchemy", child_of=parent_span)
            context = kw['context']
            if context:
                context._stan_scope = scope

            conn = kw['conn']
            url = str(conn.engine.url)
            scope.span.set_tag('sqlalchemy.sql', kw['statement'])
            scope.span.set_tag('sqlalchemy.eng', conn.engine.name)
            scope.span.set_tag('sqlalchemy.url', url_regexp.sub('//', url))
        except Exception as e:
            logger.debug(f"sqlalchemy_inst receive_before_cursor_execute: {e}")
        return


    @event.listens_for(Engine, 'after_cursor_execute', named=True)
    def receive_after_cursor_execute(**kw):
        context = kw['context']

        if context and hasattr(context, "_stan_scope"):
            scope = context._stan_scope
            if scope:
                scope.close()


    # Handle dbapi_error event; deprecated since version 0.9
    error_event = "handle_error" if sqlalchemy.__version__[0] >= "1" else "dbapi_error"

    def _set_error_tags(context, exception_string, scope_string):
        scope, context_exception = None, None

        try: 
            if error_event == "dbapi_error":
                ctx_stan_scope = context
            else:
                ctx_stan_scope = attrgetter(scope_string.split(".")[0])(context)

            if hasattr(ctx_stan_scope, "_stan_scope") and hasattr(context, exception_string):
                scope = attrgetter(scope_string)(context)
                context_exception = attrgetter(exception_string)(context)

            if scope and context_exception:
                scope.span.log_exception(context_exception)
            else:
                scope.span.log_exception("No %s specified." % error_event)

            scope.close()
        except Exception as e:
            logger.debug(f"sqlalchemy_inst _set_error_tags: {e}")


    @event.listens_for(Engine, error_event, named=True)
    def receive_handle_db_error(**kw):

        if tracing_is_off():
            return

        # support older db error event
        if error_event == "dbapi_error":
            context = kw.get('context')
            exception_string = 'exception'
            scope_string = '_stan_scope'
        else:
            context = kw.get('exception_context')
            exception_string = 'sqlalchemy_exception'
            scope_string = 'execution_context._stan_scope'

        if context:
            _set_error_tags(context, exception_string, scope_string)


    logger.debug("Instrumenting sqlalchemy")

except ImportError:
    pass
