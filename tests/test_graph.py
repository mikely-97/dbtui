from dbt_tui.backend import DbtProject, DbtModelNotFoundException
from pytest import LogCaptureFixture, raises
from logging import WARNING

def test_multiple_args_in_ref(caplog: LogCaptureFixture):
    with caplog.at_level(WARNING):
        DbtProject('tests/testing')
        assert "Invalid number of args to ref() in model i_c2: should be one, but it's 2: ['i_b', 'extra_argument']" in caplog.text
    
def test_no_args_in_ref(caplog: LogCaptureFixture):
    with caplog.at_level(WARNING):
        DbtProject('tests/testing')
        assert "Invalid number of args to ref() in model i_c2: should be one, but it's 0: []" in caplog.text
    
def test_ref_to_nonexistent(caplog: LogCaptureFixture):
    with caplog.at_level(WARNING):
        DbtProject('tests/testing')
        assert "i_c1 references 'i_b_not_exists' which is not found as a name" in caplog.text
    
def test_graph_repr():
    target = """(c_b) --> (c_c1)
(c_b) --> (c_c2)
(c_c1) --> (c_d)
(c_c2) --> (c_d)
(c_changed_name) --> (c_b)
(i_a) --> (i_b_changed)
(i_c1) --> (i_d)
(i_c2) --> (i_d)
(v_a) --> (v_b)
(v_b) --> (v_c1)
(v_b) --> (v_c2)
(v_c1) --> (v_d)
(v_c2) --> (v_d)"""
    assert DbtProject('tests/testing').graph_repr() == target

    
