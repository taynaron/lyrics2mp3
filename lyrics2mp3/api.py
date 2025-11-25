from pathlib import Path
from typing import Optional, Union

from .parsers.lyrics_az import LyricsAZ
from .parsers.lyrics_lg import LyricsLG
from .parsers.lyrics_lm import LyricsLM
from .parsers.lyrics_sl import LyricsSL


class Lyrics2MP3:
    """
    Main class for Lyrics2MP3 functionality.
    """

    def __init__(
        self,
        verbose: bool = False,
        manually_confirm: bool = False,
        write_on_not_found: bool = False,
        overwrite: bool = False,
        lg_token: Optional[str] = None,
    ):
        """
        Initialize Lyrics2MP3.

        Args:
            verbose: Enable verbose output.
            manually_confirm: Require manual confirmation for changes.
            write_on_not_found: Write '...' if no lyrics are found.
            overwrite: Overwrite existing lyrics.
            lg_token: Lyrics Genius API token. Required to use Lyrics Genius, generally the best source of lyrics.
        """
        self.verbose = verbose
        self.manually_confirm = manually_confirm
        self.write_on_not_found = write_on_not_found
        self.overwrite = overwrite

        self.have_lyrics = 0
        self.added_lyrics = 0
        self.no_lyrics_found = 0
        self.err = 0

        lyrics_args = dict(verbose=verbose, manually_confirm=manually_confirm)

        self.parsers = [
            LyricsAZ(**lyrics_args),
            LyricsLM(**lyrics_args),
            LyricsSL(**lyrics_args),
        ]

        if lg_token:
            self.parsers.insert(0, LyricsLG(lg_token, **lyrics_args))

    def get_lyrics(
        self,
        title: str,
        artist: Optional[str] = None,
        album_artist: Optional[str] = None,
    ) -> Optional[str]:
        """
        Search for lyrics using available parsers.
        """
        parsed_lyrics = None

        for parser in self.parsers:
            parsed_lyrics = parser.request(title, artist=artist)
            if parsed_lyrics:
                break

        # Fuzzy match logic
        if parsed_lyrics is None and (
            (artist and "(" in artist) or (title and "(" in title)
        ):
            if self.verbose:
                print(f"Trying {title} without parentheses")

            if album_artist:
                artist = album_artist
            elif artist and "(" in artist:
                artist = artist.split("(")[0].strip()

            if "(" in title:
                title = title.split("(")[0].strip()

            parsed_lyrics = self.get_lyrics(title, artist=artist)

        if parsed_lyrics is None and self.write_on_not_found:
            return "..."

        return parsed_lyrics

    def parse_file(
        self,
        file_path: Union[str, Path],
        ignore_artist: bool = False,
        simulate: bool = False,
    ) -> Optional[str]:
        """
        Process a single music file.
        """
        file_path = Path(file_path)
        if file_path.suffix.lower() not in (".mp3", ".m4a"):
            return None

        import taglib

        try:
            audiofile = taglib.File(str(file_path))
            old_lyrics = audiofile.tags.get("LYRICS", [""])[0]
        except OSError:
            if self.verbose:
                print(f"Could not read {file_path}, skipping")
            self.err += 1
            return

        if not self.overwrite and (
            (old_lyrics is not None and len(old_lyrics) > 10)
            or (self.write_on_not_found and old_lyrics == "...")
        ):
            if self.verbose:
                print(f"Lyrics found in music file: {file_path}, skipping")
            self.have_lyrics += 1
            return

        try:
            search_artist = None
            search_album_artist = None
            if not ignore_artist:
                search_album_artist = audiofile.tags.get("ALBUMARTIST")
                if search_album_artist:
                    search_album_artist = search_album_artist[0].lower()
                search_artist = audiofile.tags["ARTIST"][0].lower()
            search_title = audiofile.tags["TITLE"][0].lower()
        except KeyError:
            if self.verbose:
                print(f"No artist or title in music file {file_path}")
            self.err += 1
            return

        lyrics = self.get_lyrics(
            title=search_title, artist=search_artist, album_artist=search_album_artist
        )

        artist_str = f"{search_artist}: " if search_artist else ""

        if lyrics is not None:
            self.added_lyrics += 1
            if self.verbose:
                print(f"Lyrics found for {artist_str}{search_title}")
            if simulate:
                print("Simulating, not actually saving lyrics")
                return lyrics

            audiofile.tags["LYRICS"] = lyrics
            audiofile.save()
        else:
            self.no_lyrics_found += 1
            if self.verbose:
                print(f"No lyrics found for {artist_str}{search_title}")

    def get_lyrics_from_dir(
        self,
        directory_path: Union[str, Path],
        ignore_artist: bool = False,
        simulate: bool = False,
    ):
        """
        Process all music files in a directory recursively.
        """
        directory_path = Path(directory_path)
        if not directory_path.is_dir():
            raise NotADirectoryError(f'Directory "{directory_path}" not found.')

        for file_path in directory_path.rglob("*"):
            if file_path.is_file():
                self.file_lyrics(
                    file_path,
                    ignore_artist=ignore_artist,
                    simulate=simulate,
                )

    def get_lyrics_from_m3u(
        self,
        m3u_path: Union[str, Path],
        ignore_artist: bool = False,
        simulate: bool = False,
    ):
        """
        Process music files listed in an M3U playlist.
        """
        m3u_path = Path(m3u_path)
        if not m3u_path.is_file():
            raise FileNotFoundError(f'File "{m3u_path}" not found.')

        if m3u_path.suffix.lower() != ".m3u":
            raise ValueError(f'Playlist "{m3u_path}" is not M3U format.')

        with m3u_path.open("r", encoding="utf-8", errors="ignore") as m:
            for line in m:
                line = line.strip()
                if not line or line.upper().startswith("#EXT"):
                    continue

                self.file_lyrics(line, ignore_artist=ignore_artist, simulate=simulate)

    def file_lyrics(
        self,
        file_path: Union[str, Path],
        ignore_artist: bool = False,
        simulate: bool = False,
    ):
        """
        Wrapper around parse_file that also reports progress.
        """
        self.parse_file(file_path, ignore_artist=ignore_artist, simulate=simulate)
        if not self.verbose:
            self.report_progress(inline=True)

    def report_progress(self, inline: bool = False):
        l_sum = self.have_lyrics + self.added_lyrics + self.no_lyrics_found + self.err
        txt = f"{self.added_lyrics} added, {self.no_lyrics_found} not found, {self.err} errored."
        if not self.overwrite:
            txt = f"{self.have_lyrics} existing, {txt}"

        txt = f"{l_sum} processed: {txt}"
        if inline:
            print(f"\r{txt}", end="")
        else:
            print(txt)

    def print_summary(self):
        if self.verbose:
            self.report_progress()
        print()
