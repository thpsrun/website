import datetime
import os

import markdown
from django.db.models import Q
from django.shortcuts import redirect, render
from django.utils import timezone
from srl.models import Games, Players

from .youtube_shortcode import YTEmbedProcessor

DOCS_PATH = "/srlc/docs/"


def parse_md_file(file_path):
    title   = os.path.basename(file_path).replace(".md", "").replace("_", " ").title()
    author  = None
    content = []

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        if "title:" in line.lower().replace("**", ""):
            title = line.split(":", 1)[1].strip()
        elif "website tags:" in line.lower().replace("**", ""):
            continue
        elif "created by:" in line.lower().replace("**", ""):
            author = line.split(":", 1)[1].strip()
        elif "discovered by:" in line.lower().replace("**", ""):
            author = line.split(":", 1)[1].strip()
        else:
            content.append(line)

    content_output = "".join(content)
    return title, author, content_output


def render_guides_list(request, game):
    folder = os.path.join(DOCS_PATH, game)

    if not os.path.isdir(folder):
        raise redirect("/")

    guides = []

    for filename in sorted(os.listdir(folder)):
        if filename.endswith(".md"):
            file_path = os.path.join(folder, filename)
            doc_title, doc_author, _ = parse_md_file(file_path)

            player_get = (
                Players.objects.only("name", "nickname")
                .filter(Q(name__iexact=doc_author) | Q(nickname__iexact=doc_author))
                .first()
            )

            last_modified = (
                timezone.make_aware(datetime.datetime.fromtimestamp(os.path.getmtime(file_path)))
            )

            guides.append({
                "title"     : doc_title,
                "author"    : player_get if player_get else doc_author,
                "url"       : (f"/docs/{game}/{filename}").replace(".md", ""),
                "last_mod"  : last_modified,
            })

    guides.sort(key=lambda x: x["title"].lower())

    game_get = Games.objects.filter(slug=game).first()

    return render(request, "guides/docs_list.html", {
        "game"      : game.upper(),
        "game_name" : game_get.name if game_get else None,
        "guides"    : guides
    })


def render_markdown(request, game, doc):
    folder = os.path.join(DOCS_PATH, game)
    file_path = os.path.join(folder, doc + ".md")

    if not os.path.exists(file_path) or ".github" in file_path:
        return redirect("/")

    doc_title, _ , md_content = parse_md_file(file_path)

    html = markdown.markdown(
        md_content,
        extensions=["markdown.extensions.extra", YTEmbedProcessor()]
    )

    return render(request, "guides/docs.html", {
        "doc_game"      : game.upper(),
        "doc_title"     : doc_title,
        "doc_content"   : html,
    })
