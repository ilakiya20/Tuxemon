#
# Tuxemon
# Copyright (C) 2014, William Edwards <shadowapex@gmail.com>,
#                     Benjamin Bean <superman2k5@gmail.com>
#
# This file is part of Tuxemon.
#
# Tuxemon is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Tuxemon is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Tuxemon.  If not, see <http://www.gnu.org/licenses/>.
#
# Contributor(s):
#
# William Edwards <shadowapex@gmail.com>
#
#
# monster Tuxemon monster module
#
#

from __future__ import annotations

import logging
import random
import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Mapping, Optional, Sequence

from tuxemon import ai, fusion, graphics
from tuxemon.config import TuxemonConfig
from tuxemon.db import (
    ElementType,
    GenderType,
    MonsterEvolutionItemModel,
    MonsterMovesetItemModel,
    MonsterShape,
    db,
)
from tuxemon.locale import T
from tuxemon.sprite import Sprite
from tuxemon.technique.technique import Technique

if TYPE_CHECKING:
    import pygame

    from tuxemon.npc import NPC
    from tuxemon.states.combat.combat import EnqueuedAction

logger = logging.getLogger(__name__)

SIMPLE_PERSISTANCE_ATTRIBUTES = (
    "current_hp",
    "level",
    "name",
    "slug",
    "status",
    "total_experience",
    "flairs",
    "gender",
)

SHAPES = {
    MonsterShape.aquatic: {
        "armour": 8,
        "dodge": 4,
        "hp": 8,
        "melee": 6,
        "ranged": 6,
        "speed": 4,
    },
    MonsterShape.blob: {
        "armour": 8,
        "dodge": 4,
        "hp": 8,
        "melee": 4,
        "ranged": 8,
        "speed": 4,
    },
    MonsterShape.brute: {
        "armour": 7,
        "dodge": 5,
        "hp": 7,
        "melee": 8,
        "ranged": 4,
        "speed": 5,
    },
    MonsterShape.dragon: {
        "armour": 7,
        "dodge": 5,
        "hp": 6,
        "melee": 6,
        "ranged": 6,
        "speed": 6,
    },
    MonsterShape.flier: {
        "armour": 5,
        "dodge": 7,
        "hp": 4,
        "melee": 8,
        "ranged": 4,
        "speed": 8,
    },
    MonsterShape.grub: {
        "armour": 7,
        "dodge": 5,
        "hp": 7,
        "melee": 4,
        "ranged": 8,
        "speed": 5,
    },
    MonsterShape.humanoid: {
        "armour": 5,
        "dodge": 7,
        "hp": 4,
        "melee": 4,
        "ranged": 8,
        "speed": 8,
    },
    MonsterShape.hunter: {
        "armour": 4,
        "dodge": 8,
        "hp": 5,
        "melee": 8,
        "ranged": 4,
        "speed": 7,
    },
    MonsterShape.landrace: {
        "armour": 8,
        "dodge": 4,
        "hp": 8,
        "melee": 8,
        "ranged": 4,
        "speed": 4,
    },
    MonsterShape.leviathan: {
        "armour": 8,
        "dodge": 4,
        "hp": 8,
        "melee": 6,
        "ranged": 6,
        "speed": 4,
    },
    MonsterShape.polliwog: {
        "armour": 4,
        "dodge": 8,
        "hp": 5,
        "melee": 4,
        "ranged": 8,
        "speed": 7,
    },
    MonsterShape.serpent: {
        "armour": 6,
        "dodge": 6,
        "hp": 6,
        "melee": 4,
        "ranged": 8,
        "speed": 6,
    },
    MonsterShape.sprite: {
        "armour": 6,
        "dodge": 6,
        "hp": 4,
        "melee": 6,
        "ranged": 6,
        "speed": 8,
    },
    MonsterShape.varmint: {
        "armour": 6,
        "dodge": 6,
        "hp": 6,
        "melee": 8,
        "ranged": 4,
        "speed": 6,
    },
}

MAX_LEVEL = 999
MISSING_IMAGE = "gfx/sprites/battle/missing.png"


# class definition for tuxemon flairs:
class Flair:
    def __init__(self, category: str, name: str) -> None:
        self.category = category
        self.name = name


