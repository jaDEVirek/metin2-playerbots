# metin2-suite

Single-player Metin2 server suite: a Linux port of the r40250 server, a launcher,
a Flask admin panel, and the playerbot AI that populates the world.

## Layout

The engine source is **not in this repository** and never will be — see
`linux-port/fetch-sources.sh`. Our side of the server is one overlay:

| Path | What |
|---|---|
| `linux-port/overlays/playerbot/src/game/src/` | The playerbot AI, split into implementation fragments (see below). `playerbot_manager.cpp` is the tick and whatever has not been lifted out yet. |
| `linux-port/overlays/playerbot/src/game/src/playerbot_world_rules.h` | Pure travel policy, no engine types. Unit-tested. The model for extracting logic. |
| `linux-port/patches/` | Patches applied to the pristine engine source. |
| `files/admin_panel.py` | Flask admin panel. The copy under
`linux-port/docker/panel/app/` is staged there by `prepare-context.sh` and is
gitignored -- editing that one changes the running panel and commits nothing. |
| `tests/playerbot_world_rules_test.cpp` | The only C++ unit test. |

Reference copies of the engine, needed to check any API before using it:

- `../m2src-cache/tree/port40250/server/` — staged, patched build tree (`game/src`, `common/`, `extern/include`)
- `../../backups/m1-best-*/game-server/game/src/` — engine sources incl. `fishing.cpp`, `char.cpp`
- `../m2src-cache/tree/server40250/share/` — runtime data: `conf/item_proto.txt`, `conf/item_names_pl.txt`, `conf/mob_names_pl.txt`, `locale/english/map/*/`

## Verifying a change

There is no local compiler; the build is 32-bit C++23 in Docker. Syntax-check the
overlay against the real headers — this catches almost everything and takes about
a minute:

```bash
cd ../m2src-cache/tree/port40250
cp <repo>/linux-port/overlays/playerbot/src/game/src/playerbot_manager.cpp server/game/src/
cp <repo>/linux-port/overlays/playerbot/src/game/src/playerbot_world_rules.h server/game/src/
MSYS_NO_PATHCONV=1 docker run --rm -v "$(pwd -W)":/src -w /src/server/game/src gcc:13 bash -c \
  "apt-get update -qq >/dev/null 2>&1 && apt-get install -y -qq g++-multilib >/dev/null 2>&1; \
   g++ -fsyntax-only -m32 -std=c++23 -Wall -Wextra -Wno-unused-parameter -fexceptions \
   -D_THREAD_SAFE -DNDEBUG -DBOOST_BIND_GLOBAL_PLACEHOLDERS \
   -I../../../extern/include -I../../liblua/include -I../../libserverkey playerbot_manager.cpp; \
   echo EXIT=\$?"
```

`-m32` is mandatory: `packet.h` static-asserts a 32-bit `time_t` and the wire/DB
layouts depend on it. Restore the staged copies afterwards — they belong to the
build cache, not to us.

Unit test:

```bash
docker run --rm -v "$(pwd -W)":/w -w /w gcc:13 \
  bash -c "g++ -Wall -Wextra -o /tmp/t tests/playerbot_world_rules_test.cpp && /tmp/t"
```

Nothing here can be runtime-tested locally; the live signal comes from operators
running ~350 bots. Say plainly what was compiled versus what was observed.

### Adding a source file

Nothing to do. Drop a `playerbot_*.h` or `playerbot_*.cpp` into
`overlays/playerbot/src/game/src/` and every step finds it: `prepare-context.sh`
discovers the directory, the engine `Makefile` takes `$(wildcard
playerbot_*.cpp)`, the update packager expands `playerbot_*` in
`server-update-files.txt`, and the launcher copies the whole directory into the
build context before each build.

This used to cost five edits in `prepare-context.sh` alone plus a patch edit,
which is exactly why the manager grew to twelve thousand lines instead of being
split up -- and why 1.22.4 and 1.23.2 both shipped a manager without its own
headers and would not compile on any player's machine. If you add a step that
handles these files, make it discover them too. Never write another list.

