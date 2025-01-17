import discord
import pytest

from tests.conftest import end_init, start_init
from tests.utils import ATTACK_PATTERN, DAMAGE_PATTERN, SAVE_PATTERN, active_character, active_combat

pytestmark = pytest.mark.asyncio


@pytest.mark.usefixtures("init_fixture", "character", "_requires")
class TestMixedInitiative:
    """
    3 cases:
    caster not in init, channel not in init [XX]
    caster not in init, channel in init     [XI]
    caster in init, channel in init         [II]
    """

    async def test_attack_XX(self, avrae, dhttp):
        avrae.message("!attack dagger -t someone")
        embed = discord.Embed(title=r".* attacks with a Dagger!")
        embed.add_field(name="someone", value=ATTACK_PATTERN, inline=False)
        await dhttp.receive_message(embed=embed)
        await dhttp.receive_delete()

    async def test_cast_XX(self, avrae, dhttp):
        avrae.message("!cast fireball -t someone -i")
        await dhttp.receive_delete()
        embed = discord.Embed(title=r".* casts Fireball!")
        embed.add_field(name="Meta", value=rf"{DAMAGE_PATTERN}\n\*\*DC\*\*: \d+\nDEX Save", inline=False)
        await dhttp.receive_message(embed=embed)

    async def test_init_XX_to_XI(self, avrae, dhttp):  # start init, XX -> XI
        await start_init(avrae, dhttp)
        avrae.message("!init madd kobold -n 5 -h")  # add 5 kobolds, KO1-KO5, for... testing

    async def test_attack_XI(self, avrae, dhttp):
        await attack_I(avrae, dhttp)

    async def test_cast_XI(self, avrae, dhttp):
        await cast_I(avrae, dhttp)

    async def test_init_XI_to_II(self, avrae, dhttp):  # join init, XI -> II
        avrae.message("!init join")
        await dhttp.receive_delete()
        await dhttp.receive_edit()
        await dhttp.receive_message()

    async def test_attack_II(self, avrae, dhttp):
        await attack_I(avrae, dhttp, target='4', name='KO4')

    async def test_cast_II(self, avrae, dhttp):
        await cast_I(avrae, dhttp, targets=['5'], names=['KO5'])

    async def test_attack_II_self(self, avrae, dhttp):
        char = await active_character(avrae)
        await attack_I(avrae, dhttp, target=char.name, name=char.name)
        await dhttp.drain()

        # make sure damage was saved to character
        combat = await active_combat(avrae)
        char = await active_character(avrae)
        me = combat.get_combatant(char.name, strict=True)
        assert me.hp == char.hp

    async def test_cast_II_self(self, avrae, dhttp):
        char = await active_character(avrae)
        await cast_I(avrae, dhttp, targets=[char.name], names=[char.name])
        await dhttp.drain()

        # make sure damage was saved to character
        combat = await active_combat(avrae)
        char = await active_character(avrae)
        me = combat.get_combatant(char.name, strict=True)
        assert me.hp == char.hp

    async def test_init_II_to_XX(self, avrae, dhttp):  # end init, II -> XX
        await end_init(avrae, dhttp)


async def attack_I(avrae, dhttp, target='1', name='KO1'):
    combat = await active_combat(avrae)
    combatant = combat.get_combatant(name, strict=True)
    hp_before = combatant.hp

    avrae.message(f"!attack dagger -t {target} hit")

    embed = discord.Embed(title=r".* attacks with a Dagger!")
    embed.add_field(name=name, value=ATTACK_PATTERN, inline=False)
    embed.set_footer(text=rf"{name}: <-?\d+/\d+ HP>")
    await dhttp.receive_edit()
    await dhttp.receive_message(embed=embed)
    await dhttp.receive_delete()
    await dhttp.drain()

    # ensure kobold took damage
    combat = await active_combat(avrae)
    combatant = combat.get_combatant(name, strict=True)
    assert combatant.hp < hp_before


async def cast_I(avrae, dhttp, targets=('2', '3'), names=('KO2', 'KO3')):
    hp_before = {}
    combat = await active_combat(avrae)
    for k in names:
        kobold = combat.get_combatant(k, strict=True)
        hp_before[k] = kobold.hp

    t_string = ' '.join(f'-t {target}' for target in targets)
    avrae.message(f"!cast fireball {t_string} -i")

    await dhttp.receive_delete()
    await dhttp.receive_edit()
    embed = discord.Embed(title=r".* casts Fireball!")
    embed.add_field(name="Meta", value=rf"{DAMAGE_PATTERN}\n\*\*DC\*\*: \d+", inline=False)
    for target in names:
        embed.add_field(name=target, value=SAVE_PATTERN, inline=False)
    footer = '\n'.join(rf"{name}: <-?\d+/\d+ HP>" for name in names)
    embed.set_footer(text=footer)
    await dhttp.receive_message(embed=embed)
    await dhttp.drain()

    # ensure kobolds took damage
    combat = await active_combat(avrae)
    for k in names:
        kobold = combat.get_combatant(k, strict=True)
        assert kobold.hp < hp_before[k]


@pytest.mark.usefixtures("init_fixture", "character", "_requires")
class TestSpellSlotConsumption:
    """
    3 cases:
    caster not in init, channel not in init [XX]
    caster not in init, channel in init     [XI]
    caster in init, channel in init         [II]
    """

    async def cast_fireball(self, avrae, dhttp):
        char = await active_character(avrae)
        slots_before = char.spellbook.get_slots(3)

        if not slots_before:
            pytest.skip("Character cannot cast Fireball")

        if "fireball" not in char.spellbook:
            avrae.message("!sb add fireball")
            await dhttp.drain()

        avrae.message('!cast fireball')
        await dhttp.drain()

        char = await active_character(avrae)
        assert char.spellbook.get_slots(3) == slots_before - 1

    async def test_cast_consumption_XX(self, avrae, dhttp):
        await self.cast_fireball(avrae, dhttp)

    async def test_cast_consumption_XI(self, avrae, dhttp):
        await start_init(avrae, dhttp)
        await self.cast_fireball(avrae, dhttp)

    async def test_cast_consumption_II(self, avrae, dhttp):
        avrae.message("!init join")
        await dhttp.drain()
        await self.cast_fireball(avrae, dhttp)


@pytest.fixture()
async def _requires(avrae):
    character = await active_character(avrae)
    # character must have a dagger
    if not "Dagger" in [atk.name for atk in character.attacks]:
        pytest.skip("Character does not have a dagger")

    # and must be able to cast spells
    if not character.spellbook.caster_level:
        pytest.skip("Character cannot cast spells")
