using System.Linq;
using OpenRA.Mods.Common.Traits;
using OpenRA.Mods.Common.Widgets;
using OpenRA.Widgets;

namespace OpenRA.Mods.Example.Widgets.Logic
{
	/// <summary>
	/// Issues the deploy order for the current selection when the Deploy hotkey is pressed.
	/// The engine binds this hotkey through CommandBarLogic, which needs a full command bar
	/// with button artwork. This mod has no command bar, so the key is handled directly.
	/// </summary>
	public class DeployHotkeyLogic : ChromeLogic
	{
		[ObjectCreator.UseCtor]
		public DeployHotkeyLogic(Widget widget, World world, ModData modData)
		{
			var deployKey = modData.Hotkeys["Deploy"];
			var listener = widget.Get<LogicKeyListenerWidget>("DEPLOY_KEY_LISTENER");

			listener.AddHandler(e =>
			{
				if (e.Event != KeyInputEvent.Down || !deployKey.IsActivatedBy(e))
					return false;

				var queued = e.Modifiers.HasModifier(Modifiers.Shift);
				var orders = world.Selection.Actors
					.Where(a => a.Owner == world.LocalPlayer && a.IsInWorld && !a.IsDead)
					.SelectMany(a => a.TraitsImplementing<IIssueDeployOrder>()
						.Where(d => d.CanIssueDeployOrder(a, queued))
						.Select(d => d.IssueDeployOrder(a, queued)))
					.Where(o => o != null)
					.ToArray();

				if (orders.Length == 0)
					return false;

				foreach (var o in orders)
					world.IssueOrder(o);

				return true;
			});
		}
	}
}
