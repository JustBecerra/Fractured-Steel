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
using OpenRA;
using OpenRA.Mods.Common.Widgets;
using OpenRA.Mods.Example.Traits;
using OpenRA.Traits;
using OpenRA.Widgets;

namespace OpenRA.Mods.Example.Widgets.Logic
{
	public class AssemblyLoadoutLogic : ChromeLogic
	{
		[ObjectCreator.UseCtor]
		public AssemblyLoadoutLogic(Widget widget, World world)
		{
			var title = widget.Get<LabelWidget>("ASSEMBLY_TITLE");
			var detail = widget.Get<LabelWidget>("ASSEMBLY_DETAIL");

			var detailText = "Assault torso · Bipedal legs · Sword · Shield";
			detail.GetText = () => detailText;

			Actor lastBay = null;
			widget.IsVisible = () =>
			{
				var actor = world.Selection.Actors
					.FirstOrDefault(a => a.IsInWorld && !a.IsDead && a.TraitOrDefault<AssemblyBay>() != null);
				if (actor == null)
				{
					lastBay = null;
					return false;
				}

				var bay = actor.Trait<AssemblyBay>();
				detailText = $"{Pretty(bay.Torso)} · {Pretty(bay.Legs)} · {Pretty(bay.LeftArm)} · {Pretty(bay.RightArm)}";

				if (actor != lastBay)
				{
					lastBay = actor;
					actor.World.IssueOrder(new Order(AssemblyBay.OrderID, actor, false)
					{
						TargetString = $"{bay.Torso}|{bay.Legs}|{bay.LeftArm}|{bay.RightArm}"
					});
				}

				return true;
			};
		}

		static string Pretty(string condition)
		{
			if (string.IsNullOrEmpty(condition))
				return "-";
			var parts = condition.Split('-');
			return parts.Length == 0 ? condition : parts[^1];
		}
	}
}
