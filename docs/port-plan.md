# Native Armor Fusion Forge port

User-approved design: port the tested PR260 behavior into a separate Forge NRO,
retain its native interface and prove parity on stock Recomp. Source reference:
MHGURecomp-fork commit 98ec08f, tree 17783501162c8c8f441057b7c9399e5b0c89140f.

## Constraints

- Preserve every native screen, material picker, rank/slot restriction, fee,
  cancellation/held-input safeguard, decoration handling, save and separation.
- Preserve the preview-light suspension/restoration fix. No replacement UI.
- Keep the portable policy and generated AFUS metadata; never commit extracted
  game tables, saves, generated binaries or diagnostic code.
- Use entry hooks and original trampolines, preserve native incoming LR for
  caller-scoped interception, and forward stack arguments correctly.
- Compendium's existing smithy hook must coexist in either load order.
- Stock executable must have no built-in fusion implementation. Observing peer
  must have neither the built-in implementation nor the fusion NRO.
- All live tests use copied saves and hidden/windowed clients; never fullscreen.
  Do not replace the user's normal executable, mods or saves during testing.
- No new worktree, no changes to PR260 and no public comments without a later
  user request. Keep source small, readable and independently reviewable.

## Tasks

1. ARM ABI and native adapter: reuse the tested C adapter behind a narrow guest
   bridge if it preserves arguments, LR, stack scratch and return semantics.
   Otherwise use typed guest callbacks. Build a real NRO with minimal imports.
   Test the bridge and original/native call paths before live transactions.
2. Portable catalog/policy: preserve pure validation; load builder-generated
   metadata from embedded bytes/mod RomFS without host executable paths. Reuse
   existing policy/catalog tests and compare metadata against the reference.
3. Coexistence/package: make signature checks chain-aware where safe; reject
   conflicting caller-sensitive hooks before installing a partial feature.
   Add a narrow Compendium compatibility change if necessary. Package NRO,
   source/build instructions and checksums with no game assets or saves.
4. Independent review: inspect the whole port, ABI boundaries and transactions;
   correct material findings and rerun covering checks.
5. Runtime parity: stock Recomp plus NRO alone; LR/HR/G and event payment/undo,
   six cross-rank rejections, decorations, cancellation/held inputs, ordinary
   forge restoration, native save/cold reload, plain/HD preview, repeated open/
   close, Compendium both load orders, solo and actual two-client shared quest.
   Compare exact native gear/items/zenny/stats/skills with the reference proof.
6. Deliver a ready-to-share zip and source with explicit tested versions and
   remaining platform/coverage limits. Cleanly close all owned test clients.

## Progress

- Design and scope accepted by the user's instruction to transform the feature.
- Reference source/tests and earlier proof remain unchanged.
- Built the standalone NRO with embedded, reference-identical AFUS metadata
  and only three Forge imports. The stock Linux test executable is commit
  `a272b61` and contains no built-in Armor Fusion implementation.
- C policy/catalog checks, 20 metadata/build tests, three archive tests, and
  actual ARM ABI/preflight checks pass. Independent catalog/build/package
  review findings were corrected and covering checks rerun. Clean build output
  reproduces the tested NRO; no raw game tables or saves enter the archive.
- Added the narrow Compendium source/test patch and standalone offline rebuild
  instructions under `compat/`. Caller-sensitive fusion hooks remain strict.
- Native runtime checks passed six LR/HR/G/event paid fusion/separation cases,
  decorations, all six ordered mixed-rank rejections, native Save and cold
  reload in both fused/separated states, and exact equipment/items/zenny/
  statistics/skills comparisons.
- Visually reviewed 18 HD previews (five slots at LR/HR/G plus Maccao/Hero/
  Hylian); held inputs, quantity cancellation, three open/close cycles, parent
  preview/light restoration and ordinary smithy behavior passed.
- Solo/reference parity and an actual two-client local direct-IP shared quest
  passed with a stock observer lacking both fusion implementations. Network
  checkpoint proof is kept separate from native payment/save proof.
- Both actual Compendium load orders passed decorated payment/separation with
  exact comparisons, native wishlist hint, Start + Left opening, and right-stick
  capture of Petrified Blade Lv2 with the expected LR ore wishlist requirement.
- The stated runtime parity matrix is complete. Every owned test client was
  cleanly closed, including both compatibility clients.
- The final standalone Compendium build passed full-stack cold town UI,
  decorated fusion/separation and quest 101 passive HUD/input checks with seven
  NROs and twelve RomFS layers including the base game. The original installed
  stack without Armor Fusion reproduces the World Sharpness Gauge startup
  warning; gauge correctness and unrelated combat features remain outside
  the proof. Exact artifact hashes and fixture limits are in `docs/validation.md`.
- Full case/method/coverage record: `docs/validation.md`. Tested NRO SHA-256:
  `aeaf19c048f08845f44c269842cc2ab07e4d1c678c70c4a53f76546a2aa76d11`.
- Release tooling produces an allowlisted NRO archive with checksums; source
  archives use the committed source tree. Windows/Android/console, WAN/four-player
  and every-armor coverage are outside the completed test matrix.
