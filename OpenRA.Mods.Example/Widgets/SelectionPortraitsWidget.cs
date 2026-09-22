using System.Collections.Generic;
using System.Linq;
using OpenRA.Graphics;
using OpenRA.Mods.Common.Widgets;
using OpenRA.Primitives;
using OpenRA.Widgets;

namespace OpenRA.Mods.Example.Widgets
{
	/// <summary>
	/// StarCraft-style selection grid: one small chrome portrait per selected
	/// actor, wrapping left-to-right. Hidden when the selection is empty or a
	/// single unit (the large ImageWidget covers that case).
	/// </summary>
	public class SelectionPortraitsWidget : Widget
	{
		public int IconWidth = 56;
		public int IconHeight = 56;
		public int IconSpacing = 6;
		public string ImageCollection = "portraits";

		// Chrome YAML only loads scalar fields (WidgetLoader.LoadField uses
		// node.Value.Value), so a nested ActorPortraits map never arrives.
		public static readonly Dictionary<string, string> ByActor = new()
		{
			["fs_tank"] = "tank",
			["fs_paladin"] = "tank",
			["fs_frame"] = "tank",
			["fs_sentinel"] = "eship",
			["fs_hq"] = "hq",
			["fs_academy"] = "academy"
		};

		readonly World world;
		readonly List<(Rectangle Bounds, Actor Actor)> icons = new();
		readonly Dictionary<string, Sprite> sprites = new();

		[ObjectCreator.UseCtor]
		public SelectionPortraitsWidget(World world)
		{
			this.world = world;
		}

		protected SelectionPortraitsWidget(SelectionPortraitsWidget other)
			: base(other)
		{
			world = other.world;
			IconWidth = other.IconWidth;
			IconHeight = other.IconHeight;
			IconSpacing = other.IconSpacing;
			ImageCollection = other.ImageCollection;
		}

		public override Widget Clone() { return new SelectionPortraitsWidget(this); }

		public static bool TryGetPortrait(string actorName, out string image)
		{
			return ByActor.TryGetValue(actorName, out image);
		}

		public override void Draw()
		{
			icons.Clear();

			var actors = world.Selection.Actors
				.Where(a => a.IsInWorld && !a.IsDead)
				.ToArray();

			if (actors.Length <= 1)
				return;

			var origin = RenderOrigin;
			var cols = System.Math.Max(1, (Bounds.Width + IconSpacing) / (IconWidth + IconSpacing));
			var rows = System.Math.Max(1, (Bounds.Height + IconSpacing) / (IconHeight + IconSpacing));
			var max = cols * rows;
			var slot = new Size(IconWidth, IconHeight);
			var shown = 0;

			Game.Renderer.EnableAntialiasingFilter();
			foreach (var a in actors)
			{
				if (shown >= max)
					break;

				if (!ByActor.TryGetValue(a.Info.Name, out var imageName))
					continue;

				if (!sprites.TryGetValue(imageName, out var sprite))
				{
					sprite = ChromeProvider.GetImage(ImageCollection, imageName);
					sprites[imageName] = sprite;
				}

				var col = shown % cols;
				var row = shown / cols;
				var x = origin.X + col * (IconWidth + IconSpacing);
				var y = origin.Y + row * (IconHeight + IconSpacing);
				var bounds = new Rectangle(x, y, IconWidth, IconHeight);

				WidgetUtils.FillRectWithColor(bounds, Color.FromArgb(180, 8, 8, 10));
				WidgetUtils.DrawSprite(sprite, new float2(x, y), slot);
				icons.Add((bounds, a));
				shown++;
			}

			Game.Renderer.DisableAntialiasingFilter();
		}

		public override bool HandleMouseInput(MouseInput mi)
		{
			if (mi.Event != MouseInputEvent.Down || mi.Button != MouseButton.Left)
				return false;

			foreach (var icon in icons)
			{
				if (!icon.Bounds.Contains(mi.Location))
					continue;

				world.Selection.Combine(world, new[] { icon.Actor }, false, true);
				return true;
			}

			return false;
		}
	}
}
