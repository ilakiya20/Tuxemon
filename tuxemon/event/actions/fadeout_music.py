#
# Tuxemon
# Copyright (c) 2014-2017 William Edwards <shadowapex@gmail.com>,
#                         Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import annotations

import logging
from typing import NamedTuple, final

from tuxemon.event.eventaction import EventAction
from tuxemon.platform import mixer

logger = logging.getLogger(__name__)


class FadeoutMusicActionParameters(NamedTuple):
    duration: int


@final
class FadeoutMusicAction(EventAction[FadeoutMusicActionParameters]):
    """
    Fade out the music over a set amount of time in milliseconds.

    Script usage:
        .. code-block::

            fadeout_music <duration>

    Script parameters:
        duration: Number of milliseconds to fade out the music over.

    """

    name = "fadeout_music"
    param_class = FadeoutMusicActionParameters

    def start(self) -> None:
        time = self.parameters.duration
        mixer.music.fadeout(time)
        if self.session.client.current_music["song"]:
            self.session.client.current_music["status"] = "stopped"
        else:
            logger.warning("Music cannot be paused, none is playing.")
