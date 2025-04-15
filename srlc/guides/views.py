import os

import markdown
from django.shortcuts import redirect, render

from .youtube_shortcode import YTEmbedProcessor

#DOCS_PATH = os.path.join(os.path.dirname(__file__), "docs/")
DOCS_PATH = "/srlc/docs/"

def render_markdown(request,game,doc):
    folder = os.path.join(DOCS_PATH,game)
    file_path = os.path.join(folder,doc+".md")

    if not os.path.exists(file_path) or ".github" in file_path:
        return redirect("/")

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    doc_title = doc.replace(".md", "").replace("_", " ").title()

    if lines and "Title" in lines[0]:
        doc_title = lines[0].split(":",1)[1].strip()
        md_content = "".join(lines[2:])
    else:
        md_content = "".join(lines)

    html = markdown.markdown(
        md_content,
        extensions=["markdown.extensions.extra", YTEmbedProcessor()]
    )

    return render(request, "guides/docs.html", {
        "doc_game"     : game.upper(),
        "doc_title"    : doc_title,
        "doc_content"  : html,
    })