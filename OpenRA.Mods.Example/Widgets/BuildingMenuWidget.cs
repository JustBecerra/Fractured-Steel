using System;
using System.Collections.Generic;
using System.Linq;
using OpenRA.Graphics;
using OpenRA.Mods.Common.Orders;
using OpenRA.Mods.Common.Traits;
using OpenRA.Mods.Common.Widgets;
using OpenRA.Primitives;
using OpenRA.Widgets;

namespace OpenRA.Mods.Example.Widgets
{
	/// <summary>
	/// Named squares for every structure, in tech-tree order. A square is gray
	/// until its prerequisites are met. No production icons.
	/// </summary>
	public class BuildingMenuWidget : Widget
	{
		public string Actors = "";

		readonly World world;
		readonly WorldRenderer worldRenderer;
		readonly SpriteFont font;
		readonly List<Slot> slots = new();

		[ObjectCreator.UseCtor]
		public BuildingMenuWidget(World world, WorldRenderer worldRenderer)
		{
			this.world = world;
			this.worldRenderer = worldRenderer;
			font = Game.Renderer.Fonts["Bold"];
		}

		protected BuildingMenuWidget(BuildingMenuWidget other)
			: base(other)
		{
			world = other.world;
			worldRenderer = other.worldRenderer;
			font = other.font;
			Actors = other.Actors;
		}

		public override Widget Clone() { return new BuildingMenuWidget(this); }

		public override void Draw()
		{
			slots.Clear();
			var player = world.LocalPlayer;
			if (player == null || string.IsNullOrWhiteSpace(Actors))
				return;

			var names = Actors.Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries);
			if (names.Length == 0)
				return;

			var entries = new List<(string Id, ActorInfo Info)>();
			foreach (var id in names)
				if (world.Map.Rules.Actors.TryGetValue(id, out var info))
					entries.Add((id, info));

			if (entries.Count == 0)
				return;

			// Half-height squares in two rows, packed against the left edge.
			// The chrome widget sits immediately after the radar strand.
			const int margin = 8;
			const int rows = 2;
			var cols = (entries.Count + rows - 1) / rows;
			var size = Bounds.Height / 2;
			var vGap = rows * size + (rows - 1) * margin <= Bounds.Height ? margin : 0;
			var gridW = cols * size + Math.Max(0, cols - 1) * margin;
			var gridH = rows * size + (rows - 1) * vGap;
			if (gridW > Bounds.Width)
			{
				size = Math.Max(40, (Bounds.Width - Math.Max(0, cols - 1) * margin) / cols);
				vGap = rows * size + (rows - 1) * margin <= Bounds.Height ? margin : 0;
				gridW = cols * size + Math.Max(0, cols - 1) * margin;
				gridH = rows * size + (rows - 1) * vGap;
			}

			var tech = player.PlayerActor.TraitOrDefault<TechTree>();
			var origin = RenderOrigin;
			var x0 = origin.X;
			var y0 = origin.Y + Math.Max(0, (Bounds.Height - gridH) / 2);

			for (var i = 0; i < entries.Count; i++)
			{
				var (id, info) = entries[i];
				var buildable = info.TraitInfoOrDefault<BuildableInfo>();
				var queue = QueueFor(player, buildable);
				var open = buildable != null && queue != null && queue.Enabled
					&& (tech == null || tech.HasPrerequisites(buildable.Prerequisites));
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
			if (mi.Event != MouseInputEvent.Down || mi.Button != MouseButton.Left)
				return false;

			var hit = slots.FirstOrDefault(s => s.Bounds.Contains(mi.Location));
			if (hit == null || !hit.Open || hit.Queue == null)
				return true;

			var done = hit.Queue.AllQueued().FirstOrDefault(i => i.Item == hit.Id && i.Done);
			if (done != null && hit.Info.HasTraitInfo<BuildingInfo>())
			{
				world.OrderGenerator = new PlaceBuildingOrderGenerator(hit.Queue, hit.Id, worldRenderer);
				return true;
			}

			if (!hit.Queue.CanQueue(hit.Info, out _, out _))
				return true;

			world.IssueOrder(Order.StartProduction(hit.Queue.Actor, hit.Id, 1));
			return true;
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

			WidgetUtils.FillRectWithColor(
				new Rectangle(bounds.Left, bounds.Bottom - height, bounds.Width, height),
				Color.FromArgb(230, 190, 40));
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
