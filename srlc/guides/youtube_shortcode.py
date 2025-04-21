import re
from xml.etree.ElementTree import Element

from markdown.extensions import Extension
from markdown.inlinepatterns import InlineProcessor

YOUTUBE_RE = (
    r"\[youtube(?:\s+align=(center|left|right))?(?:\s+width=(\d+))?"
    r"(?:\s+height=(\d+))?\](.*?)\[/youtube\]"
)

YOUTUBE_URL_RE = (
    re.compile(r"(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([\w-]{11})")
)


class YTInlineProcessor(InlineProcessor):
    """Custom processor class that turns the [youtube] tag in .MD into embedded YouTube videos."""
    def handleMatch(self, m, data):
        align = m.group(1) or "center"
        width = m.group(2) or "560"
        height = m.group(3) or "315"
        raw_video = m.group(4).strip()

        match = YOUTUBE_URL_RE.match(raw_video)
        video_id = match.group(1) if match else raw_video

        wrapper = Element("div")
        wrapper.set("class", f"youtube-embed align-{align}")

        iframe = Element("iframe")
        iframe.set("width", width)
        iframe.set("height", height)
        iframe.set("src", f"https://www.youtube.com/embed/{video_id}")
        iframe.set("frameborder", "0")
        iframe.set(
            "allow", "accelerometer; autoplay;"
            "clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        )
        iframe.set("allowfullscreen", "true")

        wrapper.append(iframe)
        return wrapper, m.start(0), m.end(0)


class YTEmbedProcessor(Extension):
    """Processor for the [youtube] tag in .MD files."""
    def extendMarkdown(self, md):
        md.inlinePatterns.register(YTInlineProcessor(YOUTUBE_RE, md), "youtube_shortcode", 175)
