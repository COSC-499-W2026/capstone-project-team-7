"""Which clip a round plays: the teacher's chosen clip, or the default clip."""

from utils.audio_storage import audio_path, clip_path


def resolve_clip_path(location):
    """The round's chosen clip while it is live and its file exists; otherwise the default clip."""
    if location.get("clip_id") and location.get("clip_retired_at") is None:
        chosen = clip_path(location["clip_language_code"], location["clip_id"])
        if chosen.is_file():
            return chosen
    return audio_path(location["language_code"], location, location["difficulty"])
