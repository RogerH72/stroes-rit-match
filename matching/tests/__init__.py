import logging

# The tests deliberately exercise the warning and error paths of the detection
# and import code, so the app's own INFO/WARNING output would drown out the test
# results. Quiet it here rather than in settings, which the container relies on.
logging.getLogger("matching").setLevel(logging.CRITICAL)
