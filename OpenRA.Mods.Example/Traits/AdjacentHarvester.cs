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
using System.Collections.Generic;
using OpenRA.Activities;
using OpenRA.Mods.Common.Activities;
using OpenRA.Mods.Common.Traits;
using OpenRA.Mods.Common.Traits.Render;
using OpenRA.Primitives;
using OpenRA.Traits;

namespace OpenRA.Mods.Example.Traits
{
	[Desc("Harvests from the cell beside a resource pile. The pile itself stays blocked.")]
	public class AdjacentHarvesterInfo : TraitInfo, Requires<HarvesterInfo>, Requires<MobileInfo>
	{
		public override object Create(ActorInitializer init) { return new AdjacentHarvester(); }
	}

	public class AdjacentHarvester : INotifyCreated, IResolveOrder, IDockClient
	{
		public BitSet<DockType> GetDockType => default;
		public DockClientManager DockClientManager => null;

		// The stock harvester already docks. This client only replaces the
		// activity it queues once the load is dumped.
		public bool CanDock(BitSet<DockType> type, bool forceEnter = false) => false;
		public bool CanDockAt(Actor hostActor, IDockHost host, bool forceEnter = false, bool ignoreOccupancy = false) => false;
		public bool CanQueueDockAt(Actor hostActor, IDockHost host, bool forceEnter, bool isQueued) => false;
		public void OnDockStarted(Actor self, Actor hostActor, IDockHost host) { }

		public bool OnDockTick(Actor self, Actor hostActor, IDockHost dock) => true;

		public void OnDockCompleted(Actor self, Actor hostActor, IDockHost host)
		{
			var replaced = false;
			for (var act = self.CurrentActivity; act != null; act = act.NextActivity)
			{
				if (act is FindAndDeliverResources)
				{
					act.Cancel(self, true);
					replaced = true;
				}
			}

			// A queued player order after the dump should still run.
			if (replaced || self.CurrentActivity == null || self.CurrentActivity.NextActivity == null)
				self.QueueActivity(true, new AdjacentFindAndDeliver(self, null));
		}

		void INotifyCreated.Created(Actor self)
		{
			self.QueueActivity(new AdjacentFindAndDeliver(self, null));
		}

		void IResolveOrder.ResolveOrder(Actor self, Order order)
		{
			if (order.OrderString != "Harvest")
				return;

			// The stock harvester queues a move onto the pile. Drop that and stand beside it.
			CPos? cell = null;
			if (order.Target.Type != TargetType.Invalid)
				cell = self.World.Map.CellContaining(order.Target.CenterPosition);

			if (!order.Queued)
				self.CancelActivity();
			else
			{
				for (var act = self.CurrentActivity; act != null; act = act.NextActivity)
					if (act is FindAndDeliverResources)
						act.Cancel(self, true);
			}

			self.QueueActivity(order.Queued, new AdjacentFindAndDeliver(self, cell));
			self.ShowTargetLines();
		}
	}

	sealed class AdjacentFindAndDeliver : Activity
	{
		readonly Harvester harv;
		readonly Mobile mobile;
		readonly ResourceClaimLayer claimLayer;
		readonly DockClientManager dockClient;
		CPos? orderedCell;
		bool searchFailed;

		public AdjacentFindAndDeliver(Actor self, CPos? orderedCell)
		{
			harv = self.Trait<Harvester>();
			mobile = self.Trait<Mobile>();
			claimLayer = self.World.WorldActor.Trait<ResourceClaimLayer>();
			dockClient = self.Trait<DockClientManager>();
			this.orderedCell = orderedCell;
		}

		public override bool Tick(Actor self)
		{
			if (IsCanceling || harv.IsTraitDisabled)
				return true;

			if (NextActivity != null && (harv.IsFull || searchFailed))
				return true;

			if (harv.IsFull || (!harv.IsEmpty && searchFailed))
			{
				if (harv.DockClientManager.ReservedHost != null)
					return false;

				QueueChild(new MoveToDock(self, dockLineColor: dockClient.DockLineColor));
				searchFailed = false;
				return false;
			}

			var origin = orderedCell ?? self.Location;
			var radius = orderedCell != null
				? harv.Info.SearchFromHarvesterRadius
				: harv.Info.SearchFromProcRadius;
			orderedCell = null;

			var cell = ClosestPile(self, origin, radius);
			if (cell == null)
			{
				searchFailed = true;
				QueueChild(new Wait(harv.Info.WaitDuration));
				return false;
			}

			searchFailed = false;
			QueueChild(new HarvestAdjacent(self, cell.Value));
			return false;
		}

