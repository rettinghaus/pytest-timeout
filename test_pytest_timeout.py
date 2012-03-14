import os
import os.path
import signal
import threading

import pytest


pytest_plugins = 'pytester'


# This is required since our tests run py.test in a temporary
# directory and that py.test process needs to find the pytest_timeout
# module on it's sys.path.
os.environ['PYTHONPATH'] = os.path.dirname(__file__)


have_sigalrm = pytest.mark.skipif('not hasattr(signal, "SIGALRM")')


def pytest_funcarg__testdir(request):
    """pytester testdir funcarg with pytest_timeout in the plugins

    This has the effect of adding "-p pytest_timeout" to the py.test
    call of .runpytest() which is required for the --timeout parameter
    to work.
    """
    testdir = request.getfuncargvalue('testdir')
    testdir.plugins.append('pytest_timeout')
    return testdir


@have_sigalrm
def test_sigalrm(testdir):
    testdir.makepyfile("""
        import time

        def test_foo():
            time.sleep(2)
     """)
    result = testdir.runpytest('--timeout=1')
    result.stdout.fnmatch_lines([
            '*Failed: Timeout >1s*'
            ])


def test_thread(testdir):
    testdir.makepyfile("""
        import time

        def test_foo():
            time.sleep(2)
    """)
    result = testdir.runpytest('--timeout=1', '--timeout_method=thread')
    result.stderr.fnmatch_lines([
            '*++ Timeout ++*',
            '*~~ Stack of MainThread* ~~*',
            '*File *, line *, in *',
            '*++ Timeout ++*',
            ])
    assert '++ Timeout ++' in result.stderr.lines[-1]


@have_sigalrm
def test_timeout_mark_sigalrm(testdir):
    testdir.makepyfile("""
        import time, pytest

        @pytest.mark.timeout(1)
        def test_foo():
            time.sleep(2)
            assert False
    """)
    result = testdir.runpytest('--timeout=0')
    result.stdout.fnmatch_lines(['*Failed: Timeout >1s*'])


def test_timeout_mark_timer(testdir):
    testdir.makepyfile("""
        import time, pytest

        @pytest.mark.timeout(1)
        def test_foo():
            time.sleep(2)
    """)
    result = testdir.runpytest('--timeout=0', '--timeout_method=thread')
    result.stderr.fnmatch_lines(['*++ Timeout ++*'])


def test_timeout_mark_nonint(testdir):
    testdir.makepyfile("""
        import pytest

        @pytest.mark.timeout('foo')
        def test_foo():
            pass
   """)
    result = testdir.runpytest('--timeout=0')
    result.stdout.fnmatch_lines(['*ValueError*'])


def test_timeout_mark_args(testdir):
    testdir.makepyfile("""
        import pytest

        @pytest.mark.timeout(1, 2)
        def test_foo():
            pass
    """)
    result = testdir.runpytest('--timeout=0')
    result.stdout.fnmatch_lines(['*TypeError*'])


def test_timeout_mark_noargs(testdir):
    testdir.makepyfile("""
        import pytest

        @pytest.mark.timeout
        def test_foo():
            pass
    """)
    result = testdir.runpytest('--timeout=0')
    result.stdout.fnmatch_lines(['*TypeError*'])


def test_ini_timeout(testdir):
    testdir.makepyfile("""
        import time

        def test_foo():
            time.sleep(2)
    """)
    testdir.makeini("""
        [pytest]
        timeout = 1
    """)
    result = testdir.runpytest()
    assert result.ret


def test_ini_method(testdir):
    testdir.makepyfile("""
        import time

        def test_foo():
            time.sleep(2)
    """)
    testdir.makeini("""
        [pytest]
        timeout = 1
        timeout_method = thread
    """)
    result = testdir.runpytest()
    assert '=== 1 failed in ' not in result.outlines[-1]
