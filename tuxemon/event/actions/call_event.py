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


class CallEventActionParameters(NamedTuple):
    event_id: int


@final
class CallEventAction(EventAction[CallEventActionParameters]):
    """
    Execute the specified event's actions by id.

    Script usage:
        .. code-block::

            call_event <event_id>

    Script parameters:
        event_id: The id of the event whose actions will be executed.

    """

    name = "call_event"
    param_class = CallEventActionParameters

    def start(self) -> None:
        event_engine = self.session.client.event_engine
        events = self.session.client.events

        for e in events:
            if e.id == self.parameters.event_id:
                event_engine.start_event(e)
