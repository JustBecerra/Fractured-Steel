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

using OpenRA.Graphics;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.Example.Traits
{
	[Desc("Tops every painted resource cell up to Amount. Map density is stored in a byte, so a 30000 pile cannot be saved in the map.")]
	public class AlloyPilesInfo : TraitInfo, Requires<IResourceLayerInfo>
	{
		public readonly string Type = "Alloy";
		public readonly int Amount = 30000;

		public override object Create(ActorInitializer init) { return new AlloyPiles(this); }
	}

	public class AlloyPiles : IWorldLoaded
	{
		readonly AlloyPilesInfo info;

		public AlloyPiles(AlloyPilesInfo info)
		{
			this.info = info;
		}

		void IWorldLoaded.WorldLoaded(World w, WorldRenderer wr)
		{
			var layer = w.WorldActor.Trait<IResourceLayer>();
			foreach (var cell in w.Map.AllCells)
			{
				var resource = layer.GetResource(cell);
				if (resource.Type != info.Type || resource.Density >= info.Amount)
					continue;

				layer.AddResource(resource.Type, cell, info.Amount - resource.Density);
			}
		}
	}
}
