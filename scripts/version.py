from pdm.backend.hooks.version import SCMVersion

def format_version(v: SCMVersion) -> str:
    if v.distance is None:
        return str(v.version)          # on tag: 1.2.3
    return f"{v.version}.dev{v.distance}"  # between tags: 1.2.3.devN