## The playerbot sources

Everything shares **one translation unit and one anonymous namespace**, so
definition order *is* dependency order: a helper must appear above its callers.
The split is therefore a sequence of implementation fragments, included in
dependency order at the top of `playerbot_manager.cpp`:

| File | What |
|---|---|
| `playerbot_types.h` | Tuning constants, enums, `TPlayerBotAIState`, the state map, and the two goal/action transitions every subsystem makes. |
| `playerbot_log.h` | Saying something once for three hundred bots: a tag, a minute, and a count of what was swallowed. |
| `playerbot_battle_horse.h` | Earning the horse that can fight: the desert trial, and what the stable keeper does at the end of it. |
| `playerbot_config.h` | The weights an operator moves in the panel while the world runs. Re-read from a file every five seconds; neutral when it is missing. |
| `playerbot_world_rules.h` | Pure travel policy. No engine types, unit-tested. |
| `playerbot_navigation.h` | Where a bot may stand and whether two points connect. Calls nothing above it. |
| `playerbot_world_memory.h` | What the population has learned about the world, as opposed to about itself. |
| `playerbot_movement.h` | Following a route: mounts, waypoints, portals, and the known-metin registry. |
| `playerbot_gear.h` | What a bot wears and carries: equipment scoring, the progression ladder, arrows, potions. |
| `playerbot_activities.h` | The horse, and fishing. Each owns the whole tick while it runs. |
| `playerbot_missions.h` | The Biologist's collections and the level-up hunt, driven without a quest dialog. |
| `playerbot_skills.h` | The character sheet: stat points, the job's skill order, keeping buffs up. |
| `playerbot_combat.h` | How a swing or a cast is sent: the packets a bot has no client to generate. |
| `playerbot_economy.h` | Money and bag: junk, merchants, the blacksmith, market stalls. |
| `playerbot_bonus.h` | The bonus lines on worn gear: what a line is worth, what finishes an item, and what a bot will pay to change it. |
| `playerbot_travel.h` | Where a bot ought to be, and crossing between maps. |
| `playerbot_planner.h` | Which long-term goal wins: the candidates, their base priorities, and the three gates no weight can touch. |
| `playerbot_guild.h` | Founding and recruiting a guild, and who a bot has got on with. |
| `playerbot_town.h` | A town visit end to end, as a state machine that survives being interrupted. |
| `playerbot_market.h` | Buying from another bot's counter: what is worth having, the walk to the stall, and the purchase. |
| `playerbot_chat_trade.h` | Trading over the chat: what a bot shouts about its counter and its wants, and the whisper it answers a player's "Kupie"/"Sprzedam" with. Fed by patch 0007. |
| `playerbot_loot.h` | Picking things up, in and out of a fight, without sweeping the floor. |
| `playerbot_survival.h` | Saving progress, breaking off a losing fight, and the walk back after dying. |
| `playerbot_wandering.h` | What a bot does on a hunting map when nothing is asking for its attention. |
| `playerbot_status.h` | What a bot shows above its head, and the words for it. |
| `playerbot_targeting.h` | Choosing what to hit and hitting it, including the claim that keeps hundreds of bots off the same monster. |
| `playerbot_manager.cpp` | Personality, party, upkeep, the watchdog - and `CPlayerBotManager` with the tick. |

These are fragments, not normal headers: each defines objects, relies on the
engine headers the manager includes above it, and reopens the same anonymous
namespace. Include each exactly once, from `playerbot_manager.cpp`, in an order
that respects what it calls. A fragment that needs something from a later
subsystem forward-declares it rather than pulling it in -- `playerbot_gear.h`
does this for `GetPlayerBotNpcApproach`.