# class definition for first active tuxemon to use in combat:
class Monster:
    """
    Tuxemon monster.

    A class for a Tuxemon monster object. This class acts as a skeleton for
    a Tuxemon, fetching its details from a database.

    """

    def __init__(self, save_data: Optional[Mapping[str, Any]] = None) -> None:
        if save_data is None:
            save_data = dict()

        self.slug = ""
        self.name = ""
        self.category = ""
        self.description = ""
        self.instance_id = uuid.uuid4()

        self.armour = 0
        self.dodge = 0
        self.melee = 0
        self.ranged = 0
        self.speed = 0
        self.current_hp = 0
        self.hp = 0
        self.level = 0

        self.moves: List[Technique] = []
        self.moveset: List[MonsterMovesetItemModel] = []
        self.evolutions: List[MonsterEvolutionItemModel] = []
        self.flairs: Dict[str, Flair] = {}
        self.battle_cry = ""
        self.faint_cry = ""
        self.ai: Optional[ai.AI] = None
        self.owner: Optional[NPC] = None
        self.possible_genders: List[GenderType] = []

        self.money_modifier = 0
        self.experience_required_modifier = 1
        self.total_experience = 0

        self.type1 = ElementType.aether
        self.type2: Optional[ElementType] = None
        self.shape = MonsterShape.landrace

        self.status: List[Technique] = []

        self.txmn_id = 0
        self.height = 0.0
        self.weight = 0.0

        # The multiplier for checks when a monster ball is thrown this should be a value betwen 0-255 meaning that
        # 0 is 0% capture rate and 255 has a very good chance of capture. This numbers are based on the capture system
        # calculations. This is inspired by the calculations which can be found at:
        # https://bulbapedia.bulbagarden.net/wiki/List_of_Pok%C3%A9mon_by_catch_rate
        self.catch_rate = TuxemonConfig().default_monster_catch_rate

        # The catch_resistance value is calculated during the capture. The upper and lower catch_resistance
        # set the span on which the catch_resistance will be. For more imformation check capture.py
        self.upper_catch_resistance = (
            TuxemonConfig().default_upper_monster_catch_resistance
        )
        self.lower_catch_Resistance = (
            TuxemonConfig().default_lower_monster_catch_resistance
        )

        # The tuxemon's state is used for various animations, etc. For example
        # a tuxemon's state might be "attacking" or "fainting" so we know when
        # to play the animations for those states.
        self.state = ""

        # A fusion body object that contains the monster's face and body
        # sprites, as well as _color scheme.
        self.body = fusion.Body()

        # Set up our sprites.
        self.sprites: Dict[str, pygame.surface.Surface] = {}
        self.front_battle_sprite = ""
        self.back_battle_sprite = ""
        self.menu_sprite_1 = ""
        self.menu_sprite_2 = ""

        self.set_state(save_data)
        self.set_stats()
        self.set_flairs()

    def spawn(self, father: Monster) -> Monster:
        """
        Spawn a child monster.

        Creates a new Monster, with this monster as the mother and the passed
        in monster as father.

        Parameters:
            The monster.Monster to be father of this monsterous child.

        Returns:
            Child monster.

        """
        child = Monster()
        child.load_from_db(self.slug)
        child.set_level(5)

        father_tech_count = len(father.moves)
        tech_to_replace = random.randrange(0, 2)
        child.moves[tech_to_replace] = father.moves[
            random.randrange(0, father_tech_count - 1)
        ]

        return child

    def load_from_db(self, slug: str) -> None:
        """
        Loads and sets this monster's attributes from the monster.db database.

        The monster is looked up in the database by name.

        Parameters:
            slug: Slug to lookup.

        """

        # Look up the monster by name and set the attributes in this instance
        results = db.lookup(slug, table="monster")

        if results is None:
            raise RuntimeError(f"monster {slug} is not found")
        self.level = random.randint(2, 5)
        self.slug = results.slug
        self.name = T.translate(results.slug)
        self.description = T.translate(f"{results.slug}_description")
        self.category = T.translate(results.category)
        self.shape = results.shape or MonsterShape.landrace
        types = results.types
        if types:
            self.type1 = results.types[0]
            if len(types) > 1:
                self.type2 = results.types[1]

        self.txmn_id = results.txmn_id
        self.height = results.height
        self.weight = results.weight
        self.gender = random.choice(list(results.possible_genders))
        self.catch_rate = (
            results.catch_rate or TuxemonConfig().default_monster_catch_rate
        )
        self.upper_catch_resistance = (
            results.upper_catch_resistance
            or TuxemonConfig().default_upper_monster_catch_resistance
        )
        self.lower_catch_resistance = (
            results.lower_catch_resistance
            or TuxemonConfig().default_lower_monster_catch_resistance
        )

        # Look up the moves that this monster can learn AND LEARN THEM.
        moveset = results.moveset
        if moveset:
            for move in moveset:
                self.moveset.append(move)
                if move.level_learned <= self.level:
                    technique = Technique(move.technique)
                    self.learn(technique)

        # Look up the evolutions for this monster.
        evolutions = results.evolutions
        if evolutions:
            for evolution in evolutions:
                self.evolutions.append(evolution)

        # Look up the monster's sprite image paths
        self.front_battle_sprite = self.get_sprite_path(
            results.sprites.battle1
        )
        self.back_battle_sprite = self.get_sprite_path(results.sprites.battle2)
        self.menu_sprite_1 = self.get_sprite_path(results.sprites.menu1)
        self.menu_sprite_2 = self.get_sprite_path(results.sprites.menu2)

        # get sound slugs for this monster, defaulting to a generic type-based sound
        if results.sounds:
            self.combat_call = results.sounds.combat_call
            self.faint_call = results.sounds.faint_call
        else:
            self.combat_call = f"sound_{self.type1}_call"
            self.faint_call = f"sound_{self.type1}_faint"

        # Load the monster AI
        # TODO: clean up AI 'core' loading and what not
        ai_result = results.ai
        if ai_result == "SimpleAI":
            self.ai = ai.SimpleAI()
        elif ai_result == "RandomAI":
            self.ai = ai.RandomAI()

    def learn(
        self,
        technique: Technique,
    ) -> None:
        """
        Adds a technique to this tuxemon's moveset.

        Parameters:
            technique: The technique for the monster to learn.

        Examples:

        >>> bulbatux.learn(Technique())
        >>> bulbatux.moves[0].use(bulbatux, target=tuxmander)

        """

        self.moves.append(technique)

    def give_experience(self, amount: int = 1) -> None:
        """
        Increase experience.

        Gives the Monster a specified amount of experience, and levels
        up the monster if necessary.

        Parameters:
            amount: The amount of experience to add to the monster.

        Example:

        >>> bulbatux.give_experience(20)

        """
        self.total_experience += amount

        # Level up worthy monsters
        while self.total_experience >= self.experience_required(1):
            self.level_up()

    def apply_status(self, status: Technique) -> None:
        """
        Apply a status to the monster by replacing or removing
        the previous status.

        Parameters:
            status: The status technique.

        """
        count_status = len(self.status)
        if count_status == 0:
            self.status.append(status)
        else:
            # if the status exists
            if any(t for t in self.status if t.slug == status):
                return
            # if the status doesn't exist.
            else:
                if self.status[0].category == "positive":
                    if status.repl_pos == "replace":
                        self.status.clear()
                        self.status.append(status)
                    elif status.repl_pos == "remove":
                        self.status.clear()
                    else:
                        # noddingoff, exhausted, festering, dozing
                        return
                elif self.status[0].category == "negative":
                    if status.repl_neg == "replace":
                        self.status.clear()
                        self.status.append(status)
                    elif status.repl_pos == "remove":
                        self.status.clear()
                    else:
                        # chargedup, charging and dozing
                        return
                else:
                    # spyderbite and eliminated
                    self.status.append(status)

    def set_stats(self) -> None:
        """
        Set or improve stats.

        Sets the monsters initial stats, or improves stats
        when called during a level up.

        """
        if self.level < 10:
            level = 10
        else:
            level = self.level

        multiplier = level + 7
        shape = SHAPES[self.shape]
        self.armour = shape["armour"] * multiplier
        self.dodge = shape["dodge"] * multiplier
        self.hp = shape["hp"] * multiplier
        self.melee = shape["melee"] * multiplier
        self.ranged = shape["ranged"] * multiplier
        self.speed = shape["speed"] * multiplier

    def level_up(self) -> None:
        """
        Increases a Monster's level by one and increases stats accordingly.

        """
        logger.info(
            "Leveling %s from %i to %i!"
            % (self.name, self.level, self.level + 1)
        )
        # Increase Level and stats
        self.level += 1
        self.level = min(self.level, MAX_LEVEL)
        self.set_stats()

        # Learn New Moves
        for move in self.moveset:
            if move.level_learned == self.level:
                logger.info(
                    "{} learned technique {}!".format(
                        self.name, move.technique
                    )
                )
                technique = Technique(move.technique)
                self.learn(technique)

    def set_level(self, level: int = 5) -> None:
        """
        Set monster level.

        Sets the Monster's level to the specified arbitrary level,
        and modifies experience accordingly.
        Does not let level go above MAX_LEVEL or below 1.

        Parameters:
            level: The level to set the monster to.

        Example:

        >>> bulbatux.set_level(20)

        """
        if level > MAX_LEVEL:
            level = MAX_LEVEL
        elif level < 1:
            level = 1
        self.level = level
        self.total_experience = self.experience_required()
        self.set_stats()

        # Update moves
        for move in self.moveset:
            if (
                move.technique not in (m.slug for m in self.moves)
                and move.level_learned <= level
            ):
                self.learn(Technique(move.technique))

    def experience_required(self, level_ofs: int = 0) -> int:
        """
        Gets the experience requirement for the given level.

        Parameters:
            level_ofs: Difference in levels with the current level.

        Returns:
            Required experience.

        """
        return (
            self.experience_required_modifier * (self.level + level_ofs) ** 3
        )

    def get_sprite(self, sprite: str, **kwargs: Any) -> Sprite:
        """
        Gets a specific type of sprite for the monster.

        Parameters:
            sprite: Name of the sprite type.
            kwargs: Additional parameters to pass to the loading function.

        Returns:
            The surface of the monster sprite.

        """
        if sprite == "front":
            surface = graphics.load_sprite(self.front_battle_sprite, **kwargs)
        elif sprite == "back":
            surface = graphics.load_sprite(self.back_battle_sprite, **kwargs)
        elif sprite == "menu":
            assert (
                not kwargs
            ), "kwargs aren't supported for loading menu sprites"
            surface = graphics.load_animated_sprite(
                [self.menu_sprite_1, self.menu_sprite_2], 0.25
            )
        else:
            raise ValueError(f"Cannot find sprite for: {sprite}")

        # Apply flairs to the monster sprite
        for flair in self.flairs.values():
            flair_path = self.get_sprite_path(
                f"gfx/sprites/battle/{self.slug}-{sprite}-{flair.name}"
            )
            if flair_path != MISSING_IMAGE:
                flair_sprite = graphics.load_sprite(flair_path, **kwargs)
                surface.image.blit(flair_sprite.image, (0, 0))

        return surface

    def set_flairs(self) -> None:
        """Set flairs of this monster if they were not already configured."""
        if len(self.flairs) > 0 or self.slug == "":
            return

        results = db.lookup(self.slug, table="monster")
        for flair in results.flairs:
            new_flair = Flair(
                flair.category,
                random.choice(flair.names),
            )
            self.flairs[new_flair.category] = new_flair

    def get_sprite_path(self, sprite: str) -> str:
        """
        Get a sprite path.

        Paths are set up by convention, so the file extension is unknown.
        This adds the appropriate file extension if the sprite exists,
        and returns a dummy image if it can't be found.

        Returns:
            Path to sprite or placeholder image.

        """
        try:
            path = "%s.png" % sprite
            full_path = graphics.transform_resource_filename(path)
            if full_path:
                return full_path
        except OSError:
            pass

        logger.error(f"Could not find monster sprite {sprite}")
        return MISSING_IMAGE

    def load_sprites(self) -> bool:
        """
        Loads the monster's sprite images as Pygame surfaces.

        Returns:
            ``True`` if the sprites are already loaded.

        """
        if len(self.sprites):
            return True

        self.sprites["front"] = graphics.load_and_scale(
            self.front_battle_sprite
        )
        self.sprites["back"] = graphics.load_and_scale(self.back_battle_sprite)
        self.sprites["menu"] = graphics.load_and_scale(self.menu_sprite_1)
        return False

    def get_state(self) -> Mapping[str, Any]:
        """
        Prepares a dictionary of the monster to be saved to a file.

        Returns:
            Dictionary containing all the information about the monster.

        """
        save_data = {
            attr: getattr(self, attr)
            for attr in SIMPLE_PERSISTANCE_ATTRIBUTES
            if getattr(self, attr)
        }

        save_data["instance_id"] = self.instance_id.hex

        if self.status:
            save_data["status"] = [i.get_state() for i in self.status]
        body = self.body.get_state()
        if body:
            save_data["body"] = body

        save_data["moves"] = [tech.slug for tech in self.moves]

        return save_data

    def set_state(self, save_data: Mapping[str, Any]) -> None:
        """
        Loads information from saved data.

        Parameters:
            save_data: Data used to reconstruct the monster.

        """
        if not save_data:
            return

        self.load_from_db(save_data["slug"])

        for key, value in save_data.items():
            if key == "status" and value:
                self.status = [Technique(slug=i) for i in value]
            elif key == "body" and value:
                self.body.set_state(value)
            elif key == "moves" and value:
                self.moves = [Technique(slug) for slug in value]
            elif key == "instance_id" and value:
                self.instance_id = uuid.UUID(value)
            elif key in SIMPLE_PERSISTANCE_ATTRIBUTES:
                setattr(self, key, value)

        self.load_sprites()

    def end_combat(self) -> None:
        for move in self.moves:
            move.full_recharge()

        if "status_faint" in (s.slug for s in self.status):
            self.status = [Technique("status_faint")]
        else:
            self.status = []

    def speed_test(self, action: EnqueuedAction) -> int:
        assert isinstance(action.technique, Technique)
        technique = action.technique
        if technique.is_fast:
            return int(random.randrange(0, int(self.speed)) * 1.5)
        else:
            return random.randrange(0, int(self.speed))


def decode_monsters(
    json_data: Optional[Sequence[Mapping[str, Any]]],
) -> List[Monster]:
    return [Monster(save_data=mon) for mon in json_data or {}]


def encode_monsters(mons: Sequence[Monster]) -> Sequence[Mapping[str, Any]]:
    return [mon.get_state() for mon in mons]
