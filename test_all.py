import json
import shutil
import struct
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from synthetic import build_flp  # noqa: E402

from cray_flp_analyzer import service
from cray_flp_analyzer.config import Settings
from cray_flp_analyzer.convert import assess_conversion
from cray_flp_analyzer.diagnose import diagnose
from cray_flp_analyzer.flp import parse_flp, serialize
from cray_flp_analyzer.flp.semantics import interpret
from cray_flp_analyzer.repair import SampleRemap, plan_repairs, repair_copy
from cray_flp_analyzer.report import build_report, to_markdown
from cray_flp_analyzer.session import sha256_file
from cray_flp_analyzer.validate import validate_pair


class Tmp(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp(prefix="crayáñ test "))   # ruta con espacios y acentos
        self.addCleanup(shutil.rmtree, self.d, True)

    def write(self, name, data):
        p = self.d / name
        p.write_bytes(data)
        return p


class TestReader(Tmp):
    def test_empty(self):
        d = parse_flp(b"")
        self.assertFalse(d.recognized)
        self.assertTrue(d.has("EMPTY_FILE"))

    def test_not_flp(self):
        d = parse_flp(b"RIFF" + b"\x00" * 100)
        self.assertFalse(d.recognized)
        self.assertTrue(d.has("BAD_MAGIC"))
        self.assertEqual(diagnose(d).primary_code, "not_flp")

    def test_incomplete_header(self):
        d = parse_flp(b"FLhd\x06\x00\x00\x00\x00\x00")
        self.assertTrue(d.has("HEADER_TRUNCATED"))
        self.assertFalse(d.structurally_ok)

    def test_valid_roundtrip_exact(self):
        data = build_flp(samples=[r"C:\Samples\kick.wav"], plugins=["Sytrus"])
        d = parse_flp(data)
        self.assertTrue(d.structurally_ok)
        self.assertEqual(serialize(d), data)
        info = interpret(d)
        self.assertEqual(info.version, (20, 8, 3, 2304))
        self.assertAlmostEqual(info.tempo, 140.0)
        self.assertEqual(info.texts["channel_name"], ["Kick", "Bass"])

    def test_old_version_ansi(self):
        data = build_flp(version="9.0.1", samples=["C:\\ñandú.wav"])
        info = interpret(parse_flp(data))
        self.assertEqual(info.text_encoding, "cp1252")
        self.assertEqual(info.samples[0].path, "C:\\ñandú.wav")

    def test_truncated(self):
        data = build_flp()
        cut = data[:-5]
        d = parse_flp(cut)
        self.assertTrue(d.truncated)
        self.assertTrue(d.has("DATA_TRUNCATED"))
        self.assertEqual(diagnose(d).primary_code, "truncated")

    def test_truncated_inside_event(self):
        data = build_flp()
        d = parse_flp(data[:-2])
        self.assertTrue(d.tail)
        self.assertTrue(d.has("EVENT_INCOMPLETE"))

    def test_unknown_events_preserved_and_reported(self):
        data = build_flp(unknown=[(250, b"\xde\xad\xbe\xef"), (100, b"\x01\x02")])
        d = parse_flp(data)
        info = interpret(d)
        self.assertIn(250, info.unknown_ids)
        self.assertEqual(serialize(d), data)
        diag = diagnose(d)
        self.assertTrue(any(i.code == "UNINTERPRETED_EVENTS" for i in diag.issues))

    def test_trailing_data(self):
        d = parse_flp(build_flp(trailing=b"XYZ"))
        self.assertTrue(d.has("TRAILING_DATA"))
        self.assertEqual(d.trailing, b"XYZ")


class TestDiagnose(Tmp):
    def test_missing_sample_posix(self):
        data = build_flp(samples=["/no/existe/nada_zz.wav"])
        diag = diagnose(parse_flp(data))
        self.assertTrue(any(i.code == "SAMPLE_MISSING" for i in diag.issues))

    def test_windows_path_unverifiable_here_not_missing_claim(self):
        if sys.platform == "win32":
            self.skipTest("solo Linux/macOS")
        diag = diagnose(parse_flp(build_flp(samples=[r"D:\x\a.wav"])))
        self.assertTrue(any(i.code == "SAMPLE_UNVERIFIABLE" for i in diag.issues))
        self.assertFalse(any(i.code == "SAMPLE_MISSING" for i in diag.issues))

    def test_plugins_are_hypothesis_not_culprit(self):
        diag = diagnose(parse_flp(build_flp(plugins=["Serum"])))
        row = diag.plugins[0]
        self.assertEqual(row["state"], "not_checked")
        self.assertEqual(diag.primary_confidence, "hypothesis")
        self.assertTrue(all(i.confidence != "confirmed" for i in diag.issues if i.code == "PLUGIN_LISTED"))

    def test_clean_does_not_claim_success(self):
        diag = diagnose(parse_flp(build_flp()), target_major=26)
        self.assertEqual(diag.primary_code, "clean")
        txt = " ".join(i.message for i in diag.issues)
        self.assertIn("NO garantiza", txt)

    def test_newer_than_target(self):
        diag = diagnose(parse_flp(build_flp(version="26.1.0.1")), target_major=21)
        self.assertEqual(diag.primary_code, "newer")
        a = assess_conversion(diag, 21)
        self.assertEqual(a.status, "downgrade_unsupported")
        self.assertFalse(a.can_generate_file)

    def test_older_not_converted(self):
        diag = diagnose(parse_flp(build_flp(version="12.5.1.165")), target_major=26)
        self.assertEqual(assess_conversion(diag, 26).status, "not_needed")

    def test_no_version(self):
        data = build_flp()
        d = parse_flp(data)
        # eliminar evento de versión
        from cray_flp_analyzer.flp.writer import serialize as ser
        d2 = parse_flp(ser(d, [e for e in d.events if e.id != 199]))
        diag = diagnose(d2, target_major=26)
        self.assertEqual(assess_conversion(diag, 26).status, "unknown_source")

    def test_sample_candidates(self):
        lib = self.d / "librería"
        lib.mkdir()
        (lib / "Kick.WAV").write_bytes(b"x")
        diag = diagnose(parse_flp(build_flp(samples=["/viejo/kick.wav"])), sample_dirs=[str(lib)])
        self.assertEqual(len(diag.samples[0]["candidates"]), 1)