`playerbot_manager.cpp` is now the manager: who a bot is, its party, the small
upkeep passes, the inactivity watchdog, and `CPlayerBotManager` itself. The tick
stays there on purpose - it is the one thing that has to see every subsystem, so
moving it would only mean declaring all of them somewhere else.

Find a subsystem by its entry point rather than by line number:

- Planning: `PlanPlayerBotLongTermGoal`, `GetPlayerBotWeight`, `RefreshPlayerBotWeights`
- Navigation/travel: `MovePlayerBot`, `TransitionPlayerBotMap` (an instant warp),
  `MovePlayerBotToWorldPortal` (walks), `ManagePlayerBotWorldTravel`
- Combat: `FindDistributedTarget`, `ExecutePlayerBotBasicAttack`,
  `ExecutePlayerBotAttackSkill`, `HandlePlayerBotMultiPull`
- Economy: `ManagePlayerBotEquipment`, `IsPlayerBotJunkItem`,
  `ManagePlayerBot*Merchant`, `ManagePlayerBotRefining`, `ManagePlayerBotPrivateShop`,
  `ManagePlayerBotBonusReroll`
- Activities: `ManagePlayerBotHorse`, `ManagePlayerBotFishing`,
  `ManagePlayerBotBiologist`, `HandlePlayerBotTownVisit`
- Planning/report: `PlanPlayerBotLongTermGoal`, `BuildPlayerBotStatusText`

`CPlayerBotManager::Update` is the tick. Order matters and is load-bearing:
releasing an open private shop runs first -- engine state must not depend on
which subsystem wins the tick -- then the goal planner, then the subsystem hooks
(each `continue`s to claim the tick), and target acquisition and attacking run
**last**. A subsystem that owns the tick therefore also suppresses combat and the
gear pass.

### The spawn ceiling is the registry, not the slider

`PLAYERBOT_AUTOSPAWN_COUNT` asks for a number; `CPlayerBotManager::LoadRegisteredBots`
decides what is available. It accepts a PID only when the ledger row says
`complete`/`adopted` **and** the account login is exactly `playerbot_NNN` for that
PID, the social id matches, and `player_index` holds that one character in empire 2.
Anything else -- a bot renamed by hand, a character from an older bootstrap that
used different account names -- stays in the database and never spawns. That guard
is deliberate: it is what stops a raw PID turning a real player's character into a
bot. Raising the ceiling on a world like that means growing the canonical cohort
(`BOT_COUNT` in `generate_seed.py`), not loosening the rule.

Read the two lines the core logs at startup before believing any count:

```
PLAYERBOT_AUTH: loaded 511 registered bot identities
PLAYERBOT: autospawn requested=750 registered_started=511 in Chunjo
```

### Traps this file has already sprung

- `TPlayerBotAIState` member init order must match declaration order, or `-Wreorder`
  fires (the build uses `-w`, so check with `-Wall` explicitly).
- `IsPlayerBotJunkItem` **defaults to `return true`**. Anything worth keeping needs
  an explicit exemption, or bots vendor it on the next town trip.
- The inactivity watchdog resets a bot that has not moved, fought or cast for
  ~90 s. Any activity that legitimately stands still must be exempted there.
- `TMonkeyVisitContext` is initialised positionally in the test. Inserting a field
  silently shifts every later value while still compiling.
- `CHARACTER::fishing()` dereferences the sectree map and tile with no null check.
- **The route planner reads its own grid, never the sectree.** `m_blocked` in
  `playerbot_navigation.h` is `ATTR_BLOCK|ATTR_OBJECT` sampled at every cell's
  centre when the grid is built, and `IsLiveBlockedCell` asks the engine for the
  same point - so inside A*, string pulling and goal snapping they are the same
  answer at a thousand times the price. A corridor search that asked live for
  every neighbour of every node cost 31 s of every 60 at 850 bots. Only the
  walk (`SegmentClearWorld`, one segment per tick) asks live, as the safety net
  for anything placed after the grid was built.
