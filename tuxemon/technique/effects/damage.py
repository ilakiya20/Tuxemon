from __future__ import annotations

import random
from typing import NamedTuple

from tuxemon import formula
from tuxemon.monster import Monster
from tuxemon.technique.techeffect import TechEffect, TechEffectResult


class DamageEffectResult(TechEffectResult):
    damage: int
    element_multiplier: float
    should_tackle: bool


class DamageEffectParameters(NamedTuple):
    pass


class DamageEffect(TechEffect[DamageEffectParameters]):
    """
    Apply damage.

    This effect applies damage to a target monster. This effect will only
    be applied if "damage" is defined in the relevant technique's effect
    list.

    Parameters:
        user: The Monster object that used this technique.
        target: The Monster object that we are using this technique on.

    Returns:
        Dict summarizing the result.

    """

    name = "damage"
    param_class = DamageEffectParameters

    def apply(self, user: Monster, target: Monster) -> DamageEffectResult:
        hit = self.move.accuracy >= random.random()
        if hit or self.move.is_area:
            self.move.can_apply_status = True
            damage, mult = formula.simple_damage_calculate(
                self.move, user, target
            )
            if not hit:
                damage //= 2
            target.current_hp -= damage
        else:
            damage = 0
            mult = 1

        return {
            "damage": damage,
            "element_multiplier": mult,
            "should_tackle": bool(damage),
            "success": bool(damage),
        }
