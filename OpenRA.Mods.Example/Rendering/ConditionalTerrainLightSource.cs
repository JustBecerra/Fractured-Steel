using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.Example.Rendering
{
	[Desc("Adds a localized circular light to the terrain while a condition is enabled.",
		"Unlike the stock TerrainLightSource, which is always on, this can be switched on and off",
		"and can be offset from the actor's centre so the light pools where an effect points.")]
	public class ConditionalTerrainLightSourceInfo : ConditionalTraitInfo, Requires<BodyOrientationInfo>
	{
		[Desc("Radius of the lit area.")]
		public readonly WDist Range = WDist.FromCells(3);

		[Desc("Brightness of the light. 0 is no light at all.")]
		public readonly float Intensity = 0;

		[Desc("Colour of the light.")]
		public readonly float RedTint = 0;
		public readonly float GreenTint = 0;
		public readonly float BlueTint = 0;

		[Desc("Position of the light relative to the actor's body, rotated with its facing.")]
		public readonly WVec Offset = WVec.Zero;

		public override void RulesetLoaded(Ruleset rules, ActorInfo ai)
		{
			if (!rules.Actors[SystemActors.World].HasTraitInfo<TerrainLightingInfo>())
				throw new YamlException("ConditionalTerrainLightSource requires the world TerrainLighting trait.");

			base.RulesetLoaded(rules, ai);
		}

		public override object Create(ActorInitializer init) { return new ConditionalTerrainLightSource(init.Self, this); }
	}

	public class ConditionalTerrainLightSource : ConditionalTrait<ConditionalTerrainLightSourceInfo>, INotifyRemovedFromWorld
	{
		readonly TerrainLighting terrainLighting;
		readonly BodyOrientation body;
		int token = -1;

		public ConditionalTerrainLightSource(Actor self, ConditionalTerrainLightSourceInfo info)
			: base(info)
		{
			terrainLighting = self.World.WorldActor.Trait<TerrainLighting>();
			body = self.Trait<BodyOrientation>();
		}

		WPos LightPosition(Actor self)
		{
			if (Info.Offset == WVec.Zero)
				return self.CenterPosition;

			return self.CenterPosition + body.LocalToWorld(Info.Offset.Rotate(body.QuantizeOrientation(self.Orientation)));
		}

		void AddLight(Actor self)
		{
			if (token != -1 || !self.IsInWorld)
				return;

			token = terrainLighting.AddLightSource(LightPosition(self), Info.Range, Info.Intensity,
				new float3(Info.RedTint, Info.GreenTint, Info.BlueTint));
		}

		void RemoveLight()
		{
			if (token == -1)
				return;

			terrainLighting.RemoveLightSource(token);
			token = -1;
		}

		protected override void TraitEnabled(Actor self) { AddLight(self); }
		protected override void TraitDisabled(Actor self) { RemoveLight(); }

		void INotifyRemovedFromWorld.RemovedFromWorld(Actor self) { RemoveLight(); }
	}
}
