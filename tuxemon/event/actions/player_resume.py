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

from typing import NamedTuple, final

from tuxemon.event.eventaction import EventAction
from tuxemon.states.world.worldstate import WorldState


class PlayerResumeActionParameters(NamedTuple):
    pass


@final
class PlayerResumeAction(EventAction[PlayerResumeActionParameters]):
    """
    Make the player resume movement.

    Script usage:
        .. code-block::

            player_resume

    """

    name = "player_resume"
    param_class = PlayerResumeActionParameters

    def start(self) -> None:
        # Get a copy of the world state.
        world = self.session.client.get_state_by_name(WorldState)

        world.menu_blocking = False