class TestRepair(Tmp):
    def test_trim_and_original_untouched(self):
        orig = self.write("proyecto con espacios.flp", build_flp()[:-2])
        h = sha256_file(orig)
        res = repair_copy(orig, self.d / "salida", trim_tail=True)
        self.assertEqual(sha256_file(orig), h)
        self.assertTrue(res.original_untouched)
        out = Path(res.output)
        self.assertNotEqual(out, orig)
        self.assertTrue(parse_flp(out.read_bytes()).structurally_ok)
        val = validate_pair(orig.read_bytes(), out.read_bytes())
        self.assertEqual(val.A.status, "PASS")
        self.assertEqual(val.C.status, "PENDIENTE")
        self.assertTrue((self.d / "salida" / "cray_operaciones.jsonl").exists())

    def test_trim_refuses_when_not_truncated(self):
        orig = self.write("a.flp", build_flp())
        with self.assertRaises(ValueError):
            repair_copy(orig, self.d / "out", trim_tail=True)
        self.assertFalse((self.d / "out").exists() and list((self.d / "out").glob("*.flp")))

    def test_not_flp_refused(self):
        orig = self.write("x.flp", b"hola mundo no es flp")
        with self.assertRaises(ValueError):
            repair_copy(orig, self.d / "o", trim_tail=True)

    def test_remap_changes_only_sample_event(self):
        orig = self.write("m.flp", build_flp(samples=["/viejo/kick.wav"]))
        res = repair_copy(orig, self.d / "o", remaps=[SampleRemap(
            [e.index for e in parse_flp(orig.read_bytes()).events if e.id == 196][0], "/viejo/kick.wav", "/nuevo/kick.wav")])
        after = interpret(parse_flp(Path(res.output).read_bytes()))
        self.assertEqual(after.samples[0].path, "/nuevo/kick.wav")
        val = validate_pair(orig.read_bytes(), Path(res.output).read_bytes(), {196})
        self.assertEqual(val.A.status, "PASS")
        self.assertEqual(val.B.status, "PASS")

    def test_remap_wrong_old_path_refused(self):
        orig = self.write("m.flp", build_flp(samples=["/viejo/kick.wav"]))
        idx = [e.index for e in parse_flp(orig.read_bytes()).events if e.id == 196][0]
        with self.assertRaises(ValueError):
            repair_copy(orig, self.d / "o", remaps=[SampleRemap(idx, "/otra.wav", "/n.wav")])

    def test_unique_output_never_overwrites(self):
        orig = self.write("u.flp", build_flp()[:-2])
        a = repair_copy(orig, self.d / "o", trim_tail=True)
        b = repair_copy(orig, self.d / "o", trim_tail=True)
        self.assertNotEqual(a.output, b.output)


class TestValidation(Tmp):
    def test_detects_loss(self):
        full = build_flp()
        d = parse_flp(full)
        lossy = serialize(d, [e for e in d.events if e.id != 224])
        val = validate_pair(full, lossy)
        self.assertEqual(val.B.status, "FAIL")

    def test_never_declares_c_without_manual(self):
        full = build_flp()
        self.assertEqual(validate_pair(full, full).C.status, "PENDIENTE")


class TestReports(Tmp):
    def test_report_no_false_success(self):
        p = self.write("t.flp", build_flp()[:-2])
        an = service.analyze_file(p, Settings(target_mode="manual", target_major=26))
        rep = an.report()
        md = to_markdown(rep)
        self.assertEqual(rep["diagnostico"]["codigo"], "truncated")
        self.assertNotIn("garantiza que FL Studio abra", md.replace("NO garantiza que FL Studio abra", ""))
        json.dumps(rep, default=str)

    def test_repair_report_mentions_pending_level_c(self):
        p = self.write("t.flp", build_flp()[:-2])
        an = service.analyze_file(p, Settings(target_mode="manual", target_major=26))
        res, val = service.repair_file(an, self.d / "o", True, [])
        md = to_markdown(an.report(operation=res, validation=val))
        self.assertIn("PENDIENTE", md)


if __name__ == "__main__":
    unittest.main()
