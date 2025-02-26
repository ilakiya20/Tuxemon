from __future__ import annotations

import random
from typing import NamedTuple, Optional

from tuxemon import formula
from tuxemon.monster import Monster
from tuxemon.technique.techeffect import TechEffect, TechEffectResult
from tuxemon.technique.technique import Technique


class LifeLeechEffectResult(TechEffectResult):
    damage: int
    should_tackle: bool
    status: Optional[Technique]


class LifeLeechEffectParameters(NamedTuple):
    pass


class LifeLeechEffect(TechEffect[LifeLeechEffectParameters]):
    """
    This effect has a chance to apply the lifeleech status effect.

    Parameters:
        user: The Monster object that used this technique.
        target: The Monster object that we are using this technique on.

    Returns:
        Dict summarizing the result.

    """

    name = "lifeleech"
    param_class = LifeLeechEffectParameters

    def apply(self, user: Monster, target: Monster) -> LifeLeechEffectResult:
        success = self.move.potency >= random.random()
        if success:
            tech = Technique("status_lifeleech", carrier=target, link=user)
            target.apply_status(tech)
            # exception: applies status to the user
            if self.move.slug == "blood_bond":
                tech = Technique("status_lifeleech", carrier=user, link=target)
                user.apply_status(tech)
            return {"status": tech}

        # avoids Nonetype situation and reset the user
        if self.user is None:
            damage = formula.simple_lifeleech(self.move, user, target)
            target.current_hp -= damage
            user.current_hp += damage
        else:
            damage = formula.simple_lifeleech(self.move, self.user, target)
            target.current_hp -= damage
            self.user.current_hp += damage

        return {
            "damage": damage,
            "should_tackle": bool(damage),
            "success": bool(damage),
        }
