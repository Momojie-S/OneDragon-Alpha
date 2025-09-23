from dataclasses import dataclass
from typing import Optional

from agentscope.message import Msg


@dataclass
class SessionMessage:

    msg: Optional[Msg]
    message_completed: bool
    response_completed: bool
