from dataclasses import replace
import pytest
from usbguard_control.demo import DemoBackend, FIXTURES
from usbguard_control.domain import display_text, parse_device, validate_action


def test_concrete_rules_preserve_quoted_values_and_composite_interfaces():
    d = parse_device(3, 'allow id 1234:abcd name "USB { Keyboard }" serial "two words" hash "abc=" with-interface { 08:06:50 03:01:01 }')
    assert d.name == "USB { Keyboard }"
    assert d.serial == "two words"
    assert d.sensitive
    assert not d.as_dict()["canBlock"]


@pytest.mark.parametrize("index", [1, 2, 4])
def test_input_devices_bluetooth_and_hubs_cannot_be_blocked(index):
    d = parse_device(*FIXTURES[index])
    with pytest.raises(ValueError, match="seguridad"):
        validate_action(d, d, "block")


def test_unknown_interfaces_fail_closed():
    d = parse_device(3, 'allow id 1234:abcd name "Unknown" hash "abc"')
    with pytest.raises(ValueError): validate_action(d, d, "block")


def test_stale_device_id_and_missing_fingerprint_are_rejected():
    original = parse_device(*FIXTURES[0])
    for altered in (replace(original, digest="other"), replace(original, port="2-1"), replace(original, id=99)):
        with pytest.raises(ValueError, match="cambió"):
            validate_action(altered, original, "allow")
    no_hash = replace(original, digest="")
    with pytest.raises(ValueError, match="identidad"):
        validate_action(no_hash, no_hash, "allow")


@pytest.mark.parametrize("rule", ['invalid id 0000:0000', 'allow name "unfinished', 'allow with-interface { 08:06:50', 'allow with-interface nonsense'])
def test_malformed_device_rules_fail(rule):
    with pytest.raises(ValueError): parse_device(1, rule)


def test_untrusted_display_strings_are_plain_and_bounded():
    assert display_text("abc\u202edesktop\n\x00") == "abcdesktop"
    assert len(display_text("x" * 500)) == 160


def test_temporary_decision_does_not_survive_reconnect():
    backend = DemoBackend()
    device = backend.snapshot()["devices"][0]
    backend.apply(device, "allow", False, "demo")
    backend.toggle_connection()
    backend.toggle_connection()
    assert backend.snapshot()["devices"][0].target == "block"


def test_permanent_decision_survives_demo_reconnect():
    backend = DemoBackend()
    device = backend.snapshot()["devices"][0]
    assert backend.apply(device, "allow", True, "demo") > 0
    backend.toggle_connection()
    backend.toggle_connection()
    assert backend.snapshot()["devices"][0].target == "allow"
