# Validation record - 2026-11-06

Tested on Linux with stock MHGURecomp commit `a272b61`, MHGU 1.4 game data,
and the standalone Armor Fusion NRO. The executable has no built-in Armor
Fusion implementation. Clients were isolated, hidden/windowed, and used copied
saves; normal game installations, mods and saves were not replaced.

| Artifact | SHA-256 |
| --- | --- |
| Tested stock executable | `efc7ae395d50b26ada6d6b30b6253f9a1a0fe27882d9b49c6068ed2353b8036e` |
| `armor_fusion.nro` | `aeaf19c048f08845f44c269842cc2ab07e4d1c678c70c4a53f76546a2aa76d11` |

## Automated checks

`make all test test-arm` passed with a Unicorn-enabled `ARM_PYTHON`: C catalog
and policy checks, 20 metadata/build tests, three archive tests, and actual ARM
bridge/preflight tests. The ARM checks cover incoming LR, register and stack
arguments, isolated scratch, original calls, return values, safe hook chaining,
and rejection of caller-sensitive conflicts before any fusion hook is installed.

A separate clean build reproduced the NRO byte-for-byte. Generated AFUS bytes
match the reference implementation. Changing the dump path or table contents
regenerates metadata; unchanged inputs preserve incremental artifacts. The
runtime archive contains only the NRO, README, license and checksums. The tested
Compendium plus Armor Fusion use 8,454,144 aligned bytes plus 65,536 bytes of
loader headroom within the shared 12 MiB region.

## Native transactions and persistence

All six cases completed native material selection, payment, fusion and
separation. The numbers below identify equipment-box positions in the test
fixture, rather than armor IDs or a requirement on the player's box layout.

| Case | Base / appearance box positions | Result |
| --- | --- | --- |
| LR, decorated equipment | 27 / 48 | Paid fusion and separation passed; donor decoration returned |
| LR | 40 / 41 | Paid fusion and separation passed |
| HR | 50 / 51 | Paid fusion and separation passed |
| G | 60 / 61 | Paid fusion and separation passed |
| HR with Hero appearance | 50 / 70 | Paid fusion and separation passed |
| G with Hylian appearance | 60 / 75 | Paid fusion and separation passed |

Checks compared native equipment and appearance fields, selected material
deductions, fees, returned equipment/decorations, statistics and skills with the
expected transaction and reference behavior. All six ordered mixed-rank pairs
between LR, HR and G appeared disabled in the native list and rejected payment.

The decorated case was saved through the game's native Save action, closed and
cold-loaded while fused, then separated, saved, closed and cold-loaded again.
Both reloads matched the expected complete equipment, inventory, zenny,
statistics and skills exactly. This is separate from the copied checkpoints
used for the solo and multiplayer checks below.

## Native UI and previews

Eighteen frontal HD preview cases were visually reviewed: head/chest/arms/waist/legs at
LR, HR and G, plus Maccao, Hero and Hylian head appearances. Plain transactions
and HD previews retained the native interface. Held confirm/back inputs,
quantity cancellation and three repeated open/close cycles left the save
unpaid and restored the same parent preview/light state. Ordinary smithy
preview operation was also restored.

## Compendium coexistence

With the companion patch applied, both actual load orders passed decorated
fusion/payment/separation with exact comparisons, the native Add to Wishlist
hint, and Start + Left opening Compendium. Right-stick click captured Petrified
Blade Lv2, which appeared in the wishlist with its LR ore requirement in both
runs. Forge's recorded module addresses were:

| Load order | First module | Second module |
| --- | --- | --- |
| Compendium first | Compendium `0x03200000` | Armor Fusion `0x039d0000` |
| Armor Fusion first | Armor Fusion `0x03200000` | Compendium `0x03240000` |

Both compatibility clients were cleanly closed after verification.

## Solo and shared quest

Solo control and fused checkpoints entered quest 101, stage 1, camp zone 0.
All seven stable native equipment records, appearance/decorations, per-piece
skill points, active skills, statistics and identity matched the corresponding
reference captures. The fused helmet's appearance and color were visually
checked.

