from agency_common.decide import Choice, DecisionLog, RulesBackend, decide
from agency_common.decisions_cli import main

Q = Choice("colour", {"red": "", "blue": ""})


def make(tmp_path, probs, name="research.x"):
    log = DecisionLog(tmp_path)
    return decide({"n": 1}, [Q], RulesBackend({"colour": lambda s: probs}), log=log, name=name)["colour"]


def run(tmp_path, *argv, replies=()):
    lines, feed = [], iter(replies)
    code = main(["--workspace", str(tmp_path), *argv], ask=lambda prompt: next(feed), out=lines.append)
    return code, "\n".join(lines)


def test_list_filters_by_route_name_and_pending(tmp_path):
    sure = make(tmp_path, "red")
    unsure = make(tmp_path, {"red": 0.55, "blue": 0.45}, name="housekeeping.triage")
    DecisionLog(tmp_path).record_human(sure.decision_id, "red")

    _, everything = run(tmp_path, "list")
    assert sure.decision_id in everything and unsure.decision_id in everything
    _, pending = run(tmp_path, "list", "--pending")
    assert sure.decision_id not in pending and unsure.decision_id in pending
    _, only_house = run(tmp_path, "list", "--name", "housekeeping")
    assert unsure.decision_id in only_house and sure.decision_id not in only_house
    _, escalated = run(tmp_path, "list", "--route", "escalate")
    assert unsure.decision_id in escalated and sure.decision_id not in escalated


def test_empty_log_is_reported_not_an_error(tmp_path):
    assert run(tmp_path, "list") == (0, "No decisions recorded.")
    assert "No reviewed decisions" in run(tmp_path, "calibration")[1]


def test_verdict_accepts_unique_prefix_and_rejects_bad_answers(tmp_path):
    d = make(tmp_path, "red")
    code, text = run(tmp_path, "verdict", d.decision_id[:6], "blue", "--note", "wrong")
    assert code == 0 and "model said 'red'" in text
    assert DecisionLog(tmp_path).decisions()[0]["human"] == "blue"

    code, text = run(tmp_path, "verdict", d.decision_id, "green")
    assert code == 1 and "not an answer" in text
    assert run(tmp_path, "verdict", "zzzz", "red")[0] == 1


def test_ambiguous_prefix_is_an_error(tmp_path):
    make(tmp_path, "red")
    make(tmp_path, "red")
    code, text = run(tmp_path, "show", "")
    assert code == 1 and "more than one" in text


def test_review_agrees_overrides_skips_and_hides_confident_by_default(tmp_path):
    confident = make(tmp_path, "red")
    agree = make(tmp_path, {"red": 0.55, "blue": 0.45})
    override = make(tmp_path, {"red": 0.6, "blue": 0.4})
    skipped = make(tmp_path, {"red": 0.52, "blue": 0.48})

    # newest first: skipped, override, agree
    code, text = run(tmp_path, "review", replies=["s", "blue", "model was off", ""])
    verdicts = {d["decision_id"]: d["human"] for d in DecisionLog(tmp_path).decisions()}
    assert code == 0 and "Recorded 2 verdict(s)" in text
    assert verdicts == {
        confident.decision_id: None, agree.decision_id: "red", override.decision_id: "blue", skipped.decision_id: None,
    }


def test_review_quit_and_invalid_answer(tmp_path):
    make(tmp_path, {"red": 0.55, "blue": 0.45})
    make(tmp_path, {"red": 0.55, "blue": 0.45})
    _, text = run(tmp_path, "review", replies=["purple", "q"])
    assert "Not a valid answer" in text and "Recorded 0" in text
    assert all(d["human"] is None for d in DecisionLog(tmp_path).decisions())


def test_review_all_includes_confident_decisions(tmp_path):
    make(tmp_path, "red")
    assert run(tmp_path, "review")[1] == "Nothing to review."
    run(tmp_path, "review", "--all", replies=[""])
    assert DecisionLog(tmp_path).decisions()[0]["human"] == "red"


def test_calibration_report_after_reviews(tmp_path):
    right, wrong = make(tmp_path, "red"), make(tmp_path, "red")
    run(tmp_path, "verdict", right.decision_id, "red")
    run(tmp_path, "verdict", wrong.decision_id, "blue")
    _, text = run(tmp_path, "calibration")
    assert "rules" in text and "agreed 1/2 (50%)" in text


def test_latest_human_verdict_wins(tmp_path):
    d = make(tmp_path, "red")
    run(tmp_path, "verdict", d.decision_id, "blue")
    run(tmp_path, "verdict", d.decision_id, "red")
    assert DecisionLog(tmp_path).decisions()[0]["human"] == "red"
    assert DecisionLog(tmp_path).calibration()["rules"]["0.6-1.0"]["agree"] == 1
