from enum import Enum, IntEnum

class PlayerStates(IntEnum):
    PLAYING = 1
    PAUSED = 0
    STOPPED = -1

class SongStatus(Enum):
    READY = 0
    SEARCHING = 1
    SEARCHING_LOCAL = 2
    DOWNLOADING = 3
    FAILED = -1