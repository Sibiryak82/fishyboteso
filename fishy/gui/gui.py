import logging
import queue
import threading
import tkinter as tk
import uuid
from typing import Any, Callable, Dict, Optional
from dataclasses import dataclass

from ttkthemes import ThemedTk

from fishy.engine.common.event_handler import EngineEventHandler, IEngineHandler
from fishy.gui import config_top
from fishy.gui.funcs import GUIFuncs
from fishy.web import web

from ..helper.config import config
from ..helper.helper import wait_until
from . import main_gui
from .log_config import GUIStreamHandler


@dataclass
class EngineRunner:
    config: Callable
    start: Callable


class GUI:
    def __init__(self, get_engine: Callable[[], IEngineHandler]):
        self.funcs = GUIFuncs(self)
        self.get_engine = get_engine

        self.config = config
        self._start_restart = False
        self._destroyed = True
        self._log_strings = []
        self._function_queue = queue.Queue()
        self._result_dict: Dict[str, Any] = {}
        self._bot_running = False

        # UI items
        self._root: Optional[ThemedTk] = None
        self._console = None
        self._start_button = None
        self._notify_check = None
        self._engine_select: Optional[tk.OptionMenu] = None
        self._config_button: Optional[tk.Button] = None
        self._engine_var = None

        self._thread = threading.Thread(target=self.create, args=())

        self._notify = None
        self.login = None

        root_logger = logging.getLogger('')
        root_logger.setLevel(logging.DEBUG)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        new_console = GUIStreamHandler(self)
        root_logger.addHandler(new_console)

    @property
    def engine(self):
        return self.get_engine()

    @property
    def engines(self):
        engines = {
            "Semi Fisher": EngineRunner(lambda: config_top.start_semifisher_config(self),
                                        self.engine.toggle_semifisher),

            "Full-Auto Fisher": EngineRunner(lambda: config_top.start_fullfisher_config(self),
                                             self.engine.toggle_fullfisher)
        }

        return engines

    def create(self):
        main_gui._create(self)

    def start(self):
        self._thread.start()

    def _clear_function_queue(self):
        while not self._function_queue.empty():
            _id, func = self._function_queue.get()
            result = func()
            self._result_dict[_id] = result

    def call_in_thread(self, func: Callable, block=False):
        _id = str(uuid.uuid4())
        self._function_queue.put((_id, func))

        if not block:
            return None

        wait_until(lambda: _id in self._result_dict)

        return self._result_dict.pop(_id)

    def _get_start_stop_text(self):
        return "STOP (F9)" if self._bot_running else "START (F9)"
