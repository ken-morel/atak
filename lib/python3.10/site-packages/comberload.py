import sys

from functools import wraps
from importlib import import_module
from threading import Thread
from types import ModuleType
from typing import Callable


class ComberloadModule(ModuleType):
    """
    A python module to register fallbacks till packages finish loading

    ```python
    import comberload

    @comberload("prompt_toolkit")
    def get_input():
        import prompt_toolkit

        return prompt_toolkit.prompt()

    @get_input.fallback
    def fallback_get_input():
        return input()

    get_input()  # immediately uses fallback

    get_input()  # abit later, uses prompt_toolkit
    ```

    """

    __version__ = "1.1.3"
    worker_running = False
    should_work = True
    backlog = []
    done = []
    comberloaders = []
    failed = []
    _callbacks: list[Callable] = []

    class ComberLoader:
        """
        wraps over a comberloaded function running it only when the
        requirements match
        """

        _fallback = None
        _fail = None

        def __init__(self, modules: list[str], func: Callable):
            """
            Creates a comberloaded which wraps you  function till it's
            packages finish loading
            """
            self.__func__ = func
            self.modules = modules
            ComberloadModule.comberloaders.append(self)
            self.comberloaded = (
                len(set(modules) - set(ComberloadModule.done)) == 0
            )
            if self.comberloaded:
                self.call = func
            self.failed = len(set(modules) & set(ComberloadModule.failed)) > 0
            if self.failed:
                self.comberloaded = False
            wraps(func)(self)

        def call(__comberloaded_special__self, *args, **kw):
            """
            The default call for comberloaded instance, calla the
            fallback if given, else returns None
            """
            if __comberloaded_special__self._fallback is None:
                return None
            return __comberloaded_special__self._fallback(*args, **kw)

        def fallback(self, func: Callable):
            """
            decorator registers function as fallback to use when loading
            incomplete
            """
            self._fallback = func
            return func

        def fail(self, func: Callable):
            """
            decorator registers function as fallback to use when loading
            incomplete
            """
            self._fail = func
            return func

        def failback(self, func: Callable):
            """
            decorator registers function as fallback to use when loading
            incomplete
            """
            self._fail = func
            self._fallback = func
            return func

        def __call__(__comberloaded_special__self, *args, **kw):
            """
            calls callback or function depending on if loading complete
            """
            if hasattr(__comberloaded_special__self, "__self__"):
                return __comberloaded_special__self.call(
                    __comberloaded_special__self.__self__, *args, **kw
                )
            else:
                return __comberloaded_special__self.call(*args, **kw)

        def __get__(self, instance, *__, **_):
            """
            sets the __self__
            """
            self.__self__ = instance
            return self

    def __init__(self):
        """
        Creates the module
        """
        super().__init__(__name__)

    def __call__(self, *modules):
        """
        THis registers modules for comberloading
        :param modules: The list of modules to load

        :returns: A registerer to conditionally call a function
        """
        self.backlog.extend(
            [mod for mod in modules if mod not in self.backlog]
        )
        self.start_worker()

        def register_func(func: Callable):
            """
            wraps the function in a comberloader providing fallback() to
            use before loading completes
            """
            return ComberloadModule.ComberLoader(modules, func)

        def register_callback(func: Callable):
            """
            registers func as callback
            :param func: The function

            :returns: func
            """
            ComberloadModule._callbacks.append((modules, func))
            return func

        register_func.callback = register_callback

        return register_func

    def install(self):
        sys.modules[__name__] = self

    def start_worker(self) -> bool:
        """
        starts comberload's importing worker

        :returns: If it actually started, will not if worker already running
        """
        if not self.worker_running:
            self._worker_thread = Thread(target=self._worker)
            self._worker_thread.start()
            return True
        else:
            return False

    def should_exit(self, val: bool = True):
        """
        Tells the worker to close after current import completion and not to
        start again

        :param val: If should or should not stop
        """
        self.should_work = not val

    def _worker(self):
        self.worker_running = True
        while len(self.backlog) > 0 and self.should_work:
            modules = self.backlog.pop()
            self.importing = True
            modules = modules.split(".")
            for depth in range(len(modules)):
                module = ".".join(modules[: depth + 1])
                if module in self.done:
                    continue
                try:
                    import_module(module)
                except (ModuleNotFoundError, ImportError) as e:
                    if module in self.backlog:
                        self.backlog.remove(module)
                    self.failed.append(module)
                    for loader in self.comberloaders:
                        if loader.comberloaded or loader.failed:
                            continue
                        if len(set(self.failed) & set(loader.modules)) > 0:
                            loader.comberloaded = False
                            loader.failed = True
                            loader.call = loader._fail
                            loader.error = e
                else:
                    if module in self.backlog:
                        self.backlog.remove(module)
                    self.done.append(module)
                    for loader in self.comberloaders:
                        if loader.comberloaded:
                            continue
                        if len(set(self.backlog) & set(loader.modules)) == 0:
                            loader.comberloaded = True
                            loader.call = loader.__func__
                    for idx, (mods, func) in reversed(
                        tuple(enumerate(self._callbacks[:]))
                    ):
                        if len(set(self.backlog) & set(mods)) == 0:
                            self._callbacks.pop(idx)
                            func()
            self.importing = False
        self.worker_running = False


ComberloadModule().install()