		CPos? ClosestPile(Actor self, CPos origin, int radius)
		{
			CPos? best = null;
			var bestDist = int.MaxValue;
			var radiusSquared = radius * radius;
			foreach (var cell in self.World.Map.FindTilesInCircle(origin, radius, true))
			{
				if ((cell - origin).LengthSquared > radiusSquared)
					continue;

				if (!harv.CanHarvestCell(cell) || !claimLayer.CanClaimCell(self, cell))
					continue;

				if (StandCell(self, mobile, cell) == null)
					continue;

				var dist = (cell - self.Location).LengthSquared;
				if (dist >= bestDist)
					continue;

				best = cell;
				bestDist = dist;
			}

			return best;
		}

		internal static CPos? StandCell(Actor self, Mobile mobile, CPos pile)
		{
			CPos? best = null;
			var bestDist = int.MaxValue;
			foreach (var direction in CVec.Directions)
			{
				var cell = pile + direction;
				if (!self.World.Map.Contains(cell))
					continue;

				// Terrain only. A unit already standing there is handled by the move.
				if (!mobile.CanEnterCell(cell, check: BlockedByActor.None))
					continue;

				var dist = (cell - self.Location).LengthSquared;
				if (dist >= bestDist)
					continue;

				best = cell;
				bestDist = dist;
			}

			return best;
		}

		internal static bool Beside(CPos stand, CPos pile)
		{
			var d = stand - pile;
			var ax = Math.Abs(d.X);
			var ay = Math.Abs(d.Y);
			return ax <= 1 && ay <= 1 && (ax != 0 || ay != 0);
		}
	}

	sealed class HarvestAdjacent : Activity
	{
		readonly Harvester harv;
		readonly Mobile mobile;
		readonly IFacing facing;
		readonly IResourceLayer resourceLayer;
		readonly ResourceClaimLayer claimLayer;
		readonly CPos pile;
		bool triedMove;

		public HarvestAdjacent(Actor self, CPos pile)
		{
			harv = self.Trait<Harvester>();
			mobile = self.Trait<Mobile>();
			facing = self.Trait<IFacing>();
			resourceLayer = self.World.WorldActor.Trait<IResourceLayer>();
			claimLayer = self.World.WorldActor.Trait<ResourceClaimLayer>();
			this.pile = pile;
		}

		protected override void OnFirstRun(Actor self)
		{
			claimLayer.TryClaimCell(self, pile);
		}

		protected override void OnLastRun(Actor self)
		{
			claimLayer.RemoveClaim(self);
		}

		public override bool Tick(Actor self)
		{
			if (IsCanceling || harv.IsTraitDisabled || harv.IsFull || !harv.CanHarvestCell(pile))
				return true;

			if (!AdjacentFindAndDeliver.Beside(self.Location, pile))
			{
				if (triedMove)
					return true;

				var stand = AdjacentFindAndDeliver.StandCell(self, mobile, pile);
				if (stand == null)
					return true;

				triedMove = true;
				QueueChild(mobile.MoveTo(stand.Value));
				return false;
			}

			var desired = (self.World.Map.CenterOfCell(pile) - self.CenterPosition).Yaw;
			if (facing.Facing != desired)
			{
				QueueChild(new Turn(self, desired));
				return false;
			}

			var resource = resourceLayer.GetResource(pile);
			if (resource.Type == null || resourceLayer.RemoveResource(resource.Type, pile) == 0)
				return true;

			harv.AddResource(self, resource.Type);
			QueueChild(new Wait(harv.Info.BaleLoadDelay));
			return false;
		}

		public override IEnumerable<TargetLineNode> TargetLineNodes(Actor self)
		{
			yield return new TargetLineNode(Target.FromCell(self.World, pile), harv.Info.HarvestLineColor);
		}
	}
}
