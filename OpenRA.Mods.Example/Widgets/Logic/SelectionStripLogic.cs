using System.Linq;
using OpenRA.Mods.Common.Traits;
using OpenRA.Mods.Common.Widgets;
using OpenRA.Mods.Example.Widgets;
using OpenRA.Traits;
using OpenRA.Widgets;

namespace OpenRA.Mods.Example.Widgets.Logic
{
	/// <summary>
	/// Fills the bottom-bar selection panel from the current world selection.
	/// A single unit uses the large chrome portrait; two or more use the
	/// wrapping strip of small portraits. Names and HP stay as labels.
	/// </summary>
	public class SelectionStripLogic : ChromeLogic
	{
		const int SingleTextX = 352;
		const int MultiTextX = 176;
		const int OptionsReserve = 176;

		[ObjectCreator.UseCtor]
		public SelectionStripLogic(Widget widget, World world)
		{
			var nameLabel = widget.Get<LabelWidget>("SELECTION_NAME");
			var detailLabel = widget.Get<LabelWidget>("SELECTION_DETAIL");
			var emptyLabel = widget.Get<LabelWidget>("SELECTION_EMPTY");
			var portrait = widget.Get<ImageWidget>("SELECTION_PORTRAIT");
			var portraitBg = widget.Get("PORTRAIT_BG");
			var text = widget.Get("SELECTION_TEXT");
			var strip = widget.Get<SelectionPortraitsWidget>("SELECTION_STRIP");

			var name = "";
			var detail = "";
			var empty = true;
			var portraitName = "tank";
			var showLargePortrait = false;
			var showLargeFrame = false;
			var showStrip = false;

			nameLabel.GetText = () => name;
			detailLabel.GetText = () => detail;
			nameLabel.IsVisible = () => !empty;
			detailLabel.IsVisible = () => !empty && !showStrip;
			emptyLabel.IsVisible = () => empty;
			portrait.GetImageName = () => portraitName;
			portrait.IsVisible = () => showLargePortrait;
			portraitBg.IsVisible = () => showLargeFrame;
			strip.IsVisible = () => showStrip;

			var ticker = widget.Get<LogicTickerWidget>("SELECTION_TICKER");
			ticker.OnTick = () =>
			{
				var actors = world.Selection.Actors
					.Where(a => a.IsInWorld && !a.IsDead)
					.ToArray();

				empty = actors.Length == 0;
				showLargePortrait = false;
				showLargeFrame = false;
				showStrip = false;

				if (empty)
				{
					name = "";
					detail = "";
					LayoutText(text, SingleTextX);
					return;
				}

				if (actors.Length == 1)
				{
					var a = actors[0];
					name = ActorName(a);
					var health = a.TraitOrDefault<IHealth>();
					detail = health == null || health.MaxHP == 0
						? ""
						: $"HP {100 * health.DisplayHP / health.MaxHP}%";
					showLargeFrame = true;
					showLargePortrait = SelectionPortraitsWidget.TryGetPortrait(a.Info.Name, out var img);
					if (showLargePortrait)
						portraitName = img;
					LayoutText(text, SingleTextX);
					return;
				}

				name = $"{actors.Length} selected";
				detail = "";
				showStrip = actors.Any(a => SelectionPortraitsWidget.TryGetPortrait(a.Info.Name, out _));
				LayoutText(text, MultiTextX);
			};
		}

		static void LayoutText(Widget text, int x)
		{
			var width = System.Math.Max(0, text.Parent.Bounds.Width - x - OptionsReserve);
			text.Bounds = new WidgetBounds(x, text.Bounds.Y, width, text.Bounds.Height);
		}

		static string ActorName(Actor a)
		{
			var tooltip = a.TraitsImplementing<Tooltip>().FirstOrDefault(t => !t.IsTraitDisabled);
			if (tooltip == null)
				return a.Info.Name;

			return FluentProvider.GetMessage(tooltip.Info.Name);
		}
	}
}
