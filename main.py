import json

import config
import func
from func import get_request, compile_message, get_hotpool_violations, get_track_slugs, get_tracks_scores


def main():
    func.check_and_renew_token()

    get_hotpool_violations()

if __name__ == "__main__":
    main()
