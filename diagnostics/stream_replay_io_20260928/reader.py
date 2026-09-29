"""Bounded-memory initial-state extraction with full raw-byte verification."""
from pathlib import Path
import codecs
import gzip
import hashlib
import json


class JsonStream:
    def __init__(self, stream, chunk_size=65536, max_buffer=16 * 1024 * 1024):
        self.stream = stream
        self.chunk_size = chunk_size
        self.max_buffer = max_buffer
        self.decoder = codecs.getincrementaldecoder('utf-8')()
        self.json_decoder = json.JSONDecoder()
        self.digest = hashlib.sha256()
        self.buffer = ''
        self.eof = False
        self.peak_buffer = 0

    def fill(self):
        if self.eof:
            return False
        raw = self.stream.read(self.chunk_size)
        self.digest.update(raw)
        self.eof = not raw
        self.buffer += self.decoder.decode(raw, final=self.eof)
        self.peak_buffer = max(self.peak_buffer, len(self.buffer))
        if len(self.buffer) > self.max_buffer:
            raise ValueError('Replay JSON value exceeds bounded input buffer')
        return bool(raw)

    def whitespace(self):
        while True:
            self.buffer = self.buffer.lstrip(' \t\r\n')
            if self.buffer or self.eof:
                return
            self.fill()

    def peek(self):
        self.whitespace()
        return self.buffer[:1]

    def expect(self, value):
        if self.peek() != value:
            raise ValueError('Expected JSON punctuation ' + repr(value))
        self.buffer = self.buffer[1:]

    def value(self):
        self.whitespace()
        while True:
            try:
                result, end = self.json_decoder.raw_decode(self.buffer)
            except json.JSONDecodeError:
                if self.eof:
                    raise
                self.fill()
                continue
            # An unclosed numeric token can otherwise be accepted at a
            # chunk boundary, e.g. the first digit of a longer number.
            if end == len(self.buffer) and not self.eof:
                self.fill()
                continue
            if end < len(self.buffer) and self.buffer[end] not in ' \t\r\n,:]}':
                if not self.eof:
                    self.fill()
                    continue
                raise ValueError('Invalid character after JSON value')
            self.buffer = self.buffer[end:]
            return result


def read_initial(stream, expected_sha256=None, chunk_size=65536):
    reader = JsonStream(stream, chunk_size=chunk_size)
    reader.expect('{')
    seen = set()
    config = initial = None
    frames = 0
    while reader.peek() != '}':
        key = reader.value()
        if not isinstance(key, str) or key in seen:
            raise ValueError('Replay root keys must be unique strings')
        seen.add(key)
        reader.expect(':')
        if key == 'steps':
            reader.expect('[')
            while reader.peek() != ']':
                frame = reader.value()
                if not isinstance(frame, list) or len(frame) != 2:
                    raise ValueError('Expected a two-player replay frame')
                if frames == 0:
                    initial = frame
                frames += 1
                del frame
                if reader.peek() != ']':
                    reader.expect(',')
                    if reader.peek() == ']':
                        raise ValueError('Trailing comma in replay steps')
            reader.expect(']')
        else:
            value = reader.value()
            if key == 'configuration':
                config = value
            del value
        if reader.peek() != '}':
            reader.expect(',')
            if reader.peek() == '}':
                raise ValueError('Trailing comma in replay root')
    reader.expect('}')
    if reader.peek():
        raise ValueError('Trailing data after replay JSON')
    raw_sha = reader.digest.hexdigest()
    if expected_sha256 is not None and raw_sha != expected_sha256:
        raise ValueError('Decompressed replay SHA-256 mismatch')
    if not isinstance(config, dict) or initial is None:
        raise ValueError('Missing replay configuration or initial frame')
    if frames != config.get('episodeSteps'):
        raise ValueError('Replay frame count differs from episodeSteps')
    return dict(configuration=config, initial_frame=initial, frame_count=frames,
                source_replay_sha256=raw_sha, peak_buffer_characters=reader.peak_buffer)


def load_initial(path, expected_sha256, chunk_size=65536):
    with gzip.open(Path(path), 'rb') as stream:
        return read_initial(stream, expected_sha256, chunk_size)
