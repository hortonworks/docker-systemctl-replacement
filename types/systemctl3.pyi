# Stubs for systemctl3 (Python 3)
#
# NOTE: This dynamically typed stub was automatically generated by stubgen.

import collections
import logging
from collections import namedtuple
from typing import Callable, Dict, Iterable, List, NoReturn, Optional, TextIO, Tuple, Type, Union
from typing import NamedTuple, Match, TextIO, BinaryIO, Sequence, overload, Generator
from types import TracebackType

_extra_vars: List[str]
_system_folder1: Optional[str]
_all_common_enabled: List[str]
basestring: Type[str]
__copyright__: str
__version__: str
logg: logging.Logger
DEBUG_AFTER: bool
DEBUG_STATUS: bool
DEBUG_BOOTTIME: bool
DEBUG_INITLOOP: bool
DEBUG_KILLALL: bool
def logg_debug_flock(format: str, *args: Union[str, int]) -> None: ...
def logg_debug_after(format: str, *args: Union[str, int]) -> None: ...
NOT_A_PROBLEM: int
NOT_OK: int
NOT_ACTIVE: int
NOT_FOUND: int
_force: bool
_full: bool
_now: bool
_no_legend: bool
_no_ask_password: bool
_preset_mode: str
_quiet: bool
_root: str
_unit_type: Optional[str]
_unit_state: Optional[str]
_unit_property: Optional[str]
_show_all: bool
_user_mode: bool
_system_folder1: Optional[str]
_system_folder2: Optional[str]
_system_folder3: Optional[str]
_system_folder4: Optional[str]
_system_folder9: Optional[str]
_user_folder1: Optional[str]
_user_folder2: Optional[str]
_user_folder3: Optional[str]
_user_folder4: Optional[str]
_user_folder9: Optional[str]
_init_folder1: Optional[str]
_init_folder2: Optional[str]
_init_folder9: Optional[str]
_preset_folder1: Optional[str]
_preset_folder2: Optional[str]
_preset_folder3: Optional[str]
_preset_folder4: Optional[str]
_preset_folder9: Optional[str]
SystemCompatibilityVersion: int
SysInitTarget: str
SysInitWait: int
MinimumYield: float
MinimumTimeoutStartSec: int
MinimumTimeoutStopSec: int
DefaultTimeoutStartSec: int
DefaultTimeoutStopSec: int
DefaultTimeoutAbortSec: int
DefaultMaximumTimeout: int
DefaultRestartSec: float
DefaultStartLimitIntervalSec: int
DefaultStartLimitBurst: int
InitLoopSleep: int
MaxLockWait: int
DefaultPath: str
ResetLocale: List[str]
ExitWhenNoMoreServices: bool
ExitWhenNoMoreProcs: bool
DefaultUnit: str
DefaultTarget: str
REMOVE_LOCK_FILE: bool
BOOT_PID_MIN: int
BOOT_PID_MAX: int
PROC_MAX_DEPTH: int
EXPAND_VARS_MAXDEPTH: int
EXPAND_KEEP_VARS: bool
RESTART_FAILED_UNITS: bool
_pid_file_folder: str
_journal_log_folder: str
SYSTEMCTL_DEBUG_LOG: str
SYSTEMCTL_EXTRA_LOG: str
_default_targets: List[str]
_feature_targets: List[str]
_all_common_targets: List[str]
_all_common_enabled: List[str]
_all_common_disabled: List[str]
_runlevel_mappings: Dict[str, str]
_sysv_mappings: Dict[str, str]

def strINET(value: int) -> str: ...
def strYes(value: Union[str, bool, None]) -> str: ...
def strE(part: Union[str, int, float, None]) -> str: ...
def strQ(part: Union[str, int, None]) -> str: ...
def shell_cmd(cmd: List[str]) -> str: ...
def to_int(value: str, default: int = ...) -> int: ...
def to_intN(value: Optional[str], default: Optional[int] = ...) -> Optional[int]: ...
def to_list(value: Union[str, List[str], Tuple[str], Tuple[str, ...], None]) -> List[str]: ...
def unit_of(module: str) -> str: ...
def int_mode(value: str) -> Optional[int]: ...
def o22(part: str) -> str: ...
def o44(part: str) -> str: ...
def o77(part: str) -> str: ...
def path44(filename: Optional[str]) -> str: ...
def unit_name_escape(text: str) -> str: ...
def unit_name_unescape(text: str) -> str: ...
def is_good_root(root: Optional[str]) -> bool: ...
def os_path(root: Optional[str], path: str) -> str: ...
def path_replace_extension(path: str, old: str, new: str) -> str: ...
def get_PAGER() -> List[str]: ...
def os_getlogin() -> str: ...
def get_runtime_dir() -> str: ...
def get_RUN(root: bool = False) -> str: ...
def get_PID_DIR(root: bool = False) -> str: ...
def get_home() -> str: ...
def get_HOME(root: bool = False) -> str: ...
def get_USER_ID(root: bool = False) -> int: ...
def get_USER(root: bool = False) -> str: ...
def get_GROUP_ID(root: bool = False) -> int: ...
def get_GROUP(root: bool = False) -> str: ...
def get_TMP(root: bool = False) -> str: ...
def get_VARTMP(root: bool = False) -> str: ...
def get_SHELL(root: bool = False) -> str: ...
def get_RUNTIME_DIR(root: bool = False) -> str: ...
def get_CONFIG_HOME(root: bool = False) -> str: ...
def get_CACHE_HOME(root: bool = False) -> str: ...
def get_DATA_HOME(root: bool = False) -> str: ...
def get_LOG_DIR(root: bool = False) -> str: ...
def get_VARLIB_HOME(root: bool = False) -> str: ...
def expand_path(path: str, root: bool = False) -> str: ...
def shutil_chown(path: str, user: Optional[str], group: Optional[str]) -> None: ...
def shutil_fchown(fileno: int, user: Optional[str], group: Optional[str]) -> None: ...
def shutil_setuid(user: Optional[str] = ..., group: Optional[str] = ..., xgroups: Optional[List[str]] = ...) -> Dict[str, str]: ...
def shutil_truncate(filename: str) -> None: ...
def pid_exists(pid: int) -> bool: ...
def _pid_exists(pid: int) -> bool: ...
def pid_zombie(pid: int) -> bool: ...
def _pid_zombie(pid: int) -> bool: ...
def checkstatus(cmd: str) -> Tuple[bool, str]: ...
def ignore_signals_and_raise_keyboard_interrupt(signame: str) -> None: ...