- **Hubs are placed by hand, chosen by memory.** A hunting hub is a
  `TPlayerBotHuntingHub` - a spawn-point coordinate, a level band, and whether
  it is a party's work - and `ChoosePlayerBotHuntingHub` picks among the ones a
  bot qualifies for by what `playerbot_world_memory.h` has seen there: every
  target search records the monsters within reach of the bot that ran it in a
  6400-unit cell, halved every ten minutes. The memory says how full a place
  is; the table says where a place is. Do not let it invent places - a bot
  standing where a pack respawned round it is not standing where the pack
  lives. Orc Valley's table is banded: Fanatic islands 30-39, the density hubs
  36+, the three Black Orc camps 40+ with a party, the Curse Book island 45+
  with a party. `PLAYERBOT_SPOT:` logs each choice and, every ten minutes, the
  richest cells per map; a cell that keeps coming top with no hub on it is a
  hub the table is missing. A boss hub is the exception:
  `TPlayerBotHuntingHub::wBossRace` names the boss and
  `IsPlayerBotBossAlive` asks the sector whether he stands, because one
  monster every half hour is a density of nothing and the boss hubs were
  never chosen in a day of logs.
- **A hub is chosen by share, distance and time, in that order.** The score
  is the monsters in reach divided among the bots already there, halved at
  20 km, and a choice is kept for four minutes. The first version scored by
  share alone and re-chose on every wander decision: bots crossed the valley
  for a slightly better camp and back again - 160 to 334 far plans a minute
  against 26 to 65, and the tick at 57 s of every 60.
- **The engine patches under `overlays/playerbot/patches/` are applied with
  `patch --fuzz=0` by prepare-context.sh**, in order, on top of the staged
  port source - so a new one is diffed against the builder container's copy
  of the file (which is that state), not against `m2src-cache`. That state
  is **before** the High Risk step, which runs later in the same script and
  inserts `#include "high_risk.h"`: 0006 once carried that line as context,
  applied by luck on any machine whose cache already held a High Risk tree,
  and failed every fresh `installer/install.sh`. Dry-run a new patch against
  `m2src-cache/tree/port40250/server` with `--fuzz=0` before shipping it. 0006 adds two
  CONFIG tokens (`MOONLIGHT_CHEST_PERMILLE`, `..._STONE_PERMILLE`, rendered by
  `m2-render-config` from `M2_MOONLIGHT_CHEST_*`) and, in `CreateDropItem`,
  tops a Metin stone up to three skill books and rolls the chest. The chest's
  contents come from `serverfiles/special_item_group.moonlight.txt`; the
  engine keeps the *first* group it reads for a vnum, so the Dockerfile cuts
  the stock 50011 block out before appending ours. `playerbot_consumables.h`
  opens the chest and drinks the boosters; the bonus scrolls, speed potions
  and big potions it holds go through the code that already handled them.
- **An engine patch reaches a player only as the staged file.** On Windows
  the launcher stages the overlay itself and `prepare-context.sh` never runs,
  so a patch under `overlays/playerbot/patches` is applied on this machine
  and nowhere else; and `patch` inside the image cannot be trusted either -
  the staged engine files carry mixed line endings and the core patch fails
  its own reverse check on them. What ships is the patched file itself,
  listed in `launcher/server-update-files.txt` next to the `playerbot_*`
  sources (`item_manager.cpp`, `config.cpp` for 0006). A new engine patch
  means: apply it to `linux-port/docker/game/src/server` with `patch -p1`,
  and add every file it touches to that list. 1.29.0 shipped without this and
  nobody got a chest.
