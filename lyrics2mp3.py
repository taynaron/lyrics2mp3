import argparse

from lyrics2mp3.api import Lyrics2MP3

"""
Lyrics2mp3
1. Scans directory or playlist for music files.
2. Searches lyrics for each song on azlyrics.com
3. If 'write_on_not_found', inserts lyrics into music file, or '...' if not found
"""


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(
        description="lyrics2mp3: Find lyrics and add them into music files"
    )

    file_source = parser.add_mutually_exclusive_group(required=True)
    file_source.add_argument(
        "--dir", dest="directory", help="Directory to search for music files"
    )
    file_source.add_argument("--m3u", help="Playlist to search for music files")

    parser.add_argument(
        "--genius_token",
        help="API token for genius.com music database. Without this token Genius will not be used. Sign up for token at https://genius.com/api-clients",
    )
    parser.add_argument(
        "--write_on_not_found",
        action="store_true",
        help="Write '...' on files with no lyrics found.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing lyrics in music files",
    )
    parser.add_argument(
        "--ignore_artist",
        action="store_true",
        help="Ignore files' artists, look at song name only",
    )
    parser.add_argument(
        "--manually_confirm",
        action="store_true",
        help="Manually confirm any lyrics changes",
    )
    parser.add_argument(
        "--simulate",
        "-s",
        action="store_true",
        help="Simulate retrieval but change no files",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="Level of debug info to display",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    l2m = Lyrics2MP3(
        verbose=args.verbose,
        manually_confirm=args.manually_confirm,
        write_on_not_found=args.write_on_not_found,
        overwrite=args.overwrite,
        lg_token=args.genius_token,
    )

    try:
        if args.directory:
            l2m.get_lyrics_from_dir(
                args.directory, ignore_artist=args.ignore_artist, simulate=args.simulate
            )

        elif args.m3u:
            l2m.get_lyrics_from_m3u(
                args.m3u, ignore_artist=args.ignore_artist, simulate=args.simulate
            )

    except KeyboardInterrupt:
        print("\nInterrupted by user.")

    l2m.print_summary()


if __name__ == "__main__":
    main()