_default_dict_type: Type[Dict[str, List[str]]]
_default_conf_type: Type[Dict[str, Dict[str, List[str]]]]

class SystemctlConfData:
    _defaults: Dict[str, str]
    _conf_type: Type[Dict[str, Dict[str, List[str]]]]
    _dict_type: Type[Dict[str, List[str]]]
    _allow_no_value: bool
    _conf: Dict[str, Dict[str, List[str]]]
    _files: List[str]
    def __init__(self, defaults: Optional[Dict[str, str]] = ..., dict_type: Optional[Type[Dict[str, List[str]]]] = ...,
                 conf_type: Optional[Type[Dict[str, Dict[str, List[str]]]]] = ..., allow_no_value: bool = ...) -> None: ...
    def defaults(self) -> Dict[str, str]: ...
    def sections(self) -> List[str]: ...
    def add_section(self, section: str) -> None: ...
    def has_section(self, section: str) -> bool: ...
    def has_option(self, section: str, option: str) -> bool: ...
    def set(self, section: str, option: str, value: Optional[str]) -> None: ...
    def get(self, section: str, option: str, default: Optional[str] = None, allow_no_value: bool = ...) -> Optional[str]: ...
    def getstr(self, section: str, option: str, default: Optional[str] = None, allow_no_value: bool = ...) -> str: ...
    def getlist(self, section: str, option: str, default: Optional[List[str]] = ..., allow_no_value: bool = ...) -> List[str]: ...
    def filenames(self) -> List[str]: ...

class SystemctlConfigParser(SystemctlConfData):
    def read(self, filename: str) -> SystemctlConfigParser: ...
    def read_sysd(self, filename: str) -> SystemctlConfigParser: ...
    def read_sysv(self, filename: str) -> SystemctlConfigParser: ...
    def systemd_sysv_generator(self, filename: str) -> None: ...
UnitConfParser = SystemctlConfigParser

class SystemctlSocket:
    def __init__(self, conf: SystemctlConf, sock: socket.socket, skip: bool = False) -> None: ...
    def fileno(self) -> int: ...
    def listen(self, backlog: Optional[int] = None) -> None: ...
    def name(self) -> str: ...
    def addr(self) -> str: ...
    def close(self) -> None: ...
class SystemctlConf:
    data: SystemctlConfData
    env: Dict[str, str]
    status: Optional[Dict[str, str]]
    masked: Optional[str]
    module: Optional[str]
    nonloaded_path: str
    drop_in_files: Dict[str, str]
    _root: str
    _user_mode: bool
    def __init__(self, data: SystemctlConfData, module: Optional[str] = ...) -> None: ...
    def root_mode(self) -> bool: ...
    def loaded(self) -> str: ...
    def filename(self) -> Optional[str]: ...
    def overrides(self) -> List[str]: ...
    def name(self) -> str: ...
    def set(self, section: str, name: str, value: Optional[str]) -> None: ...
    def get(self, section: str, name: str, default: Optional[str], allow_no_value: bool = None) -> str: ...
    def getlist(self, section: str, name: str, default: Optional[List[str]] = None, allow_no_value: bool = None) -> List[str]: ...
    def getbool(self, section: str, name: str, default: Optional[str] = None) -> bool: ...


class PresetFile:
    _files: List[str] = ...
    _lines: List[str] = ...
    def __init__(self) -> None: ...
    def filename(self) -> Optional[str]: ...
    def read(self, filename: str) -> PresetFile: ...
    def get_preset(self, unit: str) -> Optional[str]: ...

class waitlock:
    conf: SystemctlConf = ...
    opened: int = ...
    lockfolder: str = ...
    def __init__(self, conf: SystemctlConf) -> None: ...
    def lockfile(self) -> str: ...
    def __enter__(self) -> bool: ...
    def __exit__(self, type: Optional[Type[BaseException]], value: Optional[BaseException], traceback: Optional[TracebackType]) -> None: ...