- **The frontier is four maps and one table.** `GetPlayerBotFrontierArrival`,
  `GetPlayerBotFrontierExit` and `GetPlayerBotFrontierName` in
  `playerbot_types.h` answer for Orc Valley, the desert, Mount Sohan (61,
  `map_n_snowm_01`: the Infected of 49-58 in the south, ice creatures of
  62-66 in the north) and the Spider Dungeon V1 (104, spiders 50-58);
  `GetPlayerBotFrontierMapForLevel` routes by level and pid. V1 is reached
  across the desert: `TransitionPlayerBotMap` turns any warp into or out of
  104 into a warp onto 63 with the real destination kept in
  `lDesertCrossingTo`, and `ManagePlayerBotWorldTravel` walks the bot
  between the two gates (`PLAYERBOT_DESERT_V1_GATE_*`, the Bokjung gate)
  fighting nothing but a stone within `PLAYERBOT_CROSSING_STONE_RANGE`.
  **Map 43 is not
  Sohan** - `metin2_map_c3` is the second Jinno village with soldiers of
  26-36, and 1.29.0 to 1.29.6 sent the 26-39 band there under Sohan's name;
  the map index says nothing, read `map/index` and the regen before naming
  a map. 104 was moved onto the game1 core in `m2-render-config` - a bot
  cannot walk onto a map its own core does not host; 61 was there already.
  `apply.sh` keeps the list of maps a bot may stand on and sends the rest
  back to Bokjung at every start - add a map there too, or its bots walk
  home on the next restart. Adding a fifth map: a row in each helper, a hub table in
  `playerbot_wandering.h`, the navigation whitelist, the panel's bounds,
  names and tiles, and the core's MAP_ALLOW.
- **A mission is only as good as the map its monster stands on.** The
  level-up hunt (`PLAYERBOT_HUNTING_MISSIONS`, rows to 55) is driven by the
  engine's own `levelup` quest flags and its kill hook; the bot only picks
  the row and the option. Before the row was chosen by pid alone, and nearly
  every bot at forty was found holding a mission from fifteen with `remain`
  untouched, waiting for a wolf on a map it had left for good. Now
  `PLAYERBOT_HUNTING_MOB_HOMES` says where each monster stands (read out of
  the regen files - measure, do not guess), the option whose monster is on
  the bot's map wins, and a row is passed over without reward when it is
  outgrown by `PLAYERBOT_HUNTING_OUTGROWN_LEVELS`, has no hosted monster, or
  has hung for `PLAYERBOT_HUNTING_STALL_SECONDS`. The Biologist's chain has
  the same shape: the quest's kill hook drops the specimen only once the
  state says `go_to_disciple`, so the mission is taken wherever the bot
  stands (663 of 876 bots had never taken the mushroom mission because they
  passed level 25 outside Joan); only the hand-in walks to Joan.
  `GetActivePlayerBotBiologistMission` prefers what the bot already carries,
  then what stands on its map, then the first row undone. The Orc Tooth
  row has a second half, `key_item`, that waits for the Soul Stone; the
  state index of a compiled quest is a hash, not a position (see
  `quest/object/state/`), so never compare it with a small integer.
- **Droppers are personalities, not roles.** `IsPlayerBotDropper` names the
  four; `GetPlayerBotPersonalityByPID` is how a rule that only has a
  character asks. The travel gates (`ShouldPlayerBotVisitM3`,
  `ShouldPlayerBotHuntM2Bestials`, `ShouldPlayerBotPursueHorseExpedition`)
  answer for them by level alone, the stall treats them as keepers, and the
  Metin dropper's books are never junk. Appending to the personality enum is
  safe; inserting shifts every id in the panel's status file.
- **A route a fight interrupts is parked, not dropped.** `ClearPlayerBotRoute`
  keeps a route with `PLAYERBOT_NAV_PARK_MIN_WAYPOINTS` left in
  `vecParkedRoute`, and `MovePlayerBot` takes it up again from the nearest
  waypoint the bot can walk straight to when the same destination is asked
  for on the same map. Before this a valley crossing to a hub 70 km away was
  planned from scratch after every fight along the way - a far plan costs
  150-250 ms, and there were 100-170 of them a minute, 20-29 s of every 60.
  `PLAYERBOT_LOAD` reports `resumed=`; `PLAYERBOT_NAV: far plan` names the
  destination of every plan over 1024 cells, which is how the pattern was
  found (the same hub from the same few hundred metres, every two seconds).
