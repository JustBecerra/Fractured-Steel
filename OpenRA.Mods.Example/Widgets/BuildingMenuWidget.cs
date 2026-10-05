using System;
using System.Collections.Generic;
using System.Linq;
using OpenRA.Graphics;
using OpenRA.Mods.Common.Orders;
using OpenRA.Mods.Common.Traits;
using OpenRA.Mods.Common.Widgets;
using OpenRA.Mods.Example.Widgets.Logic;
using OpenRA.Primitives;
using OpenRA.Widgets;

namespace OpenRA.Mods.Example.Widgets
{
	/// <summary>
	/// Named squares for structures or units, in tech-tree order. A square is
	/// gray until its prerequisites are met. Buildings and Units tabs share
	/// the panel. No production icons.
	/// </summary>
	public class BuildingMenuWidget : Widget
	{
		public string Actors = "";
		public string Units = "";

		readonly World world;
		readonly WorldRenderer worldRenderer;
		readonly SpriteFont font;
		readonly List<Slot> slots = new();
		readonly Lazy<TooltipContainerWidget> tooltipContainer;

		// Buildings is the tab shown when the panel first appears.
		bool showingUnits;
		Rectangle buildingsTab;
		Rectangle unitsTab;
		string hoveredId;
		int tooltipToken;

		[ObjectCreator.UseCtor]
		public BuildingMenuWidget(World world, WorldRenderer worldRenderer)
		{
			this.world = world;
			this.worldRenderer = worldRenderer;
			font = Game.Renderer.Fonts["Bold"];
			tooltipContainer = Exts.Lazy(() => Ui.Root.Get<TooltipContainerWidget>("TOOLTIP_CONTAINER"));
		}

		protected BuildingMenuWidget(BuildingMenuWidget other)
			: base(other)
		{
			world = other.world;
			worldRenderer = other.worldRenderer;
			font = other.font;
			Actors = other.Actors;
			Units = other.Units;
			showingUnits = other.showingUnits;
			tooltipContainer = Exts.Lazy(() => Ui.Root.Get<TooltipContainerWidget>("TOOLTIP_CONTAINER"));
		}

		public override Widget Clone() { return new BuildingMenuWidget(this); }

		public override void Tick()
		{
			var hit = slots.FirstOrDefault(s => s.Bounds.Contains(Viewport.LastMousePos));
			var id = hit?.Id;
			if (id == hoveredId)
				return;

			var previous = hoveredId;
			hoveredId = id;
			if (previous != null && tooltipContainer.IsValueCreated)
				tooltipContainer.Value.RemoveTooltip(tooltipToken);

			if (hit == null)
				return;

			var cost = hit.Queue != null
				? hit.Queue.GetProductionCost(hit.Info)
				: hit.Info.TraitInfoOrDefault<ValuedInfo>()?.Cost ?? 0;
			var text = DisplayName(hit.Info) + "\n" + cost + " alloy";
			tooltipToken = tooltipContainer.Value.SetTooltip("SIMPLE_TOOLTIP", new WidgetArgs
			{
				{ "getText", (Func<string>)(() => text) },
			});
		}

		public override void Draw()
		{
			slots.Clear();
			buildingsTab = Rectangle.Empty;
			unitsTab = Rectangle.Empty;

			var player = world.LocalPlayer;
			if (player == null)
				return;

			var content = LayoutTabs();
			var list = showingUnits ? Units : Actors;
			if (string.IsNullOrWhiteSpace(list) || content.Height <= 0)
				return;

			var names = list.Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);
			if (names.Length == 0)
				return;

			var entries = new List<(string Id, ActorInfo Info)>();
			foreach (var id in names)
				if (world.Map.Rules.Actors.TryGetValue(id, out var info))
					entries.Add((id, info));

			if (entries.Count == 0)
				return;

			// Half-height squares in two rows, packed against the left edge,
			// in the space under the tabs.
			const int margin = 8;
			const int rows = 2;
			var cols = (entries.Count + rows - 1) / rows;
			var size = content.Height / 2;
			var vGap = rows * size + (rows - 1) * margin <= content.Height ? margin : 0;
			var gridW = cols * size + Math.Max(0, cols - 1) * margin;
			var gridH = rows * size + (rows - 1) * vGap;
			if (gridW > content.Width)
			{
				size = Math.Max(40, (content.Width - Math.Max(0, cols - 1) * margin) / cols);
				vGap = rows * size + (rows - 1) * margin <= content.Height ? margin : 0;
				gridW = cols * size + Math.Max(0, cols - 1) * margin;
				gridH = rows * size + (rows - 1) * vGap;
			}

