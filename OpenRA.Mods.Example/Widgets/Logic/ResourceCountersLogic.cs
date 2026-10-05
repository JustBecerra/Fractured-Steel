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

using OpenRA.Mods.Common.Traits;
using OpenRA.Mods.Common.Widgets;
using OpenRA.Primitives;
using OpenRA.Widgets;

namespace OpenRA.Mods.Example.Widgets.Logic
{
	/// <summary>
	/// Right-hand resource panel. Personnel is still a placeholder.
	/// Alloy is the spendable stockpile. Energy is demand over supply.
	/// </summary>
	public class ResourceCountersLogic : ChromeLogic
	{
		[ObjectCreator.UseCtor]
		public ResourceCountersLogic(Widget widget, World world)
		{
			var power = widget.Get<LabelWidget>("POWER_COUNT");
			power.GetText = () =>
			{
				var (used, supply) = Energy(world);
				return used + "/" + supply;
			};
			power.GetColor = () =>
			{
				var (used, supply) = Energy(world);
				return used > supply ? Color.FromArgb(220, 64, 48) : Color.White;
			};
			widget.Get<LabelWidget>("ALLOY_COUNT").GetText = () => Alloy(world).ToString();
			widget.Get<LabelWidget>("CREW_COUNT").GetText = () => "0/20";
		}

		public static int Alloy(World world)
		{
			var player = world.LocalPlayer;
			if (player == null)
				return 0;

			var resources = player.PlayerActor.TraitOrDefault<PlayerResources>();
			return resources == null ? 0 : resources.GetCashAndResources();
		}

		static (int Used, int Supply) Energy(World world)
		{
			var player = world.LocalPlayer;
			if (player == null)
				return (0, 0);

			var power = player.PlayerActor.TraitOrDefault<PowerManager>();
			return power == null ? (0, 0) : (power.PowerDrained, power.PowerProvided);
		}
	}
}
