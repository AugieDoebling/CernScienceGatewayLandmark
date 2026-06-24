using System;
using System.Text;
using Game;
using Game.Prefabs;
using Game.City;            // CityModifierType, ModifierValueMode live here

namespace CernScienceGateway
{
    /// <summary>
    /// Attaches the three city-wide effects to the CERN_ScienceGateway prefab:
    ///   +5%  Interest in University Education
    ///   +5%  University Graduation Chance
    ///   +20,000 Network (telecom) Capacity
    ///
    /// HOW IT WORKS
    ///   * Finds the prefab by name through PrefabSystem.
    ///   * Ensures it has a CityModifier authoring component holding our entries.
    ///   * Calls PrefabSystem.UpdatePrefab so the change reaches the live prefab
    ///     entity's DynamicBuffer&lt;Game.City.CityModifier&gt;.
    ///
    /// VERIFY-ON-YOUR-GAME (see README): the first time this runs it DUMPS every
    /// CityModifierType value and ModifierValueMode value to the mod log. Open the
    /// log, find the exact spellings for "university interest", "university
    /// graduation" and "telecom/network capacity", and confirm the three constants
    /// in MODIFIERS below. These identifiers are version-specific.
    /// </summary>
    public sealed partial class CernEffectsSystem : GameSystemBase
    {
        // The prefab's name AND the FBX/main-mesh name must match this exactly.
        private const string PrefabName = "CERN_ScienceGateway";

        private PrefabSystem m_PrefabSystem;
        private bool m_Done;
        private bool m_DumpedEnums;

        // ----------------------------------------------------------------
        // EDIT HERE. One row per desired effect.
        //   Type  : a CityModifierType value (confirm spelling from the log dump)
        //   Delta : Relative -> fraction (0.05 == +5%);  Absolute -> flat amount
        //   Mode  : Relative for the % bonuses, Absolute for the flat +capacity
        // ----------------------------------------------------------------
        private static CityModifierInfo[] MODIFIERS => new[]
        {
            new CityModifierInfo
            {
                m_Type  = CityModifierType.UniversityInterest,    // ⚠ VERIFY name
                m_Delta = 0.05f,                                  // +5%
                m_Mode  = ModifierValueMode.Relative,
            },
            new CityModifierInfo
            {
                m_Type  = CityModifierType.UniversityGraduation,  // ⚠ VERIFY name
                m_Delta = 0.05f,                                  // +5%
                m_Mode  = ModifierValueMode.Relative,
            },
            new CityModifierInfo
            {
                m_Type  = CityModifierType.TelecomCapacity,       // ⚠ VERIFY name (network capacity)
                m_Delta = 20000f,                                 // +20,000 flat
                m_Mode  = ModifierValueMode.Absolute,
            },
        };

        protected override void OnCreate()
        {
            base.OnCreate();
            m_PrefabSystem = World.GetOrCreateSystemManaged<PrefabSystem>();
        }

        protected override void OnUpdate()
        {
            if (!m_DumpedEnums)
            {
                DumpEnums();
                m_DumpedEnums = true;
            }

            if (m_Done) return;

            // Look the prefab up. BuildingPrefab is the usual base type for a
            // placed building; if your asset imported as a different type, adjust
            // the type name in this PrefabID (the log dump notes how to check).
            var id = new PrefabID(nameof(BuildingPrefab), PrefabName);
            if (!m_PrefabSystem.TryGetPrefab(id, out PrefabBase prefab) || prefab == null)
            {
                // Not loaded yet (or wrong type/name) — try again next frame.
                return;
            }

            ApplyModifiers(prefab);
            m_Done = true;
        }

        private void ApplyModifiers(PrefabBase prefab)
        {
            try
            {
                if (!prefab.TryGet(out CityModifier cm) || cm == null)
                {
                    cm = prefab.AddComponent<CityModifier>();
                }

                cm.m_Modifiers = MODIFIERS;

                // Push the authoring change into the live prefab entity.
                m_PrefabSystem.UpdatePrefab(prefab);

                Mod.log.Info($"[{Mod.Name}] Applied {MODIFIERS.Length} city modifiers to '{PrefabName}'.");
            }
            catch (Exception e)
            {
                Mod.log.Error($"[{Mod.Name}] Failed to apply modifiers: {e}");
            }
        }

        // One-time reflection dump so you can read the REAL enum spellings from
        // the log on your installed game version.
        private void DumpEnums()
        {
            var sb = new StringBuilder();
            sb.AppendLine($"[{Mod.Name}] ==== CityModifierType values ====");
            foreach (var n in Enum.GetNames(typeof(CityModifierType)))
                sb.AppendLine("    " + n);
            sb.AppendLine($"[{Mod.Name}] ==== ModifierValueMode values ====");
            foreach (var n in Enum.GetNames(typeof(ModifierValueMode)))
                sb.AppendLine("    " + n);
            Mod.log.Info(sb.ToString());
        }
    }
}