			var tech = player.PlayerActor.TraitOrDefault<TechTree>();
			var alloy = ResourceCountersLogic.Alloy(world);
			var x0 = content.X;
			var y0 = content.Y + Math.Max(0, (content.Height - gridH) / 2);

			for (var i = 0; i < entries.Count; i++)
			{
				var (id, info) = entries[i];
				var buildable = info.TraitInfoOrDefault<BuildableInfo>();
				var queue = QueueFor(player, buildable);
				var unlocked = buildable != null && queue != null && queue.Enabled
					&& (tech == null || tech.HasPrerequisites(buildable.Prerequisites));
				var queued = unlocked && queue.AllQueued().Any(item => item.Item == id);
				// A new build needs the full cost in alloy. One already paid for
				// stays usable so it can be paused, cancelled, or placed.
				var open = unlocked && (queued || queue.GetProductionCost(info) <= alloy);
				var ready = open && queue.AllQueued().Any(item => item.Item == id && item.Done);
				var col = i % cols;
				var row = i / cols;
				var bounds = new Rectangle(
					x0 + col * (size + margin),
					y0 + row * (size + vGap),
					size,
					size);
				slots.Add(new Slot(id, info, queue, bounds, open, ready));

				var fill = open ? Color.FromArgb(78, 84, 76) : Color.FromArgb(42, 42, 42);
				var border = ready ? Color.FromArgb(220, 190, 80)
					: open ? Color.FromArgb(186, 192, 176)
					: Color.FromArgb(72, 72, 72);
				var text = open ? Color.White : Color.FromArgb(128, 128, 128);

				WidgetUtils.FillRectWithColor(bounds, fill);
				DrawProgress(queue, id, bounds);
				WidgetUtils.FillRectWithColor(new Rectangle(bounds.Left, bounds.Top, bounds.Width, 2), border);
				WidgetUtils.FillRectWithColor(new Rectangle(bounds.Left, bounds.Bottom - 2, bounds.Width, 2), border);
				WidgetUtils.FillRectWithColor(new Rectangle(bounds.Left, bounds.Top, 2, bounds.Height), border);
				WidgetUtils.FillRectWithColor(new Rectangle(bounds.Right - 2, bounds.Top, 2, bounds.Height), border);

				DrawName(DisplayName(info), bounds, text);
			}
		}

		public override bool HandleMouseInput(MouseInput mi)
		{
			if (mi.Event != MouseInputEvent.Down)
				return false;

			if (mi.Button == MouseButton.Right)
			{
				HandleRightClick(mi);
				return true;
			}

			if (mi.Button != MouseButton.Left)
				return false;

			if (buildingsTab.Contains(mi.Location))
			{
				showingUnits = false;
				return true;
			}

			if (unitsTab.Contains(mi.Location))
			{
				showingUnits = true;
				return true;
			}

			var hit = slots.FirstOrDefault(s => s.Bounds.Contains(mi.Location));
			if (hit == null || !hit.Open || hit.Queue == null)
				return true;

			var item = hit.Queue.AllQueued().FirstOrDefault(i => i.Item == hit.Id);
			if (item != null && item.Paused)
			{
				world.IssueOrder(Order.PauseProduction(hit.Queue.Actor, hit.Id, false));
				return true;
			}

			if (item != null && item.Done && hit.Info.HasTraitInfo<BuildingInfo>())
			{
				world.OrderGenerator = new PlaceBuildingOrderGenerator(hit.Queue, hit.Id, worldRenderer);
				return true;
			}

			if (!hit.Queue.CanQueue(hit.Info, out _, out _))
				return true;

			world.IssueOrder(Order.StartProduction(hit.Queue.Actor, hit.Id, 1));
			return true;
		}

		// Right-click holds a build. Left-click continues it. Right-click again cancels it.
		void HandleRightClick(MouseInput mi)
		{
			var hit = slots.FirstOrDefault(s => s.Bounds.Contains(mi.Location));
			if (hit == null || hit.Queue == null)
				return;

			var item = hit.Queue.AllQueued().FirstOrDefault(i => i.Item == hit.Id);
			if (item == null)
				return;

			if (item.Paused || item.Done)
			{
				if (item.Done && hit.Info.HasTraitInfo<BuildingInfo>())
					world.CancelInputMode();

				world.IssueOrder(Order.CancelProduction(hit.Queue.Actor, hit.Id, 1));
				return;
			}

			world.IssueOrder(Order.PauseProduction(hit.Queue.Actor, hit.Id, true));
		}

