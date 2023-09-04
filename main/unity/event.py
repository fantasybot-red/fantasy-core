import os
import asyncio
import re


class Event:
    def __init__(self):
        # Initialise a list of listeners
        self.__listeners = {}

    # Define a getter for the 'on' property which returns the decorator.
    def interaction(self, name):
        # A declorator to run addListener on the input function.
        def wrapper(func):
            self.addListener(func, name)
            return func
        return wrapper

    # Add and remove functions from the list of listeners.
    def addListener(self, func, name):
        if not name in self.__listeners.keys():
            self.__listeners[name] = []
        self.__listeners[name].append(func)

    def removeListener(self, name):
        if name not in self.__listeners.keys(): return
        self.__listeners.pop(name)

    # Trigger events.
    async def trigger(self, name, interaction, components):
        run = False
        for reg in self.__listeners:
            pr = re.compile(reg)
            out = pr.match(name)
            if out:
                run = True
                args = list(out.groups())
                if components is not None:
                    args.insert(0, components)
                for i in self.__listeners[reg]:
                    asyncio.create_task(i(interaction, *args), name=f"event-{name}-{os.urandom(16).hex()}")
        return run