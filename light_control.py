import asyncio
from kasa import SmartPlug


async def main():
    p = SmartPlug("10.0.0.180")

    await p.update()  # Request the update
    print(p.alias)  # Print out the alias

    await p.turn_on()  # Turn the device on

if __name__ == "__main__":
    asyncio.run(main())