		Rectangle LayoutTabs()
		{
			var origin = RenderOrigin;
			if (string.IsNullOrWhiteSpace(Units))
				return new Rectangle(origin.X, origin.Y, Bounds.Width, Bounds.Height);

			const int tabHeight = 28;
			const int gap = 8;
			var tabWidth = (Bounds.Width - gap) / 2;
			buildingsTab = new Rectangle(origin.X, origin.Y, tabWidth, tabHeight);
			unitsTab = new Rectangle(origin.X + tabWidth + gap, origin.Y, Bounds.Width - tabWidth - gap, tabHeight);
			DrawTab(buildingsTab, "Buildings", !showingUnits);
			DrawTab(unitsTab, "Units", showingUnits);
			return new Rectangle(origin.X, origin.Y + tabHeight + gap, Bounds.Width, Math.Max(0, Bounds.Height - tabHeight - gap));
		}

		void DrawTab(Rectangle bounds, string label, bool active)
		{
			var fill = active ? Color.FromArgb(78, 84, 76) : Color.FromArgb(42, 42, 42);
			var border = active ? Color.FromArgb(186, 192, 176) : Color.FromArgb(72, 72, 72);
			var text = active ? Color.White : Color.FromArgb(128, 128, 128);
			WidgetUtils.FillRectWithColor(bounds, fill);
			WidgetUtils.FillRectWithColor(new Rectangle(bounds.Left, bounds.Top, bounds.Width, 2), border);
			WidgetUtils.FillRectWithColor(new Rectangle(bounds.Left, bounds.Bottom - 2, bounds.Width, 2), border);
			WidgetUtils.FillRectWithColor(new Rectangle(bounds.Left, bounds.Top, 2, bounds.Height), border);
			WidgetUtils.FillRectWithColor(new Rectangle(bounds.Right - 2, bounds.Top, 2, bounds.Height), border);
			DrawName(label, bounds, text);
		}

		static void DrawProgress(ProductionQueue queue, string id, Rectangle bounds)
		{
			var item = queue?.AllQueued().FirstOrDefault(i => i.Item == id);
			if (item == null || item.TotalTime <= 0)
				return;

			var progress = item.Done ? 1f : (item.TotalTime - item.RemainingTime) / (float)item.TotalTime;
			var height = (int)(bounds.Height * progress);
			if (height <= 0)
				return;

			// Held builds keep their fill, in a duller colour so the pause is visible.
			var color = item.Paused ? Color.FromArgb(110, 140, 160) : Color.FromArgb(230, 190, 40);
			WidgetUtils.FillRectWithColor(
				new Rectangle(bounds.Left, bounds.Bottom - height, bounds.Width, height),
				color);
		}

		void DrawName(string name, Rectangle bounds, Color color)
		{
			var lines = Wrap(name, bounds.Width - 12);
			var lineHeight = font.Measure("A").Y;
			var block = lines.Count * lineHeight;
			var y = bounds.Top + Math.Max(4, (bounds.Height - block) / 2);
			foreach (var line in lines)
			{
				var width = font.Measure(line).X;
				var pos = new float2(bounds.Left + (bounds.Width - width) / 2, y);
				font.DrawTextWithContrast(line, pos, color, Color.Black, 1);
				y += lineHeight;
			}
		}

		List<string> Wrap(string name, int maxWidth)
		{
			var words = name.Split(' ', StringSplitOptions.RemoveEmptyEntries);
			var lines = new List<string>();
			var current = "";
			foreach (var word in words)
			{
				var next = current.Length == 0 ? word : current + " " + word;
				if (font.Measure(next).X <= maxWidth)
					current = next;
				else
				{
					if (current.Length > 0)
						lines.Add(current);
					current = word;
				}
			}

			if (current.Length > 0)
				lines.Add(current);

			return lines;
		}

		static string DisplayName(ActorInfo info)
		{
			var tooltip = info.TraitInfoOrDefault<TooltipInfo>();
			if (tooltip == null || string.IsNullOrEmpty(tooltip.Name))
				return info.Name;

			return FluentProvider.GetMessage(tooltip.Name);
		}

		ProductionQueue QueueFor(Player player, BuildableInfo buildable)
		{
			if (buildable == null)
				return null;

			return player.PlayerActor.TraitsImplementing<ProductionQueue>()
				.FirstOrDefault(q => buildable.Queue.Contains(q.Info.Type));
		}

		sealed class Slot
		{
			public readonly string Id;
			public readonly ActorInfo Info;
			public readonly ProductionQueue Queue;
			public readonly Rectangle Bounds;
			public readonly bool Open;
			public readonly bool Ready;

			public Slot(string id, ActorInfo info, ProductionQueue queue, Rectangle bounds, bool open, bool ready)
			{
				Id = id;
				Info = info;
				Queue = queue;
				Bounds = bounds;
				Open = open;
				Ready = ready;
			}
		}
	}
}
