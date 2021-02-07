import re
import requests
from bs4 import BeautifulSoup


class ValidationError(Exception):
    pass


cruft = re.compile("[\.,\[\]\{\}'’]")
and_ = re.compile("[\+&]")


def _clean_str(in_str):
    return and_.sub("and", cruft.sub("", in_str.lower()))


class Lyrics:
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Windows x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/62.0.3239.84 Safari/537.36"
    }

    def __init__(self, service, verbose=False):
        self.service = service
        self.verbose = verbose

    def raw_request(self, url):
        resp = requests.get(
            url=url,
            headers=Lyrics.headers,
        )
        return resp

    def parse_html(self, href):
        resp = self.raw_request(href)
        soup = BeautifulSoup(resp.text, "html.parser")
        return soup

    def parse_single_song(self, href):
        raise ValidationError("Need to implement")

    def validate_parse_song(self, href, title):
        if self.verbose > 1:
            print(f"{self.service} href: {href}")

        try:
            parsed_lyrics = self.parse_single_song(href)
        except Exception as e:
            if self.verbose > 1:
                print(f'Could not parse lyrics from {self.service} for "{title}": ', e)
            return None
        return parsed_lyrics

    def _validate_error(self, kind, file, found):
        c_file = _clean_str(file)
        c_found = _clean_str(found)
        if not (c_found in c_file or c_file in c_found):
            msg = f"Incorrect {kind} from {self.service}: {file} vs {found}"
            if self.verbose > 1:
                print(msg)
            raise ValidationError(msg)

    def validate_artist(self, artist, found_artist):
        return self._validate_error("artist", artist, found_artist)

    def validate_title(self, title, found_title):
        return self._validate_error("title", title, found_title)

    def validate_lyrics_found(self, lyrics, title):
        if lyrics is None:
            msg = f'Lyrics not found on {self.service} for "{title}"'
            if self.verbose > 1:
                print(msg)
            raise ValidationError(msg)

    def request(self, url, artist, title):
        soup = self.parse_html(url)
        try:
            parsed_lyrics = self.parse(soup, artist=artist, title=title)
        except ValidationError:
            return None

        if parsed_lyrics and self.verbose:
            print(f'Parsed lyrics from {self.service} for "{title}"')
        elif not parsed_lyrics and self.verbose > 1:
            print(f'Could not parse lyrics from {self.service} for "{title}": ')

        return parsed_lyrics
