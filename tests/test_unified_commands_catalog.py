from __future__ import annotations

from services.unified_commands_catalog import ALLOWED_FLAGS, COMMAND_GROUPS


def _catalog_flags() -> list[str]:
    return [item["flag"] for group in COMMAND_GROUPS for item in group["items"]]


def test_unified_20_command_catalog_contains_current_cli_flags() -> None:
    flags = _catalog_flags()

    expected_unified_20_flags = {
        "-i",
        "-io",
        "-toff",
        "-k",
        "-g",
        "-gips",
        "-uk",
        "-ug",
        "-ux",
        "-um",
        "-ugc",
        "-dgc",
        "-kb",
        "-kbr",
        "-xb",
        "-xbr",
        "-mb",
        "-mbr",
        "-remove",
        "-dgs",
        "-dgi",
        "-dgips",
        "-dx",
        "-dm",
        "-dk",
        "-ap",
        "-dp",
        "-cp",
        "-ape",
        "-dpe",
        "-cpe",
        "-start",
        "-stop",
        "-restart",
        "-status",
        "-tp",
        "-auto",
        "-d",
        "-fd",
        "-diag",
        "-channel",
        "-xray",
        "-mihomo",
        "-ipv6",
        "-dns",
        "-pr",
        "-extmsg",
        "-cbk",
        "-aghfix",
        "-about",
        "-ad",
        "-af",
        "-v",
    }

    assert expected_unified_20_flags.issubset(set(flags))
    assert "-tpx" not in flags
    assert "-cb" not in flags
    assert "-cbr" not in flags
    assert ALLOWED_FLAGS.issuperset(expected_unified_20_flags)


def test_unified_command_catalog_has_no_duplicate_flags() -> None:
    flags = _catalog_flags()

    assert len(flags) == len(set(flags))