def must_have_failed(waitpid: SystemctlWaitPID, cmd: List[str]) -> SystemctlWaitPID: ...
def subprocess_waitpid(pid: int) -> SystemctlWaitPID: ...
def subprocess_testpid(pid: int) -> SystemctlWaitPID: ...
def parse_unit(fullname: str) -> SystemctlUnitName: ...
def time_to_seconds(text: str, maximum: float) -> float: ...
def seconds_to_time(seconds: float) -> str: ...
def getBefore(conf: SystemctlConf) -> List[str]:
    result: List[str]
def getAfter(conf: SystemctlConf) -> List[str]:
    result: List[str]
def compareAfter(confA: SystemctlConf, confB: SystemctlConf) -> int: ...
def conf_sortedAfter(conflist: Iterable[SystemctlConf], cmp: Callable[[SystemctlConf, SystemctlConf], int] = ...) -> List[SystemctlConf]:
    class SortTuple:
        def __init__(self, rank: int, conf: SystemctlConf) -> None: ...

class SystemctlListenThread:
    def __init__(self, systemctl: Systemctl) -> None: ...
    def stop(self) -> None: ...
    def run(self) -> None: ...

class Systemctl:
    error: int = ...
    _extra_vars: List[str] = ...
    _force: bool = ...
    _full: bool = ...
    _init: bool = ...
    _no_ask_password: bool = ...
    _no_legend: bool = ...
    _now: bool = ...
    _preset_mode: str = ...
    _quiet: bool = ...
    _root: str = ...
    _show_all: bool = ...
    _unit_property: Optional[str] = ...
    _unit_state: Optional[str] = ...
    _unit_type: Optional[str] = ...
    _systemd_version: int = ...
    _pid_file_folder: str = ...
    _journal_log_folder: str = ...
    _loaded_file_sysv: Dict[str, SystemctlConf] = ...
    _loaded_file_sysd: Dict[str, SystemctlConf] = ...
    _file_for_unit_sysv: Optional[Dict[str, str]] = ...
    _file_for_unit_sysd: Optional[Dict[str, str]] = ...
    _preset_file_list: Optional[Dict[str, PresetFile]] = ...
    _default_target: str = ...
    _sysinit_target: Optional[SystemctlConf] = ...
    doExitWhenNoMoreProcs: bool = ...
    doExitWhenNoMoreServices: bool = ...
    _user_mode: bool = ...
    _user_getlogin: str = ...
    _log_file: Dict[str, int] = ...
    _log_hold: Dict[str, bytes] = ...
    _boottime: Optional[float] = ...
    _SYSTEMD_UNIT_PATH: Optional[str] = ...
    _SYSTEMD_SYSVINIT_PATH: Optional[str] = ...
    _SYSTEMD_PRESET_PATH: Optional[str] = ...
    _restarted_unit: Dict[str, List[float]] = ...
    _restart_failed_units: Dict[str, float] = ...
    _sockets: Dict[str, SystemctlSocket] = ...
    loop: threading.Lock = threading.Lock()
    def __init__(self) -> None: ...
    def user(self) -> str: ...
    def user_mode(self) -> bool: ...
    def user_folder(self) -> str: ...
    def system_folder(self) -> str: ...
    def preset_folders(self) -> Iterable[str]: ...
    def init_folders(self) -> Iterable[str]: ...
    def user_folders(self) -> Iterable[str]: ...
    def system_folders(self) -> Iterable[str]: ...
    def get_SYSTEMD_UNIT_PATH(self) -> str: ...
    def get_SYSTEMD_SYSVINIT_PATH(self) -> str: ...
    def get_SYSTEMD_PRESET_PATH(self) -> str: ...
    def sysd_folders(self) -> Iterable[str]: ...
    def scan_unit_sysd_files(self, module: Optional[str] = None) -> List[str]: ... # -> [ unit-names,... ]
    def scan_unit_sysv_files(self, module: Optional[str] = None) -> List[str]: ... # -> [ unit-names,... ]
    def unit_sysd_file(self, module: Optional[str] = None) -> Optional[str]: ... # -> filename?
    def unit_sysv_file(self, module: Optional[str] = None) -> Optional[str]: ... # -> filename?
    def unit_file(self, module: Optional[str] = None) -> Optional[str]: ... # -> filename?
    def is_sysv_file(self, filename: Optional[str]) -> Optional[bool]: ...
    def is_user_conf(self, conf: SystemctlConf) -> bool: ...
    def not_user_conf(self, conf: SystemctlConf) -> bool: ...
    def find_drop_in_files(self, unit: str) -> Dict[str, str]:
        result: Dict[str, str]
    def load_sysd_template_conf(self, module: Optional[str]) -> Optional[SystemctlConf]: ... # -> conf?
    def load_sysd_unit_conf(self, module: Optional[str]) -> Optional[SystemctlConf]: # -> conf?
        drop_in_files: Dict[str, str]
    def load_sysv_unit_conf(self, module: Optional[str]) -> Optional[SystemctlConf]: ... # -> conf?
    def load_unit_conf(self, module: Optional[str]) -> Optional[SystemctlConf]: ... # -> conf | None(not-found)
    def default_unit_conf(self, module: str, description: Optional[str] = None) -> SystemctlConf: ... # -> conf
    def get_unit_conf(self, module: str) -> SystemctlConf: ... # -> conf (conf | default-conf)
    def get_unit_type(self, module: str) -> Optional[str]: ...
    def get_unit_section(self, module: str, default: str = "Service") -> str: ...
    def get_unit_section_from(self, conf: SystemctlConf, default: str = "Service") -> str: ...
    def match_sysd_templates(self, modules: Optional[List[str]] = None, suffix: str = ".service") -> Iterable[str]: ... # -> generate[ unit ]
    def match_sysd_units(self, modules: Optional[List[str]] = None, suffix: str = ".service") -> Iterable[str]: ... # -> generate[ unit ]
    def match_sysv_units(self, modules: Optional[List[str]] = None, suffix: str = ".service") -> Iterable[str]: ... # -> generate[ unit ]
    def match_units(self, modules: Optional[List[str]] = None, suffix: str = ".service") -> List[str]: # -> [ units,.. ]
        found: List[str]
    def list_service_unit_basics(self) -> List[Tuple[str, str, str]]:
        result: List[Tuple[str, str, str]]
    def list_service_units(self, *modules: str) -> List[Tuple[str, str, str]]: # -> [ (unit,loaded+active+substate,description) ]
        result: Dict[str, str]
        active: Dict[str, str]
        substate: Dict[str, str]
        description: Dict[str, str]
    def list_units_modules(self, *modules: str) -> List[Tuple[str, str, str, ]]: ... # -> [ (unit,loaded,description) ]
    def list_service_unit_files(self, *modules: str) -> List[Tuple[str, str]]: # -> [ (unit,enabled) ]
        result: Dict[str, Optional[SystemctlConf]]
        enabled: Dict[str, str]
    def each_target_file(self) -> Iterable[Tuple[str, str]]: ...
    def list_target_unit_files(self, *modules: str) -> List[Tuple[str, str]]: # -> [ (unit,enabled) ]
        enabled: Dict[str, str]
        targets: Dict[str, Optional[str]]
    def list_unit_files_modules(self, *modules: str) -> List[Tuple[str, str]]: # -> [ (unit,enabled) ]
        result: List[Tuple[str, str]]
    def get_description(self, unit: str, default: Optional[str] = None) -> str: ...
    def get_description_from(self, conf: Optional[SystemctlConf], default: Optional[str] = None) -> str: ... # -> text
    def read_pid_file(self, pid_file: str, default: Optional[int] = None) -> Optional[int]: ...
    def wait_pid_file(self, pid_file: str, timeout: Optional[int] = None) -> Optional[int]: ... # -> pid?
    def get_status_pid_file(self, unit: str) -> str: ... # -> text
    def pid_file_from(self, conf: SystemctlConf, default: str = "") -> str: ...
    def get_pid_file(self, conf: SystemctlConf, default: Optional[str] = None) -> str: ...
    def read_mainpid_from(self, conf: SystemctlConf, default: Optional[int] = None) -> Optional[int]: ...
    def clean_pid_file_from(self, conf: SystemctlConf) -> None: ...
    def get_status_file(self, unit: str) -> str: ... # for testing
    def get_status_file_from(self, conf: SystemctlConf, default: Optional[str] = None) -> str: ...
    def get_StatusFile(self, conf: SystemctlConf, default: Optional[str] = None) -> str: ... # -> text
    def clean_status_from(self, conf: SystemctlConf) -> None: ...
    def write_status_from(self, conf: SystemctlConf, **status: Union[str, int, None]) -> bool: ... # -> bool(written)
    def read_status_from(self, conf: SystemctlConf) -> Dict[str, str]:
        status: Dict[str, str]
    def get_status_from(self, conf: SystemctlConf, name: str, default: Optional[str] = None) -> Optional[str]: ...
    def set_status_from(self, conf: SystemctlConf, name: str, value: Optional[str]) -> None: ...
    def get_boottime(self) -> float: ...
    def get_boottime_from_proc(self) -> float: ...
    def get_boottime_from_old_proc(self) -> float: ...
    def path_proc_started(self, proc: str) -> float: ...
    def get_filetime(self, filename: str) -> float: ...
    def truncate_old(self, filename: str) -> bool: ...
    def getsize(self, filename: str) -> int: ...
    def read_env_file(self, env_file: str) -> Iterable[Tuple[str, str]]: ... # -> generate[ (name,value) ]
    def read_env_part(self, env_part: str) -> Iterable[Tuple[str, str]]: ... # -> generate[ (name, value) ]
    def command_of_unit(self, unit: str) -> Union[None, List[str]]: ...
    def environment_of_unit(self, unit: str) -> Union[None, Dict[str, str]]: ...
    def extra_vars(self) -> List[str]: ...
    def get_env(self, conf: SystemctlConf) -> Dict[str, str]: ...
    def expand_env(self, cmd: str, env: Dict[str, str]) -> str:
        def get_env1(m: Match[str]) -> str: ...
        def get_env2(m: Match[str]) -> str: ...
    def expand_special(self, cmd: str, conf: SystemctlConf) -> str:
        def xx(arg: str) -> str: ...
        def yy(arg: str) -> str: ...
        def get_confs(conf: SystemctlConf) -> Dict[str, str]: ...
        def get_conf1(m: Match[str]) -> str: ...
    def exec_newcmd(self, cmd: str, env: Dict[str, str], conf: SystemctlConf) -> Tuple[ExecMode, List[str]]: ...
    def exec_cmd(self, cmd: str, env: Dict[str, str], conf: SystemctlConf) -> List[str]:
        def get_env1(m: Match[str]) -> str: ...
        def get_env2(m: Match[str]) -> str: ...
        newcmd: List[str]
    def remove_service_directories(self, conf: SystemctlConf, section: str = "Service") -> bool:
        env: Dict[str, str]
    def do_rm_tree(self, path: str) -> bool: ...
    def get_RuntimeDirectoryPreserve(self, conf: SystemctlConf, section: str = "Service") -> bool: ...
    def get_RuntimeDirectory(self, conf: SystemctlConf, section: str = "Service") -> str: ...
    def get_StateDirectory(self, conf: SystemctlConf, section: str = "Service") -> str: ...
    def get_CacheDirectory(self, conf: SystemctlConf, section: str = "Service") -> str: ...
    def get_LogsDirectory(self, conf: SystemctlConf, section: str = "Service") -> str: ...
    def get_ConfigurationDirectory(self, conf: SystemctlConf, section: str = "Service") -> str: ...
    def get_RuntimeDirectoryMode(self, conf: SystemctlConf, section: str = "Service") -> str: ...
    def get_StateDirectoryMode(self, conf: SystemctlConf, section: str = "Service") -> str: ...
    def get_CacheDirectoryMode(self, conf: SystemctlConf, section: str = "Service") -> str: ...
    def get_LogsDirectoryMode(self, conf: SystemctlConf, section: str = "Service") -> str: ...
    def get_ConfigurationDirectoryMode(self, conf: SystemctlConf, section: str = "Service") -> str: ...
    def clean_service_directories(self, conf: SystemctlConf, which: str = "") -> bool: ...
    def env_service_directories(self, conf: SystemctlConf) -> Dict[str, str]: ...
    def create_service_directories(self, conf: SystemctlConf) -> Dict[str, str]: ...
    def make_service_directory(self, path: str, mode: str) -> bool: ...
    def chown_service_directory(self, path: str, user: Optional[str], group: Optional[str]) -> bool: ...
    def do_chown_tree(self, path: str, user: Optional[str], group: Optional[str]) -> bool: ...
    def clean_modules(self, *modules: str) -> bool:
        units: List[str]
    def clean_units(self, units: List[str], what: str = "") -> bool: ...
    def clean_unit(self, unit: str, what: str = "") -> bool: ...
    def clean_unit_from(self, conf: SystemctlConf, what: str) -> bool: ...
    def log_modules(self, *modules: str) -> bool:
        units: List[str]
    def log_units(self, units: List[str], lines: Optional[int] = None, follow: bool = False) -> int: ...
    def log_unit(self, unit: str, lines: Optional[int] = None, follow: bool = False) -> int: ...
    def log_unit_from(self, conf: SystemctlConf, lines: Optional[int] = None, follow: bool = False) -> int: ...
    def get_journal_log_from(self, conf: SystemctlConf) -> str: ... # never None
    def get_journal_log(self, conf: SystemctlConf) -> str: ... # never None
    def open_journal_log(self, conf: SystemctlConf) -> TextIO: ...
    def skip_journal_log(self, conf: SystemctlConf) -> bool: ...
    def dup2_journal_log(self, conf: SystemctlConf) -> None:
        out: Optional[TextIO]
    def get_WorkingDirectory(self, conf: SystemctlConf) -> str: ...
    def chdir_workingdir(self, conf: SystemctlConf) -> Union[str, bool, None]: ...
    def get_notify_socket_from(self, conf: SystemctlConf, socketfile: Optional[str] = None, debug: bool = False) -> str: ...
    def notify_socket_from(self, conf: SystemctlConf, socketfile: Optional[str] = None) -> NotifySocket: ...
    def read_notify_socket(self, notify: NotifySocket, timeout: float) -> str: ...
    def wait_notify_socket(self, notify: NotifySocket, timeout: float, pid: Optional[int] = None, pid_file: Optional[str] = None) -> Dict[str, str]:
        results: Dict[str, str]
    def start_modules(self, *modules: str) -> bool:
        units: List[str]
    def start_units(self, units: List[str], init: Optional[bool] = None) -> bool: ...
    def start_unit(self, unit: str) -> bool: ...
    def get_TimeoutStartSec(self, conf: SystemctlConf) -> float: ...
    def get_SocketTimeoutSec(self, conf: SystemctlConf) -> float: ...
    def get_RemainAfterExit(self, conf: SystemctlConf) -> bool: ...
    def start_unit_from(self, conf: SystemctlConf) -> bool: ...
    def do_start_unit_from(self, conf: SystemctlConf) -> bool: ...
    def do_start_service_from(self, conf: SystemctlConf) -> bool: ...
    def listen_modules(self, *modules: str) -> bool:
        units: List[str]
    def listen_units(self, units: List[str]) -> bool: ...
    def listen_unit(self, unit: str) -> bool: ...
    def listen_unit_from(self, conf: SystemctlConf) -> bool: ...
    def do_listen_unit_from(self, conf: SystemctlConf) -> bool: ...
    def do_accept_socket_from(self, conf: SystemctlConf, sock: socket.socket) -> bool: ...
    def get_socket_service_from(self, conf: SystemctlConf) -> str: ...
    def do_start_socket_from(self, conf: SystemctlConf) -> bool: ...
    def create_socket(self, conf: SystemctlConf) -> Optional[socket.socket]: ...
    def create_unix_socket(self, conf: SystemctlConf, path: str, dgram: bool) -> Optional[socket.socket]: ...
    def create_port_socket(self, conf: SystemctlConf, port: str, dgram: bool) -> Optional[socket.socket]: ...
    def create_port_ipv4_socket(self, conf: SystemctlConf, addr: str, port: str, dgram: bool) -> Optional[socket.socket]: ...
    def create_port_ipv6_socket(self, conf: SystemctlConf, addr: str, port: str, dgram: bool) -> Optional[socket.socket]: ...
    def extend_exec_env(self, env: Dict[str, str]) -> Dict[str, str]: ...
    def expand_list(self, group_lines: List[str], conf: SystemctlConf) -> List[str]: ...
    def get_User(self, conf: SystemctlConf) -> Optional[str]: ...
    def get_Group(self, conf: SystemctlConf) -> Optional[str]: ...
    def get_SupplementaryGroups(self, conf: SystemctlConf) -> List[str]: ...
    def skip_journal_log(self, conf: SystemctlConf) -> bool: ...
    def dup2_journal_log(self, conf: SystemctlConf) -> None: ...
    def execve_from(self, conf: SystemctlConf, cmd: List[str], env: Dict[str, str]) -> NoReturn:
        # cmd_args: Sequence[str]
        cmd_args: List[Union[str, bytes]]
    def test_start_unit(self, unit: str) -> None: ...
    def stop_modules(self, *modules: str) -> bool:
        units: List[str]
    def stop_units(self, units: List[str]) -> bool: ...
    def stop_unit(self, unit: str) -> bool: ...
    def get_TimeoutStopSec(self, conf: SystemctlConf) -> float: ...
    def stop_unit_from(self, conf: SystemctlConf) -> bool: ...
    def do_stop_unit_from(self, conf: SystemctlConf) -> bool: ...
    def do_stop_service_from(self, conf: SystemctlConf) -> bool:
        pid: Optional[int]
    def do_stop_socket_from(self, conf: SystemctlConf) -> bool: ...
    def wait_vanished_pid(self, pid: int, timeout: float) -> bool: ...
    def reload_modules(self, *modules: str) -> bool:
        units: List[str]
    def reload_units(self, units: List[str]) -> bool: ...
    def reload_unit(self, unit: str) -> bool: ...
    def reload_unit_from(self, conf: SystemctlConf) -> bool: ...
    def do_reload_unit_from(self, conf: SystemctlConf) -> bool: ...
    def do_reload_service_from(self, conf: SystemctlConf) -> bool: ...
    def restart_modules(self, *modules: str) -> bool:
        units: List[str]
    def restart_units(self, units: List[str]) -> bool: ...
    def restart_unit(self, unit: str) -> bool: ...
    def restart_unit_from(self, conf: SystemctlConf) -> bool: ...
    def do_restart_unit_from(self, conf: SystemctlConf) -> bool: ...
    def try_restart_modules(self, *modules: str) -> bool:
        units: List[str]
    def try_restart_units(self, units: List[str]) -> bool: ...
    def try_restart_unit(self, unit: str) -> bool: ...
    def reload_or_restart_modules(self, *modules: str) -> bool:
        units: List[str]
    def reload_or_restart_units(self, units: List[str]) -> bool: ...
    def reload_or_restart_unit(self, unit: str) -> bool: ...
    def reload_or_restart_unit_from(self, conf: SystemctlConf) -> bool: ...
    def do_reload_or_restart_unit_from(self, conf: SystemctlConf) -> bool: ...
    def reload_or_try_restart_modules(self, *modules: str) -> bool:
        units: List[str]
    def reload_or_try_restart_units(self, units: List[str]) -> bool: ...
    def reload_or_try_restart_unit(self, unit: str) -> bool: ...
    def reload_or_try_restart_unit_from(self, conf: SystemctlConf) -> bool: ...
    def do_reload_or_try_restart_unit_from(self, conf: SystemctlConf) -> bool: ...
    def kill_modules(self, *modules: str) -> bool:
        units: List[str]
    def kill_units(self, units: List[str]) -> bool: ...
    def kill_unit(self, unit: str) -> bool: ...
    def kill_unit_from(self, conf: SystemctlConf) -> bool: ...
    def do_kill_unit_from(self, conf: SystemctlConf) -> bool: ...
    def _kill_pid(self, pid: int, kill_signal: Optional[int] = None) -> bool: ...
    def is_active_modules(self, *modules: str) -> List[str]:
        units: List[str]
        results: List[str]
    def is_active_from(self, conf: SystemctlConf) -> bool: ...
    def active_pid_from(self, conf: SystemctlConf) -> Optional[int]: ...
    def is_active_pid(self, pid: Optional[int]) -> Optional[int]: ...
    def get_active_unit(self, unit: str) -> str: ...
    def get_active_from(self, conf: SystemctlConf) -> str: ...
    def get_active_service_from(self, conf: Optional[SystemctlConf]) -> str: ...
    def get_active_target_from(self, conf: SystemctlConf) -> str: ...
    def get_active_target(self, target: str) -> str: ...
    def get_active_target_list(self) -> List[str]: ...
    def get_substate_from(self, conf: SystemctlConf) -> Optional[str]: ...
    def is_failed_modules(self, *modules: str) -> List[str]:
        units: List[str]
        results: List[str]
    def is_failed_from(self, conf: SystemctlConf) -> bool: ...
    def reset_failed_modules(self, *modules: str) -> bool:
        units: List[str]
    def reset_failed_unit(self, unit: str) -> bool: ...
    def reset_failed_from(self, conf: SystemctlConf) -> bool: ...
    def status_modules(self, *modules: str) -> str:
        units: List[str]
    def status_units(self, units: List[str]) -> str: ...
    def status_unit(self, unit: str) -> Tuple[int, str]: ...
    def cat_modules(self, *modules: str) -> str:
        units: List[str]
    def cat_units(self, units: List[str]) -> str: ...
    def cat_unit(self, unit: str) -> Optional[str]: ...
    def load_preset_files(self, module: Optional[str] = None) -> List[str]: ... # -> [ preset-file-names,... ]
    def get_preset_of_unit(self, unit: str) -> Optional[str]: ...
    def preset_modules(self, *modules: str) -> bool:
        units: List[str]
    def preset_units(self, units: List[str]) -> bool: ...
    def preset_all_modules(self, *modules: str) -> bool: ...
    def wanted_from(self, conf: SystemctlConf, default: Optional[str] = None) -> Optional[str]: ...
    def enablefolders(self, wanted: str) -> Iterable[str]: ...
    def enablefolder(self, wanted: str) -> str: ...
    def default_enablefolder(self, wanted: str, basefolder: Optional[str] = None) -> str: ...
    def enable_modules(self, *modules: str) -> bool:
        units: List[str]
    def enable_units(self, units: List[str]) -> bool: ...
    def enable_unit(self, unit: str) -> bool: ...
    def enable_unit_from(self, conf: SystemctlConf) -> bool: ...
    def rc3_root_folder(self) -> str: ...
    def rc5_root_folder(self) -> str: ...
    def enable_unit_sysv(self, unit_file: str) -> bool: ...
    def _enable_unit_sysv(self, unit_file: str, rc_folder: str) -> bool: ...
    def disable_modules(self, *modules: str) -> bool:
        units: List[str]
    def disable_units(self, units: List[str]) -> bool: ...
    def disable_unit(self, unit: str) -> bool: ...
    def disable_unit_from(self, conf: SystemctlConf) -> bool: ...
    def disable_unit_sysv(self, unit_file: str) -> bool: ...
    def _disable_unit_sysv(self, unit_file: str, rc_folder: str) -> bool: ...
    def is_enabled_sysv(self, unit_file: str) -> bool: ...
    def is_enabled_modules(self, *modules: str) -> List[str]:
        units: List[str]
    def is_enabled_units(self, units: List[str]) -> List[str]:
        infos: List[str]
    def is_enabled(self, unit: str) -> bool: ...
    def enabled_unit(self, unit: str) -> str: ...
    def enabled_from(self, conf: SystemctlConf) -> str: ...
    def get_enabled_from(self, conf: SystemctlConf) -> str: ...
    def mask_modules(self, *modules: str) -> bool:
        units: List[str]
    def mask_units(self, units: List[str]) -> bool: ...
    def mask_unit(self, unit: str) -> bool: ...
    def mask_folder(self) -> str: ...
    def mask_folders(self) -> Iterable[str]: ...
    def unmask_modules(self, *modules: str) -> bool:
        units: List[str]
    def unmask_units(self, units: List[str]) -> bool: ...
    def unmask_unit(self, unit: str) -> bool: ...
    def list_dependencies_modules(self, *modules: str) -> List[str]:
        units: List[str]
    def list_dependencies_units(self, units: List[str]) -> List[str]:
        result: List[str]
    def list_dependencies_unit(self, unit: str) -> List[str]:
        result: List[str]
    def list_dependencies(self, unit: str, indent: Optional[str] = None, mark: Optional[str] = None, loop: List[str] = []) -> Iterable[str]:
        mapping: Dict[str, str]
    def get_dependencies_unit(self, unit: str, styles: Optional[List[str]] = None) -> Dict[str, str]:
        deps: Dict[str, str]
    def get_required_dependencies(self, unit: str, styles: Optional[List[str]] = None) -> Dict[str, str]: ...
    def get_start_dependencies(self, unit: str, styles: Optional[List[str]] = None) -> Dict[str, List[str]]: # pragma: no cover
        deps: Dict[str, List[str]]
    def list_start_dependencies_modules(self, *modules: str) -> List[Tuple[str, str]]: ...
    def list_start_dependencies_units(self, units: List[str]) -> List[Tuple[str, str]]:
        unit_order: List[str]
        deps: Dict[str, List[str]]
        deps_conf: List[SystemctlConf]
        result: List[Tuple[str, str]]
    def sortedAfter(self, unitlist: List[str]) -> List[str]: ...
    def sortedBefore(self, unitlist: List[str]) -> List[str]: ...
    def daemon_reload_target(self) -> bool: ...
    def syntax_check(self, conf: SystemctlConf) -> int: ...
    def syntax_check_service(self, conf: SystemctlConf) -> int:
        usedExecStart: List[str]
        usedExecStop: List[str]
        usedExecReload: List[str]
    def exec_check_unit(self, conf: SystemctlConf, env: Dict[str, str], section: str = "Service", exectype: str = "") -> bool: ...
    def show_modules(self, *modules: str) -> List[str]:
        notfound: List[str]
        units: List[str]
    def show_units(self, units: List[str]) -> List[str]:
        result: List[str]
    def show_unit_items(self, unit: str) -> Iterable[Tuple[str, str]]: ...
    def each_unit_items(self, unit: str, conf: SystemctlConf) -> Iterable[Tuple[str, str]]: ...
    def get_SendSIGKILL(self, conf: SystemctlConf) -> bool: ...
    def get_SendSIGHUP(self, conf: SystemctlConf) -> bool: ...
    def get_KillMode(self, conf: SystemctlConf) -> str: ...
    def get_KillSignal(self, conf: SystemctlConf) -> str: ...
    def _ignored_unit(self, unit: str, ignore_list: List[str]) -> bool: ...
    def default_services_modules(self, *modules: str) -> List[str]:
        results: List[str]
    def target_default_services(self, target: Optional[str] = None, sysv: str = "S") -> List[str]: ...
    def enabled_target_services(self, target: str, sysv: str = "S", igno: List[str] = []) -> List[str]:
        units: List[str]
    def enabled_target_user_local_units(self, target: str, unit_kind: str = ".service", igno: List[str] = []) -> List[str]:
        units: List[str]
    def enabled_target_user_system_units(self, target: str, unit_kind: str = ".service", igno: List[str] = []) -> List[str]:
        units: List[str]
    def enabled_target_installed_system_units(self, target: str, unit_type: str = ".service", igno: List[str] = []) -> List[str]:
        units: List[str]
    def enabled_target_configured_system_units(self, target: str, unit_type: str = ".service", igno: List[str] = []) -> List[str]:
        units: List[str]
    def enabled_target_sysv_units(self, target: str, sysv: str = "S", igno: List[str] = []) -> List[str]:
        units: List[str]
        folders: List[str]
    def required_target_units(self, target: str, unit_type: str, igno: List[str]) -> List[str]:
        units: List[str]
    def get_target_conf(self, module: str) -> SystemctlConf: ...
    def get_target_list(self, module: str) -> List[str]: ...
    def default_system(self, arg: bool = True) -> bool: ...
    def start_system_default(self, init: bool = False) -> bool: ...
    def start_target_system(self, target: str, init: bool = False) -> List[str]: ...
    def do_start_target_from(self, conf: SystemctlConf) -> bool: ...
    def stop_system_default(self) -> bool: ...
    def stop_target_system(self, target: str) -> List[str]: ...
    def do_stop_target_from(self, conf: SystemctlConf) -> bool: ...
    def do_reload_target_from(self, conf: SystemctlConf) -> bool: ...
    def reload_target_system(self, target: str) -> bool: ...
    def halt_target(self, arg: bool = True) -> bool: ...
    def get_targets_folder(self) -> str: ...
    def get_default_target_file(self) -> str: ...
    def get_default_target(self, default_target: Optional[str] = None) -> str: ...
    def system_get_default(self) -> str: ...
    def set_default_modules(self, *modules: str) -> str: ...
    def init_modules(self, *modules: str) -> bool: # -> Optional[str]:
        units: List[str]
    def start_log_files(self, units: List[str]) -> None: ...
    def read_log_files(self, units: List[str]) -> None: ...
    def stop_log_files(self, units: List[str]) -> None: ...
    def get_StartLimitBurst(self, conf: SystemctlConf) -> int: ...
    def get_StartLimitIntervalSec(self, conf: SystemctlConf, maximum: Optional[int] = None) -> float: ...
    def get_RestartSec(self, conf: SystemctlConf, maximum: Optional[int] = None) -> float: ...
    def restart_failed_units(self, units: List[str], maximum: Optional[int] = None) -> List[str]:
        restart_done: List[str]
    def init_loop_until_stop(self, units: List[str]) -> Optional[str]:
        result: Optional[str]
    def reap_zombies_target(self) -> str: ...
    def reap_zombies(self) -> int: ...
    def sysinit_status(self, **status: Optional[str]) -> None: ...
    def sysinit_target(self) -> SystemctlConf: ...
    def is_system_running(self) -> str: ...
    def is_system_running_info(self) -> Optional[str]: ...
    def wait_system(self, target: Optional[str] = None) -> None: ...
    def is_running_unit_from(self, conf: SystemctlConf) -> bool: ...
    def is_running_unit(self, unit: str) -> bool: ...
    def pidlist_of(self, pid: Optional[int]) -> List[int]: ...
    def echo(self, *targets: str) -> str: ...
    def killall(self, *targets: str) -> bool: ...
    def force_ipv4(self, *args: str) -> None:
        lines: List[str]
    def force_ipv6(self, *args: str) -> None:
        lines: List[str]
    def help_modules(self, *args: str) -> List[str]:
        lines: List[str]
    def systemd_version(self) -> str: ...
    def systemd_features(self) -> str: ...
    def version_info(self) -> List[str]: ...
    def test_float(self) -> float: ...

def print_begin(argv: List[str], args: List[str]) -> None: ...
def print_begin2(args: List[str]) -> None: ...
def is_not_ok(result: bool) -> int: ...
def print_str(result: Optional[str]) -> None: ...
def print_str_list(result: Union[None, List[str]]) -> None: ...
def print_str_list_list(result: Union[List[Tuple[str]], List[Tuple[str, str]], List[Tuple[str, str, str]]]) -> None: ...
def print_str_dict(result: Union[None, Dict[str, str]]) -> None: ...
def print_str_dict_dict(result: Dict[str, Dict[str, str]]) -> None: ...
def run(command: str, *modules: str) -> int: ...
