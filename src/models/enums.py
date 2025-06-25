from enum import Enum, IntEnum, StrEnum

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

class reactions(StrEnum):
    check = '✅'
    cross = '❌'
    warn = '⚠️'
    fyou = '🖕'
    wave = '👋'
    thumbs_up = '👍'
    thinking = '🧠'
   
    cold = '🥶'
    hot = '🥵'
    mew1 = '🤫'
    mew2 = '🧏'

    pls ='🥺'
    pls_tears = '🥹'

    black_circle = '⚫'
    green_circle = '🟢'
    yellow_circle = '🟡'
    orange_circle = '🟠'
    red_circle = '🔴'

    left_arrow = '⬅️'
    right_arrow = '➡️'
    down_arrow = '⬇️'
    play = '▶️'

    internet = '🌐'
    search = '🔍'
    folder = '📁'