Two actual clients created/joined a private local direct-IP hub, posted/joined
the quest and departed into the same quest/stage with distinct player slots.
The observer ran stock Recomp with neither the fusion NRO nor built-in fusion.
Its replicated host matched all seven equipment records, appearance,
decorations, skill points, active skills, statistics and identity; the fused
helmet was visually checked from the observer. Both clients' own equipment,
statistics and skills matched their preconnection baselines. No guest memory
writes were used for networking or positioning.

These solo/multiplayer inputs were copied memory-derived checkpoints, so those
runs establish runtime/reference and replication parity. Native payment and
save persistence are established by the separate transaction tests above.

## Coverage limits and reproduction

The stated runtime matrix is complete and all owned test clients were cleanly
closed. This record does not establish Windows, Android, console, WAN/NAT, four-player
play, quest completion, another decorated/rank multiplayer case, or every
armor combination. Mixed-rank choices are correctly disabled/rejected, while
their explanation retains the reference's generic native error wording.

To repeat the matrix, build the stock executable without core fusion, verify
the NRO checksum, and use independent copied saves in windowed profiles. Test
the six transaction categories above with before/paid/separated snapshots;
exercise every ordered mixed-rank pair; save and cold-load both fused and
separated states; inspect all preview slots and cancellation cycles. Then load
patched Compendium in each order and repeat the decorated transaction and
wishlist controls. Finally join a real shared quest with an observer that has
neither implementation, and compare its replicated equipment, appearance,
statistics and skills against the host's native snapshot. Keep save/payment
proof separate from checkpoint-loading and network proof.

## Full installed mod stack

The final standalone Compendium build also passed a fresh cold-load check with
the installed plugin stack. These two Compendium artifacts are distinguished
because the standalone public build removes private build paths and uses its
own source/build packaging:

| Compendium artifact | SHA-256 | Runtime coverage |
| --- | --- | --- |
| Earlier companion compatibility build | `f03410a4fb2ec33f3b89cdddfe2b9ace7db371dead324f67c4b087ae3bf669e8` | Both two-plugin load orders above |
| Final standalone public build | `753a00043c0d2c2e496cdac04e41c52322e2e0458e7580fea4200b1ccdd53b7b` | Full installed stack: cold town UI, decorated payment/separation, actual quest HUD |

Armor Fusion remained
`aeaf19c048f08845f44c269842cc2ab07e4d1c678c70c4a53f76546a2aa76d11`
throughout. All seven NROs loaded: MapAssist, Key Quest Markers, Damage Numbers,
Compendium, HuntLog/Hunter HUD, World Sharpness Gauge and Armor Fusion. The
test used twelve RomFS layers including the base game and eleven mod layers,
with HD textures/UI/font layers retained. Aligned plugin memory was 11,010,048
bytes plus 65,536 bytes of loader headroom within 12,582,912 bytes. No plugin
import, hook-installation or resource-load failures were recorded.

In town, native controls exercised Compendium opening, weapon classes/tree/
details, material-source links, wishlist persistence, locations/grouped
gathering and controller-keyboard search. The decorated LR fusion and separation
case passed again with the expected fee, materials and returned decoration.

An actual quest 101 run showed the passive HUD with `Toadstool ×5`, zones
`2, 4, 7, 8, 9, 10, 11` and `For Wyvern's Perch Lv1`. Native movement/actions
continued to reach the hunter while the HUD was open. The missing-material
target was prepared by adding a stable recipe key to the isolated wishlist
file; inventory and game-save contents were not changed for that fixture.
Live reduction of the counter by gathering was not exercised in this run.

World Sharpness Gauge logged `WSG r65 gauge row check stopped at stage 21:
instance=0 controller=0 gauge=0`. The identical warning occurred in quest 101
with the original installed stack, original Compendium and no Armor Fusion.
That baseline Compendium SHA-256 was
`4f0d46694c4662b90a950ceeff7a684f315581031112a5e96a2044cf96e95e2f`.
This establishes the warning predates these releases; it does not establish
correct gauge drawing or exercise every unrelated plugin's combat features.
All owned full-stack and baseline clients were cleanly closed.


## Cross-class appearance change - 2026-11-24

The runtime matrix above describes the older release hash, not this change.
Issue #1 was traced against the local MHGU 1.4.0 NSO without running a game
client or modifying saves:

