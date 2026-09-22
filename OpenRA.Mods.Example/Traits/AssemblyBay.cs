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

using System;
using System.Linq;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.Example.Traits
{
	[Desc("Mech Assembly loadout. Grants the selected Frame part conditions on production.",
		"SetFrameLoadout order TargetString is torso|legs|left|right.")]
	public class AssemblyBayInfo : TraitInfo
	{
		[Desc("Default torso condition granted to produced Frames.")]
		public readonly string DefaultTorso = "torso-assault";

		[Desc("Default legs condition granted to produced Frames.")]
		public readonly string DefaultLegs = "legs-bipedal";

		[Desc("Default left-arm condition granted to produced Frames.")]
		public readonly string DefaultLeftArm = "arm-sword";

		[Desc("Default right-arm condition granted to produced Frames.")]
		public readonly string DefaultRightArm = "arm-shield";

		[ActorReference]
		[Desc("Actor names that receive the loadout.")]
		public readonly string[] FrameActors = { "fs_frame" };

		public override object Create(ActorInitializer init) { return new AssemblyBay(this); }
	}

	public class AssemblyBay : INotifyProduction, IResolveOrder
	{
		public const string OrderID = "SetFrameLoadout";

		readonly AssemblyBayInfo info;

		public string Torso { get; private set; }
		public string Legs { get; private set; }
		public string LeftArm { get; private set; }
		public string RightArm { get; private set; }

		public AssemblyBay(AssemblyBayInfo info)
		{
			this.info = info;
			Torso = info.DefaultTorso;
			Legs = info.DefaultLegs;
			LeftArm = info.DefaultLeftArm;
			RightArm = info.DefaultRightArm;
		}

		public void SetLoadout(string torso, string legs, string left, string right)
		{
			if (!string.IsNullOrEmpty(torso))
				Torso = torso;
			if (!string.IsNullOrEmpty(legs))
				Legs = legs;
			if (!string.IsNullOrEmpty(left))
				LeftArm = left;
			if (!string.IsNullOrEmpty(right))
				RightArm = right;
		}

		void IResolveOrder.ResolveOrder(Actor self, Order order)
		{
			if (order.OrderString != OrderID)
				return;

			var parts = (order.TargetString ?? "").Split('|');
			SetLoadout(
				parts.ElementAtOrDefault(0),
				parts.ElementAtOrDefault(1),
				parts.ElementAtOrDefault(2),
				parts.ElementAtOrDefault(3));
		}

		void INotifyProduction.UnitProduced(Actor self, Actor other, CPos exit)
		{
			if (!info.FrameActors.Contains(other.Info.Name, StringComparer.Ordinal))
				return;

			foreach (var condition in new[] { Torso, Legs, LeftArm, RightArm })
			{
				if (string.IsNullOrEmpty(condition))
					continue;

				other.TraitsImplementing<ExternalCondition>()
					.FirstOrDefault(t => t.Info.Condition == condition && t.CanGrantCondition(self))
					?.GrantCondition(other, self);
			}
		}
	}
}