- **Measure before tuning a budget.** `CPlayerBotManager::Update` logs
  `PLAYERBOT_LOAD:` once a minute: tick time, plans by distance bucket with
  their cost, deferrals, target searches, snapshot, map scans, saves, watchdog
  resets. CPU alone said "A*" once and the fix put every bot's map scan in the
  same second; the line says which plans, and how many milliseconds each.

- **The market is a ledger, not a shelf.** `RefreshPlayerBotMarketLedger`
  (`playerbot_market.h`, once a minute from the tick) counts the units on
  every open counter and the bots short of each material with money to buy
  it. `DecidePlayerBotMaterialListing` in `playerbot_town.h` lists a
  material only while supply is under 1.5 x 5 x demand, allows one probe
  stack when nobody is short, and logs `PLAYERBOT_MARKET: held ... reason=`
  for the rest. `GetPlayerBotShopAskingPrice` blends the prior with the
  sale median by n/(n+4) in log space, applies ((D+5)/(S+5))^0.2 within
  [0.75, 1.35] for materials, and `LimitPlayerBotAskStep` lets a price move
  five percent per ten minutes. The prior is the merchant's price times
  three or a share of the median shopping wallet, whichever is more -
  the merchant pays pennies and the bots hold millions. `PLAYERBOT_MARKET:
  ledger` every ten minutes is the report. A human buying from a counter
  is invisible to all of it: the purchase goes through CShopManager and
  never reaches this code.