- Native commit `0x348f00` keeps the base ID at record `+6` and writes the donor
  appearance ID at `+8` (`0x349068..0x349090`).
- `0x2db0b0` and `0x2db160` narrow a universal base's Blademaster/Gunner answers
  using its donor. `0x2db210` detects that narrowing; the commit's final branch
  at `0x3491a4..0x3491c4` can then unequip the base.
- Native pair validation sets only bit `0x20` for class incompatibility at
  `0x340e6c..0x340f54`. The adapter now clears that bit for catalog-recognized,
  same-rank, same-slot pairs in its owned hunter-fusion UI. Other bits remain.
- Three guarded class hooks call their stock originals with a private copy of
  the first ten record bytes whose appearance ID is zero. This preserves the
  base's native eligibility and disables donor-driven unequipping without
  changing equipment or appearance fields. These hooks apply to existing fused
  hunter armor as well as newly fused armor and require stock entry points.

`make all test test-native GAME_DIR=/path/to/game-data
ARM_PYTHON=/path/to/python-with-unicorn-and-lz4` passed. The ordinary catalog,
policy, packaging, compiled ARM bridge and hook-preflight checks passed.
`tests/test_class_arm.py` loads the private local NSO and executes its actual
class helper bodies together with the compiled adapter and bridge. Only the
metadata lookup and vtable class/slot answers are synthetic. Before the fix,
a universal base with Gunner appearance returned `(BM=0, Gunner=1, narrow=1)`;
the regression now requires `(1,1,0)`.

The new ARM matrix covers all five hunter record slots, both class directions,
universal bases with either donor class, unfused armor, unknown metadata,
non-hunter pass-through, unchanged equipment bytes and the native appearance-ID
getter. Pair-hook cases cover class-bit removal, retention of other native
restriction bits, rank and slot rejection, and unowned/non-hunter UI scopes.
The three new class-hook conflicts stop initialization before any hook installs.

The actual runtime pass below supplements those isolated native-helper tests.
The synthetic metadata fixtures alone do not establish every real combination.

## Runtime regression pass - 2026-11-24

Tested NRO SHA-256:
`320b2a48018f9b0c0bf6a0b3a75f6b3b2bee19693633511fed0842bbc3506b22`.
The private Linux runtime used stock source `06fa605`, with no core fusion, and
only its plugin/trampoline/stub/HLE memory layout expanded to accommodate peer
mods. Strict matching generated-game-library identity was retained. Tests used
copied saves, separate settings/mods, dummy audio, rejected hardware controllers,
Xvfb and a loopback-only network namespace. The running user's game, save and
installed mods were not controlled or replaced.

| Native transaction | Result |
| --- | --- |
| Equipped Hunting Blademaster armor, Gunner appearance | All five slots passed paid fusion; equipment, skills and stats retained |
| Equipped Hunting Gunner head with ranged weapon, Blademaster appearance | Paid fusion and exact separation passed; Gunner base stayed equipped |
| Equipped decorated universal Leather head, Gunner appearance | Paid fusion and separation passed; decoration and stats preserved |
| HR Leather head, HR Bherna Gunner appearance | Paid fusion and exact separation passed |
| G Bherna head, G Gunner appearance | Paid fusion and exact separation passed |

Each payment compared the native base record, appearance ID, donor consumption,
fees and material deduction, with no unrelated inventory/equipment changes.
Separation restored the original base bytes, returned the donor, and charged
no additional materials or zenny. All six ordered mixed-rank directions between
LR/HR/G were visibly disabled and rejected confirmation without payment; a
same-rank cross-class control remained enabled. Native generic rejection wording
was retained.

The five-slot equipped result was saved through the native game menu. All 106
occupied equipment records matched the serialized save. A cold process reload
retained every record, item total, zenny, active skill and hunter statistic.
The result rendered with HD Textures v4, HD UI v4 and the hunter-font replacement
at 2560x1440 internal resolution in an isolated window (2488x1400 capture).
These visual checks cover the exercised sets, not every armor model.

