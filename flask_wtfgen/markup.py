from markupsafe import Markup

def xmlattrs(attrs):
    res = Markup(" ").join(
        Markup('{0}="{1}"').format(k, v) 
        for k, v in attrs.items()
        if v != None
    )
    if res != '':
        return " " + res
    else:
        return ""

def xmltag(name, attrs):
    return Markup("<{0}{1}>").format(name, xmlattrs(attrs))

def element(name, attrs, contents):
    return Markup("{0}{1}</{2}>").format(xmltag(name, attrs),
                                         contents,
                                         name)

def button(text, classes="", context_class="default", size=None, attrs={}, type="button"):
    cls = "btn btn-"+context_class
    if size:
        cls += " btn-" + size
    a = {"class": cls + " " + classes, 
         "type": type}
    a.update(attrs)
    return element("button", 
                   a,
                   text)

def link_button(url, text, context_class="default", size=None, hint=None, link_target=None):
    cls = "btn btn-"+context_class
    if size:
        cls += " btn-" + size
    return element("a", 
                   {"class": cls, "role": "button", "href": url, "title": hint, "target": link_target},
                   text)

def form_button(url, text, classes="", context_class="default", size=None, attrs={}):
    return element("form",
                   {"method": "POST",
                    "action": url},
                   button(text, classes=classes, context_class=context_class,
                          size=size, attrs=attrs, type="submit"))

class GridColumn(object):
    __slots__ = ["widths"]
    def __init__(self, width=3, **widths):
        if not widths:
            widths = {"md": width}
            
        self.widths = widths

    def get_class(self):
        return " ".join(["col-{}-{}".format(k, v)
                         for k, v in self.widths.items()])
        
    def render(self, content):
        return element("div", {"class": self.get_class()}, content)