- **A counter line is a grid slot and an item id, not an index and a vnum.**
  `CShop::SetShopItems` lays a private shop out on a five-column grid by
  item height (a weapon is three cells, an armour two) and silently drops a
  line whose `display_pos` is already covered ("not empty position" in
  syserr); `CShopManager::Buy` indexes by that position. Numbering the
  lines 0, 1, 2 lost every second-row line under a weapon, and buyers were
  refused at empty slots with a hacker log line: 2158 refusals to 501
  purchases in one hour. `FindPlayerBotShopSlot` places lines the way
  `CGrid::FindBlank` does and `TPlayerBotShopOffer::bSlot` carries the
  result; `dwItemID` and `FindPlayerBotOfferItem` (the item exists and the
  keeper still owns it - the engine's own test) say whether the line is
  still for sale, because a sold stack's vnum is often still in the bag as
  a second stack. The buyer re-reads the counter on the tick it arrives,
  whatever the browse clock says.

- **A book is read once a day unless the panel says otherwise.** The
  engine puts SKILLBOOK_DELAY_MIN..MAX (eighteen to thirty hours) between
  two reads of one skill; `ManagePlayerBotSkillBooks` resets that with
  `SetSkillNextReadTime` after `PLAYERBOT_BOOK_FAST_DELAY` while the `BOOKS`
  key in the weights file is on (the default). A bot keeps
  `PLAYERBOT_BOOK_KEEP_PER_SKILL` books of each own skill and the rest are
  goods; a keyless treasure chest is junk once the bag is down to
  `PLAYERBOT_BAG_PRESSURE_FREE_CELLS`. The Moonlight chest opens by itself
  but only into a free cell, which is what a bag full of books and chests
  had stopped.
- **The chat reaches the bots through patch 0007, and only there.**
  `CInputMain::Chat` hands a player's shout to
  `CPlayerBotManager::OnPlayerShout` after `SendShout`, and
  `CInputMain::Whisper` hands a whisper addressed to a bot to
  `OnPlayerWhisper` instead of a descriptor with no client; `shop.h` gets
  `GetItemVector()` so a bot can read a player's counter and buy from it
  (capped at `PLAYERBOT_MARKET_STACK_WALLET_PERCENT` of the median wallet
  per line). The staged `input_main.cpp` and `shop.h` ship in
  `server-update-files.txt` like 0006's files. A bot's own shouts go out
  through `SendShout` directly and never come back through the hook. Text
  is CP1250; `FoldPlayerBotChatText` is how names are compared.

- **Hunting stones is a state, not only a role.** `IsPlayerBotMetinHunting`
  in `playerbot_types.h` is what the planner, the target scoring and the
  wandering ask; it is true for the hunter role for life and for any other
  bot during a Metin expedition (`RollPlayerBotMetinExpedition` in
  `playerbot_planner.h`: an hourly roll, `PLAYERBOT_METIN_EXPEDITION_*`, the
  METIN weight scales the chance). A rule that tests `bBotRole ==
  BOT_ROLE_METIN_HUNTER` directly is a rule the expedition does not reach.

## Engine facts worth not re-deriving

- Item types/subtypes live in `common/item_length.h`; map attributes and
  `SECTREE_SIZE`/`CELL_SIZE` in `game/src/sectree.h`.
- Map world coordinates: `world = BasePosition + cell * 100`, with `BasePosition`
  from the map's `Setting.txt` and `cell` from `npc.txt`. Map 21 is `metin2_map_b1`.
- `server_attr` is per-sector lzo1x: `int32 width, height`, then per sector a
  `uint32` size and a block expanding to 128×128 `uint32` attributes, one per
  50 world units. `ATTR_BLOCK = 1<<0`, `ATTR_WATER = 1<<1`. Decoder and a terrain
  dump: `tools/decode_server_attr.py`.
- **`ATTR_WATER` is terrain, not a wall.** The engine tests it in exactly one
  place -- whether there is water in front of a fishing rod -- and never for
  movement. A river carries `BLOCK|WATER`; a bridge deck or a ford carries
  `WATER` with the block bit cleared, and that is how a map says "cross here".
  Orc Valley is 23 islands joined by 22 such crossings, so the navigation
  treating water as blocking left every bot on the island the entrance opens
  onto: 17.6% of the walkable ground, 161 of 532 spawn groups. It blocks on
  `ATTR_BLOCK|ATTR_OBJECT` and charges `PLAYERBOT_NAV_WATER_PENALTY` per wet
  cell instead, so a bridge is used and the desert shallows are walked round.
  `tools/analyse_map_bridges.py` measures this for any map.
- **Reading a spawn file: `group.txt` and `group_group.txt` are not the same
  shape.** In `group.txt` a member line is `<idx> "<name>" <mob vnum>` and the
  mob is the **last** field; in `group_group.txt` it is `<idx> <group vnum>
  <probability>` and the group is the **middle** one. Taking the last field of
  both - which reads a probability as a group id - makes every `r` line in every
  regen.txt resolve to nothing, and the map then looks empty. It is not: Orc
  Valley alone has 4041 spawn points over 32 mob types. A regen line's type is
  its first field, `m`/`b`/`e` naming a mob directly, `g` a group, `r` a
  group_group; the id is the last field of that line.
- **Where the refine materials come from.** The 407 recipes in
  `player.refine_proto` name 84 distinct materials; 64 of them drop from a
  monster that stands on one of the fourteen hosted maps (`mob_proto` column 33
  through `etc_drop_item.txt`, or `mob_drop_item.txt`), and the fishbone comes
  from gutting a fish, which no drop table records. Orc Valley alone carries
  ten - the Orc Amulet from Elite Orc (631) and Big Bald Orc (651), the
  Esoteric Guide from 701/751, Orc Tooth, Snake Tail, Curse Book - and the Bear
  Hide that 943 pieces of +6 gear were waiting on comes from ordinary bears on
  maps 21 and 24. What was in shortage was never the drop; it was the killing:
  bots warped in at one point and never left it, and a spare material was
  vendored on the next town visit. An earlier version of this note said 28 of
  84 were obtainable. That number came from the broken group_group parser
  described above; measure again before believing any count of this kind.
- Drop tables answer three different questions and only one of them uses vnums.
  `mob_drop_item.txt` is per-mob and by vnum; `etc_drop_item.txt` and
  `common_drop_item.txt` key on the **Korean item name**, and the etc table is
  reached through `mob_proto` column 33 (`DROP_ITEM`), one designated item per
  mob. Grepping a vnum finds nothing in two of the three. The chance is
  `prob * 10000 * PERCENT_LVDELTA * rate / 100` against `number(1, 4000000)` -
  and the `PRIV_ITEM_DROP` term in `GetDropPct` is defeated by an operator
  precedence bug in the engine, so it never applies.
- Shellfish (27987) and the three pearls (27992-27994) are hardcoded in
  `fishing.cpp` and `char_item.cpp`, not in `fishing.txt`. They carry 26 and 14
  recipes respectively, so fishing is the only route past the high refines.
- **The rest of the fishing chain, as the engine does it.** A live fish
  used (`fishing::UseFish`) becomes a dead fish, a bone, a shellfish or
  nothing. A dead fish is grilled by handing it to a campfire: Dried Wood
  (27600, the Fisherman's shop, 20 000 yang) used once spawns mob 12000 for
  forty seconds, `CHARACTER::GiveItem(campfire, cell)` runs `fishing::Grill`
  and the grilled fish (27863-27883) comes back - potions of 180/350/230 HP,
  180/500 SP, a Carp for movement speed and a Rudd for dexterity
  (USE_ABILITY_UP). A shellfish (27987, `char_item.cpp` case 27987) holds a
  Stone Piece half the time, nothing 30%, then a white, blue or blood pearl
  at 10/7/3% - so opening one is a bet the bot weighs against selling it
  whole, and the population counts every outcome including the empty ones
  (`PLAYERBOT_SHELLFISH:` every ten minutes).
- Fishing: the rod goes in `WEAR_WEAPON`; bait is **not** consumed from the pouch
  but written into the rod's socket 2 by using a bait item. A cast bites after
  10–40 s and then leaves a 6 s window; `fishing::Compute` peaks ~3 s after the
  bite. Calling `fishing()` while a cast is live is the same as pulling.

## `PLAYERBOTS_FEATURE_SPECS.md`

Design intent, not a reference. It was written independently of the code and its
constants are frequently wrong — verify every VNUM, distance and API call against
the engine before using it. Modules 2 and 3 in it are already implemented, and
implemented differently from what it describes.

## Conventions

- Comments explain *why*, in English, in the voice of the surrounding code.
  Prefer explaining the constraint that forced the shape over restating the code.
- Log with the `PLAYERBOT_<AREA>:` prefix and include `pid=` and `name=`.
- Player-visible bot strings are Polish, ASCII-only (no diacritics).
- Tune with named constants at the top of the namespace, not inline literals.
- Commit messages are lowercase `type(scope): summary` in the imperative.


## Recent Session History & Unpushed State (2026-09-03)

- **Unpushed Commits (2 ahead of origin/main):**
  * 4812874: eat(playerbot): open the stalls, announce good refines, learn what lives on each map
  * d9fc647: ix(playerbot): let a parked keeper reopen its stall after a restart
- **Engine Patches:**
  * Added patch for char.cpp replacing GetPart(PART_MAIN) > 2 with IsPolymorphed(), registered in context build.
- **Stalls / Stragany Verification:**
  * Tested live with 350 running bots: 14-33 stalls active around the market in Bokjung with zero rejections, and successfully recover after server/container restarts.
- **Next Roadmap Priorities:**
  * From PLAYERBOTS_FEATURE_SPECS.md: Module 2 (Mounted combat tuning against Metin stones), Module 4 (Bot guilds and guild marks), Module 5 (Live AI Config sliders in admin panel without recompilation), Module 6 (Weekly season analytics).