The final Utility hook-order candidate
`2e869f39ab573e2c0c64f2a214364009b0691317c61c98c58bdd602c769b15e1`
was loaded with Fusion for the multiplayer run; the other client had neither
plugin. Actual native Create/Search Hub, quest posting/joining, standby and
departure placed both clients in Hub quest 10101, stage 1, camp, distinct slots.
The unmodified observer rendered all five Gunner appearances on the Blademaster
host. All seven equipment records, decorations, per-piece skill points, active
skills, identity, health and resistances matched on both sides. Utility's
in-quest gathering menu opened and closed while the session remained connected.

Raw quest attack/defense initially differed by +6/+12 on each owner's local
hunter, including the unfused stock control. Both carried Powercharm (item40)
and Armorcharm (item42). Native functions `0x2e2498` and `0x2e2fdc` apply those
bonuses through the owner-only pouch query `0x48813c` / local flag `+0x13cc`.
The actual native pouch-gate bodies were also executed independently in ARM
emulation. Removing only those known local bonuses from comparison produced
exact two-way base-stat parity; an injected one-point discrepancy still failed.
Raw captures were preserved unchanged. This was not a fusion or network-stat fix.
Both clients then used native Abandon Quest and Save prompts, returned to town,
and retained the original equipment records, inventory totals and hunter stats.

Private logs, before/paid/separated snapshots, native-save comparisons, plugin
hashes and multiplayer proof remain in ignored `build/pr-ready-lab/`. This pass
does not establish Windows/Android, WAN/NAT, four players, every armor pair or
completed quest rewards. Native transactions retained both the exercised Blademaster and Gunner bases
with their respective weapons; helper tests cover all five slots in both
directions. The UI still respects the base armor's native equipment restrictions.

Screenshots: [decorated universal base with Gunner appearance](screenshots/crossclass-universal.webp),
[unmodified multiplayer observer](screenshots/crossclass-multiplayer.webp).

## KatSmithy startup compatibility - 24 November 2026

With the copied full mod stack on the actual Windows Recomp 0.19.2 executable
**under Wine on Linux**, Fusion's old onInit hook made KatSmithy's first-update
stock-prologue probe fail (`smithy_win ... GUARD MISMATCH`). Candidate Fusion
`c4aa1f81a99d970bd702d2205b1821a28b61c1afa6b85d2eea91f7ec8512c4b8`
keeps text-base/catalog validation in onInit, then preflights and installs all
hooks once on the second update. Safe chains additionally accept the verified
Windows spill arena `[0xf0100000,0xf8100000)`; alignment and caller-sensitive
rejections remain enforced.

The copied-stack hook snapshot resolves game → Fusion `0xf17a4798` → Utility
`0x033b177c` → KatSmithy `0xf01536f4` → native continuation. This is Windows-build
execution under Wine, not physical/native Windows OS coverage. Full native-menu
and UI validation is recorded separately from this startup-chain evidence.

```sh
make all test test-native GAME_DIR=/home/rikiar/Games/MHGU/data ARM_PYTHON=/tmp/fusion-issue-venv/bin/python
```

All checks passed, including compiled ARM chaining through a high peer in both
callback orders, dynamic callback exports, spill boundaries, one-shot failure,
and unchanged class/pair rules. The earlier paid cross-class transactions and
two-client quest/appearance/stat pass used Fusion
`320b2a48018f9b0c0bf6a0b3a75f6b3b2bee19693633511fed0842bbc3506b22`.
They must not be relabeled as multiplayer tests of the new candidate: this
candidate changes startup scheduling and safe-entry recognition, not fusion
policy, classification, transactions or networking.

The same copied full nine-plugin Windows stack then passed KatSmithy's complete
weapon tree with its 3D preview, native Upgrade Equipment wishlist add/remove,
and the actual Fusion menu/armor-selector open and cancel. Selector teardown
restored both UI pointers to zero with byte-identical stable equipment, item
box, pouch and unchanged 460476z. KatSmithy accepted its stock first-update probe;
all 16 Fusion hooks were installed. These checks used a separate Wine prefix,
Xvfb, loopback-only network and private software Vulkan renderer, without
controlling or restarting the user's game. The installed main files match these
exact tested candidate NRO hashes; the original files/load order were backed up.
