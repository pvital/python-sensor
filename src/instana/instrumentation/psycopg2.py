# (c) Copyright IBM Corp. 2021
# (c) Copyright Instana Inc. 2019


import copy
import wrapt

from typing import Callable, Optional, Any, Tuple, Dict
from instana.log import logger
from instana.instrumentation.pep0249 import ConnectionFactory

try:
    import psycopg2
    import psycopg2.extras

    cf = ConnectionFactory(connect_func=psycopg2.connect, module_name="postgres")

    setattr(psycopg2, "connect", cf)
    if hasattr(psycopg2, "Connect"):
        setattr(psycopg2, "Connect", cf)

    @wrapt.patch_function_wrapper("psycopg2.extensions", "register_type")
    def register_type_with_instana(
        wrapped: Callable[..., Any],
        instance: Optional[Any],
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
    ) -> Callable[..., object]:
        args_clone = list(copy.copy(args))

        if (len(args_clone) >= 2) and hasattr(args_clone[1], "__wrapped__"):
            args_clone[1] = args_clone[1].__wrapped__

        return wrapped(*args_clone, **kwargs)

    @wrapt.patch_function_wrapper("psycopg2._json", "register_json")
    def register_json_with_instana(
        wrapped: Callable[..., Any],
        instance: Optional[Any],
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
    ) -> Callable[..., object]:
        if "conn_or_curs" in kwargs:
            if hasattr(kwargs["conn_or_curs"], "__wrapped__"):
                kwargs["conn_or_curs"] = kwargs["conn_or_curs"].__wrapped__

        return wrapped(*args, **kwargs)

    logger.debug("Instrumenting psycopg2")
except ImportError:
    pass
