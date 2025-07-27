from bs4 import BeautifulSoup, Tag
from bs4.element import NavigableString, PageElement


def preprocess_text(text: str):
    """Clean plain text"""

    import re
    text = re.sub(r"\\+", " ", text)
    text = re.sub(r"\n+", "\n", text)
    text = re.sub(r"\t", " ", text)
    text = re.sub(r"\r", " ", text)
    exclude_base64 = re.compile(r"data:image/[a-zA-Z]+;base64,[^\"']+")
    text = re.sub(exclude_base64, "", text)
    re.sub(r"\s+", " ", text).strip()
    return text


def clean_html(html: str | BeautifulSoup | Tag) -> BeautifulSoup | Tag:
    """Clean html string or `BeautifulSoup` instance"""

    match html:
        case str():
            html = html.replace("<br/>", " ")
            html = html.replace("<br />", " ")
            html = html.replace("<br>", " ")
            soup = BeautifulSoup(html, "html.parser")
        case Tag():
            soup = html

    while True:
        affected = sum([
            _clean_html_tag(soup, child)
            if isinstance(child, Tag) else _clean_html_string(soup, child)
            for child in list(soup.descendants)
        ])

        if affected > 1:
            break

    return soup


def _clean_html_string(soup: Tag | BeautifulSoup, element: PageElement) -> int:
    """Clean `NavigableString` instance"""
    if not element.parent and element != soup:
        return 0

    text = element.get_text(strip=True)
    if text == "" or text == " ":
        element.extract()
        return 1

    return 0


UNUSED_ATTRS = {
    "class", "style", "id", "title", "tabindex", "role", "hidden", "aria-hidden",
    "aria-expanded", "aria-controls", "aria-label", "aria-labelledby",
    "aria-describedby", "data-toggle", "data-target", "data-dismiss", "data-parent",
    "draggable", "spellcheck", "translate", "contenteditable", "autocapitalize",
    "autocorrect", "autocomplete", "dir", "lang", "accesskey", "contextmenu", "ondrag",
    "ondragstart", "ondragend", "ondragover", "ondragleave", "ondrop", "onmouseover",
    "onmouseout", "onmouseenter", "onmouseleave", "onclick", "ondblclick",
    "onmousedown", "onmouseup", "onmousemove", "onwheel", "onkeydown", "onkeyup",
    "onkeypress", "onfocus", "onblur", "oninput", "onchange", "valign"
}

ALLOWED_ATTRS = ["colspan", "rowspan", "scope", "headers"]


def _clean_html_tag(soup: Tag | BeautifulSoup, element: Tag) -> int:
    """Clean `Tag` instance"""

    if not element.parent and element != soup:
        return 0

    if len(element.contents) == 0:
        element.extract()
        return 1

    affected = 0

    children = list(element.children)

    def test_child(child: PageElement):
        match child:
            case NavigableString():
                return True
            case Tag(name="br"):
                return True
            case _:
                return False

    only_string = all(test_child(child) for child in children)

    for attr in [*element.attrs.keys()]:
        if attr not in ALLOWED_ATTRS:
            del element[attr]

    if only_string and len(children) == 1:
        inner_text = element.get_text(strip=True)
        if inner_text == "" or inner_text == " ":
            element.extract()
            return 1

    if only_string and len(children) > 1:
        combined_text = ""
        for child in children:
            if isinstance(child, NavigableString):
                combined_text += child.get_text(strip=True)
                child.extract()
            else:
                child.insert_before(NavigableString(combined_text))
                combined_text = ""

        element.append(NavigableString(combined_text))

        affected += 1

    match element:

        case Tag(name="a", attrs={"href": str(href)}):
            if not href.startswith("#"):
                return affected
            target = soup.select_one(href)
            if not target:
                return affected
            target.extract()
            element.replace_with(target)
            return affected + 1

        case Tag(
            name="a" | "span" | "p" | "u" | "b",
            parent=Tag(name="span" | "p" | "li"),
        ):
            if element.name == "a":
                element.extract()
                return affected

            if not only_string:
                return affected

            if element.next_sibling is not None and element.name == "p":
                element.append(NavigableString(" "))

            element.unwrap()
            return affected + 1

        case Tag(name="img"):
            element.extract()
            return affected + 1

        case _ if len(children) == 0 or element.string == "":
            element.extract()
            return affected + 1

        case _:
            return affected
