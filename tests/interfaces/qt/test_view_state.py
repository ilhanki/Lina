from lina.interfaces.qt.view_state import ApplicationViewState, ResponsiveMode
from lina.ui.design import design_tokens


def test_application_view_state_resolves_large_medium_and_compact_modes():
    layout = design_tokens("dark").layout
    state = ApplicationViewState(right_panel_visible=True)
    assert state.for_width(1600, layout).responsive_mode is ResponsiveMode.LARGE
    medium = state.for_width(1100, layout)
    assert medium.responsive_mode is ResponsiveMode.MEDIUM
    assert medium.right_panel_visible is False
    compact = state.for_width(800, layout)
    assert compact.responsive_mode is ResponsiveMode.COMPACT
    assert compact.sidebar_collapsed is True
