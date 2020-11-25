from typing import Dict, List, Generator

from segment import Segment
from youtube_video import YoutubeVideo


class SimpleSegmentizer:
    """Able to segmentize a YoutubeVideo on a simply split of n_parts.
    A segment is a subset of a transcript."""

    def __init__(self, youtube_video: YoutubeVideo, n_parts=10):
        self.youtube_video = youtube_video
        self.n_parts = n_parts

    def _split(self) -> List[float]:
        # to get n_parts, we need n_parts + 1 time stamps
        n_parts = self.n_parts + 1
        part_duration = self.youtube_video.duration / n_parts
        parts = []
        for i in range(n_parts):
            if i == 0:
                parts.append(0.0)
            else:
                parts.append(round(parts[i - 1] + part_duration, 2))
        return parts

    def _get_segment_indices(self) -> List[Dict]:
        """Create [n_parts] segment indices with the start- and end index given for each segment.

        Returns:
            List[Dict]: List of segment dicts in the form of
                [{"segment_number": 1, "start_time": 150.8}]
        """
        segments = []
        approximate_splits = self._split()

        def get_closest_segment(
            index: int,
            approximate_split: float,
            transcript: List[Dict],
        ):
            """Find, in transcript, the closest segment to the approximate split."""
            segment = {"segment_number": index}
            if index == 0:
                segment["starts_at_index"] = 0
                return segment
            smallest_delta = float("inf")
            for transcript_index, transcript_item in enumerate(transcript):
                current_delta = abs(approximate_split - transcript_item["start"])
                if current_delta < smallest_delta:
                    smallest_delta = current_delta
                else:
                    # Take previous transcript item that had the smallest delta
                    segment["starts_at_index"] = transcript_index
                    return segment

        def add_ends_at(segments, transcript):
            for i, segment in enumerate(segments):
                if i == len(segments) - 1:
                    segment["ends_at_index"] = len(transcript)
                else:
                    segment["ends_at_index"] = segments[i + 1]["starts_at_index"]
            return segments

        for index, approximate_split in enumerate(approximate_splits):
            transcript = self.youtube_video.transcript
            segment = get_closest_segment(index, approximate_split, transcript)
            segments.append(segment)

        segments = add_ends_at(segments, transcript)
        return segments

    def generate_segments(self) -> Generator[Segment, None, None]:
        segment_indices = self._get_segment_indices()
        for segment_index in segment_indices:
            start = segment_index["starts_at_index"]
            end = segment_index["ends_at_index"]
            body = self.youtube_video.transcript[start:end]
            yield Segment(body)
