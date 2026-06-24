# CERN Science Gateway — effects mod

Attaches three city-wide effects to the `CERN_ScienceGateway` building:

| Effect | Value | Mode |
|---|---|---|
| Interest in University Education | +5% | Relative |
| University Graduation Chance | +5% | Relative |
| Network (telecom) Capacity | +20,000 | Absolute |

The mesh/asset alone cannot grant city-wide bonuses — those are simulation
modifiers, so they need this small code mod alongside the asset.

## Prerequisites

1. Own Cities: Skylines II and install the **modding toolchain** from inside the
   game. This sets the `CSII_TOOLPATH` environment variable and provides
   `Mod.props` / `Mod.targets` (referenced by the `.csproj`).
2. .NET SDK + the toolchain's generated solution.

Recommended: create a fresh mod with the toolchain template, then drop `Mod.cs`
and `CernEffectsSystem.cs` into it (the included `.csproj` mirrors the template).

## Build & run

```
dotnet build -c Release
```

The toolchain copies the built mod into the local mods folder. Launch the game,
enable the mod, then place/select the CERN building.

## ⚠ One-time verification (important)

The exact `CityModifierType` names and `ModifierValueMode` names are
**version-specific** to your `Game.dll`. This mod is written with the most likely
spellings, marked `⚠ VERIFY` in `CernEffectsSystem.cs`:

- `UniversityInterest`
- `UniversityGraduation`
- `TelecomCapacity`

To confirm them on your install:

1. Build & run once. On load, the mod **dumps every `CityModifierType` and
   `ModifierValueMode` value to the log** (`%LOCALLOW%/Colossal Order/Cities
   Skylines II/Logs/CernScienceGateway.log`, or the Player.log).
2. Find the entries matching university-education *interest*, university
   *graduation*, and *telecom/network capacity*.
3. If any constant in `MODIFIERS` (top of `CernEffectsSystem.cs`) doesn't match,
   fix the spelling there and rebuild. The `Delta`/`Mode` values rarely change.

Alternative: open `Game.dll` in **ILSpy/dnSpy** and read
`Game.City.CityModifierType` directly, or inspect a vanilla education/telecom
signature building with the **Scene Explorer** mod to see real values in use.

## Notes on the prefab lookup

`CernEffectsSystem` looks the prefab up as `nameof(BuildingPrefab)` + the asset
name. If your asset imported as a different prefab type, the log dump section in
the code explains how to adjust the `PrefabID`. The prefab name must match the
asset name exactly: `CERN_ScienceGateway`.
