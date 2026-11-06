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
| Final standalone public build | `97682c1675085aa72cbb0d219d9a6381e80dd2a828efb99f0493d5b0a79d58e2` | Full installed stack: cold town UI, decorated payment/separation, actual quest HUD |

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
