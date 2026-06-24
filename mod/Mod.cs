using Colossal.Logging;
using Game;
using Game.Modding;
using Game.SceneFlow;

namespace CernScienceGateway
{
    // Entry point recognised by the CS2 modding toolchain.
    public sealed class Mod : IMod
    {
        public const string Name = "CERN Science Gateway Effects";

        public static ILog log = LogManager
            .GetLogger(nameof(CernScienceGateway))
            .SetShowsErrorsInUI(false);

        public void OnLoad(UpdateSystem updateSystem)
        {
            log.Info($"[{Name}] OnLoad");

            // Patch our building prefab once prefabs are available.
            // PrefabUpdate runs after the prefab system has loaded prefabs.
            updateSystem.UpdateAt<CernEffectsSystem>(SystemUpdatePhase.PrefabUpdate);
        }

        public void OnDispose()
        {
            log.Info($"[{Name}] OnDispose");
        }
    }
}
