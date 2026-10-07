# ------------------------------------------------------------------
# JSON utils
# ------------------------------------------------------------------


# ------------------------------------------------------------------
# Serialization
# ------------------------------------------------------------------

# Convert an object into a dictionary, keeping None as None
def objectToDict(object):
    if object is None:
        return None
    return object.toDict()