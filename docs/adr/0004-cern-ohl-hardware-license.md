# ADR-0004: CERN-OHL-S-2.0 for Hardware Licensing

## Status
Accepted (v2.0.1)

## Context
QuakeGuard is a multi-layer project with distinct software and hardware components:

- **Software** (backend, mobile, firmware logic): Licensed under AGPL-3.0
- **Hardware** (KiCad schematics, PCB layout, Gerber files): Needs a separate, hardware-specific open-source license

The AGPL-3.0 is designed for software and its concepts (source code, compilation, linking) do not map cleanly to hardware design files. Using AGPL for hardware creates legal ambiguity.

## Decision
Apply **CERN Open Hardware Licence Version 2 — Strongly Reciprocal (CERN-OHL-S-2.0)** to all hardware design files in the `hardware/` directory:

- Placed as a separate `hardware/LICENSE` file (distinct from the root `LICENSE` for software)
- The CERN-OHL-S is the hardware equivalent of copyleft: modifications to the hardware design must be shared under the same terms
- This aligns with the project's open-source philosophy while using a license designed specifically for hardware

## Consequences
- **Positive:** Legally precise — the license terms are designed for hardware "Source" (schematics, PCB layout, Gerber files) and "Products" (manufactured PCBs).
- **Positive:** Strongly reciprocal — anyone modifying the PCB design must share their modifications (consistent with AGPL copyleft philosophy for software).
- **Positive:** CERN-backed and widely recognized in the open hardware community (CERN, RISC-V, others).
- **Negative:** Two licenses in one repo can confuse contributors. Mitigated by clear directory separation and documentation.

## Alternatives Considered
- **AGPL-3.0 for everything:** Legally unclear for hardware; AGPL concepts (linking, network interaction) have no hardware equivalent.
- **CERN-OHL-P (Permissive):** Allows proprietary derivatives. Rejected to maintain copyleft consistency with the software license.
- **CERN-OHL-W (Weakly Reciprocal):** Only requires sharing modifications to the original design, not the larger work. The strongly reciprocal variant better matches AGPL's intent.
- **TAPR OHL:** Less widely adopted than CERN-OHL; CERN-OHL v2 is the current community standard.
