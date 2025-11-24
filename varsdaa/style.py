from iommi import Asset
from iommi import Style
from iommi.style_bootstrap5 import bootstrap5

varsdaa_style = Style(
    bootstrap5,
    base_template="iommi/base.html",
    root__assets=dict(
        my_project_custom_css=Asset.css(attrs__href="/static/css/project.css"),
        my_project_custom_js=Asset.js(attrs__src="/static/js/project.js"),
    ),
    Menu=dict(
        tag="nav",
        attrs__class={
            "navbar-dark": False,
            "navbar-light": True,
            "bg-light": True,
        },
    ),
)
