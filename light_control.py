import asyncio
from kasa import SmartPlug

plug = SmartPlug("127.0.0.1")
asyncio.run(plug.update())
plug.alias