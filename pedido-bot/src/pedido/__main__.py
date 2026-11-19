"""`python -m pedido`: validate the setup (Portuguese refusal, exit code 1), then serve."""
import sys

from pedido import config
from pedido.db import StartupError
from pedido.startup import check_all


def argumentos_do_servidor() -> dict:
    """Production listens on all addresses and on the platform's PORT; local use only on this machine."""
    return {"host": config.host(), "port": config.porta()}


def main() -> int:
    try:
        check_all()
    except StartupError as error:
        print(str(error), file=sys.stderr)
        return 1
    import uvicorn

    from pedido.web.app import create_app

    try:
        app = create_app()
    except StartupError as error:  # the app checks keys and migrations too
        print(str(error), file=sys.stderr)
        return 1
    uvicorn.run(app, **argumentos_do_servidor())
    return 0


if __name__ == "__main__":
    sys.exit(main())
