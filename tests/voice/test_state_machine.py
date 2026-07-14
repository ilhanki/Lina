from lina.voice.models import VoiceState
from lina.voice.state_machine import VoiceStateMachine


def test_hands_free_state_machine_happy_path():
    machine = VoiceStateMachine(VoiceState.IDLE)
    states = []
    machine.subscribe(states.append)
    path = [
        VoiceState.WAKE_LISTENING,
        VoiceState.WAKE_DETECTED,
        VoiceState.COMMAND_LISTENING,
        VoiceState.TRANSCRIBING,
        VoiceState.THINKING,
        VoiceState.SPEAKING,
        VoiceState.COOLDOWN,
        VoiceState.WAKE_LISTENING,
    ]
    assert all(machine.transition(state) for state in path)
    assert states == path


def test_invalid_transition_is_ignored_without_crash():
    machine = VoiceStateMachine(VoiceState.WAKE_LISTENING)
    assert not machine.transition(VoiceState.SPEAKING)
    assert machine.state is VoiceState.WAKE_LISTENING


def test_force_transition_supports_safe_recovery():
    machine = VoiceStateMachine(VoiceState.DISABLED)
    assert machine.transition(VoiceState.ERROR, force=True)
    assert machine.transition(VoiceState.DISABLED)
