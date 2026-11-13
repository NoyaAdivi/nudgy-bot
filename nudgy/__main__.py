import asyncio

# Python 3.14 no longer creates an event loop by itself, so we make one
asyncio.set_event_loop(asyncio.new_event_loop())

from .bot import main  # noqa: E402

main()