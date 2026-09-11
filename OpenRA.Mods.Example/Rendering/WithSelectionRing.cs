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

using System.Collections.Generic;
using System.Linq;
using OpenRA.Graphics;
using OpenRA.Primitives;
using OpenRA.Traits;

namespace OpenRA.Mods.Example.Rendering
{
	[Desc("Renders a ground ring beneath the actor while it is selected.",
		"Unlike WithDecoration this draws in the world (under the unit) rather than the on-top annotation layer.")]
	public class WithSelectionRingInfo : TraitInfo
	{
		[FieldLoader.Require]
		[Desc("Image that contains the ring sprite.")]
		public readonly string Image = null;

		[Desc("Sequence to render.")]
		public readonly string Sequence = "idle";

		[Desc("Palette to render the sprite in. The ring sprite is truecolor, so this is effectively a no-op reference.")]
		public readonly string Palette = "greyscale";

		[Desc("Z offset applied so the ring renders beneath the unit.")]
		public readonly int ZOffset = -256;

		public override object Create(ActorInitializer init) { return new WithSelectionRing(init.Self, this); }
	}

	public class WithSelectionRing : IRender, ITick
	{
		readonly WithSelectionRingInfo info;
		readonly Animation anim;

		public WithSelectionRing(Actor self, WithSelectionRingInfo info)
		{
			this.info = info;
			anim = new Animation(self.World, info.Image);
			anim.PlayRepeating(info.Sequence);
		}

		IEnumerable<IRenderable> IRender.Render(Actor self, WorldRenderer wr)
		{
			if (!self.IsInWorld || self.IsDead || !self.World.Selection.Contains(self))
				return Enumerable.Empty<IRenderable>();

			var palette = wr.Palette(info.Palette);
			return anim.Render(self.CenterPosition, WVec.Zero, info.ZOffset, palette);
		}

		IEnumerable<Rectangle> IRender.ScreenBounds(Actor self, WorldRenderer wr)
		{
			yield return anim.ScreenBounds(wr, self.CenterPosition, WVec.Zero);
		}

		void ITick.Tick(Actor self) { anim.Tick(); }
	}
}
