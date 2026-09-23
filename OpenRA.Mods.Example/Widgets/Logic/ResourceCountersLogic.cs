using OpenRA.Mods.Common.Widgets;
using OpenRA.Widgets;

namespace OpenRA.Mods.Example.Widgets.Logic
{
	/// <summary>
	/// Starting readouts for the right-hand resource panel.
	/// Power and personnel are caps; alloy is the opening stockpile.
	/// </summary>
	public class ResourceCountersLogic : ChromeLogic
	{
		[ObjectCreator.UseCtor]
		public ResourceCountersLogic(Widget widget)
		{
			widget.Get<LabelWidget>("POWER_COUNT").GetText = () => "0/16";
			widget.Get<LabelWidget>("ALLOY_COUNT").GetText = () => "200";
			widget.Get<LabelWidget>("CREW_COUNT").GetText = () => "0/20";
		}
	}
}
