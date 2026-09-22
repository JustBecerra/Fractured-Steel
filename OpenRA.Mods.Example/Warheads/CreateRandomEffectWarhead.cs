#region Copyright & License Information
/*
 * Copyright (c) The OpenRA Developers and Contributors
 * This file is part of OpenRA, which is free software. It is made
 * available to you under the terms of the GNU General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version. For more
 * information, see COPYING.
 */
#endregion

using OpenRA.GameRules;
using OpenRA.Mods.Common.Effects;
using OpenRA.Mods.Common.Warheads;
using OpenRA.Traits;

namespace OpenRA.Mods.Example.Warheads
{
	[Desc("CreateEffect that picks a sequence at random and never repeats the last one.")]
	public class CreateRandomEffectWarhead : CreateEffectWarhead
	{
		int last = -1;

		public override void DoImpact(in Target target, WarheadArgs args)
		{
			if (target.Type == TargetType.Invalid)
				return;

			var firedBy = args.SourceActor;
			if (target.Type == TargetType.Actor && !IsValidAgainst(target.Actor, firedBy))
				return;

			var explosion = Pick(firedBy.World);
			if (Image == null || explosion == null)
				return;

			var pos = target.CenterPosition;
			var palette = ExplosionPalette;
			if (UsePlayerPalette)
				palette += firedBy.Owner.InternalName;

			firedBy.World.AddFrameEndTask(w => w.Add(new SpriteEffect(pos, w, Image, explosion, palette)));
		}

		string Pick(World world)
		{
			if (Explosions == null || Explosions.Length == 0)
				return null;

			if (Explosions.Length == 1)
				return Explosions[0];

			var i = world.SharedRandom.Next(Explosions.Length);
			if (i == last)
				i = (i + 1 + world.SharedRandom.Next(Explosions.Length - 1)) % Explosions.Length;

			last = i;
			return Explosions[i];
		}
	}
}
