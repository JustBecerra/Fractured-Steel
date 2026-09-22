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

using System.Linq;
using OpenRA.Mods.Common.Traits;
using OpenRA.Mods.Common.Widgets;
using OpenRA.Widgets;

namespace OpenRA.Mods.Example.Widgets.Logic
{
	public class ProductionGroupLogic : ChromeLogic
	{
		[ObjectCreator.UseCtor]
		public ProductionGroupLogic(Widget widget, World world)
		{
			var palette = widget.Get<ProductionPaletteWidget>("PRODUCTION_PALETTE");

			ProductionQueue QueueFor(string group)
			{
				if (world.LocalPlayer == null)
					return null;

				return world.LocalPlayer.PlayerActor.TraitsImplementing<ProductionQueue>()
					.FirstOrDefault(q => q.Enabled && q.Info.Type == group);
			}

			foreach (var child in widget.Get("PRODUCTION_TYPES").Children)
			{
				if (child is not ProductionTypeButtonWidget button)
					continue;

				button.OnMouseUp = _ =>
				{
					var queue = QueueFor(button.ProductionGroup);
					if (queue != null)
						palette.CurrentQueue = queue;
				};

				button.IsDisabled = () =>
				{
					var queue = QueueFor(button.ProductionGroup);
					return queue == null || !queue.BuildableItems().Any();
				};

				button.IsHighlighted = () =>
					palette.CurrentQueue != null && palette.CurrentQueue.Info.Type == button.ProductionGroup;
			}
		}
	}
}
