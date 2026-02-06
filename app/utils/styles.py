
# MetinForge Custom Styles

SCROLLBAR_STYLESHEET = """
QScrollBar:vertical {
    border: none;
    background: #1a1a1a;
    width: 6px;
    margin: 0px 0px 0px 0px;
}
QScrollBar::handle:vertical {
    background: #5d4d2b;
    min-height: 20px;
    border-radius: 3px;
}
QScrollBar::add-line:vertical {
    height: 0px;
    subcontrol-position: bottom;
    subcontrol-origin: margin;
}
QScrollBar::sub-line:vertical {
    height: 0px;
    subcontrol-position: top;
    subcontrol-origin: margin;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

QScrollBar:horizontal {
    border: none;
    background: #1a1a1a;
    height: 6px;
    margin: 0px 0px 0px 0px;
}
QScrollBar::handle:horizontal {
    background: #5d4d2b;
    min-width: 20px;
    border-radius: 3px;
}
QScrollBar::add-line:horizontal {
    width: 0px;
    subcontrol-position: right;
    subcontrol-origin: margin;
}
QScrollBar::sub-line:horizontal {
    width: 0px;
    subcontrol-position: left;
    subcontrol-origin: margin;
}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none;
}
"""
