from pipeline.shot_taxonomy import classify_action_type


def test_classify_forehand_winner():
    assert classify_action_type("FOREHAND WINNER") == "forehand"
    assert classify_action_type("WINNER") == "unknown"


def test_classify_volley():
    assert classify_action_type("BACKHAND VOLLEY WINNER") == "volley"
